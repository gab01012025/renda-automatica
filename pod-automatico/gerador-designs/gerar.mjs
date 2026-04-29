/**
 * Gera N designs: GPT-4o (ideias) + DALL-E 3 (FUNDO sem texto) + Python PIL (texto perfeito).
 * Uso: node gerar.mjs <nicho-id> [quantidade]
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
carregarEnv(path.join(ROOT, '.env'))

const { OPENAI_API_KEY } = process.env
if (!OPENAI_API_KEY) { console.error('❌ OPENAI_API_KEY em falta'); process.exit(1) }

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

console.log(`🎨 Gerar ${quantidade} designs para "${nicho.nome}"`)

const outDir = path.join(ROOT, 'designs', nichoId)
const tmpDir = path.join(outDir, '_tmp')
fs.mkdirSync(outDir, { recursive: true })
fs.mkdirSync(tmpDir, { recursive: true })

const ideias = await gerarIdeias(nicho, quantidade)
console.log(`💡 ${ideias.length} ideias geradas`)

const timestamp = Date.now()
for (let i = 0; i < ideias.length; i++) {
  const ideia = ideias[i]
  console.log(`\n[${i + 1}/${ideias.length}] "${ideia.frase}"`)
  try {
    const isMinimalText = /TYPOGRAPHY ONLY|TYPOGRAFIE ONLY|TYPOGRAPHY-FIRST/i.test(nicho.estilo || '')
    let bgBuffer
    if (isMinimalText) {
      // Skip DALL-E: render solid color background via PIL (much higher converting on Etsy)
      bgBuffer = null
    } else {
      bgBuffer = await gerarFundo(ideia.bgPrompt)
    }
    const base = `${timestamp}-${String(i + 1).padStart(3, '0')}`
    const bgPath = path.join(tmpDir, `${base}-bg.png`)
    if (bgBuffer) fs.writeFileSync(bgPath, bgBuffer)
    console.log(`   🖼  fundo ${isMinimalText ? 'sólido (typography-only)' : 'gerado'}`)

    const finalPath = path.join(outDir, `${base}.png`)
    const metaForPy = {
      frase: ideia.frase,
      textColor: ideia.textColor || '#FFFFFF',
      shadowColor: ideia.shadowColor || '#000000',
      fontStyle: ideia.fontStyle || 'display',
      bgPath: bgBuffer ? bgPath : null,
      bgSolidColor: ideia.bgSolidColor || (isMinimalText ? '#F5EFE6' : null),
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

    fs.unlinkSync(metaPath)
    if (bgBuffer && fs.existsSync(bgPath)) fs.unlinkSync(bgPath)
    await new Promise(r => setTimeout(r, 1500))
  } catch (e) {
    console.error(`   ❌ falhou: ${e.message}`)
  }
}

try { fs.rmdirSync(tmpDir) } catch {}

console.log(`\n✅ Designs prontos em: ${outDir}`)
console.log(`   Próximo passo: node uploader-printify/upload.mjs ${nichoId}`)

async function gerarIdeias(nicho, n) {
  const prompt = `És um designer profissional de print-on-demand para Etsy. Gera ${n} ideias ÚNICAS e comercialmente viáveis para o nicho "${nicho.nome}" (${nicho.idioma}).

Público-alvo: ${nicho.publico}
Temas possíveis: ${nicho.temas.join(', ')}
Estilo visual: ${nicho.estilo}

REGRAS CRÍTICAS:
- frases curtas e impactantes (3 a 6 palavras MAX)
- linguagem: ${nicho.idioma === 'pt-PT' ? 'português EUROPEU (Portugal) — usar "tu", evitar gírias brasileiras' : nicho.idioma === 'pt-BR' ? 'português brasileiro' : nicho.idioma === 'de' ? 'DEUTSCH (German). Phrases MUST be in German.' : nicho.idioma === 'fr' ? 'FRENCH. Phrases MUST be in French.' : 'ENGLISH ONLY. Phrases MUST be in English. Do NOT use Portuguese or Spanish.'}
- nunca usar marcas registadas, nomes de clubes, jogadores, celebridades

Para cada ideia devolve:
- frase: texto que vai NA estampa, 3-6 palavras EXATAS (NO IDIOMA CORRETO acima)
- bgPrompt: prompt em INGLÊS para DALL-E criar FUNDO ABSTRATO/DECORATIVO. CRÍTICO: incluir "no text, no letters, no words, abstract decorative pattern only". Descreve cores, formas, estilo, composição centrada com espaço para texto. NUNCA mencionar a frase aqui. (IGNORADO se estilo for TYPOGRAPHY-ONLY)
- bgSolidColor: hex de UMA cor sólida de fundo (Etsy bestsellers: #F5EFE6 cream, #1a1a1a black, #2C3E50 navy, #7C9885 sage, #C97B63 terracotta, #DDA15E mustard, #E8B4B8 dusty pink). Usado se TYPOGRAPHY-ONLY.
- textColor: hex da cor do texto (contraste com bgSolidColor: #1a1a1a se fundo claro, #FFFFFF se escuro)
- shadowColor: hex da sombra (oposto do textColor)
- fontStyle: "display" (Bebas Neue bold) | "modern" (Oswald) | "serif" (Playfair elegante)
- tituloProduto: título Etsy SEO (max 70 chars, NÃO incluir "T-shirt"/"Poster")
- descricaoProduto: 3 frases naturais (NÃO mencionar IA)
- tags: array de 13 strings (max 20 chars cada)

Responde APENAS com JSON: {"ideias": [...]}`

  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: 'gpt-4o',
      temperature: 0.95,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: 'Respondes sempre com JSON válido.' },
        { role: 'user', content: prompt },
      ],
    }),
  })
  if (!r.ok) throw new Error(`OpenAI ideias: ${r.status} ${await r.text()}`)
  const data = await r.json()
  const parsed = JSON.parse(data.choices[0].message.content)
  return parsed.ideias || parsed
}

async function gerarFundo(bgPrompt) {
  const safePrompt = `${bgPrompt}. ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO TYPOGRAPHY, NO NUMBERS anywhere in the image. Pure decorative abstract pattern only, leave clear visual space in the center for text overlay.`
  const r = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: 'dall-e-3',
      prompt: safePrompt,
      size: '1024x1024',
      quality: 'hd',
      n: 1,
      response_format: 'b64_json',
    }),
  })
  if (!r.ok) throw new Error(`DALL-E: ${r.status} ${await r.text()}`)
  const data = await r.json()
  return Buffer.from(data.data[0].b64_json, 'base64')
}

function carregarEnv(file) {
  if (!fs.existsSync(file)) return
  for (const linha of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = linha.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/i)
    if (m) process.env[m[1]] ??= m[2].replace(/^"|"$/g, '')
  }
}
