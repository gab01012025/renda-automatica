#!/usr/bin/env python3
"""
Gerador de Imagens IA para Stock (Adobe Stock / Shutterstock / Freepik)
- Gera N imagens DALL-E 3 1024x1024 high quality
- Cria CSV com metadata SEO (title + keywords) pronto para upload em massa Adobe Stock
- Foco: temas que vendem MUITO em 2026 → business, lifestyle, abstract backgrounds, food, nature

Uso: python gerar-batch-stock.py [N=10]
Output: stock-images/output/YYYY-MM-DD/img-001.jpg + metadata.csv

ROI esperado: 1500+ imgs em 3 meses → €150-€500/mês passivo
"""
import os, sys, json, csv, random, hashlib, time, base64
from pathlib import Path
from datetime import datetime
import urllib.request, urllib.parse

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# ---- ENV ----
for envf in [ROOT/"produtos-digitais/.env", ROOT/"pod-automatico/.env", ROOT/".env"]:
    if envf.exists():
        for line in envf.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY missing", file=sys.stderr); sys.exit(1)

# ---- CATEGORIAS QUE VENDEM EM 2026 (research-based) ----
# Adobe Stock top sellers: business, technology, lifestyle, food, abstract, nature
CATEGORIAS = [
    {
        "nome": "business_remote",
        "prompt_base": "modern minimalist photo of a professional working remotely from a bright home office, MacBook on wooden desk, plants, natural light, lifestyle stock photography style, no people faces visible, top-down or side angle",
        "keywords_base": ["remote work", "home office", "freelancer", "laptop", "workspace", "productivity", "digital nomad", "telework", "modern office", "minimalism", "lifestyle", "business", "technology", "wood desk", "plants"]
    },
    {
        "nome": "abstract_gradient",
        "prompt_base": "abstract gradient background with smooth flowing shapes, vibrant pastel colors blue purple pink, modern wallpaper style, high resolution, clean and elegant, suitable for tech presentations and websites",
        "keywords_base": ["abstract", "gradient", "background", "wallpaper", "pastel", "modern", "design", "color", "smooth", "vibrant", "presentation", "tech", "website", "minimal", "art"]
    },
    {
        "nome": "food_flatlay",
        "prompt_base": "overhead flat lay photography of healthy mediterranean breakfast on rustic wooden table, fresh fruits, granola bowl, coffee, natural light, food blogger aesthetic, no logos no brands, professional stock photo style",
        "keywords_base": ["food", "flat lay", "breakfast", "healthy", "mediterranean", "fruits", "coffee", "rustic", "wooden", "natural light", "lifestyle", "nutrition", "morning", "fresh", "blogger"]
    },
    {
        "nome": "tech_ai",
        "prompt_base": "futuristic concept image of artificial intelligence and data, glowing blue neural network nodes connected by light streams, dark background, sci-fi technology aesthetic, professional editorial style, no text no logos",
        "keywords_base": ["artificial intelligence", "AI", "machine learning", "neural network", "technology", "data", "futuristic", "innovation", "digital", "concept", "science", "deep learning", "cyber", "automation", "blue glow"]
    },
    {
        "nome": "nature_landscape",
        "prompt_base": "stunning landscape photograph of misty mountains at sunrise, soft golden light, dramatic clouds, photorealistic, professional nature photography, wide angle, no people no buildings",
        "keywords_base": ["landscape", "mountains", "sunrise", "nature", "mist", "fog", "golden hour", "outdoor", "scenery", "travel", "wilderness", "peaceful", "wallpaper", "horizon", "dramatic"]
    },
    {
        "nome": "wellness_yoga",
        "prompt_base": "serene minimalist composition of meditation and wellness items: candle, stones, plant, neutral tones, top-down, soft natural light, spa aesthetic, no people, no text",
        "keywords_base": ["wellness", "meditation", "yoga", "mindfulness", "self care", "spa", "relaxation", "candle", "zen", "minimalist", "neutral tones", "calm", "balance", "lifestyle", "health"]
    },
    {
        "nome": "finance_growth",
        "prompt_base": "conceptual photo of financial growth: stacked coins with small green plant growing on top, blurred chart background, soft natural light, business and investment theme, professional editorial style",
        "keywords_base": ["finance", "investment", "growth", "savings", "money", "coins", "business", "wealth", "economy", "concept", "plant", "green", "success", "banking", "fintech"]
    },
    {
        "nome": "fitness_active",
        "prompt_base": "minimalist flat lay of fitness essentials: dumbbells, water bottle, towel, sneakers, workout band, on light wooden floor, top-down, bright natural light, no logos no brands, lifestyle stock style",
        "keywords_base": ["fitness", "workout", "gym", "exercise", "healthy lifestyle", "dumbbells", "training", "wellness", "active", "sport", "motivation", "flat lay", "equipment", "home gym", "cardio"]
    },
]

# ---- DALL-E call ----
def gerar_imagem(prompt: str, out_path: Path) -> bool:
    """Gera imagem 1024x1024 via DALL-E 3 e guarda em out_path"""
    body = json.dumps({
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
        "quality": "hd",
        "response_format": "b64_json"
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        b64 = data["data"][0]["b64_json"]
        out_path.write_bytes(base64.b64decode(b64))
        return True
    except Exception as e:
        print(f"   ⚠️  DALL-E fail: {e}", file=sys.stderr)
        return False

def gpt_metadata(prompt_base: str, categoria: str) -> dict:
    """Pede ao GPT-4o-mini um title curto + 25 keywords SEO para Adobe Stock"""
    sys_p = (
        "You are an Adobe Stock metadata expert. Given an image prompt, return JSON only "
        "with keys: title (max 70 chars, descriptive English, no brand names), "
        "keywords (array of EXACTLY 25 single-word or 2-word lowercase English keywords, ordered by relevance, no duplicates, no brand names)."
    )
    body = json.dumps({
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"Image prompt: {prompt_base}\nCategory: {categoria}\nReturn JSON."}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
        return json.loads(data["choices"][0]["message"]["content"])
    except Exception as e:
        print(f"   ⚠️  metadata fail: {e}", file=sys.stderr)
        return {"title": prompt_base[:70], "keywords": []}

# ---- main ----
def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = ROOT / "stock-images" / "output" / today
    out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = out_dir / "metadata.csv"
    write_header = not csv_path.exists()
    csv_f = csv_path.open("a", newline="", encoding="utf-8")
    writer = csv.writer(csv_f)
    if write_header:
        writer.writerow(["Filename", "Title", "Keywords", "Category", "Releases"])

    existing = len(list(out_dir.glob("img-*.jpg"))) + len(list(out_dir.glob("img-*.png")))
    print(f"📸 Gerar {n} imagens stock para Adobe Stock / Shutterstock")
    print(f"   Pasta: {out_dir} (já tem {existing})")

    sucessos = 0
    for i in range(n):
        cat = random.choice(CATEGORIAS)
        # variar o prompt para evitar duplicados (DALL-E rejeita iguais)
        seed = hashlib.md5(f"{cat['nome']}{time.time()}{i}".encode()).hexdigest()[:8]
        prompt = f"{cat['prompt_base']}, unique composition variant {seed}, professional stock photography, no watermark, no text, no logos"
        idx = existing + i + 1
        fn = f"img-{idx:04d}.png"
        out_path = out_dir / fn
        print(f"   [{i+1}/{n}] {cat['nome']} → {fn}")
        if not gerar_imagem(prompt, out_path):
            continue
        meta = gpt_metadata(cat["prompt_base"], cat["nome"])
        title = meta.get("title", cat["nome"])[:70]
        kws = meta.get("keywords", [])
        if isinstance(kws, list):
            kws_str = ", ".join(str(k).lower().strip() for k in kws[:25])
        else:
            kws_str = str(kws)
        writer.writerow([fn, title, kws_str, cat["nome"], "no"])
        csv_f.flush()
        sucessos += 1
        time.sleep(2)  # rate-limit DALL-E

    csv_f.close()
    print(f"\n✅ {sucessos}/{n} imagens geradas")
    print(f"📋 CSV: {csv_path}")
    print(f"\n👉 Próximo passo: criar conta Adobe Stock Contributor")
    print(f"   https://contributor.stock.adobe.com/")
    print(f"   Faz upload do CSV + imagens em batch (até 700 por upload)")

if __name__ == "__main__":
    main()
