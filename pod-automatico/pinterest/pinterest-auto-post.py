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
    """Publica 1 pin via UI."""
    await page.goto("https://pinterest.com/pin-builder/", wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    # Upload imagem
    file_input = await page.query_selector('input[type="file"]')
    if not file_input:
        # tenta abrir o picker
        await page.click('text=/upload|carregar/i', timeout=5000)
        await page.wait_for_timeout(1000)
        file_input = await page.query_selector('input[type="file"]')
    if not file_input:
        raise RuntimeError("Input de upload não encontrado")
    await file_input.set_input_files(pin["image"])
    await page.wait_for_timeout(4000)

    # Title
    title_sel = 'textarea[id*="title"], input[id*="title"], textarea[placeholder*="título" i], textarea[placeholder*="title" i]'
    el = await page.query_selector(title_sel)
    if el:
        await el.fill(pin["title"][:100])

    # Description
    desc_sel = 'div[contenteditable="true"][role="textbox"], textarea[id*="description"], textarea[placeholder*="descri" i]'
    el = await page.query_selector(desc_sel)
    if el:
        try: await el.fill(pin["description"][:500])
        except: await el.type(pin["description"][:500], delay=10)

    # Link
    link_sel = 'input[id*="link"], input[placeholder*="destino" i], input[placeholder*="link" i], input[name*="link"]'
    el = await page.query_selector(link_sel)
    if el:
        await el.fill(pin["link"])

    await page.wait_for_timeout(2000)

    # Botão Publicar
    for sel in ['button:has-text("Publicar")', 'button:has-text("Publish")', 'button:has-text("Salvar")', 'button:has-text("Save")', 'button[data-test-id*="publish"]']:
        try:
            btn = await page.query_selector(sel)
            if btn:
                await btn.click()
                await page.wait_for_timeout(5000)
                return True
        except Exception:
            continue
    return False


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
            headless=True,  # corre invisível em produção/cron
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
