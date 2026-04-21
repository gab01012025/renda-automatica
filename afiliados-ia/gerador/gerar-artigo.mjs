/**
 * Gerador de artigos SEO em PT usando GPT-4.
 *
 * Uso:
 *   node gerar-artigo.mjs                    # gera 1 artigo aleatório ainda não publicado
 *   node gerar-artigo.mjs "título do tema"   # gera artigo de tema específico de temas.json
 *
 * Requer:
 *   OPENAI_API_KEY no .env (na pasta afiliados-ia/)
 */

import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const SITE = path.join(ROOT, 'site')
const ARTIGOS = path.join(SITE, 'content/artigos')

// Carregar .env
carregarEnv(path.join(ROOT, '.env'))

const { OPENAI_API_KEY } = process.env
if (!OPENAI_API_KEY) {
  console.error('❌ OPENAI_API_KEY não encontrada. Crie um ficheiro .env na pasta afiliados-ia/ com base em .env.example')
  process.exit(1)
}

const temas = JSON.parse(fs.readFileSync(path.join(__dirname, 'temas.json'), 'utf8'))

async function main() {
  const tituloArg = process.argv[2]
  const tema = escolherTema(tituloArg)
  if (!tema) {
    console.log('✅ Todos os temas já foram publicados. Adicione novos em temas.json.')
    return
  }
  console.log(`📝 Gerando artigo: "${tema.titulo}"`)

  const artigoMD = await gerarArtigo(tema)
  const slug = gerarSlug(tema.titulo)
  const frontmatter = `---
title: "${escapeYaml(tema.titulo)}"
description: "${escapeYaml(extrairDescricao(artigoMD))}"
date: "${new Date().toISOString().slice(0, 10)}"
slug: "${slug}"
keyword: "${tema.keyword}"
---

`
  const ficheiro = path.join(ARTIGOS, `${slug}.mdx`)
  fs.writeFileSync(ficheiro, frontmatter + artigoMD)
  console.log(`✅ Artigo criado: ${ficheiro}`)
  console.log(`   → Slug: /artigos/${slug}`)
}

// ─────────────────────────────────────────────────────────

function escolherTema(tituloArg) {
  const publicados = new Set(
    fs.existsSync(ARTIGOS)
      ? fs.readdirSync(ARTIGOS).map(f => f.replace(/\.mdx$/, ''))
      : []
  )
  if (tituloArg) {
    return temas.temas.find(t => t.titulo.toLowerCase().includes(tituloArg.toLowerCase()))
  }
  const disponiveis = temas.temas.filter(t => !publicados.has(gerarSlug(t.titulo)))
  if (disponiveis.length === 0) return null
  return disponiveis[Math.floor(Math.random() * disponiveis.length)]
}

async function gerarArtigo(tema) {
  const ferramentas = tema.ferramentas.map(id => ({ id, ...temas.ferramentas[id] }))
  const linksAfiliados = ferramentas.map(f => {
    const env = f.afiliadoEnv ? process.env[f.afiliadoEnv] : null
    const url = env ? `${f.site}?ref=${env}` : f.site
    return `- **${f.nome}** (${f.categoria}, ${f.preco}) — ${url}`
  }).join('\n')

  const prompt = `Escreve um artigo em PORTUGUÊS EUROPEU de Portugal (não português do Brasil) de aproximadamente 1200-1500 palavras sobre:

"${tema.titulo}"

Tipo de artigo: ${tema.tipo}
Palavra-chave principal (para SEO): ${tema.keyword}
Ferramentas a mencionar (com links):
${linksAfiliados}

REGRAS OBRIGATÓRIAS:
1. Formato Markdown puro (headings com ##, listas com -, negrito com **)
2. NÃO incluas o título principal H1 — começa direto pelo primeiro parágrafo de introdução
3. A palavra-chave deve aparecer naturalmente na introdução, em pelo menos 1 subtítulo e na conclusão
4. Usa os links de afiliado fornecidos sempre que mencionares a ferramenta pela primeira vez (formato [Nome](URL))
5. Inclui pelo menos UMA tabela comparativa quando fizer sentido
6. Tom: honesto, direto, útil. SEM hype, SEM "revolucionário", SEM marketês.
7. Inclui secção final "Conclusão" com recomendação clara
8. Inclui FAQ com 3-5 perguntas e respostas curtas no fim (formato ## FAQ / ### Pergunta / resposta)
9. Português de Portugal (utilizador, telemóvel, ficheiro — NÃO usuário/celular/arquivo)

Começa agora:`

  const resp = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: 'gpt-4o',
      temperature: 0.7,
      messages: [
        { role: 'system', content: 'És um redator SEO profissional especializado em tecnologia e IA, a escrever em português europeu para um blog de afiliados. Os teus artigos são honestos, úteis e otimizados para Google.' },
        { role: 'user', content: prompt },
      ],
    }),
  })

  if (!resp.ok) {
    const err = await resp.text()
    throw new Error(`OpenAI API erro ${resp.status}: ${err}`)
  }
  const data = await resp.json()
  return data.choices[0].message.content.trim()
}

function gerarSlug(titulo) {
  return titulo
    .toLowerCase()
    .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, 80)
}

function extrairDescricao(md) {
  const linhas = md.split('\n').filter(l => l.trim() && !l.startsWith('#') && !l.startsWith('-') && !l.startsWith('|'))
  const primeira = linhas[0] || ''
  return primeira.replace(/[*_`]/g, '').slice(0, 155)
}

function escapeYaml(s) {
  return s.replace(/"/g, '\\"')
}

function carregarEnv(file) {
  if (!fs.existsSync(file)) return
  for (const linha of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = linha.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/i)
    if (m) process.env[m[1]] ??= m[2].replace(/^"|"$/g, '')
  }
}

main().catch(err => { console.error(err); process.exit(1) })
