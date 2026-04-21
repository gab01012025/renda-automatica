import fs from 'node:fs'
import path from 'node:path'
import matter from 'gray-matter'
import { notFound } from 'next/navigation'
import type { Metadata } from 'next'

export async function generateStaticParams() {
  const dir = path.join(process.cwd(), 'content/artigos')
  if (!fs.existsSync(dir)) return []
  return fs.readdirSync(dir)
    .filter(f => f.endsWith('.mdx'))
    .map(f => ({ slug: f.replace(/\.mdx$/, '') }))
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const post = carregarPost(params.slug)
  if (!post) return {}
  return {
    title: post.data.title,
    description: post.data.description,
  }
}

function carregarPost(slug: string) {
  const file = path.join(process.cwd(), 'content/artigos', `${slug}.mdx`)
  if (!fs.existsSync(file)) return null
  const src = fs.readFileSync(file, 'utf8')
  const parsed = matter(src)
  return parsed
}

export default async function ArtigoPage({ params }: { params: { slug: string } }) {
  const post = carregarPost(params.slug)
  if (!post) notFound()

  // Importa dinamicamente o MDX
  const { default: MDXContent } = await import(`@/content/artigos/${params.slug}.mdx`)

  return (
    <article className="prose prose-slate max-w-none">
      <h1 className="text-4xl font-extrabold mb-3">{post.data.title}</h1>
      <p className="text-slate-500 text-sm mb-10">{post.data.date}</p>
      <MDXContent />
      <hr className="my-12" />
      <p className="text-sm text-slate-500 italic">
        💡 Este artigo contém links de afiliado. Se comprar através deles, ganhamos uma pequena comissão (sem custo extra para si) que ajuda a manter este site.
      </p>
    </article>
  )
}
