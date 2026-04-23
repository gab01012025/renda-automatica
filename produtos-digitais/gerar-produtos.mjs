#!/usr/bin/env node
/**
 * Gerador de Produtos Digitais Gumroad
 * Gera 3 PDFs vendáveis: Prompts ChatGPT Programadores, Templates Notion Freelancer, Bundle 200 Prompts AI PT
 */
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const OUT_DIR = path.join(ROOT, 'produtos-digitais', 'pdfs')
fs.mkdirSync(OUT_DIR, { recursive: true })

// Carregar .env manualmente
const envPath = path.join(__dirname, '.env')
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, 'utf-8').split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/)
    if (m) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
  }
}
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
if (!OPENAI_API_KEY) throw new Error('OPENAI_API_KEY missing')

const PRODUTOS = [
  {
    id: 'prompts-chatgpt-programadores',
    titulo: '100 Prompts ChatGPT para Programadores',
    preco: 9,
    publico: 'devs Portugal/Brasil que usam ChatGPT no dia-a-dia',
    descricao: 'Pack profissional com 100 prompts otimizados para programadores: code review, debugging, refactoring, documentação, testes, arquitetura, SQL, regex, etc. Em PT.',
    secoes: [
      'Code Review & Refactoring (15 prompts)',
      'Debugging & Erros (15 prompts)',
      'Documentação Automática (10 prompts)',
      'Testes & TDD (10 prompts)',
      'Arquitetura & Design Patterns (10 prompts)',
      'SQL & Bases de Dados (10 prompts)',
      'Regex & Strings (10 prompts)',
      'DevOps & Deploy (10 prompts)',
      'Segurança & OWASP (5 prompts)',
      'Performance & Otimização (5 prompts)',
    ],
  },
  {
    id: 'prompts-marketing-pt',
    titulo: '150 Prompts ChatGPT para Marketing em Português',
    preco: 12,
    publico: 'gestores de marketing, freelancers, donos de pequenos negócios PT/BR',
    descricao: 'Os 150 melhores prompts para criar conteúdo, campanhas, emails, copy de vendas e SEO em português. Testados em 2026.',
    secoes: [
      'Copywriting de Vendas (20 prompts)',
      'Email Marketing (20 prompts)',
      'Posts Redes Sociais (20 prompts)',
      'SEO & Blog Posts (20 prompts)',
      'Anúncios Facebook/Google (15 prompts)',
      'Headlines & Títulos (15 prompts)',
      'Análise de Concorrência (10 prompts)',
      'Personas & Audiência (10 prompts)',
      'Funis de Vendas (10 prompts)',
      'Reviews & Testemunhos (10 prompts)',
    ],
  },
  {
    id: 'bundle-prompts-ai-pt',
    titulo: 'Bundle Mega: 300 Prompts AI em Português',
    preco: 19,
    publico: 'utilizadores avançados de IA que querem máximo de produtividade',
    descricao: 'O bundle definitivo: 300 prompts em PT cobrindo escrita, marketing, design, programação, vida pessoal, finanças, estudos. Inclui prompts para Claude, ChatGPT, Gemini.',
    secoes: [
      'Escrita Criativa (30 prompts)',
      'Marketing & Vendas (40 prompts)',
      'Programação (40 prompts)',
      'Design & Branding (25 prompts)',
      'Estudos & Aprendizagem (30 prompts)',
      'Finanças Pessoais (25 prompts)',
      'Saúde & Bem-estar (20 prompts)',
      'Vida Pessoal & Relações (20 prompts)',
      'Empreendedorismo (30 prompts)',
      'Produtividade Geral (40 prompts)',
    ],
  },
]

async function gerarSecao(produto, secao) {
  const numPrompts = parseInt(secao.match(/\((\d+)/)?.[1] || '10')
  const tema = secao.split('(')[0].trim()
  
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: 'gpt-4o',
      temperature: 0.85,
      messages: [
        {
          role: 'system',
          content: `És um expert em prompts AI. Gera ${numPrompts} prompts profissionais em português europeu (pt-PT) sobre "${tema}". Cada prompt deve ser:\n- 100% em português (não inglês, não brasileirismos exagerados)\n- Pronto a copiar para ChatGPT/Claude\n- Específico e útil (não genérico)\n- Com placeholders [ENTRE COLCHETES] para o utilizador preencher\nFormato markdown: ### N. Título curto\nDepois prompt completo em bloco. Separa cada prompt com "---".`,
        },
        {
          role: 'user',
          content: `Gera ${numPrompts} prompts para "${tema}" do produto "${produto.titulo}". Público: ${produto.publico}.`,
        },
      ],
    }),
  })
  if (!r.ok) throw new Error(`OpenAI: ${r.status} ${await r.text()}`)
  const data = await r.json()
  return data.choices[0].message.content
}

function gerarMarkdown(produto, secoesContent) {
  let md = `# ${produto.titulo}\n\n`
  md += `> **Preço:** €${produto.preco}\n`
  md += `> **Para:** ${produto.publico}\n\n`
  md += `${produto.descricao}\n\n`
  md += `---\n\n## 📌 Como Usar Este Pack\n\n`
  md += `1. Copia o prompt da secção que precisas\n`
  md += `2. Substitui os [PLACEHOLDERS] pela tua informação\n`
  md += `3. Cola no ChatGPT, Claude ou Gemini\n`
  md += `4. Refina o output se necessário\n\n`
  md += `**Dica pro:** combina prompts diferentes para resultados melhores.\n\n---\n\n`
  
  produto.secoes.forEach((secao, i) => {
    md += `## ${i + 1}. ${secao.split('(')[0].trim()}\n\n`
    md += secoesContent[i] + '\n\n---\n\n'
  })
  
  md += `\n## 💎 BÓNUS\n\nObrigado pela compra! Se gostaste deste pack:\n- Deixa review no Gumroad\n- Vê os outros packs em https://gumroad.com/printhouselx\n- Loja Etsy: https://etsy.com/shop/PrintHouseLX\n\n© 2026 PrintHouseLX. Uso pessoal e profissional permitido. Revenda proibida.\n`
  return md
}

async function gerarPDF(produto) {
  console.log(`\n📦 Gerando: ${produto.titulo} (€${produto.preco})`)
  
  const secoesContent = []
  for (let i = 0; i < produto.secoes.length; i++) {
    const secao = produto.secoes[i]
    process.stdout.write(`   [${i + 1}/${produto.secoes.length}] ${secao.split('(')[0].trim()}... `)
    const content = await gerarSecao(produto, secao)
    secoesContent.push(content)
    console.log('✓')
  }
  
  const md = gerarMarkdown(produto, secoesContent)
  const mdPath = path.join(OUT_DIR, `${produto.id}.md`)
  fs.writeFileSync(mdPath, md, 'utf-8')
  console.log(`   ✅ Markdown salvo: ${mdPath}`)
  
  // Markdown → HTML estilizado → PDF via wkhtmltopdf
  const htmlPath = path.join(OUT_DIR, `${produto.id}.html`)
  const css = `
    body { font-family: Georgia, serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; color: #222; }
    h1 { color: #c41e3a; border-bottom: 3px solid #c41e3a; padding-bottom: 10px; }
    h2 { color: #1a1a1a; border-left: 4px solid #c41e3a; padding-left: 12px; margin-top: 32px; }
    blockquote { background: #fff8e7; padding: 12px 20px; border-left: 4px solid #d4a017; margin: 16px 0; }
    code { background: #f3f3f3; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
    hr { border: none; border-top: 1px dashed #ccc; margin: 24px 0; }
    strong { color: #c41e3a; }
  `
  const htmlResult = spawnSync('pandoc', [mdPath, '-o', htmlPath, '--standalone', '--metadata', `title:${produto.titulo}`, '-H', '/dev/stdin'], { input: `<style>${css}</style>`, encoding: 'utf-8' })
  
  if (htmlResult.status !== 0) {
    console.log(`   ⚠️  HTML falhou: ${htmlResult.stderr}`)
    return { mdPath }
  }
  console.log(`   ✅ HTML gerado: ${htmlPath}`)
  
  const pdfPath = path.join(OUT_DIR, `${produto.id}.pdf`)
  const pdfResult = spawnSync('wkhtmltopdf', ['--encoding', 'UTF-8', '--margin-top', '20mm', '--margin-bottom', '20mm', '--margin-left', '20mm', '--margin-right', '20mm', '--enable-local-file-access', htmlPath, pdfPath], { encoding: 'utf-8' })
  if (pdfResult.status === 0) {
    const sizeMB = (fs.statSync(pdfPath).size / 1024 / 1024).toFixed(2)
    console.log(`   ✅ PDF gerado: ${pdfPath} (${sizeMB} MB)`)
  } else {
    console.log(`   ⚠️  PDF falhou: ${pdfResult.stderr?.slice(0,200)}`)
  }
  
  return { mdPath }
}

async function main() {
  console.log(`🚀 Gerar ${PRODUTOS.length} produtos digitais Gumroad\n`)
  for (const produto of PRODUTOS) {
    try {
      await gerarPDF(produto)
    } catch (e) {
      console.error(`❌ Erro em ${produto.id}: ${e.message}`)
    }
  }
  console.log(`\n✅ Concluído. Pastas: ${OUT_DIR}`)
}

main().catch(console.error)
