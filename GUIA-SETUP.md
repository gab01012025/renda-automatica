# 🚦 Guia de Setup — do zero ao ar (passo-a-passo)

Siga exatamente esta ordem. Tempo total estimado: **4-6 horas** no primeiro dia.

---

## 📋 Checklist de contas a criar (faça TUDO primeiro, depois instale)

- [ ] **GitHub** — https://github.com/join (grátis)
- [ ] **Vercel** — https://vercel.com/signup (grátis, use login do GitHub)
- [ ] **OpenAI Platform** — https://platform.openai.com/signup + adicionar **€30 de crédito** em Billing
- [ ] **Printify** — https://printify.com/app/register (grátis)
- [ ] **Etsy Seller** — https://www.etsy.com/sell (taxa $15 para abrir — procure no Google "Etsy 40 free listings referral" para conseguir link com isenção)
- [ ] **Cloudflare** — https://dash.cloudflare.com/sign-up (grátis, vai usar para comprar o domínio)
- [ ] **Programas de afiliados** (aprovação pode demorar 1-7 dias — submeta JÁ):
  - [ ] Hostinger Afiliados — https://www.hostinger.com/afiliados
  - [ ] Amazon Afiliados PT — https://afiliados.amazon.es
  - [ ] Awin — https://www.awin.com/pt

---

## 🖥️ Passo 1 — Preparar o computador (15 min)

Instalar Node.js 20+ se ainda não tiver:
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install -y nodejs npm
# ou via nvm (recomendado)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# Verificar
node --version   # deve mostrar v20.x.x
```

Abrir um terminal na pasta do projeto:
```bash
cd "/home/gabifran/novo test2"
```

---

## 🔵 Passo 2 — Motor A: Site de afiliados (1h30)

### 2.1 Instalar dependências
```bash
cd afiliados-ia/site
npm install
cd ..
```

### 2.2 Criar .env com sua OpenAI key
```bash
cp .env.example .env
# Abra .env e cole a chave real da OpenAI
```
Como obter a key: https://platform.openai.com/api-keys → Create → copia a string `sk-proj-...`

### 2.3 Gerar os primeiros artigos (teste local)
```bash
cd "/home/gabifran/novo test2/afiliados-ia"
node gerador/gerar-artigo.mjs
# Se der certo, gera um .mdx em site/content/artigos/
```

### 2.4 Ver o site localmente
```bash
cd site
npm run dev
# Abrir http://localhost:3000 no browser
```
Confirme que aparece o artigo que gerou. Ctrl+C para parar.

### 2.5 Comprar domínio (~€10)
Opções (escolher UMA):
- **Cloudflare Registrar** (mais barato): https://dash.cloudflare.com → Domain Registration → Register Domains
- **Dominios.pt** (local, suporte PT): https://www.dominios.pt

Sugestões de domínio (tente por ordem):
1. `ia-em-portugues.pt`
2. `iaportuguesa.com`
3. `ferramentasia.pt`
4. `melhoria.pt` (curto, memorável)

### 2.6 Subir para GitHub
```bash
cd "/home/gabifran/novo test2"
git init
git add .
git commit -m "inicio: sistema renda automatizada"

# Criar repo em https://github.com/new (chame-lhe "renda-automatica", PRIVADO)
git remote add origin https://github.com/SEU_USER/renda-automatica.git
git branch -M main
git push -u origin main
```

### 2.7 Deploy no Vercel
1. Abrir https://vercel.com/new
2. Importar repo `renda-automatica`
3. **Root Directory:** clique em "Edit" e selecione `afiliados-ia/site`
4. **Environment Variables** — adicionar:
   - `OPENAI_API_KEY` = sua chave (não obrigatório para rodar mas útil para builds com dados)
5. Clicar **Deploy**

Em 2 minutos: `https://renda-automatica-xxxxx.vercel.app` já online.

### 2.8 Apontar domínio para Vercel
No Vercel → Project → Settings → Domains → adicionar seu domínio.
Siga as instruções de DNS (adicionar registo A ou CNAME no Cloudflare). Fica ativo em 5-60 min.

### 2.9 Ativar publicação automática semanal
No GitHub → seu repo → Settings → **Secrets and variables** → **Actions** → New repository secret:
- `OPENAI_API_KEY` = sua chave OpenAI
- (depois que aprovarem afiliados: `AFILIADO_HOSTINGER`, etc.)

Depois vá em **Actions** → ligar workflows → selecione "Publicar artigo semanal" → **Run workflow** para testar já.

✅ Motor A pronto. Toda segunda-feira 9h UTC publica 1 artigo novo sozinho.

---

## 🟢 Passo 3 — Motor B: POD automatizado (1h30)

### 3.1 Preparar Printify + Etsy
1. Abrir conta Etsy, completar loja (nome, logo simples, política de devolução)
2. No Printify: Stores → Add New Store → **Etsy** → autorizar
3. Printify → My account → Connections → **API** → Generate token → copiar
4. Descobrir Shop ID: Printify → Stores → clicar na loja → URL tem `/store/12345678/`, esse número é o shop ID

### 3.2 Setup local
```bash
cd "/home/gabifran/novo test2/pod-automatico"
npm install
cp .env.example .env
# Abra .env e preencha:
#   OPENAI_API_KEY
#   PRINTIFY_API_KEY
#   PRINTIFY_SHOP_ID
```

### 3.3 Primeiro teste (5 designs)
```bash
node pipeline.mjs frases-motivacionais-pt 5
```
Vai:
1. Gerar 5 ideias com GPT-4
2. Criar 5 PNGs com DALL-E 3
3. Fazer upload para Printify
4. Publicar na sua loja Etsy

**Custo esperado: ~$0.80 (≈€0,75)**

### 3.4 Validar no Etsy
- Abra a sua loja Etsy
- Verifique se os 5 produtos apareceram (podem demorar 5-15 min a sincronizar)
- **Revise títulos, descrições e imagens manualmente** — DALL-E às vezes escreve texto errado

### 3.5 Comprar um para você (crucial)
Compre 1 camisa sua mesmo (use cupão Etsy se tiver). Quando chegar, avalie:
- Qualidade impressão
- Cor do tecido
- Tempo de entrega

Se estiver mau → trocar de Print Provider no Printify antes de escalar.

### 3.6 Escalar (a partir da semana 2)
Gerar 20 designs por dia, alternando nichos:
```bash
# Segunda
node pipeline.mjs frases-motivacionais-pt 20

# Terça
node pipeline.mjs cafe-lisboa 20

# Quarta
node pipeline.mjs pets-engracados 20

# ...
```

Cada sessão de 20 designs = ~$3 em APIs + 30-40 min do seu tempo (maior parte é o GPT/DALL-E a processar).

---

## 🎯 Passo 4 — Hábitos semanais (2-4h/semana)

### Toda segunda-feira (1h)
- [ ] Ver quantas vendas Etsy no fim de semana
- [ ] Ver tráfego do site afiliados (Vercel Analytics ou adicionar Plausible/PostHog grátis)
- [ ] Aprovar artigo gerado automaticamente (ver se ficou bom, não precisa editar)

### Toda quarta-feira (1h)
- [ ] Gerar 30-50 novos designs POD
- [ ] Responder mensagens Etsy (raras, mas existem)

### Todo sábado (1-2h)
- [ ] Adicionar 3-5 novos temas ao `gerador/temas.json`
- [ ] Se tiver afiliado aprovado: atualizar IDs no `.env` e nos Secrets GitHub
- [ ] Postar resposta útil em 1-2 tópicos Reddit/Quora linkando para um artigo (tráfego!)

---

## 💳 Resumo dos custos reais (primeiros 3 meses)

| Item | Mês 1 | Mês 2 | Mês 3 |
|---|---|---|---|
| Domínio | €10 | €0 | €0 |
| OpenAI API (afiliados) | €5 | €8 | €10 |
| OpenAI API (POD, ~150 designs/mês) | €12 | €15 | €15 |
| Etsy listings | €4 | €2 | €2 |
| Printify | €0 | €0 | €0 |
| Vercel / GitHub / Cloudflare | €0 | €0 | €0 |
| **Total mês** | **€31** | **€25** | **€27** |

Com €200 aguenta ~6-7 meses de operação. Tempo mais que suficiente para começar a vender.

---

## ❓ FAQ

**"E se eu não gostar dos artigos gerados?"**
Edite `gerador/gerar-artigo.mjs` na constante `prompt` e refine as instruções. Pode regerar um artigo específico.

**"Como faço se o DALL-E gerar texto errado na imagem?"**
Acontece. Apague esse PNG+JSON em `designs/<nicho>/` e rode de novo para gerar substituição.

**"Vou pagar impostos em Portugal sobre isto?"**
Sim. Se gerar >€1000/ano precisa abrir atividade (recibo verde). Até lá pode declarar em anexo B do IRS. Consulte um contabilista com os primeiros €500 ganhos.

**"Posso rodar tudo numa Raspberry Pi / servidor sempre ligado?"**
Não precisa. Geração corre em segundos quando você manda. Cron do afiliados roda no GitHub (grátis, servidor deles).

**"E se a OpenAI mudar preços ou bloquear conta?"**
Scripts funcionam com qualquer API compatível OpenAI (Anthropic Claude tem wrapper, Groq, Together.ai). Alteração é trocar URL e modelo. Mas por enquanto OpenAI é o mais confiável.

---

## 🆘 Se travar em algum passo

1. Leia o erro com atenção — 90% das vezes é variável de ambiente faltando ou API key errada
2. Rode com `DEBUG=1 node ...` para mais logs
3. Volte aqui e diga EXATAMENTE em que passo travou e qual a mensagem de erro — eu ajudo a desbloquear
