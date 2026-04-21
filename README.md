# 🤖 Sistema de Renda Automatizada — Gabriel

**Dois motores em paralelo, ambos 90% automáticos depois de montados:**

- 🔵 **Motor A** — Site de afiliados sobre "Ferramentas de IA em Português" (tráfego orgânico → comissões)
- 🟢 **Motor B** — Print-on-Demand automatizado (designs IA → Printify → Etsy)

---

## 💰 Orçamento de €200 — como aplicar

| Item | Custo | Onde |
|---|---|---|
| Domínio `.pt` afiliados (1 ano) | €10 | Dominios.pt ou Cloudflare |
| OpenAI API (créditos iniciais) | €30 | platform.openai.com |
| Etsy setup + primeiras 20 listings | €5 | etsy.com ($0,20 por listing) |
| Cloudflare Workers (opcional, escala) | €0 | cloudflare.com |
| Vercel hosting | €0 | vercel.com (grátis) |
| Printify conta | €0 | printify.com |
| **Reserva operacional (ads, imprevistos, APIs extra)** | **€155** | — |
| **TOTAL fixo inicial** | **€45** | |

A reserva de €155 vai aguentar 3-4 meses de APIs com folga e permite testar €30-50 em anúncios Pinterest (tráfego barato pra POD).

---

## ⏱️ Cronograma realista

| Mês | Motor A (Afiliados) | Motor B (POD) | Renda esperada |
|---|---|---|---|
| 1 | Setup + primeiros 20 artigos | Setup + 50 designs + 20 listings | €0-30 |
| 2 | 40 artigos, Google começa a indexar | 100 listings, primeiras vendas | €20-100 |
| 3 | 60 artigos, primeiro tráfego | Escala pra 200 listings | €50-250 |
| 6 | 120 artigos, SEO maduro | 500 listings, top sellers identificados | €300-1.000 |
| 12 | Autoridade estabelecida | Coleções premium | €800-3.000 |

**Importante:** primeiros 2 meses vão parecer que não funciona. **É normal.** SEO e Etsy levam tempo. Não desista antes do mês 3.

---

## 📁 Estrutura

```
novo test2/
├── README.md                   ← você está aqui
├── GUIA-SETUP.md               ← passo-a-passo completo
├── afiliados-ia/               ← Motor A
│   ├── site/                   ← Next.js 14 + MDX (o site em si)
│   ├── gerador/                ← Scripts de geração automática
│   └── README.md
└── pod-automatico/             ← Motor B
    ├── gerador-designs/        ← DALL-E → PNGs
    ├── uploader-printify/      ← PNG → Printify → Etsy
    ├── nichos.json             ← configuração de temas
    └── README.md
```

---

## 🎯 Como a automação funciona (visão geral)

### Motor A — Afiliados IA
1. Cron semanal (GitHub Actions, grátis) dispara
2. Script pega temas de `temas.json` (ex: "Melhor ChatGPT alternativa em português")
3. GPT-4 gera artigo MDX de 1500 palavras com links de afiliado
4. Script faz commit no repo → Vercel redeploy automático
5. Artigo ao vivo em 2 minutos, sem você tocar

### Motor B — POD
1. Script pega ideias de `nichos.json` (ex: "frases motivacionais PT")
2. GPT-4 cria 20 frases criativas
3. DALL-E 3 gera imagem/design para cada
4. Script faz upload para Printify (cria produto)
5. Printify publica no Etsy automaticamente
6. Cliente compra → Printify imprime e envia → você recebe margem

---

## ⚠️ Expectativa REAL

- Mês 1-2: você vai duvidar que funciona. Confie no processo, só rode os scripts.
- Mês 3-4: primeiras vendas chegam. Vai parecer pouco. É normal.
- Mês 6+: bola de neve. Conteúdo antigo gera renda sem você fazer nada.
- Mês 12+: se mantiver, €1k-3k/mês é realista. Sem garantias.

**Regra de ouro:** se você parar de rodar os geradores, o sistema seca. Automatizado ≠ esquecido. São 2-4h/semana de manutenção (revisar qualidade, atualizar temas, responder 1-2 emails Etsy/semana).

---

## 🚦 Próximos passos (ordem correta)

1. Ler [GUIA-SETUP.md](GUIA-SETUP.md) inteiro
2. Criar contas (OpenAI, Printify, Etsy, Vercel, GitHub)
3. Comprar domínio
4. Setup Motor A: `cd afiliados-ia/ && cat README.md`
5. Setup Motor B: `cd pod-automatico/ && cat README.md`
6. Rodar primeira geração e DEIXAR NO AR
