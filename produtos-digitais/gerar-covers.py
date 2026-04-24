#!/usr/bin/env python3
"""Gera covers 1280x720 PNG para os 3 PDFs Gumroad — sem API, só PIL."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "covers"
OUT.mkdir(exist_ok=True)

PRODUTOS = [
    {
        "id": "prompts-chatgpt-programadores",
        "titulo": "100 Prompts ChatGPT",
        "subtitulo": "para Programadores",
        "tag": "Code Review • Debug • TDD • SQL",
        "preco": "€9",
        "bg": (15, 23, 42),    # slate-900
        "accent": (96, 165, 250),  # blue-400
    },
    {
        "id": "prompts-marketing-pt",
        "titulo": "150 Prompts ChatGPT",
        "subtitulo": "para Marketing em Português",
        "tag": "Copy • Ads • Email • SEO • Social",
        "preco": "€12",
        "bg": (88, 28, 135),   # purple-900
        "accent": (251, 191, 36),  # amber-400
    },
    {
        "id": "bundle-prompts-ai-pt",
        "titulo": "Bundle 250 Prompts AI",
        "subtitulo": "Programadores + Marketing",
        "tag": "MEGA PACK • Poupa 36%",
        "preco": "€19",
        "bg": (20, 83, 45),    # green-900
        "accent": (74, 222, 128),  # green-400
    },
]


def font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for p in paths:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def make_cover(p):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H), p["bg"])
    d = ImageDraw.Draw(img)

    # Gradient diagonal accent
    for i in range(0, W, 3):
        alpha = int(20 * (1 - i / W))
        d.line([(i, 0), (i, H)], fill=tuple(min(255, c + alpha) for c in p["bg"]))

    # Border accent left
    d.rectangle([(0, 0), (12, H)], fill=p["accent"])

    # Tag (top)
    d.text((60, 60), p["tag"], font=font(28, True), fill=p["accent"])

    # Título
    d.text((60, 180), p["titulo"], font=font(96, True), fill="white")
    d.text((60, 290), p["subtitulo"], font=font(54, True), fill="white")

    # Linha
    d.rectangle([(60, 400), (300, 408)], fill=p["accent"])

    # Bottom: PT/BR + preço
    d.text((60, 500), "🇵🇹 🇧🇷 PDF profissional · 100% PT", font=font(32), fill="white")
    d.text((60, 560), "Pronto a usar · Acesso vitalício", font=font(28), fill=(200, 200, 200))

    # Preço big
    d.text((950, 540), p["preco"], font=font(140, True), fill=p["accent"])

    out = OUT / f"{p['id']}.png"
    img.save(out, "PNG")
    print(f"✅ {out.name}")


for p in PRODUTOS:
    make_cover(p)
