/**
 * Gera N artigos em lote (respeitando limite diário da OpenAI).
 * Uso: node gerar-lote.mjs [quantidade]
 * Default: 5 artigos
 */
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const N = parseInt(process.argv[2] || '5', 10)

for (let i = 0; i < N; i++) {
  console.log(`\n━━━ Artigo ${i + 1}/${N} ━━━`)
  const r = spawnSync('node', [path.join(__dirname, 'gerar-artigo.mjs')], { stdio: 'inherit' })
  if (r.status !== 0) {
    console.error('⚠️ Falhou, a continuar...')
  }
  // Pausa 3s entre chamadas para não irritar rate limit
  await new Promise(r => setTimeout(r, 3000))
}
console.log(`\n✅ ${N} artigos gerados.`)
