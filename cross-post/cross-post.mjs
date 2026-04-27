#!/usr/bin/env node
/**
 * Cross-publish: pega artigos MDX → publica no Medium + Dev.to + Hashnode
 * Requer secrets:
 *   MEDIUM_TOKEN     → settings.medium.com → "Integration tokens"
 *   DEVTO_TOKEN      → dev.to/settings/extensions → "DEV Community API Keys"
 *   HASHNODE_TOKEN   → hashnode.com/settings/developer → "Personal Access Tokens"
 *   MEDIUM_USER_ID   → opcional, busca-se via /me
 *   HASHNODE_PUB_ID  → ID da publicação Hashnode (opcional)
 *
 * Uso:
 *   node cross-post.mjs                  # publica todos os artigos não publicados
 *   node cross-post.mjs <slug>           # publica 1 específico
 *   node cross-post.mjs --dry-run        # mostra o que faria, sem publicar
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const ARTIGOS = path.join(ROOT, 'afiliados-ia', 'site', 'content', 'artigos')
const STATE_FILE = path.join(__dirname, '_published.json')
const SITE_URL = process.env.SITE_URL || 'https://renda-automatica.vercel.app'

// Carregar .env
for (const p of [path.join(__dirname, '.env'), path.join(ROOT, 'produtos-digitais', '.env')]) {
  if (fs.existsSync(p)) {
    for (const line of fs.readFileSync(p, 'utf-8').split('\n')) {
      const m = line.match(/^([A-Z_]+)=(.*)$/)
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
    }
  }
}

const MEDIUM = process.env.MEDIUM_TOKEN
const DEVTO = process.env.DEVTO_TOKEN
const HASHNODE = process.env.HASHNODE_TOKEN
let HASHNODE_PUB = process.env.HASHNODE_PUB_ID

// Limita por execução para evitar rate-limit (Devto: 10 req/30s)
const MAX_PER_RUN = parseInt(process.env.CROSSPOST_MAX_PER_RUN || '3', 10)
const DEVTO_DELAY_MS = parseInt(process.env.CROSSPOST_DEVTO_DELAY_MS || '8000', 10)

const sleep = (ms) => new Promise(r => setTimeout(r, ms))

async function ensureHashnodePubId() {
  if (!HASHNODE || HASHNODE_PUB) return
  try {
    const r = await fetch('https://gql.hashnode.com/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: HASHNODE },
      body: JSON.stringify({ query: '{ me { publications(first: 1) { edges { node { id title } } } } }' }),
    })
    const j = await r.json()
    const id = j?.data?.me?.publications?.edges?.[0]?.node?.id
    if (id) {
      HASHNODE_PUB = id
      process.env.HASHNODE_PUB_ID = id
      console.log(`   🔎 HASHNODE_PUB_ID auto-detectado: ${id}`)
    }
  } catch (e) {
    console.log(`   ⚠️ não consegui auto-detectar HASHNODE_PUB_ID: ${e.message}`)
  }
}

const DRY = process.argv.includes('--dry-run')
const slugArg = process.argv.find(a => !a.startsWith('--') && a !== process.argv[0] && a !== process.argv[1])

function parseFrontmatter(raw) {
  const m = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/)
  if (!m) return { meta: {}, body: raw }
  const meta = {}
  for (const line of m[1].split('\n')) {
    const km = line.match(/^([a-zA-Z_]+):\s*(.*)$/)
    if (km) {
      let v = km[2].trim()
      if (v.startsWith('[') && v.endsWith(']')) {
        v = v.slice(1, -1).split(',').map(s => s.trim().replace(/^["']|["']$/g, '')).filter(Boolean)
      } else {
        v = v.replace(/^["']|["']$/g, '')
      }
      meta[km[1]] = v
    }
  }
  return { meta, body: m[2] }
}

function loadState() {
  try { return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8')) } catch { return {} }
}
function saveState(s) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(s, null, 2))
}

async function publishMedium(meta, body, canonical) {
  if (!MEDIUM) return { skip: 'no MEDIUM_TOKEN' }
  // Buscar user id
  const me = await fetch('https://api.medium.com/v1/me', {
    headers: { Authorization: `Bearer ${MEDIUM}`, Accept: 'application/json' },
  })
  if (!me.ok) return { error: `me ${me.status}` }
  const userId = (await me.json()).data.id
  // Publicar
  const r = await fetch(`https://api.medium.com/v1/users/${userId}/posts`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${MEDIUM}`, 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      title: meta.title || meta.titulo,
      contentFormat: 'markdown',
      content: `${body}\n\n---\n\n*Originalmente publicado em [${SITE_URL}](${canonical})*`,
      canonicalUrl: canonical,
      tags: (meta.tags || ['IA', 'tecnologia']).slice(0, 5),
      publishStatus: 'public',
    }),
  })
  if (!r.ok) return { error: `medium ${r.status} ${(await r.text()).slice(0, 200)}` }
  const j = await r.json()
  return { url: j.data.url, id: j.data.id }
}

async function publishDevTo(meta, body, canonical) {
  if (!DEVTO) return { skip: 'no DEVTO_TOKEN' }
  const r = await fetch('https://dev.to/api/articles', {
    method: 'POST',
    headers: { 'api-key': DEVTO, 'Content-Type': 'application/json' },
    body: JSON.stringify({
      article: {
        title: meta.title || meta.titulo,
        body_markdown: body,
        published: true,
        canonical_url: canonical,
        tags: (meta.tags || ['ai']).slice(0, 4).map(t => String(t).toLowerCase().replace(/[^a-z0-9]/g, '')),
        description: meta.description || meta.descricao || '',
      },
    }),
  })
  if (!r.ok) return { error: `devto ${r.status} ${(await r.text()).slice(0, 200)}` }
  const j = await r.json()
  return { url: j.url, id: j.id }
}

async function publishHashnode(meta, body, canonical) {
  if (!HASHNODE) return { skip: 'no HASHNODE_TOKEN' }
  if (!HASHNODE_PUB) return { skip: 'no HASHNODE_PUB_ID' }
  const query = `mutation PublishPost($input: PublishPostInput!) {
    publishPost(input: $input) { post { id url } }
  }`
  const r = await fetch('https://gql.hashnode.com/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: HASHNODE },
    body: JSON.stringify({
      query,
      variables: {
        input: {
          title: meta.title || meta.titulo,
          contentMarkdown: body,
          publicationId: HASHNODE_PUB,
          tags: (meta.tags || ['ai']).slice(0, 5).map(t => ({ slug: String(t).toLowerCase().replace(/[^a-z0-9]/g, ''), name: t })),
          originalArticleURL: canonical,
        },
      },
    }),
  })
  if (!r.ok) return { error: `hashnode ${r.status}` }
  const j = await r.json()
  if (j.errors) return { error: `hashnode gql: ${JSON.stringify(j.errors).slice(0, 200)}` }
  return { url: j.data?.publishPost?.post?.url, id: j.data?.publishPost?.post?.id }
}

async function processArticle(file, state) {
  const slug = file.replace(/\.mdx?$/, '')
  if (slug === 'bem-vindo') return null  // skip welcome
  const raw = fs.readFileSync(path.join(ARTIGOS, file), 'utf-8')
  const { meta, body } = parseFrontmatter(raw)
  const canonical = `${SITE_URL}/artigos/${slug}`

  console.log(`\n📄 ${slug}`)
  console.log(`   Title: ${meta.title || meta.titulo || '(no title)'}`)

  const result = state[slug] || { platforms: {} }
  const updates = {}

  for (const [name, fn] of [['medium', publishMedium], ['devto', publishDevTo], ['hashnode', publishHashnode]]) {
    if (result.platforms[name]?.url) {
      console.log(`   ↺ ${name}: já publicado (${result.platforms[name].url})`)
      continue
    }
    if (DRY) {
      console.log(`   [dry] iria publicar em ${name}`)
      continue
    }
    process.stdout.write(`   📤 ${name}...`)
    try {
      const r = await fn(meta, body, canonical)
      if (r.skip) console.log(` ⏭️  ${r.skip}`)
      else if (r.error) console.log(` ❌ ${r.error}`)
      else { console.log(` ✓ ${r.url}`); updates[name] = r }
    } catch (e) {
      console.log(` ❌ ${e.message.slice(0, 100)}`)
    }
  }

  if (Object.keys(updates).length > 0) {
    state[slug] = { ...result, platforms: { ...result.platforms, ...updates }, last: new Date().toISOString() }
    saveState(state)
  }
  return updates
}

async function main() {
  if (!fs.existsSync(ARTIGOS)) {
    console.error(`❌ Pasta artigos não existe: ${ARTIGOS}`)
    process.exit(1)
  }
  console.log(`📡 Cross-post — Medium / Dev.to / Hashnode`)
  console.log(`   MEDIUM_TOKEN: ${MEDIUM ? '✓' : '✗ (skip)'}`)
  console.log(`   DEVTO_TOKEN: ${DEVTO ? '✓' : '✗ (skip)'}`)
  console.log(`   HASHNODE_TOKEN: ${HASHNODE ? '✓' : '✗ (skip)'}`)
  if (DRY) console.log(`   🧪 DRY RUN — nada será publicado`)

  await ensureHashnodePubId()

  const state = loadState()
  const files = fs.readdirSync(ARTIGOS).filter(f => f.endsWith('.mdx') || f.endsWith('.md'))
  let targets = slugArg ? files.filter(f => f.startsWith(slugArg)) : files

  // Prioriza artigos ainda não publicados em nenhuma plataforma
  if (!slugArg) {
    targets = targets.filter(f => {
      const slug = f.replace(/\.mdx?$/, '')
      const p = state[slug]?.platforms || {}
      return !(p.devto?.url && p.hashnode?.url)
    }).slice(0, MAX_PER_RUN)
  }
  console.log(`   🎯 ${targets.length} artigo(s) nesta execução (cap=${MAX_PER_RUN})`)

  for (const f of targets) {
    try { await processArticle(f, state) } catch (e) { console.error(`❌ ${f}: ${e.message}`) }
    await sleep(DEVTO_DELAY_MS)
  }
  console.log(`\n✅ Concluído. Estado em ${STATE_FILE}`)
}

main().catch(console.error)
