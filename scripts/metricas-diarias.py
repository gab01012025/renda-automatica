#!/usr/bin/env python3
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "scripts" / "relatorios"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

YT_UP = ROOT / "youtube-faceless" / "_uploaded.json"
TT_UP = ROOT / "tiktok-auto" / "_uploaded.json"
GUM_UP = ROOT / "produtos-digitais" / "_uploaded.json"


def norm_key(text):
    return " ".join((text or "").strip().lower().split())


def load_env_files():
    for envf in [ROOT / "produtos-digitais" / ".env", ROOT / ".env"]:
        if not envf.exists():
            continue
        for raw in envf.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def parse_ts(text):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(text, fmt)
        except Exception:
            pass
    return None


def load_json(path, key):
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text()).get(key, [])
    except Exception:
        return []


def count_recent(items, hours=24):
    cutoff = datetime.now() - timedelta(hours=hours)
    total = 0
    for it in items:
        ts = parse_ts(it.get("ts", ""))
        if ts and ts >= cutoff:
            total += 1
    return total


def fetch_gumroad_sales(token):
    sales = []
    page = 1
    while page <= 10:
        q = urllib.parse.urlencode({"access_token": token, "page": page})
        url = f"https://api.gumroad.com/v2/sales?{q}"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.loads(r.read())
            batch = data.get("sales", [])
            if not batch:
                break
            sales.extend(batch)
            page += 1
        except Exception:
            break
    return sales


def gumroad_metrics():
    token = os.environ.get("GUMROAD_ACCESS_TOKEN") or os.environ.get("GUMROAD_API_KEY")
    products = load_json(GUM_UP, "products")

    # Build aliases so we can match sales to configured product IDs/slugs.
    aliases = {}
    for p in products:
        pid = p.get("id", "")
        name = p.get("nome", "")
        url = p.get("url", "")
        keys = [pid, name]
        if isinstance(url, str) and "/products/" in url:
            try:
                slug = url.split("/products/")[1].split("/")[0]
                keys.append(slug)
            except Exception:
                pass
        for k in keys:
            nk = norm_key(k)
            if nk and pid:
                aliases[nk] = pid

    out = {
        "enabled": bool(token),
        "sales_24h": 0,
        "revenue_24h_eur": 0.0,
        "by_product": {},
        "aliases": aliases,
    }
    if not token:
        return out

    cutoff = datetime.utcnow() - timedelta(hours=24)
    sales = fetch_gumroad_sales(token)
    for s in sales:
        created = parse_ts((s.get("created_at") or "").replace("Z", ""))
        if not created or created < cutoff:
            continue
        out["sales_24h"] += 1

        # Gumroad price fields vary by account/currency.
        cents = s.get("price") or s.get("amount_cents") or 0
        currency = (s.get("currency") or "").lower()
        if isinstance(cents, str):
            try:
                cents = int(cents)
            except Exception:
                cents = 0
        if currency == "eur":
            out["revenue_24h_eur"] += float(cents) / 100.0

        sale_name = s.get("product_name") or s.get("product_permalink") or "unknown"
        sale_permalink = s.get("product_permalink") or ""
        candidates = [sale_name, sale_permalink]
        pid = None
        for c in candidates:
            pid = aliases.get(norm_key(c))
            if pid:
                break
        key = pid or sale_name

        row = out["by_product"].setdefault(key, {"sales": 0, "revenue_eur": 0.0})
        row["sales"] += 1
        if currency == "eur":
            row["revenue_eur"] += float(cents) / 100.0

    out["revenue_24h_eur"] = round(out["revenue_24h_eur"], 2)
    for _, row in out["by_product"].items():
        row["revenue_eur"] = round(row["revenue_eur"], 2)
    return out


def bitly_clicks_metrics():
    token = os.environ.get("BITLY_TOKEN")
    mapping_raw = os.environ.get("BITLY_LINKS_JSON", "")
    out = {"enabled": bool(token and mapping_raw), "total_clicks_24h": None, "by_product": {}}
    if not token or not mapping_raw:
        return out

    try:
        mapping = json.loads(mapping_raw)
    except Exception:
        return out

    total = 0
    for product_id, bitlink in mapping.items():
        key = bitlink.replace("https://", "").replace("http://", "")
        url = f"https://api-ssl.bitly.com/v4/bitlinks/{urllib.parse.quote(key, safe='')}/clicks/summary?unit=day&units=1"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        clicks = None
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
            clicks = int(data.get("total_clicks", 0))
            total += clicks
        except Exception:
            clicks = None
        out["by_product"][norm_key(product_id)] = clicks

    out["total_clicks_24h"] = total
    return out


def main():
    load_env_files()

    yt = load_json(YT_UP, "videos")
    tt = load_json(TT_UP, "videos")
    gum = gumroad_metrics()
    clicks = bitly_clicks_metrics()

    conversions = {"enabled": bool(gum.get("enabled") and clicks.get("enabled")), "by_product": {}, "overall": None}
    if conversions["enabled"]:
        total_sales = gum.get("sales_24h", 0)
        total_clicks = clicks.get("total_clicks_24h") or 0
        if total_clicks > 0:
            conversions["overall"] = round((total_sales / total_clicks) * 100.0, 2)
        for product, row in gum.get("by_product", {}).items():
            c = clicks.get("by_product", {}).get(norm_key(product))
            if c and c > 0:
                conversions["by_product"][product] = round((row["sales"] / c) * 100.0, 2)
            else:
                conversions["by_product"][product] = None

    now = datetime.now()
    report = {
        "generated_at": now.isoformat(),
        "traffic": {
            "youtube_uploads_24h": count_recent(yt, 24),
            "youtube_uploads_48h": count_recent(yt, 48),
            "tiktok_uploads_24h": count_recent(tt, 24),
            "tiktok_uploads_48h": count_recent(tt, 48),
        },
        "cliques": clicks,
        "conversao": conversions,
        "receita": gum,
        "notes": [
            "Para cliques/conversão por produto automáticos, configure BITLY_TOKEN e BITLY_LINKS_JSON no .env.",
            "Para receita automática, configure GUMROAD_ACCESS_TOKEN no .env.",
        ],
    }

    dated = REPORT_DIR / f"metricas-{now.strftime('%Y-%m-%d')}.json"
    latest = REPORT_DIR / "metricas-latest.json"
    dated.write_text(json.dumps(report, ensure_ascii=False, indent=2))
    latest.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"✅ Relatório diário: {dated}")
    print(f"📌 Latest: {latest}")
    print(json.dumps({
        "youtube_24h": report["traffic"]["youtube_uploads_24h"],
        "tiktok_24h": report["traffic"]["tiktok_uploads_24h"],
        "sales_24h": report["receita"]["sales_24h"],
        "revenue_24h_eur": report["receita"]["revenue_24h_eur"],
        "clicks_24h": report["cliques"]["total_clicks_24h"],
        "conversion_overall_pct": report["conversao"]["overall"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
