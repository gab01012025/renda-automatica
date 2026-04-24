#!/usr/bin/env python3
"""
KDP Prep — converte os 5 ebooks (.md) em formato pronto para Amazon KDP:
  • manuscript.epub  (formato preferido)
  • cover.jpg        (1600x2560 portrait, KDP exige >1000px lado maior)
  • metadata.json    (title, subtitle, description, 7 keywords, 2 categorias, preço)

Saída: kdp-ebooks/kdp-pronto-upload/<id>/

Depois faz upload manual em https://kdp.amazon.com (1ª vez) — automação Playwright
fica para v2 (KDP bloqueia muito automação por reviews).
"""
import json, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
EBOOKS = ROOT / "ebooks"
OUT = ROOT / "kdp-pronto-upload"
OUT.mkdir(exist_ok=True)

EBOOK_META = {
    "chatgpt-advogados-pt": {
        "titulo": "ChatGPT para Advogados: Guia Prático 2026",
        "subtitulo": "Como usar IA para petições, contratos e pareceres em 1/3 do tempo",
        "lingua": "pt",
        "preco": 4.99,
        "autor": "Gabriel Barreto",
        "descricao": "Descubra como advogados em Portugal e Brasil estão a usar ChatGPT para reduzir 70% do tempo gasto em petições, contratos e pareceres. Guia prático com prompts testados, workflow diário e casos reais. Para advogados, juristas e estagiários que querem entrar na revolução da IA jurídica sem complicação técnica.",
        "keywords": ["ChatGPT advogados", "IA direito", "advocacia digital", "petições automáticas", "contratos IA", "jurisprudência inteligência artificial", "advogado Portugal Brasil"],
        "categorias": ["LAW > Practical Guides", "COMPUTERS > Artificial Intelligence > General"],
    },
    "chatgpt-imobiliaria-pt": {
        "titulo": "ChatGPT para Imobiliárias: Vender Mais com IA",
        "subtitulo": "Descrições que vendem, leads automáticos, e fecho em tempo recorde",
        "lingua": "pt",
        "preco": 4.99,
        "autor": "Gabriel Barreto",
        "descricao": "O guia definitivo para agentes imobiliários PT/BR aumentarem vendas com IA. Descrições de imóveis que convertem, anúncios automáticos para Idealista/Imovirtual, follow-ups por email, posts para redes sociais e até chatbots de atendimento. Tudo com ChatGPT — sem código.",
        "keywords": ["ChatGPT imobiliária", "IA imóveis", "venda imóveis", "marketing imobiliário", "Idealista anúncios", "agente imobiliário Portugal", "Imovirtual"],
        "categorias": ["BUSINESS & ECONOMICS > Real Estate > General", "BUSINESS & ECONOMICS > Marketing > Direct"],
    },
    "copywriting-ia-pt": {
        "titulo": "Copywriting com IA: 50 Templates que Vendem",
        "subtitulo": "Das headlines aos emails de vendas — tudo gerado com ChatGPT",
        "lingua": "pt",
        "preco": 5.99,
        "autor": "Gabriel Barreto",
        "descricao": "50 templates de copywriting prontos a usar, em português, criados com ChatGPT e testados em campanhas reais. Headlines, anúncios Facebook/Google, emails de vendas, landing pages, posts de Instagram, scripts VSL. Para empreendedores, freelancers e marketers que querem vender mais sem ser copywriter profissional.",
        "keywords": ["copywriting português", "templates ChatGPT", "vendas online", "anúncios Facebook", "email marketing", "marketing digital PT", "landing page"],
        "categorias": ["BUSINESS & ECONOMICS > Marketing > Direct", "BUSINESS & ECONOMICS > Advertising & Promotion"],
    },
    "excel-ia-pt": {
        "titulo": "Excel com IA: Domine Planilhas em 2026",
        "subtitulo": "Fórmulas complexas, automações e dashboards — tudo com ChatGPT",
        "lingua": "pt",
        "preco": 4.99,
        "autor": "Gabriel Barreto",
        "descricao": "Pare de procurar fórmulas no Google. Aprenda como pedir ao ChatGPT que gere fórmulas Excel complexas, macros VBA, automações e dashboards inteiráteis em segundos. Para profissionais administrativos, financeiros, contabilistas e gestores que vivem dentro do Excel.",
        "keywords": ["Excel ChatGPT", "fórmulas Excel", "VBA macros", "dashboards Excel", "automação planilhas", "Excel português", "produtividade escritório"],
        "categorias": ["COMPUTERS > Spreadsheet Software > Microsoft Excel", "COMPUTERS > Artificial Intelligence > General"],
    },
    "receitas-low-carb-ia-en": {
        "titulo": "Low-Carb AI Recipes: 50 Meals in Under 30 Minutes",
        "subtitulo": "Personalized meal planning powered by ChatGPT",
        "lingua": "en",
        "preco": 3.99,
        "autor": "Gabriel Barreto",
        "descricao": "50 fast, low-carb recipes generated and tested with AI. Personalize them in seconds using the included ChatGPT prompts: swap ingredients, scale portions, build weekly meal plans. Perfect for busy people on keto, low-carb or weight-loss journeys.",
        "keywords": ["low carb recipes", "keto cookbook", "AI cooking", "meal planning", "weight loss recipes", "ChatGPT recipes", "30 minute meals"],
        "categorias": ["COOKING > Health & Healing > Low Carbohydrate", "COOKING > Methods > Quick & Easy"],
    },
}


def make_cover(out_path, titulo, subtitulo, autor, lingua):
    """Capa portrait 1600x2560 KDP."""
    W, H = 1600, 2560
    paleta = {
        "pt": ((30, 41, 59), (96, 165, 250)),     # slate / blue
        "en": ((23, 37, 84), (251, 191, 36)),    # navy / amber
    }
    bg, accent = paleta.get(lingua, paleta["pt"])
    img = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(img)

    # Faixa accent
    d.rectangle([(0, 0), (W, 40)], fill=accent)
    d.rectangle([(0, H - 40), (W, H)], fill=accent)
    d.rectangle([(0, 0), (40, H)], fill=accent)

    def font(size, bold=True):
        try:
            return ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                size,
            )
        except Exception:
            return ImageFont.load_default()

    # Título — wrap manual
    palavras = titulo.split()
    linhas, atual = [], ""
    for p in palavras:
        teste = (atual + " " + p).strip()
        if len(teste) > 18:
            linhas.append(atual)
            atual = p
        else:
            atual = teste
    if atual:
        linhas.append(atual)
    y = 400
    for ln in linhas[:4]:
        d.text((100, y), ln, font=font(120), fill="white")
        y += 150

    # Linha
    d.rectangle([(100, y + 60), (700, y + 80)], fill=accent)

    # Subtítulo
    sub_lines, atual = [], ""
    for w in subtitulo.split():
        teste = (atual + " " + w).strip()
        if len(teste) > 30:
            sub_lines.append(atual)
            atual = w
        else:
            atual = teste
    if atual:
        sub_lines.append(atual)
    y += 150
    for ln in sub_lines[:4]:
        d.text((100, y), ln, font=font(56, False), fill=(220, 220, 220))
        y += 80

    # Autor (bottom)
    d.text((100, H - 220), autor.upper(), font=font(64), fill=accent)
    d.text((100, H - 140), "POWERED BY AI", font=font(36, False), fill=(180, 180, 180))

    img.save(out_path, "JPEG", quality=92)


def md_to_epub(md_path, epub_path, titulo, autor, lingua):
    """Converte .md → .epub via pandoc."""
    cmd = [
        "pandoc",
        str(md_path),
        "-o", str(epub_path),
        f"--metadata=title:{titulo}",
        f"--metadata=author:{autor}",
        f"--metadata=lang:{lingua}",
        "--toc",
        "--toc-depth=2",
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"   ⚠️ pandoc: {res.stderr.strip()[:200]}")
        return False
    return True


def main():
    feitos = 0
    for ebid, meta in EBOOK_META.items():
        md = EBOOKS / f"{ebid}.md"
        if not md.exists():
            print(f"⏭️  {ebid} — md não existe")
            continue
        dest = OUT / ebid
        dest.mkdir(exist_ok=True)

        # 1. EPUB
        epub = dest / "manuscript.epub"
        if not epub.exists():
            ok = md_to_epub(md, epub, meta["titulo"], meta["autor"], meta["lingua"])
            if not ok:
                continue
            print(f"✅ {ebid}/manuscript.epub")
        else:
            print(f"   {ebid}/manuscript.epub (já existe)")

        # 2. Cover JPG portrait
        cover = dest / "cover.jpg"
        if not cover.exists():
            make_cover(cover, meta["titulo"], meta["subtitulo"],
                       meta["autor"], meta["lingua"])
            print(f"✅ {ebid}/cover.jpg")

        # 3. Metadata
        meta_path = dest / "metadata.json"
        meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))

        # 4. PDF backup (alternativa ao EPUB)
        pdf_src = EBOOKS / f"{ebid}.pdf"
        if pdf_src.exists():
            shutil.copy(pdf_src, dest / "manuscript.pdf")

        feitos += 1

    # README com instruções
    readme = OUT / "README.md"
    readme.write_text(f"""# KDP — Pronto para Upload

{feitos} ebooks preparados em `kdp-pronto-upload/<id>/`:

Por cada pasta:
- `manuscript.epub`  — sobe este (Amazon prefere EPUB sobre PDF)
- `cover.jpg`        — 1600x2560 portrait (Amazon exige > 1000px)
- `metadata.json`    — title, subtitle, descrição, 7 keywords, 2 categorias, preço
- `manuscript.pdf`   — backup caso EPUB dê erro

## Upload manual (1ª vez, ~10 min/ebook)

1. https://kdp.amazon.com → Sign in
2. Bookshelf → **Create eBook**
3. **Página 1 — Detalhes**: copia title/subtitle/desc/keywords do `metadata.json`
4. **Página 2 — Conteúdo**: upload `manuscript.epub` + `cover.jpg`
5. **Página 3 — Preço**: usa o preço do JSON (royalty 70% se entre $2.99-$9.99)
6. **Publish** — aprovação 24-72h

## Setup obrigatório (1ª vez)
- Tax interview (W-8BEN para Portugal — escolhe "Portugal" → tratado)
- Bank account ou cheque para royalties
- KDP exige conta separada se quiseres LLC; pessoa singular funciona

## Royalties esperados
| Ebook | Preço | Royalty 70% |
|---|---|---|
| Advogados | $4.99 | $3.49/venda |
| Imobiliária | $4.99 | $3.49/venda |
| Copywriting | $5.99 | $4.19/venda |
| Excel | $4.99 | $3.49/venda |
| Low-Carb (EN) | $3.99 | $2.79/venda |

100 vendas/mês × $3.50 = **$350/mês passivos**
""", encoding="utf-8")
    print(f"\n✅ {feitos} ebooks prontos em {OUT}")
    print(f"📖 Lê {OUT / 'README.md'} para passos de upload manual")


if __name__ == "__main__":
    main()
