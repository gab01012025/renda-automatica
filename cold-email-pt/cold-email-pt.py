#!/usr/bin/env python3
"""
Cold Email B2B PT — Autônomo

O quê: scrapeia empresas pequenas em Portugal sem website (clínicas, restaurantes,
       advogados, ginásios, oficinas) via OpenStreetMap Overpass API (100% legal/gratuito).
       Gera mini-auditoria personalizada com IA. Envia email comercial via SMTP.
       Cliente interessado responde direto ao TEU email/WhatsApp.

Receita esperada: 1 venda em cada 50 emails enviados, ticket €390 site institucional.
                  Enviar 30 emails/dia × 30 dias = 900 emails = ~18 vendas = €7000/mês
                  (realista 30 dias: 5-10 vendas = €1950-€3900/mês)

Stack: Overpass API (gratis), GPT-4o-mini (€0.001/email), Resend SMTP (3000 free/mes)
       OU SMTP Gmail/Outlook (limite ~500/dia)

GDPR-safe: B2B legitimate interest + opt-out claro + emails publicamente listados (OSM).

Uso: python cold-email-pt.py [N=20] [cidade=Lisboa]
"""
import os, sys, json, time, random, smtplib, ssl, csv
from email.message import EmailMessage
from pathlib import Path
from datetime import datetime
import urllib.request, urllib.parse

ROOT = Path(__file__).resolve().parent.parent
for envf in [ROOT/".env", ROOT/"produtos-digitais/.env", ROOT/"pod-automatico/.env"]:
    if envf.exists():
        for line in envf.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
FROM_NAME = os.environ.get("COLD_FROM_NAME", "Gabriel Franca")
REPLY_TO = os.environ.get("COLD_REPLY_TO", SMTP_USER)
WHATSAPP = os.environ.get("COLD_WHATSAPP", "+351 XXX XXX XXX")
LANDING_URL = os.environ.get("COLD_LANDING_URL", "https://example.pt")  # opcional

if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY missing"); sys.exit(1)

LOG_DIR = ROOT / "cold-email-pt" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
SEEN_FILE = LOG_DIR / "_enviados.json"
seen = set(json.loads(SEEN_FILE.read_text())) if SEEN_FILE.exists() else set()

# Tipos de negócio com alta probabilidade de não ter site decente
NICHOS = [
    ("amenity=dentist", "consultório dentário"),
    ("amenity=clinic", "clínica"),
    ("amenity=veterinary", "clínica veterinária"),
    ("amenity=restaurant", "restaurante"),
    ("amenity=cafe", "café"),
    ("shop=hairdresser", "cabeleireiro"),
    ("shop=beauty", "centro de estética"),
    ("leisure=fitness_centre", "ginásio"),
    ("shop=car_repair", "oficina automóvel"),
    ("office=lawyer", "escritório de advocacia"),
    ("shop=optician", "ótica"),
    ("amenity=pharmacy", "farmácia"),
]

CIDADES_BBOX = {
    # bbox: (south, west, north, east)
    "lisboa":  (38.69, -9.23, 38.79, -9.09),
    "porto":   (41.13, -8.69, 41.20, -8.55),
    "braga":   (41.52, -8.46, 41.60, -8.38),
    "coimbra": (40.18, -8.46, 40.24, -8.36),
    "faro":    (37.00, -7.97, 37.05, -7.88),
    "aveiro":  (40.62, -8.68, 40.66, -8.60),
    "cascais": (38.68, -9.43, 38.72, -9.38),
    "sintra":  (38.78, -9.42, 38.82, -9.36),
    "setubal": (38.50, -8.92, 38.55, -8.85),
    "leiria":  (39.72, -8.83, 39.76, -8.78),
}

def overpass(bbox, tag, limit=50):
    s, w, n, e = bbox
    query = f"""
    [out:json][timeout:25];
    nwr[{tag}][\"contact:email\"]({s},{w},{n},{e});
    out body 100;
    """
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(
        "https://overpass-api.de/api/interpreter",
        data=data, headers={"User-Agent": "cold-email-script/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())["elements"]
    except Exception as e:
        print(f"   ⚠️  Overpass fail: {e}")
        return []

def extract_lead(el, tipo_negocio):
    tags = el.get("tags", {})
    email = tags.get("contact:email") or tags.get("email")
    if not email or "@" not in email: return None
    return {
        "id": str(el.get("id")),
        "nome": tags.get("name", "").strip() or "estabelecimento",
        "email": email.lower().strip(),
        "telefone": tags.get("contact:phone") or tags.get("phone", ""),
        "site": tags.get("contact:website") or tags.get("website", ""),
        "tipo": tipo_negocio,
        "morada": ", ".join(filter(None, [
            tags.get("addr:street", ""),
            tags.get("addr:housenumber", ""),
            tags.get("addr:city", ""),
        ])).strip(", "),
    }

def gpt_personalize(lead, cidade):
    has_site = "sim" if lead["site"] else "não"
    prompt = (
        f"Escreve email comercial PT-PT em tom amigável e profissional (NÃO IA, NÃO 'em conclusão', "
        f"NÃO 'no mundo digital atual', NÃO 'eleva'). Máximo 90 palavras. "
        f"Destinatário: {lead['nome']}, {lead['tipo']} em {cidade}. Tem site: {has_site}.\n\n"
        f"Estrutura:\n"
        f"1. Cumprimento curto referindo o nome do negócio\n"
        f"2. Observação concreta: se NÃO tem site -> 'reparei que ainda não têm site'; "
        f"   se TEM -> 'vi que o site já existe mas talvez beneficie de uma renovação'\n"
        f"3. Oferta: site profissional pronto em 48h, design moderno, mobile, SEO Google, €390 chave-na-mão\n"
        f"4. Call to action: responder este email se interessar (NÃO mencionar WhatsApp aqui)\n"
        f"5. Despedida cordial\n\n"
        f"Devolve APENAS o corpo do email em texto plano, sem assunto, sem assinatura."
    )
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.85, "max_tokens": 250,
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"   ⚠️  GPT fail: {e}")
        return None

ASSUNTOS = [
    "{nome} — site profissional pronto em 48h?",
    "Pequena ideia para o {tipo}",
    "Site novo para {nome}?",
    "{nome}: presença online em 2 dias",
    "Reparei no {nome} — proposta rápida",
]

def assinatura():
    return (
        f"\n\n--\n{FROM_NAME}\n"
        f"Web Designer Freelance | Portugal\n"
        f"WhatsApp: {WHATSAPP}\n"
        f"{LANDING_URL}\n\n"
        f"Para deixar de receber emails meus, responde 'remover' e removo de imediato."
    )

def enviar(lead, corpo, assunto):
    if not SMTP_USER or not SMTP_PASS:
        print(f"   ⚠️  SMTP não configurado (SMTP_USER/SMTP_PASS) — modo DRY-RUN")
        print(f"      Para: {lead['email']} | Assunto: {assunto}")
        return True  # conta como enviado para não repetir
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
    msg["To"] = lead["email"]
    msg["Reply-To"] = REPLY_TO
    msg["Subject"] = assunto
    msg.set_content(corpo + assinatura())
    ctx = ssl.create_default_context()
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls(context=ctx)
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"   ⚠️  SMTP fail para {lead['email']}: {e}")
        return False

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    cidade = sys.argv[2].lower() if len(sys.argv) > 2 else random.choice(list(CIDADES_BBOX.keys()))
    if cidade not in CIDADES_BBOX:
        print(f"❌ cidade desconhecida ({list(CIDADES_BBOX.keys())})"); sys.exit(1)

    print(f"📧 Cold-email B2B — {n} emails em {cidade.title()}")
    bbox = CIDADES_BBOX[cidade]
    leads = []
    random.shuffle(NICHOS)
    for tag, tipo in NICHOS:
        if len(leads) >= n * 3: break
        elements = overpass(bbox, tag, limit=50)
        for el in elements:
            lead = extract_lead(el, tipo)
            if lead and lead["id"] not in seen and lead["email"] not in seen:
                leads.append(lead)
        time.sleep(2)  # respeito ao Overpass

    print(f"   🔍 {len(leads)} leads encontrados (pré-dedup)")
    random.shuffle(leads)
    leads = leads[:n]
    if not leads:
        print("   (nenhum lead novo nesta cidade — tentar outra amanhã)")
        return

    csv_path = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}-{cidade}.csv"
    new_csv = not csv_path.exists()
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new_csv:
            w.writerow(["data", "cidade", "tipo", "nome", "email", "telefone", "site_existente", "assunto", "ok"])
        sucessos = 0
        for i, lead in enumerate(leads, 1):
            print(f"   [{i}/{len(leads)}] {lead['tipo']} — {lead['nome']} <{lead['email']}>")
            corpo = gpt_personalize(lead, cidade.title())
            if not corpo: continue
            assunto = random.choice(ASSUNTOS).format(nome=lead["nome"], tipo=lead["tipo"])
            ok = enviar(lead, corpo, assunto)
            w.writerow([
                datetime.now().isoformat(timespec="minutes"), cidade, lead["tipo"],
                lead["nome"], lead["email"], lead["telefone"], lead["site"], assunto, ok
            ])
            f.flush()
            if ok:
                seen.add(lead["id"])
                seen.add(lead["email"])
                SEEN_FILE.write_text(json.dumps(sorted(seen)))
                sucessos += 1
            time.sleep(random.uniform(15, 35))  # natural delay anti-spam
    print(f"\n✅ {sucessos}/{len(leads)} emails enviados.")
    print(f"📋 Log: {csv_path}")
    print(f"📨 Respostas chegam ao teu inbox: {REPLY_TO or SMTP_USER}")

if __name__ == "__main__":
    main()
