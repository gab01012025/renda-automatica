import './globals.css'
import type { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: {
    default: 'IA em Português — Ferramentas e Reviews',
    template: '%s | IA em Português',
  },
  description: 'Reviews, comparações e guias sobre as melhores ferramentas de Inteligência Artificial em português. Conteúdo atualizado semanalmente.',
  openGraph: {
    type: 'website',
    locale: 'pt_PT',
    siteName: 'IA em Português',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-PT">
      <body>
        <header className="border-b border-slate-200 bg-white sticky top-0 z-40 backdrop-blur bg-white/90">
          <div className="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
            <Link href="/" className="text-xl font-extrabold">
              🤖 IA em <span className="text-blue-600">Português</span>
            </Link>
            <nav className="flex gap-6 text-slate-600 font-medium">
              <Link href="/" className="hover:text-slate-900">Início</Link>
              <Link href="/artigos" className="hover:text-slate-900">Artigos</Link>
              <Link href="/sobre" className="hover:text-slate-900">Sobre</Link>
            </nav>
          </div>
        </header>

        <main className="max-w-3xl mx-auto px-6 py-10">
          {children}
        </main>

        <footer className="border-t border-slate-200 mt-20 py-10 text-center text-sm text-slate-500">
          <p>© {new Date().getFullYear()} IA em Português. Alguns links são de afiliados — se comprar por eles recebemos uma comissão sem custo extra para si.</p>
        </footer>
      </body>
    </html>
  )
}
