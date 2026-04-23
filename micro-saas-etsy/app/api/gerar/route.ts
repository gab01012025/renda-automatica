import { NextRequest, NextResponse } from 'next/server'

// Rate limit em memória (simples, reseta no cold start)
const ipCount = new Map<string, { count: number; reset: number }>()
const LIMIT = 10 // por IP por hora
const WINDOW = 60 * 60 * 1000

export const runtime = 'nodejs'

export async function POST(req: NextRequest) {
  try {
    const ip = req.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown'
    const now = Date.now()
    const entry = ipCount.get(ip)
    if (entry && entry.reset > now) {
      if (entry.count >= LIMIT) {
        return NextResponse.json({ error: 'Limite por hora excedido. Tenta mais tarde ou subscreve €5/mês.' }, { status: 429 })
      }
      entry.count++
    } else {
      ipCount.set(ip, { count: 1, reset: now + WINDOW })
    }

    const { produto, tipo, estilo, publico } = await req.json()
    if (!produto || produto.length < 5) {
      return NextResponse.json({ error: 'Descreve melhor o produto (min 5 chars)' }, { status: 400 })
    }

    const apiKey = process.env.OPENAI_API_KEY
    if (!apiKey) return NextResponse.json({ error: 'Servidor sem API key configurada' }, { status: 500 })

    const prompt = `Gera dados Etsy SEO otimizados para este produto:
- Produto: ${produto}
- Tipo: ${tipo}
- Estilo: ${estilo}
- Público: ${publico || 'geral'}

Devolve JSON com:
- titulo: máximo 140 caracteres, com keywords SEO no início, em PT-PT (não brasileiro)
- descricao: 4-6 frases persuasivas, com benefícios + ocasiões de uso + qualidade. Em PT-PT. Termina com call-to-action sutil.
- tags: array com EXATAMENTE 13 tags, máximo 20 caracteres cada, em PT (mistura PT e EN para ranking internacional), sem repetições, focadas em buscas reais Etsy

Responde APENAS JSON: {"titulo": "...", "descricao": "...", "tags": [...]}`

    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${apiKey}` },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        temperature: 0.85,
        response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: 'És especialista em SEO Etsy. Respondes sempre JSON válido em PT-PT.' },
          { role: 'user', content: prompt },
        ],
      }),
    })

    if (!r.ok) {
      return NextResponse.json({ error: 'Falha na geração. Tenta novamente.' }, { status: 500 })
    }
    const data = await r.json()
    const parsed = JSON.parse(data.choices[0].message.content)
    if (!parsed.titulo || !parsed.descricao || !parsed.tags) {
      return NextResponse.json({ error: 'Resposta inválida da IA' }, { status: 500 })
    }
    parsed.tags = (parsed.tags || []).slice(0, 13)
    return NextResponse.json(parsed)
  } catch (e: any) {
    return NextResponse.json({ error: e.message || 'Erro inesperado' }, { status: 500 })
  }
}
