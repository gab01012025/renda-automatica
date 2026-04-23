# 🤖 Cron Noturno — Setup Instructions

Workflow em `.github/workflows/cron-noturno.yml` corre **todos os dias às 03:00 UTC** (04:00 Lisboa) e gera automaticamente:

- 3 designs novos (nicho rotativo)
- Upload Printify → Etsy
- 3 pins Pinterest novos
- 1 artigo SEO novo
- Commit + push + deploy Vercel

## Setup (1× único)

No GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:

| Nome | Valor |
|---|---|
| `OPENAI_API_KEY` | `sk-...` (mesma do `.env`) |
| `PRINTIFY_API_KEY` | (mesma do `pod-automatico/.env`) |
| `VERCEL_TOKEN` | obter em https://vercel.com/account/tokens |
| `VERCEL_ORG_ID` | `cat afiliados-ia/site/.vercel/project.json` |
| `VERCEL_PROJECT_ID` | (idem) |

Depois disto, o sistema funciona 100% autónomo. Custo: ~$0.30/dia OpenAI = ~$9/mês.

## Trigger manual (testar agora)

GitHub repo → **Actions → Cron Noturno → Run workflow**

## Monitorização

Cada execução aparece em **Actions** com logs completos. Falhas em qualquer step não param os outros (todos têm `|| echo`).

## Como desativar temporariamente

Comentar a linha `- cron: '0 3 * * *'` no `.yml` ou Settings → Actions → Disable.
