# 💰 Novas Fontes de Renda Ativadas

Geradas hoje, prontas para upload. Trabalho manual: **~30 min total**.

---

## 1. 📚 KDP — 5 Ebooks Amazon Kindle

**Pasta:** `kdp-ebooks/ebooks/`

| Ebook | Língua | Preço | Ficheiros |
|-------|--------|-------|-----------|
| ChatGPT para Advogados | PT | €4.99 | `chatgpt-advogados-pt.pdf` + `-capa.png` |
| ChatGPT para Imobiliárias | PT | €4.99 | `chatgpt-imobiliaria-pt.pdf` + `-capa.png` |
| Copywriting com IA | PT | €3.99 | `copywriting-ia-pt.pdf` + `-capa.png` |
| Excel turbinado com IA | PT | €4.99 | `excel-ia-pt.pdf` + `-capa.png` |
| Low-Carb Recipes (100) | EN | €3.99 | `receitas-low-carb-ia-en.pdf` + `-capa.png` |

### Como publicar (5 min cada):
1. https://kdp.amazon.com → Sign in (cria conta se não tens, é grátis)
2. **Create** → **Kindle eBook**
3. **Title:** copia do nome do ficheiro
4. **Description:** abre o `.md` correspondente, copia a Introdução
5. **Categories:** Self-Help → Personal Transformation (PT); Cookbooks (EN)
6. **Keywords (7):** "ChatGPT português", "IA Portugal", "prompts AI", etc.
7. **Upload manuscript:** carrega o `.pdf`
8. **Upload cover:** carrega o `-capa.png`
9. **Pricing:** 70% royalty, €3.99-4.99 (€2.99-9.99 elegíveis)
10. **Publish** → 4-72h em revisão Amazon, depois live

**Estimativa:** €30-150/mês por ebook depois de 2-3 meses de SEO orgânico Amazon.

---

## 2. 🎬 YouTube Shorts Faceless (automático no cron)

**Pasta:** `youtube-faceless/videos/`

Gera **1 Short por dia** automaticamente (após cron ativo):
- Script GPT-4o (PT-PT, 45-55s)
- Voz natural pt-PT (edge-tts grátis)
- Imagem fundo DALL-E 3 (vertical 9:16)
- Vídeo MP4 1080x1920 pronto para YouTube

### Setup canal (1x):
1. https://studio.youtube.com → criar canal **"Curiosidades IA"** ou similar
2. Logo: usa qualquer imagem `-bg.png` da pasta
3. Descrição: "Curiosidades sobre Inteligência Artificial em 60 segundos. Vídeos diários."

### Upload diário (2 min/vídeo):
1. https://studio.youtube.com → **CREATE → Upload videos**
2. Arrasta o `.mp4` mais recente
3. Abre o `.json` com mesmo nome → copia título, descrição, tags
4. Marca **"Yes, it's made for kids"** = NÃO
5. **Visibility: Public** → Publish

**Monetização:** após 1000 subs + 4000h watchtime (Shorts contam para o feed). Estima-se €50-300/mês quando ativa.

### Próximo passo (opcional, posso automatizar):
- YouTube Data API v3 → upload automático (precisa OAuth uma vez)

---

## 3. 📡 Cross-post — Medium + Dev.to + Hashnode

**Script:** `cross-post/cross-post.mjs`

Republica **automaticamente** os 10 artigos do site `renda-automatica.vercel.app` em 3 plataformas (com `canonical_url` apontando para o original — sem penalização SEO).

### Setup (5 min):
Adiciona estes secrets no GitHub (https://github.com/gab01012025/renda-automatica/settings/secrets/actions):

| Secret | Como obter |
|--------|-----------|
| `MEDIUM_TOKEN` | https://medium.com/me/settings/security → "Integration tokens" → cria "renda-auto" |
| `DEVTO_TOKEN` | https://dev.to/settings/extensions → "DEV Community API Keys" → Generate |
| `HASHNODE_TOKEN` | https://hashnode.com/settings/developer → "Personal Access Tokens" → Generate |
| `HASHNODE_PUB_ID` | (opcional) ID da tua publicação Hashnode, vê na URL `hashnode.com/...` |

Faz commit com 1 token só (Medium é o mais fácil) e o cron noturno publica sozinho diariamente.

**Receita:** Medium Partner Program paga por tempo de leitura (~€0.01-0.05/min lido). Com 10 artigos × 2-5 min × 100-500 leituras/mês = €5-50/mês passivo.

---

## 4. ✅ Cron Noturno — Status

O workflow `.github/workflows/cron-noturno.yml` agora corre **diariamente às 03:00 UTC**:

1. ✓ 3 designs POD (nicho rotativo)
2. ✓ Upload Printify auto-publish
3. ✓ 3 pins Pinterest
4. ✓ 1 artigo SEO novo
5. ✓ **NOVO:** Cross-post Medium/Dev.to/Hashnode
6. ✓ **NOVO:** 1 YouTube Short
7. ✓ Commit + push
8. ✓ Deploy Vercel

**Para ativar:** verifica conta GitHub (SMS) em https://github.com/settings/billing e clica em "Run workflow" no repo Actions.

---

## 📊 Receita estimada total (cumulativa, 6 meses)

| Stream | Mês 1 | Mês 3 | Mês 6 |
|--------|-------|-------|-------|
| Etsy POD (200 produtos) | €50 | €200 | €500 |
| Afiliados site (cross-post) | €5 | €30 | €100 |
| Gumroad PDFs (3) | €20 | €80 | €150 |
| **KDP ebooks (5) NOVO** | €0 | €100 | €400 |
| **YouTube Shorts NOVO** | €0 | €0 | €100 |
| **Medium Partner NOVO** | €5 | €25 | €60 |
| Micro-SaaS EtsyDescAI | €0 | €30 | €100 |
| **TOTAL/mês** | **€80** | **€465** | **€1.410** |

Tudo passivo após setup inicial. 🚀
