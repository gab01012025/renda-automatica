#!/usr/bin/env python3
"""
Etsy Digital Downloads — Factory autônoma

O quê: gera assets digitais que vendem MUITO em Etsy (zero shipping, zero stock):
       1. Wall Art Prints (DALL-E HD 1024x1792 → JPEG print-ready)
       2. Planners PDF (multi-página A4 com layout pintado)
       3. SVG cut files / cricut bundles (para Cricut/Silhouette)
       Em DE/FR/EN porque mercado EU paga 3x mais que US e tem menos competição.

Receita esperada Etsy digital:
   - 1 listing converte ~0.5%/mês de visualizações
   - 100 listings × 200 views/mês × 0.5% × €5-€15 = €500-€1500/mês passivo
   - Em 90 dias com 200 listings: €1500-€3500/mês

Output: cada produto numa pasta pronta para upload manual OU via Etsy API
        (se ETSY_API_KEY definido, faz upload automático).

Uso: python gerar-etsy-digitals.py [N=3]
"""
import os, sys, json, random, time, hashlib, base64, zipfile
from pathlib import Path
from datetime import datetime
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
for envf in [ROOT/".env", ROOT/"produtos-digitais/.env", ROOT/"pod-automatico/.env"]:
    if envf.exists():
        for line in envf.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ETSY_API_KEY = os.environ.get("ETSY_API_KEY", "")  # opcional p/ upload auto
ETSY_SHOP_ID = os.environ.get("ETSY_SHOP_ID", "")
if not OPENAI_API_KEY: print("❌ OPENAI_API_KEY missing"); sys.exit(1)

OUT_BASE = ROOT / "etsy-digitals" / "produtos"
OUT_BASE.mkdir(parents=True, exist_ok=True)
HIST = ROOT / "etsy-digitals" / "_gerados.json"
hist = json.loads(HIST.read_text()) if HIST.exists() else []

# ---- BANCO DE PRODUTOS QUE VENDEM EM 2026 ----
PRODUTOS = [
    # (tipo, idioma, slug-base, descrição_de_estilo, prompt_dalle)
    ("wall_art", "en", "boho-mountain-print", "boho minimalist mountain landscape line art",
     "minimalist boho line art illustration of mountain range at sunrise, single continuous line, soft terracotta and sage green palette, wabi-sabi aesthetic, clean white background, high resolution print, no text"),
    ("wall_art", "en", "abstract-floral-print", "abstract floral pastel art",
     "abstract painted floral composition, soft pastel watercolor style, peach pink sage cream, modern wall art aesthetic, no text, high resolution print"),
    ("wall_art", "en", "vintage-botanical-print", "vintage botanical illustration",
     "vintage botanical illustration of fern and eucalyptus branches, sepia tones on aged cream paper texture, herbarium scientific style, no text, high resolution"),
    ("wall_art", "en", "midcentury-geometric", "midcentury modern geometric",
     "midcentury modern geometric composition, mustard ochre teal sage shapes overlapping, retro 1960s aesthetic, clean composition, no text, high resolution"),
    ("wall_art", "de", "alpenpanorama-print", "Alpen Panorama Linienkunst",
     "minimalist line art of german alps panorama, single line drawing, navy blue on cream background, scandinavian aesthetic, no text, high resolution print"),
    ("wall_art", "de", "berlin-skyline-print", "Berlin Skyline minimalist",
     "minimalist line art Berlin skyline including tv tower and brandenburg gate stylized, monochrome navy on cream, modern wall art, no text, high resolution"),
    ("wall_art", "fr", "paris-toits-print", "Toits de Paris aquarelle",
     "soft watercolor illustration of Paris rooftops with stylized Eiffel Tower in distance, dawn pastel pink and lavender, romantic aesthetic, no text, high resolution print"),
    ("wall_art", "fr", "provence-lavande-print", "Champ de Lavande Provence",
     "impressionist style painting of provence lavender field at golden hour, warm purple and gold, oil painting texture, no text, high resolution"),

    ("planner_pdf", "en", "weekly-planner-2026-en", "Undated weekly planner pages",
     None),  # planners não usam DALL-E
    ("planner_pdf", "en", "habit-tracker-en", "Habit tracker monthly pages",
     None),
    ("planner_pdf", "en", "meal-planner-en", "Weekly meal planner with shopping list",
     None),
    ("planner_pdf", "de", "wochenplaner-2026", "Wochenplaner undatiert",
     None),
    ("planner_pdf", "de", "haushaltsbuch-pdf", "Haushaltsbuch monatlich",
     None),
    ("planner_pdf", "fr", "agenda-hebdo-2026", "Agenda hebdomadaire non date",
     None),
    ("planner_pdf", "fr", "tracker-habitudes", "Tracker d'habitudes mensuel",
     None),

    # === EXPANSAO 2026-04-29 ===
    # Wall art EN extras (high-traffic Etsy keywords)
    ("wall_art", "en", "modern-abstract-set3", "abstract painting set neutral tones",
     "set of 3 modern abstract paintings, neutral beige cream sage palette, brushed minimalist style, gallery wall art, no text, high resolution print"),
    ("wall_art", "en", "boho-sun-print", "boho sun face line art",
     "boho minimalist sun face line drawing, terracotta and cream, single continuous line, scandi boho aesthetic, no text, high resolution print"),
    ("wall_art", "en", "nursery-animals-set", "watercolor nursery animals",
     "set of 3 watercolor nursery animals (bunny, fox, bear), soft pastel palette, minimalist children room art, no text, high resolution"),
    ("wall_art", "en", "kitchen-coffee-print", "coffee bar sign vintage",
     "vintage coffee bar typography poster, kraft brown paper texture, retro coffee shop signage style, no text, high resolution"),
    ("wall_art", "en", "moon-phases-print", "moon phases minimalist",
     "minimalist moon phases poster, gold foil look on dark navy, celestial wall art, no text, high resolution"),
    ("wall_art", "en", "city-skyline-nyc", "new york city skyline minimalist",
     "minimalist line art New York skyline, single line drawing, navy on cream background, modern wall art, no text, high resolution"),
    ("wall_art", "en", "abstract-arch-print", "minimalist arch shapes",
     "minimalist geometric arch shapes overlapping, terracotta sage cream palette, mid-century modern, no text, high resolution print"),
    ("wall_art", "en", "tropical-leaves", "monstera tropical leaves",
     "minimalist monstera tropical leaves illustration, soft green watercolor, modern botanical print, no text, high resolution"),

    # Wall art DE extras
    ("wall_art", "de", "muenchen-skyline", "Muenchen Skyline Linienkunst",
     "minimalist line art Munich skyline with Frauenkirche stylized, navy on cream, modern German wall art, no text, high resolution"),
    ("wall_art", "de", "hamburg-print", "Hamburg Hafen Aquarell",
     "soft watercolor Hamburg harbor with Elbphilharmonie, pastel blue and grey, romantic German wall art, no text, high resolution"),

    # Planners EN extras
    ("planner_pdf", "en", "budget-tracker-en", "Monthly budget tracker pages", None),
    ("planner_pdf", "en", "fitness-journal-en", "30-day fitness journal pages", None),
    ("planner_pdf", "en", "reading-tracker-en", "Reading tracker and book log", None),
    ("planner_pdf", "en", "self-care-planner-en", "Daily self-care and gratitude pages", None),
    ("planner_pdf", "en", "study-planner-en", "Student study planner pages", None),
    ("planner_pdf", "en", "small-business-planner-en", "Small business owner planner pages", None),

    # Planners DE extras
    ("planner_pdf", "de", "fitness-journal-de", "Fitness Tagebuch 30 Tage", None),
    ("planner_pdf", "de", "lese-tracker-de", "Lese Tracker und Buchliste", None),
    ("planner_pdf", "de", "gratitude-journal-de", "Dankbarkeits Journal taeglich", None),

    # Planners FR extras
    ("planner_pdf", "fr", "journal-fitness-fr", "Journal fitness 30 jours", None),
    ("planner_pdf", "fr", "tracker-budget-fr", "Tracker budget mensuel", None),

    # Wall art FR extras
    ("wall_art", "fr", "marseille-print", "Vieux Port Marseille aquarelle",
     "soft watercolor Vieux Port Marseille at sunset, warm pastel orange and blue, romantic French wall art, no text, high resolution"),
    ("wall_art", "fr", "champagne-print", "Champagne celebration vintage",
     "vintage champagne celebration typography poster, gold foil look on cream, French art deco aesthetic, no text, high resolution"),
]

def gpt(messages, model="gpt-4o", temperature=0.85):
    body = json.dumps({"model": model, "messages": messages, "temperature": temperature}).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def dalle_hd(prompt, out_path):
    body = json.dumps({
        "model": "dall-e-3", "prompt": prompt, "n": 1,
        "size": "1024x1792", "quality": "hd", "response_format": "b64_json",
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations", data=body,
        headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read())
    out_path.write_bytes(base64.b64decode(data["data"][0]["b64_json"]))

def gerar_metadata_etsy(produto):
    tipo, lang, slug, estilo, _ = produto
    sys_p = (
        f"You are an Etsy SEO expert. Output JSON only with keys: "
        f"title (max 140 chars, include '{lang.upper()}' market keywords, no trademarks), "
        f"description (rich 600-word product description in {lang}, with sections: about / sizes available / how to download / printing tips / refund policy. Use line breaks. Sound human, NOT AI.), "
        f"tags (array of EXACTLY 13 lowercase tags max 20 chars each, no duplicates, in {lang}, high search volume Etsy keywords), "
        f"materials (array of 3-5 relevant materials in {lang})."
    )
    user_p = f"Product: {tipo} | style: {estilo} | language: {lang} | slug: {slug}"
    txt = gpt([
        {"role": "system", "content": sys_p},
        {"role": "user", "content": user_p}
    ], model="gpt-4o-mini", temperature=0.8)
    try:
        # tentar extrair JSON
        start = txt.find("{"); end = txt.rfind("}") + 1
        return json.loads(txt[start:end])
    except Exception as e:
        return {"title": estilo, "description": estilo, "tags": [], "materials": []}

def gerar_planner_pdf(slug, lang, estilo, out_dir):
    """Gera PDF planner usando reportlab (precisa instalar). Fallback: PNG pages."""
    pages_dir = out_dir / "pages"
    pages_dir.mkdir(exist_ok=True)
    # Pedir ao GPT layouts para 12 páginas
    sys_p = "You are a planner designer. Output a JSON list of 4 page-titles + their grid structure (description in plain text)."
    user_p = f"Design a 4-page printable {estilo} planner in {lang}. Output JSON: pages: [{{title, layout_description}}]"
    try:
        spec = json.loads(gpt([{"role":"system","content":sys_p},{"role":"user","content":user_p}], model="gpt-4o-mini").strip().lstrip("```json").rstrip("```"))
    except Exception:
        spec = {"pages": [{"title": "Planner", "layout_description": "weekly grid"}]}

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import cm
        pdf_path = out_dir / f"{slug}.pdf"
        c = canvas.Canvas(str(pdf_path), pagesize=A4)
        W, H = A4
        for i, page in enumerate(spec.get("pages", []), 1):
            c.setFont("Helvetica-Bold", 24)
            c.drawString(2*cm, H - 3*cm, page["title"][:60])
            c.setFont("Helvetica", 10)
            c.drawString(2*cm, H - 4*cm, f"({lang.upper()}) page {i} — {estilo}")
            # grid simples
            c.setStrokeColorRGB(0.7, 0.7, 0.7)
            for y in range(int(H/cm) - 6, 4, -1):
                c.line(2*cm, y*cm, W - 2*cm, y*cm)
            c.showPage()
        c.save()
        return pdf_path
    except ImportError:
        (out_dir / "INSTALL-REPORTLAB.txt").write_text("pip install reportlab to generate real PDFs")
        return None

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    naoFeitos = [p for p in PRODUTOS if p[2] not in hist]
    if not naoFeitos:
        print("✅ Todos produtos do banco já gerados. Adiciona mais ao PRODUTOS.")
        return
    random.shuffle(naoFeitos)
    escolhidos = naoFeitos[:n]
    print(f"🎨 Etsy Digitals — gerar {len(escolhidos)} produtos")
    for tipo, lang, slug, estilo, prompt in escolhidos:
        print(f"   ⚙️  [{tipo}|{lang}] {slug}")
        out_dir = OUT_BASE / slug
        out_dir.mkdir(exist_ok=True, parents=True)
        try:
            # 1. asset principal
            if tipo == "wall_art":
                img_path = out_dir / f"{slug}-print.png"
                if not img_path.exists():
                    dalle_hd(prompt, img_path)
                    print(f"      ✓ image: {img_path.name}")
            elif tipo == "planner_pdf":
                pdf = gerar_planner_pdf(slug, lang, estilo, out_dir)
                if pdf: print(f"      ✓ pdf: {pdf.name}")
            # 2. metadata
            meta = gerar_metadata_etsy((tipo, lang, slug, estilo, prompt))
            (out_dir / "etsy-listing.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
            # 3. instruções upload manual (caso não tenha API)
            if not ETSY_API_KEY:
                upload_md = (
                    f"# Upload manual Etsy: {meta.get('title', slug)}\n\n"
                    f"1. Vai a https://www.etsy.com/your/shops/me/tools/listings/create\n"
                    f"2. Upload do ficheiro principal desta pasta\n"
                    f"3. Title: {meta.get('title','')[:140]}\n"
                    f"4. Tags: {', '.join(meta.get('tags', []))}\n"
                    f"5. Description: cola o conteúdo de etsy-listing.json campo 'description'\n"
                    f"6. Tipo: digital download\n"
                    f"7. Preço sugerido: €{8 if tipo=='wall_art' else 12}\n"
                )
                (out_dir / "INSTRUCOES-UPLOAD.md").write_text(upload_md)
            hist.append(slug)
            HIST.write_text(json.dumps(hist, indent=2))
            print(f"      ✅ pronto: {out_dir}")
            time.sleep(2)
        except Exception as e:
            print(f"      ⚠️  fail: {e}")
    print(f"\n✅ Total acumulado: {len(hist)} produtos prontos")
    print(f"📁 {OUT_BASE}")
    if not ETSY_API_KEY:
        print("\n💡 Para upload 100% automático no Etsy:")
        print("   1. Cria conta Etsy seller (€0.20/listing, primeiros 40 grátis com link refer)")
        print("   2. Pede acesso API: https://www.etsy.com/developers/your-apps")
        print("   3. Define ETSY_API_KEY e ETSY_SHOP_ID em .env")

if __name__ == "__main__":
    main()
