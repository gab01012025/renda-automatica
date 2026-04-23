# 💳 Próximo Passo: Adicionar Stripe ao Micro-SaaS

Quando tiveres 10+ utilizadores grátis usando, é hora de cobrar.

## Setup (30 min, depois passivo)

### 1. Criar conta Stripe
- https://stripe.com → Sign up
- Verificar país: Portugal
- IBAN para receber pagamentos

### 2. Criar produto Stripe
- Products → Add product
- Nome: "EtsyDescAI Premium"
- Preço: €5/mês (recurring)
- Copiar o `price_id` (começa com `price_...`)

### 3. Adicionar ao Vercel
```bash
cd micro-saas-etsy
vercel env add STRIPE_SECRET_KEY production    # sk_live_...
vercel env add STRIPE_WEBHOOK_SECRET production # whsec_...
vercel env add STRIPE_PRICE_ID production       # price_...
```

### 4. Instalar dependência
```bash
npm install stripe
```

### 5. Criar API routes
- `app/api/checkout/route.ts` — cria sessão Stripe Checkout
- `app/api/webhook/route.ts` — recebe eventos (subscription.created/deleted)
- Database simples: KV Vercel ou Supabase grátis

### 6. UI: botão "Upgrade €5/mês" quando atinge limite

## Quanto rende?

100 utilizadores grátis × 3% conversão = **3 subs × €5 = €15/mês**

500 utilizadores grátis × 5% conversão = **25 subs × €5 = €125/mês**

Custo OpenAI por sub: ~€0.50/mês → **margem 90%**

## Aquisição de utilizadores

1. **SEO**: artigo "Como gerar descrições Etsy SEO em PT" (já tens estrutura no site afiliados)
2. **Pinterest**: pins promovendo o tool
3. **Reddit r/Etsy** + r/portugal (sem spam, partilhar valor)
4. **Cross-link**: micro-saas linka para Etsy + site afiliados linka para micro-saas

---

**Status atual**: tool live em https://micro-saas-etsy.vercel.app, sem Stripe ainda. Funciona como lead magnet para a tua loja Etsy.
