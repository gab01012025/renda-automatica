# 💰 Renda Automática — Estado Atual

> Atualizado: 23 abril 2026

## 🟢 Sistemas LIVE em produção

### 1. POD (Print On Demand) — Etsy
- **Loja**: [PrintHouseLX](https://etsy.com/shop/PrintHouseLX) — ID 27267952
- **Produtos**: ~169 (119 antes + 50 novos: casamento + profissões + astrologia + maternidade + aniversários)
- **Pipeline**: GPT-4o + DALL-E 3 + PIL + Printify API
- **Custo por design**: ~$0.04 (texto + imagem)
- **Margem por venda**: ~€8-15

### 2. Site Afiliados
- **URL**: https://renda-automatica.vercel.app
- **Artigos**: 10 (8 antigos + 2 novos: melhores-geradores-ia, vender-templates-notion)
- **Stack**: Next.js 14 + MDX + Tailwind
- **Monetização**: links afiliados Etsy + Gumroad + ferramentas IA

### 3. Pinterest Marketing
- **Conta**: PrintHouseLX (Portugal, EUR)
- **Pins gerados**: 37 prontos em `pod-automatico/pinterest/pins-prontos/`
- **Campanha paga**: €20 Mundial PT 2026 (em revisão Pinterest)
- **CSV**: `pins-pinterest-upload.csv`

### 4. 🆕 Micro-SaaS EtsyDescAI
- **URL**: https://micro-saas-etsy.vercel.app
- **O que faz**: gera título + descrição + 13 tags Etsy em segundos (GPT-4o-mini)
- **Modelo**: 3 grátis por sessão, depois €5/mês (Stripe a integrar)
- **Custo OpenAI**: ~$0.0003 por geração → margem 98%
- **Status**: ✅ funcional, testado em produção

### 5. 🆕 Produtos Digitais Gumroad
- **3 PDFs prontos** em `produtos-digitais/pdfs/`:
  - 100 Prompts ChatGPT Programadores (€9, 88KB)
  - 150 Prompts Marketing PT (€12, 116KB)
  - Bundle 300 Prompts AI (€19, 160KB)
- **Setup pendente**: criar conta Gumroad + upload (instruções em `COMO-VENDER-NO-GUMROAD.md`)
- **Margem**: 90% (Gumroad fica com 10%)

### 6. 🆕 Cron Noturno Always-On
- **Workflow**: `.github/workflows/cron-noturno.yml`
- **Schedule**: todos os dias às 03:00 UTC
- **O que faz automaticamente**:
  - 3 designs novos (nicho rotativo)
  - Upload Printify → Etsy
  - 3 pins Pinterest
  - 1 artigo SEO
  - Commit + push + deploy Vercel
- **Setup pendente**: adicionar 5 secrets no GitHub (instruções em `.github/CRON-SETUP.md`)
- **Custo**: ~$9/mês OpenAI

---

## 📋 Próximas Ações Manuais (Gabriel)

### Hoje/Amanhã (15 min)
1. ✅ **Verificar produtos novos no Etsy** (50 designs novos: casamento/profissões/astrologia/maternidade/aniversários)
2. ✅ **Visitar https://micro-saas-etsy.vercel.app** e testar
3. ✅ **Visitar https://renda-automatica.vercel.app** e ver os 2 artigos novos

### Esta semana (1h)
4. **Criar conta Gumroad** + upload dos 3 PDFs (instruções em `produtos-digitais/COMO-VENDER-NO-GUMROAD.md`)
5. **Configurar cron noturno**: GitHub Settings → Secrets → adicionar 5 secrets (instruções em `.github/CRON-SETUP.md`)
6. **Continuar upload Pinterest** (5 pins/dia, 32 restantes)

### Quando tiver vendas Etsy + Gumroad
7. **Integrar Stripe no micro-saas** para subscrições €5/mês
8. **Criar 2º site afiliados nicho** (proposta: melhoresvpns-pt.vercel.app)

---

## 💸 Realidade dos Números

Baseado em projeções reais 2026 (não promessas):

| Mês | Etsy POD | Gumroad PDFs | Micro-SaaS | Site Afiliados | **Total** |
|---|---|---|---|---|---|
| 1 | €0-50 | €0-30 | €0 | €0 | **€0-80** |
| 3 | €100-300 | €50-200 | €0-50 | €20-100 | **€170-650** |
| 6 | €300-800 | €200-600 | €100-400 | €100-300 | **€700-2100** |
| 12 | €500-1500 | €500-1500 | €300-1000 | €300-800 | **€1600-4800** |

**Importante**: nada disto está garantido. Depende de execução constante (Pinterest diário, novas listings, SEO).

---

## 🎯 Filosofia

- **Não vender sonho**: sistemas reais, números honestos
- **Automação > volume**: cron noturno trabalha enquanto descansas
- **Múltiplas fontes**: 5 canais diferentes diluem risco
- **Reutilização**: mesmos designs vendem em Etsy + Pinterest + servem de conteúdo para artigos
