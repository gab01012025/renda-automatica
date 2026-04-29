/**
 * Gerador de Artigos SEO MULTI-IDIOMA para Afiliados Amazon
 *
 * Cobre 4 mercados (Amazon.com, .es, .de, .fr) → tráfego Google grátis em 4 países.
 * Cada artigo é "best X 2026" em buyer-intent keyword com links afiliados Amazon.
 *
 * Receita esperada (após 3-6 meses de indexação):
 *   - 100 artigos × 30 visitas/dia × 3% CTR Amazon × 4% comissão × €40 ticket = €144/dia (€4.3k/mês)
 *   - Realista 6 meses: 50% disso = €2k/mês
 *
 * Uso: node gerar-artigo-multilang.mjs [N=2]
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, '..')
const SITE = path.join(ROOT, 'site')

// .env
const envPath = path.join(ROOT, '.env')
if (fs.existsSync(envPath)) {
  for (const line of fs.readFileSync(envPath, 'utf-8').split('\n')) {
    const m = line.match(/^([A-Z_]+)=(.*)$/)
    if (m) process.env[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
  }
}
const OPENAI_API_KEY = process.env.OPENAI_API_KEY
if (!OPENAI_API_KEY) { console.error('OPENAI_API_KEY missing'); process.exit(1) }

// Amazon Affiliate Tags por região (define no .env quando criares conta Amazon Associates)
const AMZ_TAG = {
  com: process.env.AMZ_TAG_COM || 'tag-default-20',
  es:  process.env.AMZ_TAG_ES  || 'tag-default-21',
  de:  process.env.AMZ_TAG_DE  || 'tag-default-21',
  fr:  process.env.AMZ_TAG_FR  || 'tag-default-21',
  it:  process.env.AMZ_TAG_IT  || 'tag-default-21',
  uk:  process.env.AMZ_TAG_UK  || 'tag-default-21',
}

// Idiomas → mercado Amazon → buyer keywords (high commercial intent)
const MERCADOS = {
  en: { dominio: 'co.uk', nome: 'English / UK', moeda: '£', tagKey: 'uk', kws: [
    'best wireless earbuds 2026 uk', 'best standing desk 2026 uk', 'best portable monitor 2026',
    'best ergonomic office chair 2026', 'best running shoes for flat feet 2026',
    'best espresso machine under 500', 'best mechanical keyboard 2026',
    'best webcam for streaming 2026', 'best air purifier for allergies 2026',
    'best smart bulbs alexa 2026', 'best gaming headset under 100',
    'best electric toothbrush 2026', 'best resistance bands set',
    'best blue light glasses 2026', 'best dash cam 2026',
    'best camping tent for 2 people', 'best bluetooth speaker outdoor',
    'best laptop stand for desk', 'best vertical mouse ergonomic',
    'best yoga mat thick 2026',
  ]},
  es: { dominio: 'es', nome: 'Español / España', moeda: '€', tagKey: 'es', kws: [
    'mejores auriculares inalambricos 2026', 'mejor mesa elevable 2026',
    'mejor silla oficina ergonomica 2026', 'mejor robot aspirador 2026',
    'mejor cafetera espresso 2026', 'mejor cuchillo cocina 2026',
    'mejor freidora aire 2026', 'mejor monitor portatil 2026',
    'mejor altavoz bluetooth exterior', 'mejor cepillo electrico dental',
    'mejor purificador aire para alergias', 'mejor proyector 4k 2026',
    'mejor portatil estudiantes 2026', 'mejor camara seguridad casa',
    'mejor smartwatch barato 2026', 'mejor patinete electrico 2026',
    'mejor batidora vaso 2026', 'mejor router wifi mesh 2026',
    'mejor cama elevable adulto', 'mejor colchon viscoelastico 2026',
  ]},
  de: { dominio: 'de', nome: 'Deutsch / Deutschland', moeda: '€', tagKey: 'de', kws: [
    'beste kabellose kopfhoerer 2026', 'bester hoehenverstellbarer schreibtisch 2026',
    'bester ergonomischer buerostuhl 2026', 'bester saugroboter 2026',
    'beste espressomaschine 2026', 'bestes kuechenmesser 2026',
    'beste heissluftfritteuse 2026', 'bester tragbarer monitor 2026',
    'bester bluetooth lautsprecher outdoor', 'beste elektrische zahnbuerste',
    'bester luftreiniger fuer allergiker', 'bester 4k beamer 2026',
    'bester laptop fuer studenten 2026', 'beste ueberwachungskamera aussen',
    'beste smartwatch unter 200 euro', 'bester e-scooter 2026',
    'bester standmixer 2026', 'bester wifi mesh router 2026',
    'beste matratze 90x200 2026', 'beste boxspringbett 2026',
  ]},
  fr: { dominio: 'fr', nome: 'Français / France', moeda: '€', tagKey: 'fr', kws: [
    'meilleurs ecouteurs sans fil 2026', 'meilleur bureau assis debout 2026',
    'meilleure chaise bureau ergonomique 2026', 'meilleur aspirateur robot 2026',
    'meilleure machine espresso 2026', 'meilleur couteau cuisine 2026',
    'meilleure friteuse a air 2026', 'meilleur moniteur portable 2026',
    'meilleure enceinte bluetooth exterieur', 'meilleure brosse a dents electrique',
    'meilleur purificateur air allergies', 'meilleur videoprojecteur 4k 2026',
    'meilleur ordinateur portable etudiant', 'meilleure camera surveillance maison',
    'meilleure montre connectee 2026', 'meilleure trottinette electrique 2026',
    'meilleur blender vase 2026', 'meilleur routeur wifi mesh 2026',
    'meilleur matelas memoire forme 2026', 'meilleur sommier electrique 2026',
  ]},
  it: { dominio: 'it', nome: 'Italiano / Italia', moeda: '€', tagKey: 'it', kws: [
    'migliori auricolari wireless 2026', 'migliore scrivania regolabile 2026',
    'migliore sedia ufficio ergonomica 2026', 'migliore robot aspirapolvere 2026',
    'migliore macchina espresso 2026', 'migliore coltello cucina 2026',
    'migliore friggitrice aria 2026', 'migliore monitor portatile 2026',
    'migliore altoparlante bluetooth esterno', 'migliore spazzolino elettrico',
    'migliore purificatore aria allergie', 'migliore proiettore 4k 2026',
    'migliore portatile studenti 2026', 'migliore telecamera sorveglianza casa',
    'migliore smartwatch economico 2026', 'migliore monopattino elettrico 2026',
    'migliore frullatore vaso 2026', 'migliore router wifi mesh 2026',
    'migliore materasso memory 2026', 'migliore rete elettrica matrimoniale',
  ]},
}

const HIST = path.join(__dirname, '_publicados-multilang.json')
const publicados = fs.existsSync(HIST) ? JSON.parse(fs.readFileSync(HIST, 'utf-8')) : []

function escolhe() {
  const langs = Object.keys(MERCADOS)
  const lang = langs[Math.floor(Math.random() * langs.length)]
  const m = MERCADOS[lang]
  const naoFeitos = m.kws.filter(k => !publicados.includes(`${lang}:${k}`))
  if (naoFeitos.length === 0) return null
  const kw = naoFeitos[Math.floor(Math.random() * naoFeitos.length)]
  return { lang, mercado: m, kw }
}

function slugify(s) {
  return s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,'')
    .replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'').slice(0,80)
}

async function gpt(messages, temperature = 0.75) {
  const r = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${OPENAI_API_KEY}` },
    body: JSON.stringify({ model: 'gpt-4o', temperature, messages }),
  })
  if (!r.ok) throw new Error(`OpenAI ${r.status}: ${await r.text()}`)
  const d = await r.json()
  return d.choices[0].message.content
}

async function gerarArtigo({ lang, mercado, kw }) {
  const tag = AMZ_TAG[mercado.tagKey || mercado.dominio]
  const amzSearch = `https://www.amazon.${mercado.dominio}/s?k=${encodeURIComponent(kw)}&tag=${tag}`

  const sysByLang = {
    en: 'You are an expert product reviewer writing in fluent natural English. NO AI-detector phrases like "in conclusion", "in todays digital age", "elevate". Write like a real human reviewer with personal anecdotes, specific use-cases, real concerns.',
    es: 'Eres un experto reviewer escribiendo en español natural y fluido (España, no Latinoamerica). NADA de "en conclusion" ni "en la era digital". Escribe como una persona real con experiencias personales especificas.',
    de: 'Du bist ein erfahrener Produkttester, der natuerliches fluentes Deutsch schreibt. KEINE KI-Phrasen wie "abschliessend" oder "in der heutigen digitalen Welt". Schreibe wie ein echter Mensch mit persoenlichen Erfahrungen.',
    fr: 'Tu es un expert testeur de produits ecrivant en francais naturel et fluide. PAS de phrases IA comme "en conclusion" ou "dans le monde numerique actuel". Ecris comme une vraie personne avec des experiences personnelles specifiques.',
    it: 'Sei un esperto recensore di prodotti che scrive in italiano naturale e fluido. NIENTE frasi da IA come "in conclusione" o "nellera digitale di oggi". Scrivi come una persona reale con esperienze personali specifiche.',
  }

  const articleInstr = {
    en: `Write a 1500-word article titled "${kw}" with sections: intro (problem you faced), top 7 picks (each with: heading, 2 paragraphs review with pros/cons, who its for), comparison table, buying guide (what to look for), FAQ (5 Q&A), final verdict. Use markdown. EVERY product mention must include this Amazon affiliate link: ${amzSearch} disguised as natural "Check on Amazon" or "See current price" anchor text. Use realistic 2026 product names (no fake brands - use generic "popular brand X" if needed).`,
    es: `Escribe articulo de 1500 palabras titulado "${kw}" con secciones: intro (problema personal), top 7 productos (cada uno: titulo, 2 parrafos review con pros/contras, para quien es), tabla comparativa, guia de compra (que mirar), FAQ (5 P&R), veredicto final. Usa markdown. CADA mencion de producto debe incluir este link afiliado Amazon: ${amzSearch} disfrazado como "Ver en Amazon" o "Ver precio actual". Usa nombres realistas 2026.`,
    de: `Schreibe 1500-Woerter-Artikel mit Titel "${kw}" mit Sektionen: Intro (persoenliches Problem), Top 7 Produkte (je: Ueberschrift, 2 Absaetze Review mit Pros/Cons, fuer wen), Vergleichstabelle, Kaufberatung (worauf achten), FAQ (5 F&A), Fazit. Markdown verwenden. JEDE Produkterwaehnung muss diesen Amazon Affiliate-Link enthalten: ${amzSearch} getarnt als "Auf Amazon ansehen" oder "Aktuellen Preis pruefen".`,
    fr: `Ecris article de 1500 mots intitule "${kw}" avec sections: intro (probleme personnel), top 7 produits (chacun: titre, 2 paragraphes review avec pros/cons, pour qui), tableau comparatif, guide d'achat (quoi regarder), FAQ (5 Q&R), verdict final. Markdown. CHAQUE mention de produit doit inclure ce lien affilie Amazon: ${amzSearch} deguise en "Voir sur Amazon" ou "Verifier le prix".`,
    it: `Scrivi un articolo di 1500 parole intitolato "${kw}" con sezioni: intro (problema personale), top 7 prodotti (ognuno: titolo, 2 paragrafi recensione con pro/contro, per chi e), tabella comparativa, guida all'acquisto (cosa guardare), FAQ (5 D&R), verdetto finale. Markdown. OGNI menzione di prodotto deve includere questo link affiliato Amazon: ${amzSearch} mascherato come "Vedi su Amazon" o "Controlla il prezzo attuale".`,
  }

  const md = await gpt([
    { role: 'system', content: sysByLang[lang] },
    { role: 'user', content: articleInstr[lang] },
  ], 0.85)

  const descByLang = {
    en: 'Independent product comparison and buying guide for 2026.',
    es: 'Comparativa independiente y guia de compra 2026.',
    de: 'Unabhaengiger Produktvergleich und Kaufberatung 2026.',
    fr: 'Comparatif independant et guide d\'achat 2026.',
    it: 'Confronto indipendente e guida all\'acquisto 2026.',
  }
  return { md, desc: descByLang[lang], amzSearch }
}

async function main() {
  const n = parseInt(process.argv[2] || '2', 10)
  const dir = path.join(SITE, 'content/artigos')
  fs.mkdirSync(dir, { recursive: true })
  let feitos = 0
  for (let i = 0; i < n; i++) {
    const pick = escolhe()
    if (!pick) { console.log('✅ Todas keywords feitas'); break }
    const { lang, kw } = pick
    console.log(`📝 [${i+1}/${n}] ${lang.toUpperCase()} — ${kw}`)
    try {
      const { md, desc } = await gerarArtigo(pick)
      const slug = `${lang}-${slugify(kw)}`
      const fm = `---
title: "${kw}"
description: "${desc}"
date: "${new Date().toISOString().slice(0,10)}"
slug: "${slug}"
lang: "${lang}"
keyword: "${kw}"
---

`
      fs.writeFileSync(path.join(dir, `${slug}.mdx`), fm + md)
      publicados.push(`${lang}:${kw}`)
      fs.writeFileSync(HIST, JSON.stringify(publicados, null, 2))
      feitos++
      console.log(`   ✅ ${slug}.mdx`)
    } catch (e) {
      console.error(`   ⚠️  ${e.message}`)
    }
  }
  console.log(`\n✅ ${feitos} artigos publicados (total acumulado: ${publicados.length})`)
}

main().catch(e => { console.error(e); process.exit(1) })
