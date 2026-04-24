#!/usr/bin/env python3
"""
Pinterest Auto-Poster (sem API, usa browser automation)

Workflow:
1. Primeira vez: corres `--login` → abre Chrome, fazes login manual no Pinterest 1 vez
   → sessão fica guardada em ~/.cache/pinterest-session/
2. Daí em diante: cron corre `gerar-pins.py` (que cria os PNGs + CSV) +
   `pinterest-auto-post.py [N]` (publica N pins novos sem teu input)

Uso:
    python pinterest-auto-post.py --login          # 1ª vez, abre browser para login
    python pinterest-auto-post.py 3                # publica 3 pins novos
    python pinterest-auto-post.py --status         # mostra quais já foram publicados
"""
import asyncio, csv, json, sys, os, random
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
PINS_DIR = ROOT / "pins-prontos"
CSV_PATH = ROOT / "pins-pinterest-upload.csv"
# Usa cópia do perfil REAL do Chrome (evita deteção do Google como "browser inseguro")
SESSION_DIR = Path.home() / ".cache" / "pinterest-chrome-profile"
REAL_CHROME_PROFILE = Path.home() / ".config" / "google-chrome"
CHROME_BIN = "/usr/bin/google-chrome"
PUBLISHED_FILE = ROOT / "_published-pins.json"

SESSION_DIR.mkdir(parents=True, exist_ok=True)
HEADLESS = True  # overridden by --debug/--show flag


def load_published():
    if PUBLISHED_FILE.exists():
        return json.loads(PUBLISHED_FILE.read_text())
    return {"pins": []}


def save_published(data):
    PUBLISHED_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_pins_from_csv():
    pins = []
    if not CSV_PATH.exists():
        return pins
    with open(CSV_PATH, encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            # CSV tem: Title, Description, Link, Image, Board, Keywords (varia por gerador)
            img_field = row.get("Local file") or row.get("Image") or row.get("imagem") or row.get("file") or ""
            img_path = PINS_DIR / Path(img_field).name if img_field else None
            if not img_path or not img_path.exists():
                continue
            pins.append({
                "title": row.get("Title") or row.get("titulo") or "",
                "description": row.get("Description") or row.get("descricao") or "",
                "link": row.get("Link") or row.get("link") or "https://etsy.com/shop/PrintHouseLX",
                "image": str(img_path),
                "board": row.get("Pinterest board") or row.get("Board") or row.get("board") or "",
                "keywords": row.get("Keywords") or row.get("tags") or "",
            })
    return pins


async def do_login():
    """Abre Chrome real (não o Chromium do Playwright) com perfil dedicado.
    Google não deteta como 'browser inseguro' porque é o Chrome verdadeiro.
    """
    print("🔐 A abrir Google Chrome — faz login no Pinterest (podes usar 'Continuar com Google').")
    print(f"   Perfil dedicado: {SESSION_DIR}")
    print("   Quando terminares, fecha a janela do Chrome.\n")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(SESSION_DIR),
            headless=False,
            executable_path=CHROME_BIN,        # usa CHROME real, não chromium do playwright
            channel="chrome",
            viewport={"width": 1280, "height": 800},
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-default-browser-check",
            ],
            ignore_default_args=["--enable-automation"],  # esconde flag de automação
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        # Anti-detection: remove navigator.webdriver
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        await page.goto("https://pinterest.com/login")
        print("👉 Faz login na janela. Depois fecha o Chrome.\n")
        try:
            while True:
                await asyncio.sleep(2)
                if not ctx.pages:
                    break
        except Exception:
            pass
        await ctx.close()
    print("✅ Sessão guardada. Próximas execuções correm sem login manual.")


async def post_pin(page, pin):
    """Publica 1 pin via UI. Retorna True só se URL mudar para /pin/<id>/."""
    DEBUG = "/tmp/pinterest-debug"
    os.makedirs(DEBUG, exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in pin["title"][:30])

    await page.goto("https://pt.pinterest.com/pin-creation-tool/", wait_until="domcontentloaded")
    await page.wait_for_timeout(6000)

    # ---- 1. Upload imagem ----
    file_input = await page.query_selector('input[type="file"]')
    if not file_input:
        await page.screenshot(path=f"{DEBUG}/{safe}-1-no-input.png", full_page=True)
        raise RuntimeError(f"Input upload não encontrado ({DEBUG}/{safe}-1-no-input.png)")
    await file_input.set_input_files(pin["image"])
    # Aguardar imagem aparecer (preview)
    try:
        await page.wait_for_selector('img[src*="blob:"], img[alt*="pin" i], canvas', timeout=15000)
    except Exception:
        pass
    await page.wait_for_timeout(4000)

    # ---- 2. Título ----
    for sel in [
        '#storyboard-selector-title',
        'textarea[id*="title" i]',
        'input[id*="title" i]',
        'textarea[placeholder*="título" i]',
        'textarea[placeholder*="title" i]',
    ]:
        el = await page.query_selector(sel)
        if el:
            try:
                await el.click()
                await el.fill(pin["title"][:100])
                break
            except Exception:
                continue

    # ---- 3. Descrição (contenteditable Draft.js) ----
    desc_text = (pin["description"] or "")[:500]
    if desc_text:
        for sel in [
            'div[data-test-id="pin-draft-description"] div[contenteditable="true"]',
            'div[aria-label*="descri" i][contenteditable="true"]',
            'div[contenteditable="true"][role="textbox"]',
            'div[contenteditable="true"][data-text="true"]',
            'div[contenteditable="true"]',
        ]:
            el = await page.query_selector(sel)
            if el:
                try:
                    await el.click()
                    await page.keyboard.type(desc_text, delay=5)
                    break
                except Exception:
                    continue

    # ---- 4. Link destino ----
    for sel in [
        'input[id*="link" i]',
        'input[placeholder*="destino" i]',
        'input[placeholder*="link" i]',
        'input[name*="link"]',
    ]:
        el = await page.query_selector(sel)
        if el:
            try:
                await el.click()
                await el.fill(pin["link"])
                break
            except Exception:
                continue

    await page.wait_for_timeout(2000)

    # ---- 5. Selecionar Board (OBRIGATÓRIO) ----
    # Pinterest PT chama "Pasta", não "board". PrintHouseLX é nome da CONTA, não pasta.
    # Usar pasta existente. Override via env var PINTEREST_BOARD se quiser outra.
    board_name = os.environ.get("PINTEREST_BOARD", "Mundial Portugal 2026")
    board_picked = False

    # Espera dropdown de PASTA aparecer (label "Pasta" no formulário)
    dropdown_btn = None
    for sel in [
        '[data-test-id="board-dropdown-select-button"]',
        'button[data-test-id*="board-dropdown"]',
        'div:has(> label:has-text("Pasta")) button',
        'button:has-text("Escolha uma pasta")',
        'button:has-text("Choose a board")',
    ]:
        try:
            dropdown_btn = await page.wait_for_selector(sel, timeout=8000, state="visible")
            if dropdown_btn:
                break
        except Exception:
            continue

    if not dropdown_btn:
        await page.screenshot(path=f"{DEBUG}/{safe}-2-no-dropdown.png", full_page=True)
        return False

    try:
        await dropdown_btn.scroll_into_view_if_needed()
        await dropdown_btn.click(force=True)
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{DEBUG}/{safe}-2c-dropdown-open.png", full_page=True)
    except Exception as e:
        await page.screenshot(path=f"{DEBUG}/{safe}-2b-dropdown-click-fail.png", full_page=True)
        return False

    # Procurar pasta (scope no popup do dropdown — evita clicar no menu de conta)
    try:
        search = await page.wait_for_selector(
            'input[placeholder*="esquis" i], input[placeholder*="quadro" i], input[placeholder*="board" i], input[placeholder*="asta" i]',
            timeout=4000, state="visible"
        )
        if search:
            await search.fill(board_name)
            await page.wait_for_timeout(2000)
    except Exception:
        pass

    # Clica no resultado da pesquisa: priorizar elementos com IMG (boards reais têm thumbnail)
    # e perto do input de pesquisa (mesmo container)
    try:
        # Itens dentro do popup do dropdown — usa role=button com img como filho
        candidates = await page.query_selector_all('div[role="button"]:has(img)')
        for el in candidates:
            if not await el.is_visible():
                continue
            txt = (await el.text_content() or "").strip()
            if not txt or len(txt) > 80:
                continue
            # Match exato ou contém o nome
            if board_name.lower() in txt.lower():
                await el.click(force=True)
                await page.wait_for_timeout(2500)
                board_picked = True
                print(f"    ✓ pasta: {txt[:40]}")
                break
    except Exception:
        pass

    # Fallback: primeiro board real (com img) que não seja o switcher de conta
    if not board_picked:
        try:
            candidates = await page.query_selector_all('div[role="button"]:has(img)')
            for el in candidates:
                if not await el.is_visible():
                    continue
                txt = (await el.text_content() or "").strip()
                if not txt or len(txt) > 80:
                    continue
                # Skip nome da conta (PrintHouseLX)
                if "PrintHouseLX" in txt and "Pasta" not in txt:
                    continue
                # Skip headers
                if txt.lower().startswith(("todas", "all", "empresas", "ativos")):
                    continue
                await el.click(force=True)
                await page.wait_for_timeout(2500)
                board_picked = True
                print(f"    ⚠️ fallback pasta: {txt[:40]}")
                break
        except Exception:
            pass

    if not board_picked:
        await page.screenshot(path=f"{DEBUG}/{safe}-3-no-board-pick.png", full_page=True)
        return False

    await page.wait_for_timeout(2000)
    await page.screenshot(path=f"{DEBUG}/{safe}-3b-after-board.png", full_page=True)

    # ---- 6. Botão Publicar ----
    pre_url = page.url
    clicked = False
    for sel in [
        '[data-test-id="board-dropdown-save-button"]',
        '[data-test-id="storyboard-creation-nav-done"]',
        'button[data-test-id*="publish"]',
        'button[data-test-id*="save"]:not([data-test-id*="board"])',
        'button:has-text("Publicar")',
        'button:has-text("Publish")',
        'div[role="button"]:has-text("Publicar")',
    ]:
        el = await page.query_selector(sel)
        if el and await el.is_visible():
            try:
                await el.click()
                clicked = True
                break
            except Exception:
                continue

    if not clicked:
        await page.screenshot(path=f"{DEBUG}/{safe}-4-no-publish-btn.png", full_page=True)
        return False

    # ---- 7. VERIFICAR sucesso real (URL muda para /pin/<id> ou aparece toast de sucesso) ----
    success = False
    for _ in range(20):  # até 20s
        await page.wait_for_timeout(1000)
        if "/pin/" in page.url and page.url != pre_url:
            success = True
            break
        # toast de sucesso
        toast = await page.query_selector('text=/publicad|published|salvo|saved|criad|created/i')
        if toast:
            success = True
            break

    if not success:
        await page.screenshot(path=f"{DEBUG}/{safe}-5-no-confirm.png", full_page=True)
    else:
        await page.screenshot(path=f"{DEBUG}/{safe}-OK.png", full_page=True)
    return success


async def auto_post(n=3):
    pins = load_pins_from_csv()
    if not pins:
        print(f"❌ Sem pins no CSV ({CSV_PATH})")
        return
    state = load_published()
    pubs = set(p["image"] for p in state["pins"])
    pendentes = [p for p in pins if p["image"] not in pubs]
    if not pendentes:
        print("✅ Todos os pins do CSV já foram publicados.")
        return
    alvo = pendentes[:n]
    print(f"📌 {len(alvo)} pins novos a publicar (de {len(pendentes)} pendentes)\n")

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(SESSION_DIR),
            headless=HEADLESS,
            executable_path=CHROME_BIN,
            channel="chrome",
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # Verificar login
        await page.goto("https://pinterest.com")
        await page.wait_for_timeout(3000)
        if "/login" in page.url:
            print("❌ Sessão expirada. Corre: python pinterest-auto-post.py --login")
            await ctx.close()
            return

        for i, pin in enumerate(alvo, 1):
            print(f"  [{i}/{len(alvo)}] {pin['title'][:50]}", end=" ... ", flush=True)
            try:
                ok = await post_pin(page, pin)
                if ok:
                    state["pins"].append({"image": pin["image"], "title": pin["title"]})
                    save_published(state)
                    print("✓")
                    # delay aleatório entre pins (evitar rate-limit/anti-bot)
                    await asyncio.sleep(random.randint(20, 45))
                else:
                    print("⚠️ botão publicar não encontrado")
            except Exception as e:
                print(f"❌ {str(e)[:80]}")
                await asyncio.sleep(10)

        await ctx.close()
    print(f"\n✅ Concluído. Total publicados: {len(state['pins'])}")


def status():
    state = load_published()
    pins = load_pins_from_csv()
    pubs = set(p["image"] for p in state["pins"])
    print(f"📊 CSV: {len(pins)} pins | Publicados: {len(state['pins'])} | Pendentes: {len([p for p in pins if p['image'] not in pubs])}")
    if state["pins"]:
        print("\nÚltimos 5 publicados:")
        for p in state["pins"][-5:]:
            print(f"  ✓ {p['title'][:60]}")


def main():
    global HEADLESS
    HEADLESS = "--debug" not in sys.argv and "--show" not in sys.argv
    if "--login" in sys.argv:
        asyncio.run(do_login())
    elif "--status" in sys.argv:
        status()
    else:
        n = 3
        for a in sys.argv[1:]:
            if a.isdigit(): n = int(a)
        asyncio.run(auto_post(n))


if __name__ == "__main__":
    main()
