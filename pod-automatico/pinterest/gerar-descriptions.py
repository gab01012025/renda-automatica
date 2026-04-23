#!/usr/bin/env python3
"""
Gera descriptions SEO + hashtags + título por pin para upload Pinterest.
Output: CSV pronto para colar/upload manual no Pinterest.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINS_DIR = ROOT / "pinterest" / "pins-prontos"
META = PINS_DIR / "_pins-meta.json"
CSV_OUT = ROOT / "pinterest" / "pins-pinterest-upload.csv"

# Descriptions otimizadas SEO PT (Pinterest gosta de naturais com keywords)
DESCRIPTIONS = {
    "mundial-futebol-pt": {
        "title": "Camisas Portugal Mundial 2026 — Design Único",
        "desc": "Mostra o teu orgulho português no Mundial 2026 com camisas e posters únicos. Designs originais com cores nacionais — verde e vermelho — perfeitos para adeptos. Disponíveis em vários tamanhos. Encontra na loja PrintHouseLX no Etsy. Ideal para presente para fãs de futebol.",
        "tags": "mundial 2026, portugal, camisa portugal, futebol portugal, presente futebol, adepto portugal, lusitano, verde e vermelho, etsy portugal, t-shirt portugal",
    },
    "frases-motivacionais-pt": {
        "title": "T-shirt Motivacional Portugal — Frases que Inspiram",
        "desc": "T-shirts e posters com frases motivacionais em português. Designs minimalistas modernos para quem quer carregar uma mensagem positiva. Perfeito para presente, ginásio, escritório ou casa. Loja PrintHouseLX no Etsy.",
        "tags": "frases motivacionais, t-shirt portugal, motivação, mindset, autoconfiança, presente, poster motivacional, tipografia, etsy",
    },
    "memes-pt": {
        "title": "T-shirt Humor Português — Memes Fixes",
        "desc": "T-shirts e posters com humor 100% português. Para quem fala 'Tás Bem?' a sério. Presente perfeito para amigos, família, colegas. Designs modernos com expressões portuguesas autênticas. Loja PrintHouseLX no Etsy.",
        "tags": "memes portugal, humor português, t-shirt engraçada, presente português, tugas, expressões portuguesas, etsy portugal",
    },
    "cafe-lisboa": {
        "title": "Lisboa em Aguarela — Posters e T-shirts",
        "desc": "Souvenirs únicos de Lisboa com aguarela e azulejos portugueses. Para amantes de café, viagens e cultura lusa. Presente especial para turistas e expatriados. Loja PrintHouseLX no Etsy.",
        "tags": "lisboa, portugal souvenir, café, azulejos, aguarela, presente lisboa, poster lisboa, t-shirt lisboa, turismo portugal",
    },
    "programadores-br": {
        "title": "Camiseta Programador BR — Humor Tech",
        "desc": "Camisetas com humor de programador e dev. Presente perfeito para devs, engenheiros, estudantes de TI. Design moderno e confortável. Loja PrintHouseLX no Etsy.",
        "tags": "programador, dev, javascript, presente programador, camiseta tech, humor tech, t-shirt dev, ti, etsy brasil",
    },
    "pets-engracados": {
        "title": "T-shirt Pet — Para Tutores Apaixonados",
        "desc": "Designs divertidos para mães e pais de pet. T-shirts e posters com humor cão e gato. Presente ideal para apaixonados por animais. Loja PrintHouseLX no Etsy.",
        "tags": "pet, mãe de pet, cão, gato, presente pet, t-shirt animal, humor pet, tutor de pet, etsy",
    },
}


def main():
    pins = json.loads(META.read_text(encoding="utf-8"))
    rows = []
    for p in pins:
        cfg = DESCRIPTIONS.get(p["nicho"], {})
        title = f'{cfg.get("title", "")} — {p["headline"]}'
        # Pinterest: max 100 chars title
        title = title[:100]
        desc = cfg.get("desc", "")
        if p.get("frase"):
            desc = f'{p["frase"]}. {desc}'
        # Pinterest: max 500 chars description
        desc = desc[:500]
        rows.append({
            "Title": title,
            "Media URL": "",  # vazio — vais fazer upload manual
            "Pinterest board": p["nicho"].replace("-", " ").title(),
            "Thumbnail": "",
            "Description": desc,
            "Link": "https://www.etsy.com/shop/PrintHouseLX",
            "Publish date": "",
            "Keywords": cfg.get("tags", ""),
            "Local file": p["file"],
        })

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"✅ {len(rows)} entradas geradas em: {CSV_OUT}")
    print(f"\n📋 Ficheiros para carregar:")
    print(f"   {PINS_DIR}/")
    print(f"\n💡 Workflow:")
    print(f"   1. Cria conta Pinterest Business (grátis)")
    print(f"   2. Cria 6 boards: 'Mundial Futebol Pt', 'Frases Motivacionais Pt', etc")
    print(f"   3. Para cada pin: upload imagem .jpg + cola Title/Description/Link/Tags")
    print(f"   4. Recomendado: 3 pins/dia (não todos no mesmo dia)")


if __name__ == "__main__":
    main()
