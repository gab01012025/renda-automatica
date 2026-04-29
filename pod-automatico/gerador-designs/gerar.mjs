/**
 * Gera N designs SEM LLM: pool curado de frases bestseller + Pollinations.ai (imagem GRÁTIS)
 * + DALL-E como fallback se OPENAI_API_KEY tiver crédito.
 * Uso: node gerar.mjs <nicho-id> [quantidade]
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
carregarEnv(path.join(ROOT, '.env'))

const nichos = JSON.parse(fs.readFileSync(path.join(ROOT, 'nichos.json'), 'utf8'))
const nichoId = process.argv[2]
const quantidade = parseInt(process.argv[3] || '5', 10)

if (!nichoId) {
  console.error('Uso: node gerar.mjs <nicho-id> [quantidade]')
  console.error('Nichos: ' + nichos.nichos.map(n => n.id).join(', '))
  process.exit(1)
}

const nicho = nichos.nichos.find(n => n.id === nichoId)
if (!nicho) { console.error(`Nicho "${nichoId}" não encontrado`); process.exit(1) }
if (!nicho.pool_frases || !nicho.pool_frases.length) {
  console.error(`Nicho "${nichoId}" não tem pool_frases`); process.exit(1)
}

console.log(`🎨 Gerar ${quantidade} designs para "${nicho.nome}"`)

const outDir = path.join(ROOT, 'designs', nichoId)
const tmpDir = path.join(outDir, '_tmp')
fs.mkdirSync(outDir, { recursive: true })
fs.mkdirSync(tmpDir, { recursive: true })

// Track which frases já foram usadas (evita repetir)
const usadasPath = path.join(outDir, '_usadas.json')
const usadas = fs.existsSync(usadasPath) ? new Set(JSON.parse(fs.readFileSync(usadasPath, 'utf8'))) : new Set()
const disponivel = nicho.pool_frases.filter(f => !usadas.has(f))
if (disponivel.length === 0) {
  console.log('⚠ Pool esgotado neste nicho — reset para reciclar.')
  usadas.clear()
}
const pool = disponivel.length > 0 ? disponivel : [...nicho.pool_frases]
shuffle(pool)
const ideias = pool.slice(0, quantidade).map(p => parseFrase(p, nicho))

const timestamp = Date.now()
for (let i = 0; i < ideias.length; i++) {
  const ideia = ideias[i]
  console.log(`\n[${i + 1}/${ideias.length}] "${ideia.frase}"${ideia.motif ? ' [' + ideia.motif + ']' : ''}`)
  try {
    const base = `${timestamp}-${String(i + 1).padStart(3, '0')}`
    const bgPath = path.join(tmpDir, `${base}-bg.png`)
    let bgBuffer = null
    try {
      bgBuffer = await gerarFundo(ideia.bgPrompt)
      fs.writeFileSync(bgPath, bgBuffer)
      console.log('   🖼  fundo gerado (Pollinations)')
    } catch (e) {
      console.warn(`   ⚠ fundo falhou (${e.message}), usando cor sólida`)
    }

    const finalPath = path.join(outDir, `${base}.png`)
    const metaForPy = {
      frase: ideia.frase,
      textColor: ideia.textColor,
      shadowColor: ideia.shadowColor,
      fontStyle: ideia.fontStyle,
      bgPath: bgBuffer ? bgPath : null,
      bgSolidColor: ideia.bgSolidColor,
      outPath: finalPath,
    }
    const metaPath = path.join(tmpDir, `${base}-meta.json`)
    fs.writeFileSync(metaPath, JSON.stringify(metaForPy))
    const py = spawnSync('python3', [path.join(__dirname, 'compose.py'), metaPath], { stdio: 'inherit' })
    if (py.status !== 0) throw new Error('compose.py falhou')

    fs.writeFileSync(path.join(outDir, `${base}.json`), JSON.stringify({
      nicho: nichoId,
      produtos: nicho.produtos,
      frase: ideia.frase,
      tituloProduto: ideia.tituloProduto,
      descricaoProduto: ideia.descricaoProduto,
      tags: ideia.tags,
    }, null, 2))
    console.log(`   ✅ ${base}.png`)

    usadas.add(ideia._poolEntry)
    fs.writeFileSync(usadasPath, JSON.stringify([...usadas], null, 2))

    fs.unlinkSync(metaPath)
    if (bgBuffer && fs.existsSync(bgPath)) fs.unlinkSync(bgPath)
    await new Promise(r => setTimeout(r, 800))
  } catch (e) {
    console.error(`   ❌ falhou: ${e.message}`)
  }
}

try { fs.rmdirSync(tmpDir) } catch {}

console.log(`\n✅ Designs prontos em: ${outDir}`)
console.log(`   Próximo passo: node uploader-printify/upload.mjs ${nichoId}`)

// ---------- helpers ----------
function shuffle(a) { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1));[a[i], a[j]] = [a[j], a[i]] } }

function parseFrase(entry, nicho) {
  const [frase, motif] = entry.split('|').map(s => s.trim())
  const cores = nicho.cores_fundo || ['#F5EFE6']
  const fontes = nicho.fontes || ['display']
  const bgSolid = cores[Math.floor(Math.random() * cores.length)]
  const isDark = isColorDark(bgSolid)
  const fontStyle = fontes[Math.floor(Math.random() * fontes.length)]
  const fundoBase = nicho.fundo_estilo ? nicho.fundo_estilo.replace(/\{motif\}/g, motif || 'decorative element').replace(/\{animal\}/g, motif || 'animal') : ''
  const bgPrompt = fundoBase
  const slug = frase.toLowerCase().replace(/[^a-z0-9 ]/g, '').replace(/\s+/g, '-').slice(0, 50)
  const tituloProduto = (frase + ' | ' + (nicho.nome.split(' ')[0] || 'Vintage') + ' Design').slice(0, 70)
  const descricaoProduto = `${frase}. ${nicho.estilo.split('.')[0]}. Quality print on premium fabric — perfect gift for ${nicho.publico.split(',')[0]}.`
  const tags = buildTags(frase, nicho)
  return {
    frase,
    motif: motif || null,
    bgPrompt,
    bgSolidColor: bgSolid,
    textColor: isDark ? '#F5EFE6' : '#1a1a1a',
    shadowColor: isDark ? '#000000' : '#FFFFFF',
    fontStyle,
    tituloProduto,
    descricaoProduto,
    tags,
    _poolEntry: entry,
  }
}

function buildTags(frase, nicho) {
  const base = (nicho.nome + ' ' + frase).toLowerCase()
    .replace(/[^a-z0-9 ]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length >= 3 && w.length <= 18)
  const extra = ['gift', 'vintage', 'shirt', 'poster', 'aesthetic', 'trendy', 'unique', 'cute', 'minimalist']
  const all = [...new Set([...base, ...extra])].slice(0, 13)
  return all.map(t => t.slice(0, 20))
}

function isColorDark(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || '')
  if (!m) return false
  const n = parseInt(m[1], 16)
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255
  return (r * 299 + g * 587 + b * 114) / 1000 < 128
}

async function gerarFundo(bgPrompt) {
  if (!bgPrompt) throw new Error('sem bgPrompt')
  const safePrompt = `${bgPrompt}. ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO TYPOGRAPHY anywhere in the image.`
  // 1) DALL-E se houver crédito
  if (process.env.OPENAI_API_KEY) {
    try {
      const r = await fetch('https://api.openai.com/v1/images/generations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${process.env.OPENAI_API_KEY}` },
        body: JSON.stringify({ model: 'dall-e-3', prompt: safePrompt, size: '1024x1024', quality: 'hd', n: 1, response_format: 'b64_json' }),
      })
      if (r.ok) {
        const data = await r.json()
        return Buffer.from(data.data[0].b64_json, 'base64')
      }
    } catch {}
  }
  // 2) Pollinations.ai (FREE, with retry on 429)
  for (let attempt = 0; attempt < 4; attempt++) {
    const seed = Math.floor(Math.random() * 1e9)
    const url = `https://image.pollinations.ai/prompt/${encodeURIComponent(safePrompt)}?width=1024&height=1024&nologo=true&enhance=true&seed=${seed}&model=flux`
    const r = await fetch(url)
    if (r.ok) return Buffer.from(await r.arrayBuffer())
    if (r.status !== 429) throw new Error(`Pollinations: ${r.status}`)
    const wait = 8000 * (attempt + 1)
    console.warn(`   ⏳ Pollinations 429, retry em ${wait/1000}s...`)
    await new Promise(r => setTimeout(r, wait))
  }
  throw new Error('Pollinations: 429 após 4 retries')
}

function carregarEnv(file) {
  if (!fs.existsSync(file)) return
  for (const linha of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = linha.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/i)
    if (m) process.env[m[1]] ??= m[2].replace(/^"|"$/g, '')
  }
}
