#!/usr/bin/env python3
"""Pinterest pin generator v2 — clean lifestyle layout, only new pivot niches."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
DESIGNS_DIR = ROOT / "designs"
FONTS_DIR = ROOT / "fonts"
OUT_DIR = ROOT / "pinterest" / "pins-prontos"
OUT_DIR.mkdir(parents=True, exist_ok=True)

NICHOS_NOVOS = {
    "retro-sunset-en", "vintage-animal-en", "halloween-spooky-en",
    "christmas-funny-en", "mental-health-en", "deutsch-spruche",
}

PIN_W, PIN_H = 1000, 1500
BRAND = "PrintHouseLX"
BG = (250, 247, 240)
INK = (35, 35, 40)
ACCENT = (180, 130, 90)
MUTED = (120, 115, 110)

HEADLINES = {
    "retro-sunset-en": ["Adventure Wall Art", "Vintage National Park Vibes", "Outdoor Lover Gift", "Road Trip Ready"],
    "vintage-animal-en": ["Vintage Pet Print", "Cat Lover Gift Idea", "Dog Mom Wall Art", "Botanical Animal Art"],
    "halloween-spooky-en": ["Spooky Cute Aesthetic", "Halloween Gift Ideas", "Witchy Vibes Decor", "Year Round Spooky"],
    "christmas-funny-en": ["Funny Christmas Tee", "Holiday Gift Idea", "Ugly Sweater Vibes", "Cozy Christmas Print"],
    "mental-health-en": ["Soft Era Aesthetic", "Self Care Reminder", "Therapy Girlie Gift", "Mental Health Era"],
    "deutsch-spruche": ["Lustige Sprüche zum Anziehen", "Geschenk für jeden Anlass", "Deutscher Humor mit Stil", "Trag deinen Spruch"],
}


def fit_text(draw, text, font_path, max_w, max_h, start, min_size=28, line_spacing=10):
    size = start
    while size >= min_size:
        font = ImageFont.truetype(font_path, size)
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            bb = draw.textbbox((0, 0), t, font=font)
            if bb[2] - bb[0] <= max_w:
                cur = t
            else:
                if cur: lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        line_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + line_spacing
        if line_h * len(lines) <= max_h:
            return font, lines, line_h
        size -= 4
    return font, lines, line_h


def shadow_card(pin, x, y, w, h, blur=18, opacity=70):
    shadow = Image.new("RGBA", (w + 80, h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([(40, 40), (w + 40, h + 40)], radius=20, fill=(0, 0, 0, opacity))
    shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
    pin.paste(shadow, (x - 40, y - 30), shadow)


def make_pin(design_path, headline, out_path):
    pin = Image.new("RGB", (PIN_W, PIN_H), BG)
    draw = ImageDraw.Draw(pin)
    brand_font = ImageFont.truetype(str(FONTS_DIR / "Oswald.ttf"), 22)
    bb = draw.textbbox((0, 0), BRAND.upper(), font=brand_font)
    draw.text(((PIN_W - (bb[2] - bb[0])) // 2, 50), BRAND.upper(), fill=MUTED, font=brand_font)
    draw.line([(PIN_W // 2 - 60, 90), (PIN_W // 2 + 60, 90)], fill=ACCENT, width=2)

    card_size, card_x, card_y = 820, (PIN_W - 820) // 2, 130
    shadow_card(pin, card_x, card_y, card_size, card_size, blur=22, opacity=55)
    card = Image.new("RGB", (card_size, card_size), (255, 255, 255))
    img = Image.open(design_path).convert("RGB")
    inner = card_size - 80
    img.thumbnail((inner, inner), Image.LANCZOS)
    if img.size != (inner, inner):
        canvas = Image.new("RGB", (inner, inner), (255, 255, 255))
        canvas.paste(img, ((inner - img.size[0]) // 2, (inner - img.size[1]) // 2))
        img = canvas
    card.paste(img, (40, 40))
    mask = Image.new("L", (card_size, card_size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([(0, 0), (card_size, card_size)], radius=20, fill=255)
    pin.paste(card, (card_x, card_y), mask)

    hf, lines, lh = fit_text(draw, headline, str(FONTS_DIR / "Playfair.ttf"),
                              max_w=PIN_W - 140, max_h=200, start=64, min_size=36)
    y = 1010 + (200 - lh * len(lines)) // 2
    for line in lines:
        bb = draw.textbbox((0, 0), line, font=hf)
        draw.text(((PIN_W - (bb[2] - bb[0])) // 2, y), line, fill=INK, font=hf)
        y += lh

    cta_font = ImageFont.truetype(str(FONTS_DIR / "Oswald.ttf"), 26)
    cta = "FIND IT ON ETSY  \u2192"
    bb = draw.textbbox((0, 0), cta, font=cta_font)
    draw.line([(PIN_W // 2 - 80, 1360), (PIN_W // 2 + 80, 1360)], fill=ACCENT, width=1)
    draw.text(((PIN_W - (bb[2] - bb[0])) // 2, 1380), cta, fill=ACCENT, font=cta_font)

    pin.save(out_path, "JPEG", quality=92)


def main(per=5):
    total, meta = 0, []
    for nicho_dir in sorted(DESIGNS_DIR.iterdir()):
        if not nicho_dir.is_dir(): continue
        nicho = nicho_dir.name
        if nicho not in NICHOS_NOVOS: continue
        pngs = sorted([p for p in nicho_dir.glob("*.png")])[:per]
        if not pngs:
            print(f"  \u26a0 {nicho}: sem designs ainda")
            continue
        heads = HEADLINES.get(nicho, [f"Beautiful {nicho}"])
        for i, png in enumerate(pngs):
            h = heads[i % len(heads)]
            out = OUT_DIR / f"pin-{nicho}-{i+1:02d}.jpg"
            make_pin(png, h, out)
            print(f"  \u2705 {out.name}  ({h})")
            meta.append({"file": out.name, "nicho": nicho, "headline": h, "design": str(png.relative_to(ROOT))})
            total += 1
    (OUT_DIR / "_pins-meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n\U0001f3af {total} pins gerados (apenas designs novos pivot)")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
