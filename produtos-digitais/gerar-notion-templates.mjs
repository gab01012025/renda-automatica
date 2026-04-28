#!/usr/bin/env node
/**
 * Gerador de Notion Templates Premium para Gumroad
 *
 * O quê: gera templates Notion ricos (markdown estruturado que utilizador importa)
 *        + capa visual + descrição Gumroad SEO-otimizada
 * Porquê: mercado Notion templates explodiu PT/BR/EU. €9-€39 por template, zero suporte.
 *
 * Uso: node gerar-notion-templates.mjs [N=2]
 * Output: produtos-digitais/notion-templates/<slug>/{template.md, descricao.txt, capa-prompt.txt}
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const OUT_DIR = path.join(ROOT, 'produtos-digitais', 'notion-templates')
fs.mkdirSync(OUT_DIR, { recursive: true })

// Carregar .env
const envPath = path.join(__dirname, '.env')
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, 'utf-8').split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/)
    if (m) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
  }
}
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
if (!OPENAI_API_KEY) throw new Error('OPENAI_API_KEY missing')

// Banco de templates rotacionados — alvos de alta procura PT/EU
const TEMPLATES = [
  { slug: 'planner-financeiro-pt', titulo: 'Planner Financeiro Pessoal 2026 PT', publico: 'pessoas em Portugal/Brasil que querem controlo financeiro', preco: 14, lang: 'pt-PT' },
  { slug: 'gestao-freelancer-workana', titulo: 'Gestão Completa Freelancer Workana/Upwork', publico: 'freelancers PT/BR que querem organizar clientes, propostas e cobranças', preco: 19, lang: 'pt-PT' },
  { slug: 'estudo-concurso-publico', titulo: 'Painel de Estudos para Concursos Públicos PT/BR', publico: 'estudantes para concursos públicos e Enem', preco: 12, lang: 'pt-BR' },
  { slug: 'fitness-tracker-pt', titulo: 'Fitness e Dieta Tracker Notion PT', publico: 'pessoas que querem perder peso ou ganhar massa', preco: 9, lang: 'pt-PT' },
  { slug: 'crm-pequeno-negocio', titulo: 'CRM Simples para Pequeno Negócio PT', publico: 'donos de pequenos negócios em Portugal sem orçamento para HubSpot', preco: 24, lang: 'pt-PT' },
  { slug: 'second-brain-pt', titulo: 'Second Brain Português — Sistema PARA Completo', publico: 'knowledge workers que querem organizar ideias e projetos', preco: 19, lang: 'pt-PT' },
  { slug: 'planner-casamento-pt', titulo: 'Planner de Casamento PT — Lista Completa', publico: 'noivos a planear casamento em Portugal', preco: 17, lang: 'pt-PT' },
  { slug: 'content-creator-pt', titulo: 'Dashboard Criador de Conteúdo PT (TikTok+IG+YT)', publico: 'criadores de conteúdo em PT que querem organizar posts', preco: 15, lang: 'pt-PT' },
  { slug: 'investidor-bolsa-pt', titulo: 'Tracker Investidor Bolsa e ETFs PT (IRS Friendly)', publico: 'investidores particulares em Portugal', preco: 22, lang: 'pt-PT' },
  { slug: 'finanzplaner-de', titulo: 'Finanzplaner 2026 für Deutschland', publico: 'Deutsche die ihre Finanzen organisieren wollen', preco: 17, lang: 'de-DE' },
  { slug: 'freelancer-deutschland', titulo: 'Freelancer Komplett-System Deutschland', publico: 'Freelancer in DE/AT/CH', preco: 24, lang: 'de-DE' },
  { slug: 'budget-france', titulo: 'Budget Personnel 2026 France', publico: 'francais qui veulent gerer leur budget', preco: 14, lang: 'fr-FR' },
]

const _hist = path.join(OUT_DIR, '_gerados.json')
const gerados = fs.existsSync(_hist) ? JSON.parse(fs.readFileSync(_hist, 'utf-8')) : []

function pickRotacao(n) {
  const naoFeitos = TEMPLATES.filter(t => !gerados.includes(t.slug))
  if (naoFeitos.length >= n) return naoFeitos.slice(0, n)
  return [...naoFeitos, ...TEMPLATES.slice(0, n - naoFeitos.length)]
}

async function gpt(messages, temperature = 0.8) {
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({ model: 'gpt-4o', temperature, messages }),
  })
  if (!r.ok) throw new Error(`OpenAI ${r.status}: ${await r.text()}`)
  const data = await r.json()
  return data.choices[0].message.content
}

async function gerarTemplateNotion(t) {
  const sys = `Es um expert em Notion templates premium vendidos no Gumroad/Etsy. Gera um template Notion COMPLETO em markdown rico, pronto para o comprador importar via "Import from markdown" no Notion. Linguagem: ${t.lang}.

REGRAS:
- Estrutura realista de databases (usa tabelas markdown), galleries, kanban descritivos
- Inclui valores de exemplo realistas (nao "lorem ipsum")
- Cabecalhos H1/H2/H3 organizados
- Use emojis estrategicamente (1 por seccao, nao spam)
- Inclui formulas Notion onde fizer sentido (com sintaxe correta)
- Inclui callouts /quote / /toggle como markdown
- Tom profissional mas acessivel
- Minimo 1500 palavras de conteudo real`

  const user = `Cria template completo: "${t.titulo}". Publico: ${t.publico}. Preco final: €${t.preco}.

Inclui obrigatoriamente:
1. Pagina de boas-vindas com instrucoes
2. 3-5 databases interligadas (com colunas tipadas: Select, Multi-select, Date, Number, Formula, Relation)
3. Dashboard com views (Calendario, Kanban, Lista, Galeria descritos)
4. Pelo menos 5 entries de exemplo em cada database
5. Seccao de tutoriais "Como personalizar"
6. FAQ
7. Notas finais com convite a deixar review`

  return gpt([{ role: 'system', content: sys }, { role: 'user', content: user }], 0.85)
}

async function gerarDescricaoGumroad(t) {
  const sys = `Es um copywriter que vende Notion templates no Gumroad. Cria descricao em ${t.lang} com:
- Headline magnetico (1 linha)
- Pain point + solucao (2 paragrafos)
- O que esta incluido (lista bullet com 8-12 itens com emojis)
- Para quem e (3 perfis)
- Reviews simuladas (3 reviews realistas com nome+localizacao)
- Bonus (2 bonus inclusos no pack)
- Garantia (devolucao 30 dias)
- CTA forte
- Tags Gumroad no final (10 tags relevantes separadas por virgula)`

  const user = `Cria descricao Gumroad para "${t.titulo}" (preco €${t.preco}). Publico: ${t.publico}.`
  return gpt([{ role: 'system', content: sys }, { role: 'user', content: user }], 0.9)
}

async function gerarPromptCapa(t) {
  return `professional Notion template cover image, modern minimal design, soft pastel gradient background (sage green to cream), centered title "${t.titulo}" in bold sans-serif, small Notion-style icon (clipboard or sparkle), clean editorial layout, 1280x720 aspect ratio, no real Notion logo, no copyrighted icons, premium SaaS aesthetic`
}

async function main() {
  const n = parseInt(process.argv[2] || '2', 10)
  const escolhidos = pickRotacao(n)
  console.log(`📓 Notion Templates — gerar ${escolhidos.length}`)
  for (const t of escolhidos) {
    const dir = path.join(OUT_DIR, t.slug)
    if (fs.existsSync(path.join(dir, 'template.md'))) {
      console.log(`   ⏭️  ${t.slug} ja existe, skip`)
      continue
    }
    fs.mkdirSync(dir, { recursive: true })
    console.log(`   ⚙️  ${t.slug}: gerar template...`)
    const tmpl = await gerarTemplateNotion(t)
    fs.writeFileSync(path.join(dir, 'template.md'), tmpl)
    console.log(`   ✍️  ${t.slug}: gerar descricao Gumroad...`)
    const desc = await gerarDescricaoGumroad(t)
    fs.writeFileSync(path.join(dir, 'descricao.txt'), desc)
    fs.writeFileSync(path.join(dir, 'capa-prompt.txt'), await gerarPromptCapa(t))
    fs.writeFileSync(path.join(dir, 'meta.json'), JSON.stringify(t, null, 2))
    if (!gerados.includes(t.slug)) gerados.push(t.slug)
    fs.writeFileSync(_hist, JSON.stringify(gerados, null, 2))
    console.log(`   ✅ ${t.slug} pronto: ${dir}`)
  }
  console.log(`\n✅ Total templates gerados: ${gerados.length}/${TEMPLATES.length}`)
  console.log(`👉 Proximo: cria conta Gumroad/LemonSqueezy, faz upload de cada pasta como produto separado.`)
}

main().catch(e => { console.error(e); process.exit(1) })
