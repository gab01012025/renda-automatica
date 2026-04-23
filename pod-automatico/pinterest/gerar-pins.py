#!/usr/bin/env python3
"""
Gerador de Pins Pinterest a partir dos designs POD existentes.
Formato: 1000x1500 (vertical, ratio 2:3 — ideal Pinterest).
Layout: header brand | imagem produto | headline PT | CTA Etsy
"""
import json
import os
import sys
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
DESIGNS_DIR = ROOT / "designs"
FONTS_DIR = ROOT / "fonts"
OUT_DIR = ROOT / "pinterest" / "pins-prontos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PIN_W, PIN_H = 1000, 1500
BRAND = "PrintHouseLX"
CTA = "PROCURA NA ETSY"

# Headlines persuasivos por nicho (Pinterest gosta de hooks)
HEADLINES = {
    "mundial-futebol-pt": [
        "Camisas Portugal Mundial 2026",
        "Mostra o Teu Orgulho Lusitano",
        "Verde e Vermelho no Coração",
        "Designs Únicos para Adeptos PT",
        "Veste Portugal no Mundial",
    ],
    "frases-motivacionais-pt": [
        "Frases que Mudam o Teu Dia",
        "Motivação Diária no Estilo",
        "T-shirts com Atitude PT",
        "Mindset Vencedor",
        "Veste a Tua Energia",
    ],
    "memes-pt": [
        "Humor Português 100%",
        "Memes que Todo Português Entende",
        "Tugas Vão Adorar",
        "Presente Perfeito Para Amigos",
        "Tás Bem? Estás Fixe!",
    ],
    "cafe-lisboa": [
        "Lisboa em Aguarela",
        "Para Quem Ama Café e Lisboa",
        "Souvenir Diferente de Portugal",
        "Azulejos em T-shirt e Poster",
        "Lisboa no Estilo",
    ],
    "programadores-br": [
        "Para Devs que Curtem Humor",
        "Camisetas de Programador BR",
        "Stack Overflow Approved",
        "Presente Ideal para Dev",
        "Bug? Não. Feature.",
    ],
    "pets-engracados": [
        "Para Tutores que Amam o Pet",
        "Humor Pet Tugas e Brasileiros",
        "Presente para Pais de Pet",
        "Cão & Gato em Estilo",
        "Confissões de Pet",
    ],
}


def fit_font(text, max_w, max_h, font_path, start=80, min_size=24):
    size = start
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        # Wrap
        words = text.split()
        lines, cur = [], ""
        dummy = Image.new("RGB", (10, 10))
        d = ImageDraw.Draw(dummy)
        for w in words:
            t = (cur + " " + w).strip()
            bb = d.textbbox((0, 0), t, font=font)
            if bb[2] - bb[0] <= max_w:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        line_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 8
        total_h = line_h * len(lines)
        if total_h <= max_h:
            return font, lines, line_h
        size -= 4
    return font, lines, line_h


def make_pin(design_path: Path, headline: str, out_path: Path):
    # Canvas branco off
    pin = Image.new("RGB", (PIN_W, PIN_H), (250, 248, 245))

    # Topo: faixa preta com brand
    draw = ImageDraw.Draw(pin)
    draw.rectangle([(0, 0), (PIN_W, 80)], fill=(15, 15, 15))
    brand_font = ImageFont.truetype(str(FONTS_DIR / "BebasNeue.ttf"), 42)
    bb = draw.textbbox((0, 0), BRAND, font=brand_font)
    bw = bb[2] - bb[0]
    draw.text(((PIN_W - bw) // 2, 18), BRAND, fill=(255, 215, 0), font=brand_font)

    # Imagem produto (quadrada, 900x900) centrada com margem 50
    img = Image.open(design_path).convert("RGB")
    img_size = 900
    img.thumbnail((img_size, img_size), Image.LANCZOS)
    # Crop centrada se nao for quadrada
    if img.size != (img_size, img_size):
        img = img.resize((img_size, img_size), Image.LANCZOS)
    pin.paste(img, ((PIN_W - img_size) // 2, 110))

    # Headline (zona inferior 1030-1380)
    headline_font, lines, line_h = fit_font(
        headline,
        max_w=PIN_W - 100,
        max_h=280,
        font_path=str(FONTS_DIR / "BebasNeue.ttf"),
        start=84,
        min_size=40,
    )
    total_h = line_h * len(lines)
    y = 1050 + (280 - total_h) // 2
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=headline_font)
        w = bb[2] - bb[0]
        draw.text(((PIN_W - w) // 2, y), line, fill=(15, 15, 15), font=headline_font)
        y += line_h

    # CTA banner
    cta_font = ImageFont.truetype(str(FONTS_DIR / "BebasNeue.ttf"), 48)
    draw.rectangle([(0, 1400), (PIN_W, 1500)], fill=(220, 20, 60))
    bb = draw.textbbox((0, 0), CTA, font=cta_font)
    cw = bb[2] - bb[0]
    draw.text(((PIN_W - cw) // 2, 1422), CTA, fill=(255, 255, 255), font=cta_font)

    pin.save(out_path, "JPEG", quality=92)
    return out_path


def main(per_nicho=5):
    total = 0
    pin_meta = []
    for nicho_dir in sorted(DESIGNS_DIR.iterdir()):
        if not nicho_dir.is_dir():
            continue
        nicho = nicho_dir.name
        feitos = nicho_dir / "feitos"
        if not feitos.exists():
            continue
        pngs = sorted(feitos.glob("*.png"))[:per_nicho]
        headlines = HEADLINES.get(nicho, [f"Design {nicho}"])
        for i, png in enumerate(pngs):
            headline = headlines[i % len(headlines)]
            # Tenta ler frase do JSON associado para pin description depois
            json_path = png.with_suffix(".json")
            frase = ""
            if json_path.exists():
                try:
                    meta = json.loads(json_path.read_text(encoding="utf-8"))
                    frase = meta.get("frase", "")
                except Exception:
                    pass

            out_name = f"pin-{nicho}-{i+1:02d}.jpg"
            out_path = OUT_DIR / out_name
            make_pin(png, headline, out_path)
            print(f"  ✅ {out_name}  ({headline})")
            pin_meta.append({
                "file": out_name,
                "nicho": nicho,
                "headline": headline,
                "frase": frase,
            })
            total += 1
    # Salva metadata para depois gerar descriptions
    meta_file = OUT_DIR / "_pins-meta.json"
    meta_file.write_text(json.dumps(pin_meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n🎯 {total} pins gerados em: {OUT_DIR}")
    print(f"📋 Metadata: {meta_file}")


if __name__ == "__main__":
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    print(f"📌 Gerar {per} pins por nicho")
    main(per)
