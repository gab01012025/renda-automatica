import type { MDXComponents } from 'mdx/types'

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
    h1: ({ children }) => <h1 className="text-4xl font-extrabold mt-10 mb-6">{children}</h1>,
    h2: ({ children }) => <h2 className="text-3xl font-bold mt-10 mb-4 text-slate-800">{children}</h2>,
    h3: ({ children }) => <h3 className="text-2xl font-semibold mt-8 mb-3 text-slate-800">{children}</h3>,
    p: ({ children }) => <p className="text-lg leading-relaxed mb-5 text-slate-700">{children}</p>,
    a: ({ href, children }) => (
      <a href={href} target="_blank" rel="noopener sponsored" className="text-blue-600 hover:text-blue-800 underline font-medium">
        {children}
      </a>
    ),
    ul: ({ children }) => <ul className="list-disc pl-6 mb-5 space-y-2 text-slate-700">{children}</ul>,
    ol: ({ children }) => <ol className="list-decimal pl-6 mb-5 space-y-2 text-slate-700">{children}</ol>,
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-blue-500 bg-blue-50 px-6 py-3 my-6 italic text-slate-700">
        {children}
      </blockquote>
    ),
    code: ({ children }) => <code className="bg-slate-100 text-pink-700 px-1.5 py-0.5 rounded text-sm">{children}</code>,
    table: ({ children }) => (
      <div className="overflow-x-auto my-6">
        <table className="min-w-full border-collapse border border-slate-300">{children}</table>
      </div>
    ),
    th: ({ children }) => <th className="border border-slate-300 bg-slate-100 px-4 py-2 text-left font-semibold">{children}</th>,
    td: ({ children }) => <td className="border border-slate-300 px-4 py-2">{children}</td>,
    ...components,
  }
}
