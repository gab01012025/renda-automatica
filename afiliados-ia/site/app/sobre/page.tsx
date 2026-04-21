export const metadata = { title: 'Sobre' }

export default function SobrePage() {
  return (
    <div className="prose prose-slate max-w-none">
      <h1 className="text-4xl font-extrabold mb-6">Sobre o IA em Português</h1>
      <p className="text-lg text-slate-700 leading-relaxed">
        Este site existe para ajudar pessoas e empresas de Portugal e Brasil a escolher as melhores
        ferramentas de Inteligência Artificial — em português, sem marketês, sem hype.
      </p>
      <p className="text-lg text-slate-700 leading-relaxed mt-4">
        Testamos cada ferramenta antes de recomendar. Quando uma ferramenta não presta, dizemos.
        Quando é boa, explicamos para quem faz sentido.
      </p>
      <h2 className="text-2xl font-bold mt-10 mb-4">Como ganhamos dinheiro</h2>
      <p className="text-lg text-slate-700 leading-relaxed">
        Muitos dos links neste site são de afiliado. Se comprar uma ferramenta através deles,
        recebemos uma pequena comissão sem custo extra para si. Isto permite-nos manter o site
        sem cobrar pelos artigos e sem encher tudo de publicidade agressiva.
      </p>
      <p className="text-lg text-slate-700 leading-relaxed mt-4">
        As nossas recomendações não são influenciadas por comissões — recomendamos o que é bom,
        não o que paga mais.
      </p>
    </div>
  )
}
