# Motor A — Site de Afiliados IA em Português

## O que é

Site Next.js 14 que publica artigos SEO sobre ferramentas de IA com links de afiliado. Artigos são gerados automaticamente pelo GPT-4 e publicados via GitHub Actions uma vez por semana.

## Estrutura

```
afiliados-ia/
├── site/                          # Next.js (o site público)
│   ├── app/                       # Rotas
│   ├── content/artigos/*.mdx      # Conteúdo publicado
│   └── package.json
├── gerador/
│   ├── temas.json                 # Banco de temas + ferramentas + afiliados
│   ├── gerar-artigo.mjs           # Gera 1 artigo via GPT-4
│   └── gerar-lote.mjs             # Gera N artigos
├── .env.example                   # Copiar para .env e preencher
└── .gitignore
```

## Setup local (1ª vez)

```bash
cd afiliados-ia

# 1. Configurar secrets
cp .env.example .env
# Edite .env e coloque a sua OPENAI_API_KEY

# 2. Instalar dependências
cd site
npm install

# 3. Rodar o site localmente
npm run dev
# → abre http://localhost:3000
```

## Gerar artigos manualmente

```bash
cd afiliados-ia

# Gerar 1 artigo (tema aleatório ainda não publicado)
node gerador/gerar-artigo.mjs

# Gerar artigo de tema específico
node gerador/gerar-artigo.mjs "ChatGPT"

# Gerar 5 artigos em lote
node gerador/gerar-lote.mjs 5
```

Cada artigo custa ~$0.10-0.20 em OpenAI API (GPT-4o). Com €30 de crédito dá para 150-300 artigos.

## Publicar online (Vercel)

```bash
cd site
npm install -g vercel
vercel --prod
```

Ou use o GitHub:
1. Faça push do repo para GitHub
2. Em https://vercel.com/new importe o repo
3. **Importante:** em "Root Directory" selecione `afiliados-ia/site`
4. Deploy automático a cada push

## Ativar publicação automática (grátis)

1. Subir o repo para GitHub
2. Settings → Secrets and variables → Actions → adicionar:
   - `OPENAI_API_KEY`
   - `AFILIADO_HOSTINGER`, `AFILIADO_JASPER`, etc. (se já tiver)
3. Pronto. O workflow em `.github/workflows/publicar-artigo.yml` roda toda segunda-feira às 9h e publica 1 artigo novo.

Para testar já, vá em Actions → "Publicar artigo semanal" → "Run workflow".

## Programas de afiliados para se inscrever

| Programa | Comissão | Link inscrição |
|---|---|---|
| Hostinger | 60% primeira venda | https://www.hostinger.com/afiliados |
| Jasper AI | 30% recorrente | https://www.jasper.ai/partners |
| ElevenLabs | 20% | https://elevenlabs.io/partner |
| Amazon Afiliados PT | 3-10% por categoria | https://afiliados.amazon.es |
| Awin (Portugal) | variável, muitas marcas | https://www.awin.com |
| Impact.com | muitas marcas IA | https://impact.com |

Depois de aprovado, ponha os IDs no `.env` (e nos Secrets do GitHub) — os artigos novos vão usar automaticamente.

## Escalar para 2 artigos/semana

Edite `.github/workflows/publicar-artigo.yml`, troque a linha:
```yaml
- cron: '0 9 * * 1'
```
para:
```yaml
- cron: '0 9 * * 1,4'   # Segunda e quinta
```

## Adicionar novos temas

Editar `gerador/temas.json`, secção `temas`. Formato:
```json
{
  "titulo": "Título SEO-friendly",
  "tipo": "review | tutorial | comparativo | lista | guia",
  "ferramentas": ["chatgpt", "claude"],
  "keyword": "palavra-chave-principal"
}
```

## Quando começa a dar dinheiro

- **Mês 1-2:** 0€ (Google ainda a indexar, sem tráfego)
- **Mês 3-4:** primeiros €10-50 (tráfego começa)
- **Mês 6:** €100-500 (artigos antigos ganham ranking)
- **Mês 12:** €500-3000 (se mantiver cadência)

**Atalho para acelerar:** responder perguntas em fóruns PT (Reddit r/portugal, r/brasil, Quora em PT) linkando para artigos do site sempre que fizer sentido. Tráfego direto + sinal positivo pro Google.
