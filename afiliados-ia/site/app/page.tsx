import fs from 'node:fs'
import path from 'node:path'
import matter from 'gray-matter'
import Link from 'next/link'

export default function Home() {
  const posts = listarArtigos()
  return (
    <>
      <section className="py-10 text-center">
        <h1 className="text-5xl font-extrabold mb-4">Ferramentas de IA em Português</h1>
        <p className="text-xl text-slate-600 max-w-2xl mx-auto">
          Reviews honestos, comparações e guias para tirar o máximo das melhores ferramentas de Inteligência Artificial — tudo em PT.
        </p>
      </section>

      <section className="mt-16">
        <h2 className="text-2xl font-bold mb-6">Artigos recentes</h2>
        {posts.length === 0 ? (
          <p className="text-slate-500 italic">Ainda sem artigos. Rode o gerador para publicar o primeiro.</p>
        ) : (
          <div className="space-y-6">
            {posts.map(p => (
              <Link key={p.slug} href={`/artigos/${p.slug}`} className="block p-6 rounded-xl border border-slate-200 hover:border-blue-400 hover:shadow-md transition">
                <h3 className="text-xl font-bold mb-2">{p.title}</h3>
                <p className="text-slate-600">{p.description}</p>
                <p className="text-xs text-slate-400 mt-3">{p.date}</p>
              </Link>
            ))}
          </div>
        )}
      </section>
    </>
  )
}

function listarArtigos() {
  const dir = path.join(process.cwd(), 'content/artigos')
  if (!fs.existsSync(dir)) return []
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.mdx'))
    .map(f => {
      const src = fs.readFileSync(path.join(dir, f), 'utf8')
      const { data } = matter(src)
      return {
        slug: f.replace(/\.mdx$/, ''),
        title: data.title || f,
        description: data.description || '',
        date: data.date || '',
      }
    })
    .sort((a, b) => (a.date < b.date ? 1 : -1))
}
