# KDP — Pronto para Upload

5 ebooks preparados em `kdp-pronto-upload/<id>/`:

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
