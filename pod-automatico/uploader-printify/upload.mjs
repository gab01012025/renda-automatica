/**
 * Upload de designs gerados → Printify (cria produtos)
 *
 * Uso: node upload.mjs <nicho-id>
 *
 * Lê PNGs + JSONs em designs/<nicho-id>/ e:
 *   1. Faz upload da imagem para Printify
 *   2. Cria um produto para cada tipo em produtos[] (camisa/poster/etc)
 *   3. Marca produto como publicado (vai para Etsy/loja conectada)
 *   4. Marca ficheiro como processado (move para designs/<nicho>/feitos/)
 *
 * Docs API: https://developers.printify.com/
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
carregarEnv(path.join(ROOT, '.env'))

const {
  PRINTIFY_API_KEY, PRINTIFY_SHOP_ID,
  PRINTIFY_BLUEPRINT_CAMISA_UNISEX, PRINTIFY_PROVIDER_CAMISA, PRECO_CAMISA_USD,
  PRINTIFY_BLUEPRINT_POSTER, PRINTIFY_PROVIDER_POSTER, PRECO_POSTER_USD,
} = process.env

if (!PRINTIFY_API_KEY || !PRINTIFY_SHOP_ID) {
  console.error('❌ PRINTIFY_API_KEY e PRINTIFY_SHOP_ID são obrigatórios no .env')
  process.exit(1)
}

const PRODUTOS = {
  camisa: {
    kind: 'camisa',
    blueprint_id: parseInt(PRINTIFY_BLUEPRINT_CAMISA_UNISEX || '384'),
    print_provider_id: parseInt(PRINTIFY_PROVIDER_CAMISA || '29'),
    preco: parseInt(PRECO_CAMISA_USD || '2499'),
  },
  poster: {
    kind: 'poster',
    blueprint_id: parseInt(PRINTIFY_BLUEPRINT_POSTER || '97'),
    print_provider_id: parseInt(PRINTIFY_PROVIDER_POSTER || '2'),
    preco: parseInt(PRECO_POSTER_USD || '1999'),
  },
}

const nichoId = process.argv[2]
if (!nichoId) {
  console.error('Uso: node upload.mjs <nicho-id>')
  process.exit(1)
}

const pastaDesigns = path.join(ROOT, 'designs', nichoId)
const pastaFeitos = path.join(pastaDesigns, 'feitos')
fs.mkdirSync(pastaFeitos, { recursive: true })

const pngs = fs.readdirSync(pastaDesigns).filter(f => f.endsWith('.png'))
if (pngs.length === 0) {
  console.log('Nenhum design novo em ' + pastaDesigns)
  process.exit(0)
}

console.log(`📦 ${pngs.length} designs para publicar`)

for (const png of pngs) {
  const base = png.replace(/\.png$/, '')
  const jsonFile = path.join(pastaDesigns, `${base}.json`)
  if (!fs.existsSync(jsonFile)) { console.warn(`⚠️ sem meta: ${base}`); continue }
  const meta = JSON.parse(fs.readFileSync(jsonFile, 'utf8'))

  console.log(`\n→ ${meta.tituloProduto}`)
  try {
    // 1) upload imagem
    const pngBuffer = fs.readFileSync(path.join(pastaDesigns, png))
    const imageId = await uploadImagem(`${base}.png`, pngBuffer)
    console.log(`   📤 imagem: ${imageId}`)

    // 2) criar produto para cada tipo em meta.produtos
    for (const tipo of meta.produtos) {
      const tpl = PRODUTOS[tipo]
      if (!tpl) { console.warn(`   ⚠️ produto desconhecido: ${tipo}`); continue }
      const produtoId = await criarProduto({ imageId, meta, tpl })
      console.log(`   ✅ ${tipo} criado: ${produtoId}`)
      await publicar(produtoId)
      console.log(`   📢 ${tipo} publicado`)
      await new Promise(r => setTimeout(r, 1500))
    }

    // 3) marcar como feito
    fs.renameSync(path.join(pastaDesigns, png), path.join(pastaFeitos, png))
    fs.renameSync(jsonFile, path.join(pastaFeitos, `${base}.json`))
  } catch (e) {
    console.error(`   ❌ ${e.message}`)
  }
}

console.log('\n✅ Upload concluído.')

// ─────────────────────────────────────

async function printify(method, url, body) {
  const r = await fetch(`https://api.printify.com/v1${url}`, {
    method,
    headers: {
      Authorization: `Bearer ${PRINTIFY_API_KEY}`,
      'Content-Type': 'application/json',
      'User-Agent': 'pod-automatico',
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!r.ok) throw new Error(`Printify ${method} ${url}: ${r.status} ${await r.text()}`)
  return r.json()
}

async function uploadImagem(filename, buffer) {
  const data = await printify('POST', '/uploads/images.json', {
    file_name: filename,
    contents: buffer.toString('base64'),
  })
  return data.id
}

async function criarProduto({ imageId, meta, tpl }) {
  // Pegar variantes disponíveis do blueprint/provider
  const variantesInfo = await printify('GET', `/catalog/blueprints/${tpl.blueprint_id}/print_providers/${tpl.print_provider_id}/variants.json`)
  // Escolher um subset razoável (primeiras 12 variantes) — evitar criar produto com centenas
  const variantes = (variantesInfo.variants || []).slice(0, 12).map(v => ({
    id: v.id,
    price: tpl.preco,
    is_enabled: true,
  }))

  const sufixoTipo = { camisa: 'T-Shirt', poster: 'Poster' }[tpl.kind] || ''
  const tituloBase = (meta.tituloProduto || '').replace(/\s*-?\s*(T-?Shirt|Poster|Camisa|Camiseta)\b.*$/i, '').trim()
  const tituloFinal = sufixoTipo ? `${tituloBase} | ${sufixoTipo}` : tituloBase
  const produto = await printify('POST', `/shops/${PRINTIFY_SHOP_ID}/products.json`, {
    title: tituloFinal,
    description: meta.descricaoProduto,
    blueprint_id: tpl.blueprint_id,
    print_provider_id: tpl.print_provider_id,
    variants: variantes,
    print_areas: [{
      variant_ids: variantes.map(v => v.id),
      placeholders: [{
        position: 'front',
        images: [{ id: imageId, x: 0.5, y: 0.5, scale: 1, angle: 0 }],
      }],
    }],
    tags: (meta.tags || []).slice(0, 13),
  })
  return produto.id
}

async function publicar(produtoId) {
  return printify('POST', `/shops/${PRINTIFY_SHOP_ID}/products/${produtoId}/publish.json`, {
    title: true, description: true, images: true, variants: true, tags: true,
  })
}

function carregarEnv(file) {
  if (!fs.existsSync(file)) return
  for (const linha of fs.readFileSync(file, 'utf8').split('\n')) {
    const m = linha.match(/^([A-Z_][A-Z0-9_]*)=(.*)$/i)
    if (m) process.env[m[1]] ??= m[2].replace(/^"|"$/g, '')
  }
}
