# EtsyDescAI — Micro-SaaS

Gerador IA de títulos, descrições e tags Etsy em português. Powered by GPT-4o-mini.

## Run local

```bash
npm install
echo "OPENAI_API_KEY=sk-..." > .env.local
npm run dev
```

## Deploy Vercel

```bash
vercel --prod
# adicionar OPENAI_API_KEY nas env vars Vercel
```

## Modelo de Negócio

- **Free tier**: 3 gerações por sessão (sem registo) — drives traffic
- **Premium €5/mês**: ilimitado + histórico (próxima feature, integrar Stripe)
- **Custo OpenAI**: ~$0.0003 por geração com gpt-4o-mini → margem ~98%

## SEO Strategy

- Keyword principal: "gerador descrições etsy português"
- Long tail: "como escrever título etsy SEO 2026"
- Ranking via afiliados-ia (linkagem cruzada com renda-automatica.vercel.app)
