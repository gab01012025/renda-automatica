/**
 * Gera N designs para um nicho usando GPT-4 (ideias) + DALL-E 3 (imagens).
 *
 * Uso:
 *   node gerar.mjs <nicho-id> [quantidade]
 *
 * Exemplo:
 *   node gerar.mjs frases-motivacionais-pt 5
 *
 * Output: designs/<nicho-id>/<timestamp>-<n>.{png,json}
 *   - PNG: imagem 1024x1024 pronta para upload
 *   - JSON: metadados (frase, título SKU, descrição, tags) pro uploader
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
carregarEnv(path.join(ROOT, '.env'))

const { OPENAI_API_KEY } = process.env
if (!OPENAI_API_KEY) {
  console.error('❌ OPENAI_API_KEY em falta. Crie .env na pasta pod-automatico/ (ver .env.example).')
  process.exit(1)
}

const nichos = JSON.parse(fs.readFileSync(path.join(ROOT, 'nichos.json'), 'utf8'))
const nichoId = process.argv[2]
const quantidade = parseInt(process.argv[3] || '5', 10)

if (!nichoId) {
  console.error('Uso: node gerar.mjs <nicho-id> [quantidade]')
  console.error('Nichos disponíveis: ' + nichos.nichos.map(n => n.id).join(', '))
  process.exit(1)
}

const nicho = nichos.nichos.find(n => n.id === nichoId)
if (!nicho) {
  console.error(`Nicho "${nichoId}" não encontrado em nichos.json`)
  process.exit(1)
}

console.log(`🎨 Gerar ${quantidade} designs para "${nicho.nome}"`)

const outDir = path.join(ROOT, 'designs', nichoId)
fs.mkdirSync(outDir, { recursive: true })

// 1) Pedir ao GPT-4 N ideias únicas (frase + prompt visual + título produto + tags)
const ideias = await gerarIdeias(nicho, quantidade)
console.log(`💡 ${ideias.length} ideias geradas`)

// 2) Para cada ideia, gerar imagem com DALL-E 3
const timestamp = Date.now()
for (let i = 0; i < ideias.length; i++) {
  const ideia = ideias[i]
  console.log(`\n[${i + 1}/${ideias.length}] "${ideia.frase}"`)
  try {
    const pngBuffer = await gerarImagem(ideia.promptVisual)
    const base = `${timestamp}-${String(i + 1).padStart(3, '0')}`
    fs.writeFileSync(path.join(outDir, `${base}.png`), pngBuffer)
    fs.writeFileSync(path.join(outDir, `${base}.json`), JSON.stringify({
      nicho: nichoId,
      produtos: nicho.produtos,
      ...ideia,
    }, null, 2))
    console.log(`   ✅ ${base}.png`)
    await new Promise(r => setTimeout(r, 1500)) // rate limit
  } catch (e) {
    console.error(`   ❌ falhou: ${e.message}`)
  }
}

console.log(`\n✅ Designs prontos em: ${outDir}`)
console.log(`   Próximo passo: node uploader-printify/upload.mjs ${nichoId}`)

// ───────────────────────────────────────────

async function gerarIdeias(nicho, n) {
  const prompt = `És um designer de estampa para print-on-demand. Gera ${n} ideias ÚNICAS e comercialmente viáveis para o nicho "${nicho.nome}" (${nicho.idioma}).

Público-alvo: ${nicho.publico}
Temas possíveis: ${nicho.temas.join(', ')}
Estilo visual geral: ${nicho.estilo}

Para cada ideia devolve um objeto JSON com:
- frase: texto curto (máx 8 palavras) em ${nicho.idioma === 'pt-PT' ? 'português de Portugal' : 'português do Brasil'}. Tem de ser original, NÃO pode violar direitos de autor/marcas.
- promptVisual: prompt em INGLÊS para DALL-E 3 criar a arte. Descreve composição, cores, estilo (${nicho.estilo}). Deve incluir o texto "${nicho.idioma === 'pt-PT' ? '[texto]' : '[texto]'}" EXATAMENTE como está na frase. Pede "flat design, printable on t-shirt, centered, transparent or solid background, high contrast, vector style".
- tituloProduto: título EM ${nicho.idioma === 'pt-PT' ? 'PORTUGUÊS DE PORTUGAL' : 'PORTUGUÊS DO BRASIL'} otimizado para Etsy SEO (70 caracteres máx, inclui palavras-chave: ${nicho.nome.toLowerCase()})
- descricaoProduto: descrição de 3-4 frases para Etsy, em ${nicho.idioma}
- tags: array de 13 tags (máx 20 caracteres cada) para Etsy

Responde APENAS com um array JSON válido, sem texto antes ou depois, sem markdown.`

  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: 'gpt-4o',
      temperature: 0.9,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: 'Respondes sempre com JSON válido.' },
        { role: 'user', content: prompt + '\n\nEnvolve o array numa chave "ideias": { "ideias": [...] }' },
      ],
    }),
  })
  if (!r.ok) throw new Error(`OpenAI ideias: ${r.status} ${await r.text()}`)
  const data = await r.json()
  const parsed = JSON.parse(data.choices[0].message.content)
  return parsed.ideias || parsed
}

async function gerarImagem(promptVisual) {
  const r = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: 'dall-e-3',
      prompt: promptVisual,
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
