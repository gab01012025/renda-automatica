'use client'
import { useState } from 'react'

type Result = { titulo: string; descricao: string; tags: string[] }

export default function Home() {
  const [produto, setProduto] = useState('')
  const [tipo, setTipo] = useState('t-shirt')
  const [estilo, setEstilo] = useState('moderno')
  const [publico, setPublico] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState('')
  const [usados, setUsados] = useState(0)

  async function gerar(e: React.FormEvent) {
    e.preventDefault()
    if (usados >= 3) {
      setError('Limite gratuito atingido. Para uso ilimitado: €5/mês (em breve checkout).')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const r = await fetch('/api/gerar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ produto, tipo, estilo, publico }),
      })
      if (!r.ok) throw new Error((await r.json()).error || 'Erro')
      const data = await r.json()
      setResult(data)
      setUsados((n) => n + 1)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function copy(text: string) {
    navigator.clipboard.writeText(text)
  }

  return (
    <main className="max-w-3xl mx-auto px-6 py-10">
      <div className="text-center mb-10">
        <div className="inline-block bg-rose-600 text-white px-4 py-1 rounded-full text-sm font-bold mb-4">
          🚀 Gerador IA para Etsy
        </div>
        <h1 className="text-4xl md:text-5xl font-black text-gray-900 leading-tight">
          Títulos & Descrições <span className="text-rose-600">Etsy</span> em 10 segundos
        </h1>
        <p className="text-lg text-gray-600 mt-4">
          Para de gastar 30 minutos por produto. IA gera título SEO, descrição persuasiva e 13 tags otimizadas. Em português.
        </p>
        <div className="mt-3 text-sm text-gray-500">
          ✅ 3 gerações grátis • ✅ Sem registo • ✅ GPT-4
        </div>
      </div>

      <form onSubmit={gerar} className="bg-white rounded-2xl shadow-xl p-6 space-y-4">
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-1">O que vendes? *</label>
          <input
            type="text"
            value={produto}
            onChange={(e) => setProduto(e.target.value)}
            required
            placeholder="Ex: T-shirt com estampa de gato astronauta"
            className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-rose-500 outline-none"
          />
        </div>
        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Tipo</label>
            <select value={tipo} onChange={(e) => setTipo(e.target.value)} className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg outline-none focus:border-rose-500">
              <option>t-shirt</option>
              <option>poster</option>
              <option>caneca</option>
              <option>sweatshirt</option>
              <option>tote bag</option>
              <option>arte digital</option>
              <option>joalharia</option>
              <option>decoração</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Estilo</label>
            <select value={estilo} onChange={(e) => setEstilo(e.target.value)} className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg outline-none focus:border-rose-500">
              <option>moderno</option>
              <option>vintage</option>
              <option>minimalista</option>
              <option>boho</option>
              <option>fofo/kawaii</option>
              <option>elegante</option>
              <option>humor</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-1">Público</label>
            <input
              value={publico}
              onChange={(e) => setPublico(e.target.value)}
              placeholder="Ex: mulheres 25-40"
              className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg outline-none focus:border-rose-500"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-gradient-to-r from-rose-600 to-orange-600 text-white py-4 rounded-lg font-bold text-lg hover:opacity-90 disabled:opacity-50 transition"
        >
          {loading ? '🪄 A gerar...' : `✨ Gerar (${3 - usados} grátis)`}
        </button>
        {error && <div className="text-rose-600 text-sm bg-rose-50 p-3 rounded">{error}</div>}
      </form>

      {result && (
        <div className="mt-8 space-y-4">
          <ResultBox label="📌 Título Etsy (SEO otimizado)" value={result.titulo} onCopy={() => copy(result.titulo)} />
          <ResultBox label="📝 Descrição" value={result.descricao} onCopy={() => copy(result.descricao)} multiline />
          <div className="bg-white rounded-xl p-5 shadow">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-gray-900">🏷️ 13 Tags Otimizadas</h3>
              <button
                onClick={() => copy(result.tags.join(', '))}
                className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded"
              >
                Copiar todas
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {result.tags.map((t, i) => (
                <span key={i} className="bg-rose-100 text-rose-800 px-3 py-1 rounded-full text-sm">{t}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      <div className="mt-12 text-center">
        <h2 className="text-2xl font-bold mb-4">Gostaste? 💜</h2>
        <p className="text-gray-600 mb-6">Vê os meus produtos físicos com designs IA</p>
        <a
          href="https://etsy.com/shop/PrintHouseLX"
          target="_blank"
          rel="noopener"
          className="inline-block bg-rose-600 text-white px-8 py-3 rounded-lg font-bold hover:bg-rose-700"
        >
          🛍️ Visita PrintHouseLX no Etsy
        </a>
      </div>

      <footer className="mt-16 text-center text-sm text-gray-500">
        <p>Feito por <a className="text-rose-600 underline" href="https://etsy.com/shop/PrintHouseLX">PrintHouseLX</a> · Powered by GPT-4</p>
      </footer>
    </main>
  )
}

function ResultBox({ label, value, onCopy, multiline }: { label: string; value: string; onCopy: () => void; multiline?: boolean }) {
  return (
    <div className="bg-white rounded-xl p-5 shadow">
      <div className="flex justify-between items-center mb-2">
        <h3 className="font-bold text-gray-900">{label}</h3>
        <button onClick={onCopy} className="text-sm bg-gray-100 hover:bg-gray-200 px-3 py-1 rounded">
          📋 Copiar
        </button>
      </div>
      <div className={`text-gray-800 ${multiline ? 'whitespace-pre-wrap' : ''}`}>{value}</div>
    </div>
  )
}
