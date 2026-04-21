# Motor B — POD Automatizado (Printify + Etsy)

## O que é

Pipeline que gera designs com IA (GPT-4 + DALL-E 3) e faz upload automático para Printify. A Printify publica na Etsy, imprime sob demanda e envia para o cliente. Você recebe a margem.

## Como funciona (fluxo completo)

```
GPT-4 (ideias: frase + tags + SEO)
     ↓
DALL-E 3 (imagem PNG 1024x1024)
     ↓
Printify API (cria produto camisa/poster/etc)
     ↓
Printify publica na Etsy (sua loja conectada)
     ↓
Cliente compra → Printify imprime → Printify envia
     ↓
💰 você recebe ~$8-15 de margem por camisa vendida
```

## Setup inicial (uma vez — ~2h)

### 1. Criar contas
- **Printify**: https://printify.com (grátis)
- **Etsy**: https://www.etsy.com/sell (taxa de abertura $15, mas perdoada com código promocional referral)
- **Conectar Etsy ↔ Printify**: Printify dashboard → Stores → Add new → Etsy

### 2. Obter API key do Printify
- Printify → My account → Connections → API → **Generate new token**
- Shop ID: Printify → Stores → ver URL, o número após /store/

### 3. Escolher blueprints (tipos de produto)
Visite: https://api.printify.com/v1/catalog/blueprints.json (abrir no browser, é público)

Para camisas unissex, recomendo:
- **Blueprint 384** — Unisex Heavy Cotton Tee (Gildan 5000)
- **Provider 29** — Monster Digital (entrega rápida EU)

Para posters:
- **Blueprint 97** — Enhanced Matte Paper Poster
- **Provider 2** — Sensaria (EU)

⚠️ **Verifique providers disponíveis em Portugal/Europa** antes de escolher — envio de USA para PT demora 15+ dias.

### 4. Configurar .env
```bash
cp .env.example .env
# Editar .env com suas keys
```

### 5. Instalar dependências
```bash
npm install
```

## Usar o pipeline

### Gerar designs (só geração, ainda não publica)
```bash
node gerador-designs/gerar.mjs frases-motivacionais-pt 5
# Cria 5 PNGs + 5 JSONs em designs/frases-motivacionais-pt/
# Custo: ~$0.40 (GPT-4) + 5 × $0.08 (DALL-E HD) = ~$0.80
```

### Fazer upload para Printify (os PNGs já gerados)
```bash
node uploader-printify/upload.mjs frases-motivacionais-pt
# Cria produtos na sua loja Printify e publica na Etsy
```

### Pipeline completo (ideias → designs → publicação)
```bash
node pipeline.mjs frases-motivacionais-pt 10
```

## Nichos incluídos (editar em `nichos.json`)

| ID | Nicho | Idioma | Produtos |
|---|---|---|---|
| `frases-motivacionais-pt` | Motivacional | PT-PT | Camisa, Poster |
| `futebol-portugal` | Futebol | PT-PT | Camisa |
| `cafe-lisboa` | Café/Lisboa | PT-PT | Camisa, Poster |
| `programadores-br` | Dev humor | PT-BR | Camisa |
| `pets-engracados` | Pets | PT-BR | Camisa, Poster |

## Estratégia de escala

### Semana 1: validar que tudo funciona
- Gerar 10 designs do nicho `frases-motivacionais-pt`
- Upload e verificar no Etsy se aparecem certos
- Comprar 1 você mesmo para testar qualidade de impressão

### Semana 2-4: escalar
- 20 designs/dia, 5 dias por semana = 100/semana
- Variar nichos (não fazer só 1)
- Meta: 500 listings ativas fim do mês 2

### Mês 3+: otimizar
- Ver quais designs vendem no Etsy Stats
- Descontinuar os que não vendem em 60 dias
- Criar variações dos vencedores (mesmo design, cores/fontes diferentes)

## Regras de ouro

1. **NUNCA use marcas ou nomes de pessoas famosas** (jogadores, cantores). Etsy e Printify banem e pode haver processos.
2. **NUNCA use imagens protegidas** (logos de clubes, personagens Disney, etc).
3. **Sempre revise os primeiros 20 designs manualmente** antes de publicar — DALL-E às vezes erra texto.
4. **Etsy tem taxa de $0.20 por listing**, e renovação a cada 4 meses ($0.20 de novo). 100 listings = $20, renovação $60/ano.
5. **Printify não cobra mensalidade**. Só paga por produto vendido.

## Quanto vai faturar (realista)

| Mês | Listings ativas | Vendas/mês | Margem média | Lucro líquido |
|---|---|---|---|---|
| 1 | 50-100 | 0-2 | $10 | $0-20 |
| 2 | 200 | 3-10 | $10 | $30-100 |
| 3 | 400 | 10-30 | $10 | $100-300 |
| 6 | 800 | 40-80 | $10 | $400-800 |
| 12 | 1500+ | 100-300 | $10 | $1000-3000 |

A taxa de conversão no Etsy é ~1-3% por 1000 views. A maioria dos designs NÃO vai vender — o lucro vem dos 5-10% que viram hits.

## Custos operacionais mensais (depois de montado)

- OpenAI API (100 designs/mês): ~$15
- Etsy renovações: ~$5/mês em regime
- Printify: $0
- **Total: ~$20/mês** de custos fixos

Por isso, com 3-4 vendas/mês já compensa os custos.
