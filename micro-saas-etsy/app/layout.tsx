import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'EtsyDescAI — Gerador IA de Títulos e Descrições Etsy (PT/BR)',
  description: 'Gera títulos SEO + descrições + 13 tags otimizadas para Etsy em segundos. Em português. Powered by GPT-4.',
  keywords: 'etsy, descrições etsy, SEO etsy, gerador IA, títulos etsy, tags etsy',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt">
      <body className="bg-gradient-to-br from-orange-50 to-rose-50 min-h-screen">{children}</body>
    </html>
  )
}
