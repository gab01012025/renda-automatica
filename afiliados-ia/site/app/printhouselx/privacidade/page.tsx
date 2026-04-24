export const metadata = {
  title: 'Política de Privacidade — Renda Automática',
  description: 'Política de privacidade do site renda-automatica.vercel.app e aplicações relacionadas.',
}

export default function Privacidade() {
  return (
    <main className="prose prose-invert mx-auto max-w-3xl px-6 py-12">
      <h1>Política de Privacidade</h1>
      <p><strong>Última atualização:</strong> 24 de abril de 2026</p>

      <h2>1. Quem somos</h2>
      <p>
        Este site (<a href="https://renda-automatica.vercel.app">renda-automatica.vercel.app</a>) e
        aplicações associadas (incluindo integrações com Pinterest, YouTube, Medium, Etsy e Printify)
        são operados por <strong>Gabriel Barreto</strong> em Portugal, sob a marca pessoal PrintHouseLX.
      </p>

      <h2>2. Que dados recolhemos</h2>
      <ul>
        <li><strong>Visitantes do site:</strong> apenas dados anónimos via Vercel Analytics (país, browser, página). Não usamos cookies de tracking.</li>
        <li><strong>Aplicações automatizadas:</strong> usam tokens de acesso fornecidos pelo próprio dono da conta (Gabriel Barreto) para publicar conteúdo nas suas próprias contas Pinterest, YouTube, Medium, etc. Não acedemos a dados de outros utilizadores dessas plataformas.</li>
        <li><strong>Não recolhemos:</strong> emails, nomes, dados de pagamento, IPs identificáveis nem dados sensíveis de terceiros.</li>
      </ul>

      <h2>3. Para que usamos os dados</h2>
      <p>
        Apenas para análise interna de tráfego (quantos leem cada artigo) e para automatizar
        publicações nas contas pessoais/profissionais do operador (Gabriel Barreto / PrintHouseLX).
      </p>

      <h2>4. Partilha com terceiros</h2>
      <p>
        Não partilhamos dados com terceiros, exceto provedores essenciais de infraestrutura
        (Vercel para hosting, OpenAI para geração de conteúdo) que processam dados ao abrigo
        dos seus próprios termos.
      </p>

      <h2>5. Os teus direitos (GDPR)</h2>
      <p>
        Tens direito a aceder, corrigir ou eliminar quaisquer dados pessoais que possamos ter sobre ti.
        Como praticamente não recolhemos dados pessoais identificáveis, este pedido raramente se aplica.
        Para qualquer questão, contacta:{' '}
        <a href="mailto:gabriel@printhouselx.com">gabriel@printhouselx.com</a>.
      </p>

      <h2>6. Cookies</h2>
      <p>
        Não usamos cookies de tracking nem publicidade. Apenas cookies técnicos essenciais ao
        funcionamento do Next.js, sem identificadores pessoais.
      </p>

      <h2>7. Alterações a esta política</h2>
      <p>
        Atualizações serão publicadas nesta página com nova data no topo. Mudanças significativas
        serão anunciadas no site.
      </p>

      <h2>8. Contacto</h2>
      <p>
        Email: <a href="mailto:gabriel@printhouselx.com">gabriel@printhouselx.com</a><br />
        Loja Etsy: <a href="https://etsy.com/shop/PrintHouseLX">PrintHouseLX</a>
      </p>
    </main>
  )
}
