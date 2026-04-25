#!/usr/bin/env python3
"""
Gumroad auto-uploader (Playwright + Chrome real, sem API).
Cria os 3 produtos digitais com PDF + cover + descrição + preço.

Setup:
  python upload-gumroad.py --login    # 1ª vez: login no Gumroad
  python upload-gumroad.py            # cria produtos pendentes
  python upload-gumroad.py --status
  python upload-gumroad.py --show     # debug não-headless
"""
import asyncio, json, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
PDFS = ROOT / "pdfs"
COVERS = ROOT / "covers"
SESSION_DIR = Path.home() / ".cache" / "gumroad-chrome-profile"
CHROME_BIN = "/usr/bin/google-chrome"
PUBLISHED = ROOT / "_uploaded.json"
DEBUG = Path("/tmp/gumroad-debug")
DEBUG.mkdir(exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)
HEADLESS = True

PRODUTOS = [
    {
        "id": "prompts-chatgpt-programadores",
        "nome": "100 Prompts ChatGPT para Programadores (PT)",
        "preco": 9,
        "summary": "Pack profissional com 100 prompts otimizados em português para ChatGPT, Claude e Gemini.",
        "descricao": """🚀 100 prompts profissionais em português para ChatGPT, Claude e Gemini.

✅ Code Review & Refactoring (15 prompts)
✅ Debugging & Erros (15 prompts)
✅ Documentação Automática (10 prompts)
✅ Testes & TDD (10 prompts)
✅ Arquitetura & Design Patterns (10 prompts)
✅ SQL & Bases de Dados (10 prompts)
✅ Regex & Strings (10 prompts)
✅ DevOps & Deploy (10 prompts)
✅ Segurança & OWASP (5 prompts)
✅ Performance & Otimização (5 prompts)

📥 Acesso vitalício · PDF · 100% PT

Compatível com: ChatGPT, Claude, Gemini, Copilot, Mistral.

Para devs Portugal/Brasil que querem 10x produtividade no dia-a-dia.""",
    },
    {
        "id": "prompts-marketing-pt",
        "nome": "150 Prompts ChatGPT para Marketing em Português",
        "preco": 12,
        "summary": "150 prompts em PT para copy, ads, email marketing, SEO, redes sociais e branding.",
        "descricao": """💼 150 prompts profissionais em PT para marketers e empreendedores.

✅ Copywriting & Vendas (25 prompts)
✅ Anúncios Facebook/Instagram/Google (25 prompts)
✅ Email Marketing (20 prompts)
✅ SEO & Conteúdo Blog (20 prompts)
✅ Redes Sociais (LinkedIn, TikTok, Instagram) (20 prompts)
✅ Branding & Posicionamento (15 prompts)
✅ Pesquisa de Mercado (10 prompts)
✅ Storytelling & Narrativas (10 prompts)
✅ Funis de Conversão (5 prompts)

📥 Acesso vitalício · PDF · 100% PT

Para marketers, empreendedores e freelancers que vendem em PT/BR.""",
    },
    {
        "id": "bundle-prompts-ai-pt",
        "nome": "MEGA BUNDLE: 250 Prompts AI em Português (Devs + Marketing)",
        "preco": 19,
        "summary": "Os 2 packs num só. Programadores (100) + Marketing (150) = 250 prompts. Poupa 36%.",
        "descricao": """🔥 MEGA BUNDLE — Os 2 packs num só, com 36% desconto.

✅ 100 Prompts ChatGPT para Programadores
✅ 150 Prompts ChatGPT para Marketing em PT

= 250 prompts profissionais em português.

🎁 Bónus: receberás atualizações futuras grátis (novos prompts adicionados sempre que houver).

📥 Acesso vitalício · 1 PDF unificado · 100% PT

Em vez de €21 (€9 + €12), pagas só €19. Poupa €2 + recebe atualizações.

Para devs e marketers Portugal/Brasil.""",
    },
]


def state_load():
    return json.loads(PUBLISHED.read_text()) if PUBLISHED.exists() else {"products": []}


def state_save(d):
    PUBLISHED.write_text(json.dumps(d, indent=2, ensure_ascii=False))


async def launch(p, headless):
    return await p.chromium.launch_persistent_context(
        str(SESSION_DIR),
        headless=headless,
        executable_path=CHROME_BIN,
        channel="chrome",
        viewport={"width": 1280, "height": 900},
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )


async def do_login():
    async with async_playwright() as p:
        ctx = await launch(p, headless=False)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto("https://gumroad.com/login")
        print("\n👉 Faz login no Gumroad e fecha o browser quando dentro do dashboard.\n")
        try:
            await page.wait_for_event("close", timeout=600_000)
        except Exception:
            pass


async def fill_input(page, selectors, value, delay=20):
    for sel in selectors:
        try:
            el = await page.wait_for_selector(sel, timeout=5000, state="visible")
            if el:
                await el.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await el.type(str(value), delay=delay)
                return True
        except Exception:
            continue
    return False


async def click_first(page, selectors):
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el and await el.is_visible():
                await el.click()
                return True
        except Exception:
            continue
    return False


async def create_product(page, p):
    pdf = PDFS / f"{p['id']}.pdf"
    cover = COVERS / f"{p['id']}.png"
    if not pdf.exists():
        return False, f"PDF não encontrado: {pdf}"

    await page.goto("https://gumroad.com/products/new", wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    if "login" in page.url:
        return False, "sessão expirada (executa --login)"

    # 1. Nome do produto (wizard novo)
    name_ok = False
    try:
        name_field = page.get_by_label("Name").first
        await name_field.click()
        await name_field.fill("")
        await name_field.fill(p["nome"])
        name_ok = True
    except Exception:
        pass
    if not name_ok:
        name_ok = await fill_input(page, [
            'input[name="name"]',
            'label:has-text("Name") + input',
            'input[placeholder*="Name" i]',
            'main input[type="text"]',
        ], p["nome"])
    if not name_ok:
        # fallback final: click por coordenada no campo Name (wizard novo)
        try:
            await page.mouse.click(760, 185)
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Delete")
            await page.keyboard.type(p["nome"], delay=12)
            await page.wait_for_timeout(500)
            typed = await page.evaluate(
                """() => {
                    const i = document.querySelector('main input');
                    return i ? (i.value || '').trim() : '';
                }"""
            )
            name_ok = len(typed) > 0
        except Exception:
            pass
    if not name_ok:
        # fallback por índice: primeiro input do main é o Name
        try:
            fields = await page.query_selector_all("main input[type='text']")
            if fields:
                await fields[0].click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await fields[0].type(p["nome"], delay=12)
                name_ok = True
        except Exception:
            pass
    if not name_ok:
        await page.screenshot(path=str(DEBUG / f"{p['id']}-1-no-name.png"), full_page=True)
        return False, "campo nome não encontrado"

    # 1b. Novo wizard do Gumroad: escolher tipo do produto e avançar
    type_ok = await click_first(page, [
        'text="Digital product"',
        'text="E-book"',
    ])
    if not type_ok:
        await page.screenshot(path=str(DEBUG / f"{p['id']}-1-no-type.png"), full_page=True)
        return False, "tipo de produto não encontrado"

    next_ok = await click_first(page, [
        'button:has-text("Next")',
        'button:has-text("Next: Customize")',
        'button:has-text("Continue")',
    ])
    if not next_ok:
        await page.screenshot(path=str(DEBUG / f"{p['id']}-1-no-next.png"), full_page=True)
        return False, "botão Next não encontrado"
    await page.wait_for_timeout(5000)

    # 2. Preço
    if not await fill_input(page, [
        'input[name="price"]',
        'label:has-text("Price") + input',
        'input[placeholder*="rice" i]',
        'input[type="number"]',
    ], p["preco"]):
        # fallback por índice: em alguns layouts o 2º input text é preço
        try:
            text_inputs = await page.query_selector_all("main input[type='text']")
            if len(text_inputs) >= 2:
                await text_inputs[1].click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await text_inputs[1].type(str(p["preco"]), delay=12)
            else:
                print("   ⚠️ preço não encontrado,", end=" ", flush=True)
        except Exception:
            print("   ⚠️ preço não encontrado,", end=" ", flush=True)

    await page.wait_for_timeout(1000)

    # 3. Submit "Next"/"Create"
    await click_first(page, [
        'button:has-text("Next")',
        'button:has-text("Create")',
        'button:has-text("Continue")',
        'button[type="submit"]',
    ])
    await page.wait_for_timeout(5000)

    # 4. Já no editor — upload PDF
    file_inputs = await page.query_selector_all('input[type="file"]')
    uploaded_pdf = False
    for fi in file_inputs:
        try:
            accept = (await fi.get_attribute("accept") or "").lower()
            if "pdf" in accept or accept == "":
                await fi.set_input_files(str(pdf))
                print("   uploaded pdf,", end=" ", flush=True)
                uploaded_pdf = True
                break
        except Exception:
            continue
    if not uploaded_pdf:
        # fallback: primeiro input file visível
        for fi in file_inputs:
            try:
                if await fi.is_visible():
                    await fi.set_input_files(str(pdf))
                    print("   uploaded pdf,", end=" ", flush=True)
                    uploaded_pdf = True
                    break
            except Exception:
                continue
    if not uploaded_pdf:
        print("   ⚠️ pdf input não encontrado,", end=" ", flush=True)

    await page.wait_for_timeout(8000)  # espera processamento

    # 5. Cover (segundo input file ou drag area)
    file_inputs = await page.query_selector_all('input[type="file"]')
    for fi in file_inputs:
        try:
            accept = (await fi.get_attribute("accept") or "").lower()
            if "image" in accept or "png" in accept or "jpg" in accept:
                await fi.set_input_files(str(cover))
                print("cover,", end=" ", flush=True)
                break
        except Exception:
            continue

    await page.wait_for_timeout(5000)

    # 6. Descrição (rich text editor)
    for sel in [
        'div[contenteditable="true"]',
        '[role="textbox"]',
    ]:
        ed = await page.query_selector(sel)
        if ed and await ed.is_visible():
            try:
                await ed.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.press("Delete")
                await ed.type(p["descricao"], delay=2)
                print("desc,", end=" ", flush=True)
                break
            except Exception:
                continue

    await page.wait_for_timeout(2000)

    # 7. Save (rascunho)
    saved = False
    for sel in [
        'button:has-text("Save")',
        'button:has-text("Save and continue")',
        'button[aria-label*="ave" i]',
    ]:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                saved = True
                break
        except Exception:
            continue

    await page.wait_for_timeout(5000)
    await page.screenshot(path=str(DEBUG / f"{p['id']}-OK.png"), full_page=True)

    # 8. Publish (segundo botão depois de save)
    for sel in [
        'button:has-text("Publish")',
        'button:has-text("Publicar")',
    ]:
        try:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                await btn.click()
                print("PUBLISHED!", end=" ", flush=True)
                await page.wait_for_timeout(3000)
                break
        except Exception:
            continue

    url = page.url
    if "/products/new" in url:
        return False, "produto não criado (permaneceu em /products/new)"
    return True, url


async def main():
    state = state_load()
    done = set(p["id"] for p in state["products"])
    pendentes = [p for p in PRODUTOS if p["id"] not in done]
    if not pendentes:
        print("✅ Todos os produtos já estão no Gumroad")
        return
    print(f"📦 A criar {len(pendentes)} produtos no Gumroad\n")

    async with async_playwright() as p:
        ctx = await launch(p, HEADLESS)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )

        for i, prod in enumerate(pendentes, 1):
            print(f"  [{i}/{len(pendentes)}] {prod['nome'][:60]}...", end=" ", flush=True)
            try:
                ok, info = await create_product(page, prod)
            except Exception as e:
                ok, info = False, str(e)
            if ok:
                print(f"\n   ✅ {info}")
                state["products"].append({
                    "id": prod["id"],
                    "nome": prod["nome"],
                    "preco": prod["preco"],
                    "url": info,
                    "ts": time.strftime("%Y-%m-%d %H:%M"),
                })
                state_save(state)
            else:
                print(f"\n   ⚠️ {info} (ver {DEBUG})")
            await page.wait_for_timeout(5000)

        await ctx.close()
    print(f"\n✅ Total no Gumroad: {len(state['products'])}")


def status():
    s = state_load()
    print(f"📦 {len(s['products'])} produtos no Gumroad")
    for p in s["products"]:
        print(f"  • €{p['preco']:>3}  {p['nome']}")
        print(f"          {p['url']}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--show" in args or "--debug" in args:
        HEADLESS = False
        args = [a for a in args if a not in ("--show", "--debug")]
    if "--login" in args:
        asyncio.run(do_login())
    elif "--status" in args:
        status()
    else:
        asyncio.run(main())
