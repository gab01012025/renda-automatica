/**
 * hotmart-helper.mjs — gera links de afiliado Hotmart via API
 * Uso: node afiliados-ia/gerador/hotmart-helper.mjs
 */
import 'dotenv/config'

const BASIC = process.env.HOTMART_BASIC
if (!BASIC) { console.error('HOTMART_BASIC missing in .env'); process.exit(1) }

async function getToken() {
  const r = await fetch('https://api-sec-vlc.hotmart.com/security/oauth/token?grant_type=client_credentials', {
    method: 'POST',
    headers: { Authorization: `Basic ${BASIC}` },
  })
  const j = await r.json()
  return j.access_token
}

async function listMyProducts(token) {
  // produtos onde sou afiliado
  const r = await fetch('https://developers.hotmart.com/payments/api/v1/sales/history?max_results=10', {
    headers: { Authorization: `Bearer ${token}` },
  })
  return r.json()
}

async function main() {
  const token = await getToken()
  console.log('✅ Hotmart token OK (len=' + token.length + ')')
  console.log('\n💡 Para gerar links de afiliado:')
  console.log('   1. Vai a https://app-vlc.hotmart.com/marketplace')
  console.log('   2. Procura nichos: "marketing digital", "emagrecer", "ingles", "investir"')
  console.log('   3. Clica "Promover" no produto top → gera o teu link único')
  console.log('   4. O link tem formato: https://go.hotmart.com/XXXXXXXX')
  console.log('   5. Copia o XXXXXXXX (o teu HOTMART_AFF_ID por produto) e adiciona ao .env\n')
  // tenta listar histórico (pode falhar se sem vendas, é normal)
  try {
    const sales = await listMyProducts(token)
    console.log('Sales history:', JSON.stringify(sales).slice(0, 200))
  } catch (e) {
    console.log('(sem histórico ainda — normal)')
  }
}

main().catch(e => { console.error(e); process.exit(1) })
