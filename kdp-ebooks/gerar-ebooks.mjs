#!/usr/bin/env node
/**
 * Gerador de Ebooks KDP (Amazon Kindle Direct Publishing)
 * Gera 5 ebooks de 30-50 páginas em PT/EN sobre nichos de alta procura.
 * Output: .md + .html + .pdf + capa.png (via DALL-E)
 */
import fs from 'node:fs'
import path from 'node:path'
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const OUT_DIR = path.join(__dirname, 'ebooks')
fs.mkdirSync(OUT_DIR, { recursive: true })

// Carregar OPENAI_API_KEY
const envCandidates = [
  path.join(__dirname, '.env'),
  path.join(ROOT, 'produtos-digitais', '.env'),
  path.join(ROOT, 'pod-automatico', '.env'),
]
for (const p of envCandidates) {
  if (fs.existsSync(p)) {
    for (const line of fs.readFileSync(p, 'utf-8').split('\n')) {
      const m = line.match(/^([A-Z_]+)=(.*)$/)
      if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
    }
  }
}
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
if (!OPENAI_API_KEY) throw new Error('OPENAI_API_KEY missing')

const EBOOKS = [
  {
    id: 'chatgpt-advogados-pt',
    titulo: 'ChatGPT para Advogados: Guia Prático 2026',
    subtitulo: 'Como usar IA para petições, contratos e pareceres em 1/3 do tempo',
    lingua: 'pt-PT',
    publico: 'advogados, juristas e estagiários em Portugal e Brasil',
    preco: 4.99,
    capitulos: [
      'Porque a IA vai mudar a advocacia (e o que fazer quanto a isso)',
      'Instalar e configurar o ChatGPT em 5 minutos',
      'Prompts essenciais para petições iniciais',
      'Redação automática de contratos',
      'Análise de jurisprudência com IA',
      'Pareceres jurídicos em minutos',
      'Revisão e melhoria de textos forenses',
      'Protecção de dados e sigilo profissional',
      'Workflow diário: exemplos reais',
      'Próximos passos: de principiante a expert',
    ],
  },
  {
    id: 'chatgpt-imobiliaria-pt',
    titulo: 'ChatGPT para Imobiliárias: Vender Mais com IA',
    subtitulo: 'Descrições que vendem, leads automáticos, e fecho em tempo recorde',
    lingua: 'pt-PT',
    publico: 'agentes imobiliários e mediadores PT/BR',
    preco: 4.99,
    capitulos: [
      'O mercado imobiliário em 2026 e a revolução IA',
      'Prompts para descrições de imóveis que vendem',
      'Gerar anúncios Idealista e Imovirtual automaticamente',
      'Emails follow-up com leads (templates prontos)',
      'Análise comparativa de mercado com IA',
      'Posts Instagram e Facebook para imobiliária',
      'Chatbot atendimento 24/7',
      'Apresentações de imóveis a clientes',
      'Negociação: como usar IA para fechar',
      'Checklists e automação do dia-a-dia',
    ],
  },
  {
    id: 'copywriting-ia-pt',
    titulo: 'Copywriting com IA: 50 Templates que Vendem',
    subtitulo: 'Das headlines aos emails de vendas — tudo gerado com ChatGPT',
    lingua: 'pt-PT',
    publico: 'empreendedores, freelancers e gestores de marketing',
    preco: 3.99,
    capitulos: [
      'Copywriting 101: o que funciona em 2026',
      'A fórmula AIDA adaptada para IA',
      '10 headlines magnéticas (com prompts)',
      '10 emails de vendas passo a passo',
      '10 páginas de vendas completas',
      '10 anúncios Facebook/Instagram',
      '10 posts LinkedIn virais',
      'Estrutura perfeita de VSL (Video Sales Letter)',
      'Como testar e otimizar copy gerado por IA',
      'Estudo de caso: de €0 a €10k/mês',
    ],
  },
  {
    id: 'excel-ia-pt',
    titulo: 'Excel Turbinado com IA: do Zero ao Avançado',
    subtitulo: 'Fórmulas, macros e dashboards gerados pelo ChatGPT em segundos',
    lingua: 'pt-PT',
    publico: 'profissionais que usam Excel diariamente (gestão, contabilidade, RH)',
    preco: 4.99,
    capitulos: [
      'Porquê combinar Excel e IA agora',
      'Prompts para fórmulas complexas (PROCV, SOMASES, INDICE/CORRESP)',
      'Macros VBA geradas pelo ChatGPT',
      'Dashboards profissionais em 10 minutos',
      'Automatizar relatórios mensais',
      'Limpeza de dados com IA',
      'Fórmulas financeiras (TIR, VAL, amortização)',
      'Fórmulas estatísticas e análise de dados',
      'Power Query + IA: combo definitivo',
      'Casos reais: contabilidade, RH, vendas',
    ],
  },
  {
    id: 'receitas-low-carb-ia-en',
    titulo: 'Low-Carb Recipes Made Easy: 100 AI-Generated Meals',
    subtitulo: 'Breakfast, lunch, dinner — all under 20g carbs, ready in 30 min',
    lingua: 'en-US',
    publico: 'english-speaking readers on keto or low-carb diet',
    preco: 3.99,
    capitulos: [
      'Low-carb basics: what you need to know',
      '20 breakfast recipes under 10g carbs',
      '20 lunch recipes ready in 20 minutes',
      '20 dinner recipes the whole family loves',
      '10 snack ideas for busy days',
      '10 dessert recipes (yes, really)',
      '10 meal-prep friendly recipes',
      '7-day meal plan',
      'Shopping list generator',
      'FAQ and troubleshooting',
    ],
  },
]

async function gerarCapitulo(ebook, idx) {
  const titulo = ebook.capitulos[idx]
  const lang = ebook.lingua === 'en-US' ? 'English (US)' : 'Portuguese (pt-PT, European Portuguese)'
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: 'gpt-4o',
      temperature: 0.75,
      messages: [
        {
          role: 'system',
          content: `You are a bestselling non-fiction author writing in ${lang}. Write a complete chapter (~1500-2000 words) that is practical, actionable, and engaging. Use markdown: ## subheadings, bullet lists, numbered steps, **bold** key terms, > blockquotes for tips. No filler. End with a short "Key Takeaways" bullet list.`,
        },
        {
          role: 'user',
          content: `Book: "${ebook.titulo}"\nAudience: ${ebook.publico}\nChapter ${idx + 1}: "${titulo}"\n\nWrite this chapter in ${lang}. Be specific, include real examples, prompts, tables where useful.`,
        },
      ],
    }),
  })
  if (!r.ok) throw new Error(`OpenAI: ${r.status} ${await r.text()}`)
  const data = await r.json()
  return data.choices[0].message.content
}

async function gerarCapa(ebook) {
  console.log(`   🎨 Gerando capa DALL-E...`)
  const prompt = `Book cover for "${ebook.titulo}". ${ebook.subtitulo}. Modern, professional, minimalist design. Bold typography. Eye-catching colors. Kindle ebook cover aspect ratio (portrait 1600x2560). No text errors, clean layout. Genre: non-fiction self-help / business.`
  const r = await fetch('https://api.openai.com/v1/images/generations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({
      model: 'dall-e-3',
      prompt,
      n: 1,
      size: '1024x1792',
      quality: 'standard',
    }),
  })
  if (!r.ok) {
    console.log(`   ⚠️  Capa falhou: ${r.status}`)
    return null
  }
  const data = await r.json()
  const imgUrl = data.data[0].url
  const imgRes = await fetch(imgUrl)
  const buf = Buffer.from(await imgRes.arrayBuffer())
  const capaPath = path.join(OUT_DIR, `${ebook.id}-capa.png`)
  fs.writeFileSync(capaPath, buf)
  console.log(`   ✅ Capa salva: ${capaPath}`)
  return capaPath
}

function gerarMarkdown(ebook, capitulosContent) {
  const isEN = ebook.lingua === 'en-US'
  let md = `# ${ebook.titulo}\n\n## ${ebook.subtitulo}\n\n`
  md += `---\n\n`
  md += isEN ? `## Table of Contents\n\n` : `## Índice\n\n`
  ebook.capitulos.forEach((c, i) => { md += `${i + 1}. ${c}\n` })
  md += `\n---\n\n`
  md += isEN ? `## Introduction\n\n` : `## Introdução\n\n`
  md += isEN
    ? `Welcome. This book is designed to be practical — no fluff, no filler. Every chapter delivers immediate value you can apply today. Let's begin.\n\n---\n\n`
    : `Bem-vindo(a). Este livro foi desenhado para ser prático — sem enrolação. Cada capítulo entrega valor imediato que podes aplicar hoje. Vamos começar.\n\n---\n\n`

  ebook.capitulos.forEach((cap, i) => {
    md += `# ${isEN ? 'Chapter' : 'Capítulo'} ${i + 1}: ${cap}\n\n`
    md += capitulosContent[i] + '\n\n---\n\n'
  })

  md += isEN ? `## Final Words\n\n` : `## Palavras Finais\n\n`
  md += isEN
    ? `Thank you for reading. If this book helped you, please leave a review on Amazon — it really helps independent authors.\n\n© 2026 PrintHouseLX. All rights reserved.\n`
    : `Obrigado por leres. Se este livro te ajudou, por favor deixa uma review na Amazon — ajuda muito autores independentes.\n\n© 2026 PrintHouseLX. Todos os direitos reservados.\n`
  return md
}

async function gerarEbook(ebook) {
  console.log(`\n📚 Gerando ebook: ${ebook.titulo} (€${ebook.preco})`)
  console.log(`   Língua: ${ebook.lingua} | Capítulos: ${ebook.capitulos.length}`)

  const capitulos = []
  for (let i = 0; i < ebook.capitulos.length; i++) {
    process.stdout.write(`   [${i + 1}/${ebook.capitulos.length}] ${ebook.capitulos[i].slice(0, 60)}... `)
    try {
      const c = await gerarCapitulo(ebook, i)
      capitulos.push(c)
      console.log('✓')
    } catch (e) {
      console.log(`✗ ${e.message.slice(0, 80)}`)
      capitulos.push(`_(erro na geração deste capítulo)_`)
    }
  }

  const md = gerarMarkdown(ebook, capitulos)
  const mdPath = path.join(OUT_DIR, `${ebook.id}.md`)
  fs.writeFileSync(mdPath, md, 'utf-8')
  console.log(`   ✅ Markdown: ${mdPath}`)

  // HTML
  const htmlPath = path.join(OUT_DIR, `${ebook.id}.html`)
  const cssPath = path.join(OUT_DIR, '_style.css')
  const css = `
    body { font-family: Georgia, "Times New Roman", serif; max-width: 780px; margin: 40px auto; padding: 24px; line-height: 1.65; color: #1a1a1a; }
    h1 { color: #1a1a1a; border-bottom: 2px solid #c41e3a; padding-bottom: 8px; font-size: 28px; page-break-before: always; }
    h1:first-of-type { page-break-before: avoid; }
    h2 { color: #c41e3a; font-size: 22px; margin-top: 28px; }
    h3 { color: #333; font-size: 18px; }
    blockquote { background: #fff8e7; padding: 12px 20px; border-left: 4px solid #d4a017; font-style: italic; }
    code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; font-size: 0.9em; }
    pre { background: #f8f8f8; padding: 12px; border-radius: 5px; overflow-x: auto; }
    strong { color: #c41e3a; }
    hr { border: none; border-top: 1px solid #ddd; margin: 24px 0; }
    ul, ol { padding-left: 24px; }
    li { margin: 6px 0; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0; }
    th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; }
    th { background: #f5f5f5; }
  `
  fs.writeFileSync(cssPath, `<style>${css}</style>`, 'utf-8')
  const htmlResult = spawnSync('pandoc', [mdPath, '-o', htmlPath, '--standalone', '--metadata', `title:${ebook.titulo}`, '-H', cssPath], { encoding: 'utf-8' })
  if (htmlResult.status !== 0) {
    console.log(`   ⚠️  HTML falhou: ${htmlResult.stderr?.slice(0, 200)}`)
  } else {
    console.log(`   ✅ HTML: ${htmlPath}`)
  }

  // PDF (interior do livro KDP) — usa path absoluto com file://
  const pdfPath = path.join(OUT_DIR, `${ebook.id}.pdf`)
  const pdfResult = spawnSync('wkhtmltopdf', [
    '--encoding', 'UTF-8',
    '--margin-top', '20mm', '--margin-bottom', '20mm',
    '--margin-left', '18mm', '--margin-right', '18mm',
    '--enable-local-file-access',
    '--page-size', 'A5',
    `file://${htmlPath}`, pdfPath,
  ], { encoding: 'utf-8' })
  if (pdfResult.status === 0) {
    const sizeMB = (fs.statSync(pdfPath).size / 1024 / 1024).toFixed(2)
    console.log(`   ✅ PDF A5 (KDP): ${pdfPath} (${sizeMB} MB)`)
  } else {
    console.log(`   ⚠️  PDF falhou: ${pdfResult.stderr?.slice(0, 200)}`)
  }

  // Capa (só se ainda não existe)
  const capaPath = path.join(OUT_DIR, `${ebook.id}-capa.png`)
  if (!fs.existsSync(capaPath)) {
    try {
      await gerarCapa(ebook)
    } catch (e) {
      console.log(`   ⚠️  Capa erro: ${e.message.slice(0, 100)}`)
    }
  } else {
    console.log(`   ↺ Capa já existe`)
  }
}

async function main() {
  const arg = process.argv[2]
  const lista = arg ? EBOOKS.filter(e => e.id === arg) : EBOOKS
  if (!lista.length) {
    console.error(`Ebook "${arg}" não encontrado. IDs: ${EBOOKS.map(e => e.id).join(', ')}`)
    process.exit(1)
  }
  console.log(`🚀 Gerando ${lista.length} ebook(s) KDP\n`)
  for (const e of lista) {
    try { await gerarEbook(e) } catch (e2) { console.error(`❌ ${e2.message}`) }
  }
  console.log(`\n✅ Concluído. Pasta: ${OUT_DIR}\n`)
  console.log(`📤 Próximos passos manuais (KDP):`)
  console.log(`   1. kdp.amazon.com → Sign in`)
  console.log(`   2. Create new Kindle eBook`)
  console.log(`   3. Upload o PDF (interior) + PNG (capa)`)
  console.log(`   4. Keywords: 7 (usar as dos capítulos)`)
  console.log(`   5. Price: €${EBOOKS[0].preco}-${EBOOKS[2].preco} (70% royalty)`)
}

main().catch(console.error)
