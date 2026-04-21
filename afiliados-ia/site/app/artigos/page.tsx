import fs from 'node:fs'
import path from 'node:path'
import matter from 'gray-matter'
import Link from 'next/link'

export const metadata = { title: 'Todos os artigos' }

export default function ArtigosPage() {
  const posts = listarTodos()
  return (
    <>
      <h1 className="text-4xl font-extrabold mb-8">Todos os artigos</h1>
      {posts.length === 0 ? (
        <p className="text-slate-500 italic">Ainda sem artigos.</p>
      ) : (
        <div className="space-y-4">
          {posts.map(p => (
            <Link key={p.slug} href={`/artigos/${p.slug}`} className="block p-5 rounded-lg border border-slate-200 hover:border-blue-400 hover:shadow transition">
              <h3 className="text-lg font-bold">{p.title}</h3>
              <p className="text-slate-600 text-sm mt-1">{p.description}</p>
              <p className="text-xs text-slate-400 mt-2">{p.date}</p>
            </Link>
          ))}
        </div>
      )}
    </>
  )
}

function listarTodos() {
  const dir = path.join(process.cwd(), 'content/artigos')
  if (!fs.existsSync(dir)) return []
  return fs.readdirSync(dir).filter(f => f.endsWith('.mdx')).map(f => {
    const { data } = matter(fs.readFileSync(path.join(dir, f), 'utf8'))
    return { slug: f.replace(/\.mdx$/, ''), title: data.title, description: data.description, date: data.date }
  }).sort((a, b) => (a.date < b.date ? 1 : -1))
}
