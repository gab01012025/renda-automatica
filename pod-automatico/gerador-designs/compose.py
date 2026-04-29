"""
Compõe texto sobre fundo gerado por DALL-E.
Uso: python3 compose.py <meta.json>

meta.json: { frase, textColor, shadowColor, fontStyle, bgPath, outPath }
"""
import json
import sys
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
FONT_MAP = {
    'display': os.path.join(FONTS_DIR, 'BebasNeue.ttf'),
    'modern':  os.path.join(FONTS_DIR, 'Oswald.ttf'),
    'serif':   os.path.join(FONTS_DIR, 'Playfair.ttf'),
}

CANVAS = 1024
MARGIN = 120  # margem lateral para o texto
MAX_TEXT_HEIGHT = 700  # altura máx que o texto pode ocupar

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def wrap_text(text, font, max_width, draw):
    """Quebra texto em linhas que cabem na largura."""
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = ' '.join(current + [w])
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width:
            current.append(w)
        else:
            if current:
                lines.append(' '.join(current))
            current = [w]
    if current:
        lines.append(' '.join(current))
    return lines

def fit_font_size(text, font_path, max_width, max_height, draw, max_size=200):
    """Encontra o maior tamanho de fonte que faça o texto caber."""
    size = max_size
    while size > 30:
        font = ImageFont.truetype(font_path, size)
        lines = wrap_text(text, font, max_width, draw)
        # altura total
        line_h = font.getbbox('Ag')[3] - font.getbbox('Ag')[1]
        line_spacing = int(line_h * 1.15)
        total_h = line_spacing * len(lines)
        # largura máx
        max_w = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            max_w = max(max_w, bbox[2] - bbox[0])
        if total_h <= max_height and max_w <= max_width:
            return font, lines, line_spacing
        size -= 5
    font = ImageFont.truetype(font_path, 30)
    return font, wrap_text(text, font, max_width, draw), 36

def main():
    meta = json.load(open(sys.argv[1]))
    bg_path = meta.get('bgPath')
    bg_solid = meta.get('bgSolidColor')

    if bg_path and os.path.exists(bg_path):
        bg = Image.open(bg_path).convert('RGBA')
        if bg.size != (CANVAS, CANVAS):
            bg = bg.resize((CANVAS, CANVAS), Image.LANCZOS)
        # Slim text band at bottom 18% (let illustration shine on top 82%)
        text_y_start = int(CANVAS * 0.82)
        text_y_end = CANVAS - 30
        text_max_height = text_y_end - text_y_start - 30
        text_y_center = (text_y_start + text_y_end) // 2
        from PIL import ImageDraw as _ID
        overlay = Image.new('RGBA', bg.size, (0, 0, 0, 0))
        odraw = _ID.Draw(overlay)
        # Soft cream band, slightly translucent so background still bleeds through
        band_color = (245, 239, 230, 215)
        odraw.rectangle([0, text_y_start - 12, CANVAS, CANVAS], fill=band_color)
        # Thin dark separator line on top of band
        odraw.rectangle([60, text_y_start - 14, CANVAS - 60, text_y_start - 12], fill=(26, 26, 26, 180))
        bg = Image.alpha_composite(bg, overlay)
        skip_shadow = True
        meta['textColor'] = '#1a1a1a'
        bottom_band = True
    else:
        # Typography-only mode: solid background, NO shadow (cleaner Etsy look)
        color = bg_solid or '#F5EFE6'
        bg = Image.new('RGBA', (CANVAS, CANVAS), hex_to_rgb(color) + (255,))
        skip_shadow = True
        bottom_band = False

    draw = ImageDraw.Draw(bg)
    text = meta['frase'].upper() if meta.get('fontStyle', 'display') == 'display' else meta['frase']
    font_path = FONT_MAP.get(meta.get('fontStyle'), FONT_MAP['display'])
    if not os.path.exists(font_path):
        font_path = FONT_MAP['display']

    text_color = hex_to_rgb(meta.get('textColor', '#FFFFFF'))
    shadow_color = hex_to_rgb(meta.get('shadowColor', '#000000'))

    font, lines, line_spacing = fit_font_size(
        text, font_path,
        max_width=CANVAS - 2 * MARGIN,
        max_height=text_max_height if bottom_band else MAX_TEXT_HEIGHT,
        draw=draw,
        max_size=110 if bottom_band else 200,
    )

    total_h = line_spacing * len(lines)
    if bottom_band:
        # center text vertically inside the bottom band
        y = text_y_center - total_h // 2
    else:
        # center vertically full canvas
        y = (CANVAS - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (CANVAS - w) // 2
        if not skip_shadow:
            for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (3, 3)]:
                draw.text((x + dx, y + dy), line, font=font, fill=shadow_color + (180,))
        draw.text((x, y), line, font=font, fill=text_color + (255,))
        y += line_spacing

    bg.convert('RGB').save(meta['outPath'], 'PNG', optimize=True)
    print(f'   ✏  texto sobreposto: {meta["frase"][:50]}')

if __name__ == '__main__':
    main()
