/**
 * Gerador de Artigos SEO BR — MULTI-MARKETPLACE (Shopee + Mercado Livre + AliExpress + Hotmart)
 *
 * O quê: artigos PT-BR review/comparativo com links afiliados de 4 marketplaces brasileiros.
 *        Brasil = mercado gigante de compras online + comissões altas (Shopee 5-10%, ML 4-15%, Hotmart 30-80%).
 *
 * Receita esperada (após 3-6 meses):
 *   - 100 artigos × 50 visitas/dia × 5% CTR × 6% comissão × R$80 ticket = R$1200/dia (~R$36k/mês)
 *   - Realista 6 meses: 30% disso = R$10k/mês (~€1700/mês)
 *
 * Uso: node gerar-artigo-br.mjs [N=2]
 *
 * .env requer:
 *   SHOPEE_AFF_ID=  (https://affiliate.shopee.com.br)
 *   ML_AFF_TAG=     (https://www.mercadolivre.com.br/afiliados)
 *   ALIEXPRESS_AFF_ID= (https://portals.aliexpress.com)
 *   HOTMART_AFF_ID= (https://app-vlc.hotmart.com)
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const SITE = path.join(ROOT, 'site')

const envPath = path.join(ROOT, '.env')
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, 'utf-8').split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/)
    if (m) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
  }
}
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
if (!OPENAI_API_KEY) { console.error('OPENAI_API_KEY missing'); process.exit(1) }

// Affiliate IDs (placeholder se não definidos — links continuam a funcionar mas sem comissão)
const AFF = {
  shopee: process.env.SHOPEE_AFF_ID || '',
  ml: process.env.ML_AFF_TAG || '',
  ali: process.env.ALIEXPRESS_AFF_ID || '',
  hotmart: process.env.HOTMART_AFF_ID || '',
  amzBR: process.env.AMZ_TAG_BR || '', // Amazon BR opcional
}

// Constrói link de busca com tag afiliada para cada marketplace
// ML: usa matt_tool=affiliates_app + matt_word=USER (formato real do programa de afiliados ML BR)
// Shopee: ?af_id=XXX (formato real Shopee Affiliate Marketing Solution)
function buildLinks(kw) {
  const q = encodeURIComponent(kw)
  return {
    shopee: AFF.shopee
      ? `https://shopee.com.br/search?keyword=${q}&af_id=${AFF.shopee}&af_sub_siteid=&af_siteid=`
      : `https://shopee.com.br/search?keyword=${q}`,
    ml: AFF.ml
      ? `https://lista.mercadolivre.com.br/${q}?matt_tool=affiliates_app&matt_word=${AFF.ml}&matt_source=share`
      : `https://lista.mercadolivre.com.br/${q}`,
    ali: AFF.ali
      ? `https://pt.aliexpress.com/wholesale?SearchText=${q}&aff_short_key=${AFF.ali}`
      : `https://pt.aliexpress.com/wholesale?SearchText=${q}`,
    amzBR: AFF.amzBR
      ? `https://www.amazon.com.br/s?k=${q}&tag=${AFF.amzBR}`
      : `https://www.amazon.com.br/s?k=${q}`,
  }
}

// 60 keywords BR buyer-intent (compras 2026)
const KWS_BR = [
  // tech
  'melhor fone bluetooth 2026', 'melhor smartwatch barato 2026', 'melhor notebook custo beneficio 2026',
  'melhor smart tv 50 polegadas 2026', 'melhor cadeira gamer barata', 'melhor mouse sem fio 2026',
  'melhor teclado mecanico barato', 'melhor monitor para trabalhar home office',
  'melhor caixa de som bluetooth 2026', 'melhor power bank 2026',
  // casa
  'melhor air fryer 2026', 'melhor robo aspirador 2026', 'melhor liquidificador potente',
  'melhor cafeteira expresso domestica', 'melhor purificador de agua barato',
  'melhor ventilador de teto silencioso', 'melhor ar condicionado portatil',
  'melhor maquina de lavar 12kg', 'melhor geladeira frost free',
  // beleza/saude
  'melhor secador de cabelo profissional', 'melhor escova rotativa', 'melhor barbeador eletrico 2026',
  'melhor balanca digital corporal', 'melhor escova de dente eletrica',
  // fitness
  'melhor esteira ergometrica dobravel', 'melhor bicicleta ergometrica para casa',
  'melhor halter ajustavel', 'melhor faixa de resistencia kit',
  // bebê/mãe
  'melhor carrinho de bebe leve', 'melhor cadeirinha auto bebe',
  // moda
  'melhor tenis para correr feminino', 'melhor mochila masculina trabalho',
  // pet
  'melhor racao para gato castrado', 'melhor caixa de areia gato',
  // escritorio
  'melhor cadeira ergonomica home office', 'melhor mesa regulavel altura',
  // câmera/video
  'melhor camera de seguranca wifi', 'melhor webcam para live',
  // cozinha
  'melhor jogo de panelas antiaderente', 'melhor faca de chef profissional',
  // bebida
  'melhor garrafa termica 1 litro',
  // eletro pequeno
  'melhor aspirador vertical sem fio', 'melhor sanduicheira grill',
  'melhor processador de alimentos', 'melhor fritadeira sem oleo grande',
  // hotmart-friendly digital
  'curso online programacao do zero', 'curso ingles online intensivo',
  'curso de marketing digital pratico', 'curso de excel avancado',
  'curso de fotografia para iniciantes', 'ebook emagrecer sem dieta',
  'curso de yoga em casa', 'curso de design grafico canva',
  'curso de tarot iniciante', 'curso de confeitaria gourmet',
]

const HIST = path.join(ROOT, '_publicados-br.json')
const publicados = fs.existsSync(HIST) ? JSON.parse(fs.readFileSync(HIST, 'utf-8')) : []

function escolheKw() {
  const restantes = KWS_BR.filter(k => !publicados.includes(k))
  if (restantes.length === 0) return null
  return restantes[Math.floor(Math.random() * restantes.length)]
}

function slugify(s) {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 80)
}

async function gpt(messages, temperature = 0.85) {
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({ model: 'gpt-4o', temperature, messages }),
  })
  if (!r.ok) throw new Error(`OpenAI ${r.status}: ${await r.text()}`)
  const d = await r.json()
  return d.choices[0].message.content
}

async function gerarArtigoBR(kw) {
  const links = buildLinks(kw)
  const isCurso = /curso|ebook|aprender|aula/i.test(kw)
  // nichos onde Hotmart converte bem (cursos relacionados ao produto físico)
  const hotmartRelevant = /skincare|beleza|cabelo|emagrec|fitness|treino|investir|ingles|idioma|marketing|renda/i.test(kw)
  const hotmartLink = AFF.hotmart ? `https://go.hotmart.com/${AFF.hotmart}` : null

  const sys = 'Você é um reviewer brasileiro experiente que escreve em português do Brasil natural e fluido. NADA de "no mundo digital de hoje", "em conclusão" ou frases de IA. Escreva como uma pessoa real, com experiências pessoais específicas, gírias leves brasileiras (tipo "vale muito a pena", "bem bacana", "saiu por uma pechincha"), opinião honesta com prós e contras reais.'

  const linksText = isCurso
    ? `LINKS DE AFILIADO PARA INSERIR NATURALMENTE NO ARTIGO:
- Hotmart (cursos digitais): ${hotmartLink || 'https://hotmart.com/pt-br/marketplace'}
- Amazon BR (livros relacionados): ${links.amzBR}`
    : `LINKS DE AFILIADO PARA INSERIR NATURALMENTE NO ARTIGO (cada produto mencionado deve ter PELO MENOS 1 destes links como CTA):
- Shopee BR: ${links.shopee}  (use para produtos baratos/médios, CTA "Ver na Shopee")
- Mercado Livre BR: ${links.ml}  (use para entrega rápida BR, CTA "Conferir no Mercado Livre")
- AliExpress BR: ${links.ali}  (use para alternativa importada barata, CTA "Ver oferta AliExpress")
- Amazon BR: ${links.amzBR}  (use para premium, CTA "Comparar na Amazon")${hotmartRelevant && hotmartLink ? `
- Hotmart (curso digital relacionado): ${hotmartLink}  (mencione UMA vez como upsell, ex: "se quiser aprofundar, este curso ensina X", CTA "Ver curso completo")` : ''}`

  const instr = `Escreva artigo de 1500 palavras, título "${kw}", seguindo esta estrutura:

1. Intro pessoal (problema que você teve / por que esse produto importa) — 200 palavras
2. ${isCurso ? '5 cursos analisados' : 'Top 7 produtos analisados'} (cada um: subtítulo, 2 parágrafos com prós/contras reais, "para quem é melhor", e 1 link afiliado natural disfarçado de CTA)
3. Tabela comparativa em markdown
4. Guia de compra: o que olhar antes de comprar (5 critérios) — 250 palavras
5. FAQ (5 perguntas reais que o brasileiro faz) — cada resposta 50 palavras
6. Veredicto final + recomendação ${isCurso ? 'do melhor curso para iniciante' : 'do melhor custo-benefício, melhor premium e melhor barato'}

${linksText}

REGRAS:
- markdown válido com ## e ### para subtítulos
- nomes de produtos GENÉRICOS (não inventar marcas falsas; usar "modelo X popular", "marca conhecida Y")
- preços em R$ realistas para 2026
- NUNCA mencionar IA, ChatGPT, GPT
- usar "você" não "tu"`

  const md = await gpt([
    { role: 'system', content: sys },
    { role: 'user', content: instr },
  ], 0.9)

  return {
    md,
    desc: 'Análise independente e comparativo dos melhores produtos para 2026 com preços e onde comprar no Brasil.',
    links,
  }
}

async function main() {
  const n = parseInt(process.argv[2] || '2', 10)
  const dir = path.join(SITE, 'content/artigos-br')
  fs.mkdirSync(dir, { recursive: true })
  let feitos = 0
  for (let i = 0; i < n; i++) {
    const kw = escolheKw()
    if (!kw) { console.log('✅ Todas keywords BR feitas'); break }
    console.log(`📝 [${i+1}/${n}] BR — ${kw}`)
    try {
      const { md, desc } = await gerarArtigoBR(kw)
      const slug = `br-${slugify(kw)}`
      const fm = `---
title: "${kw}"
description: "${desc}"
date: "${new Date().toISOString().slice(0,10)}"
slug: "${slug}"
lang: "pt-BR"
keyword: "${kw}"
market: "brasil"
---

`
      fs.writeFileSync(path.join(dir, `${slug}.mdx`), fm + md)
      publicados.push(kw)
      fs.writeFileSync(HIST, JSON.stringify(publicados, null, 2))
      feitos++
      console.log(`   ✅ ${slug}.mdx`)
    } catch (e) {
      console.error(`   ⚠️  ${e.message}`)
    }
  }
  console.log(`\n✅ ${feitos} artigos BR (acumulado: ${publicados.length}/${KWS_BR.length})`)
}

main().catch(e => { console.error(e); process.exit(1) })
