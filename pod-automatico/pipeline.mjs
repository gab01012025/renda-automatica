/**
 * Pipeline completo: gera designs + faz upload.
 * Uso: node pipeline.mjs <nicho-id> [quantidade]
 */
import { spawnSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const nicho = process.argv[2]
const qtd = process.argv[3] || '5'

if (!nicho) { console.error('Uso: node pipeline.mjs <nicho-id> [qtd]'); process.exit(1) }

console.log('━━━ Fase 1: gerar designs ━━━')
const r1 = spawnSync('node', [path.join(__dirname, 'gerador-designs/gerar.mjs'), nicho, qtd], { stdio: 'inherit' })
if (r1.status !== 0) process.exit(r1.status)

console.log('\n━━━ Fase 2: upload para Printify ━━━')
const r2 = spawnSync('node', [path.join(__dirname, 'uploader-printify/upload.mjs'), nicho], { stdio: 'inherit' })
if (r2.status !== 0) process.exit(r2.status)

console.log('\n🎉 Pipeline completo.')
