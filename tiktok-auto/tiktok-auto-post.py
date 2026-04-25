#!/usr/bin/env python3
"""
TikTok Auto-Uploader (Playwright + real Chrome, sem API).

Reaproveita os MP4s gerados em ../youtube-faceless/videos/.

Setup (1ª vez):
  python tiktok-auto-post.py --login   # abre Chrome visível, login manual

Uso:
  python tiktok-auto-post.py [N]       # publica N vídeos novos (default 1)
  python tiktok-auto-post.py --status
  python tiktok-auto-post.py --show    # corre não-headless (debug)
"""
import asyncio, json, sys, os, time, random
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
VIDEOS_DIR = ROOT.parent / "youtube-faceless" / "videos"
SESSION_DIR = Path.home() / ".cache" / "tiktok-chrome-profile"
CHROME_BIN = "/usr/bin/google-chrome"
PUBLISHED_FILE = ROOT / "_uploaded.json"
DEBUG = "/tmp/tiktok-debug"
Path(DEBUG).mkdir(exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)

HEADLESS = True
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=upload"

BUNDLE_PRICE = os.environ.get("BUNDLE_PRICE", "29")


def load_state():
    if PUBLISHED_FILE.exists():
        return json.loads(PUBLISHED_FILE.read_text())
    return {"videos": []}


def save_state(d):
    PUBLISHED_FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def safe_name(s):
    return "".join(c if c.isalnum() else "_" for c in s)[:50]


async def dismiss_modals(page):
    """Fecha popups/tooltips do TikTok Studio que interceptam cliques."""
    # Botões em PT/EN/ES
    labels = ["Cancelar", "Cancel", "Entendi", "Got it", "Aceitar tudo",
              "Aceitar", "Accept all", "Accept", "OK", "Recusar"]
    for _ in range(5):
        clicked = False
        for label in labels:
            try:
                btn = await page.query_selector(f'button:has-text("{label}")')
                if btn and await btn.is_visible():
                    await btn.click(timeout=2000)
                    await page.wait_for_timeout(500)
                    clicked = True
            except Exception:
                pass
        # Botão X de fecho
        try:
            for x in await page.query_selector_all('[aria-label*="lose" i], [aria-label*="echar" i], [aria-label*="errar" i]'):
                if await x.is_visible():
                    await x.click(timeout=1500)
                    await page.wait_for_timeout(400)
                    clicked = True
        except Exception:
            pass
        if not clicked:
            break


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
        await page.goto("https://www.tiktok.com/login")
        print("\n👉 Faz login no TikTok no browser que abriu.")
        print("   Depois fecha o browser para guardar a sessão.\n")
        try:
            await page.wait_for_event("close", timeout=600_000)
        except Exception:
            pass


async def upload_one(page, video_path: Path, meta: dict):
    safe = safe_name(video_path.stem)
    titulo = meta.get("titulo", video_path.stem)[:80]
    descricao = meta.get("descricao", "")
    tags = meta.get("tags", []) or []

    # Caption: titulo + CTA comercial + tags como hashtags
    hashtags = " ".join(f"#{t.replace(' ', '').lower()}" for t in tags[:8])
    cta = f"💰 Bundle PRO + bônus por €{BUNDLE_PRICE} — link na bio"
    if "barretovibes004.gumroad.com" in descricao or "/l/sgppj" in descricao:
        cta = f"💰 Oferta: Bundle PRO + bônus por €{BUNDLE_PRICE} — link na bio"
    caption = f"{titulo}\n\n{cta}\n\n{hashtags} #fyp #foryou #shorts".strip()
    caption = caption[:2150]  # limite TikTok

    await page.goto(UPLOAD_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(4000)
    await dismiss_modals(page)

    # 1. Upload do ficheiro (input[type=file] mesmo que invisível)
    file_input = None
    for sel in ['input[type="file"]', 'input[accept*="video"]']:
        try:
            file_input = await page.wait_for_selector(sel, timeout=10000, state="attached")
            if file_input:
                break
        except Exception:
            continue
    if not file_input:
        await page.screenshot(path=f"{DEBUG}/{safe}-1-no-input.png", full_page=True)
        return False, "no file input"

    await file_input.set_input_files(str(video_path))
    print("    upload em progresso...", end=" ", flush=True)

    # 2. Espera processamento (caption editor aparece)
    caption_editor = None
    for _ in range(60):  # até 60s
        await page.wait_for_timeout(1000)
        await dismiss_modals(page)
        for sel in [
            'div[contenteditable="true"][data-text]',
            'div[contenteditable="true"][role="combobox"]',
            'div[contenteditable="true"]',
        ]:
            ed = await page.query_selector(sel)
            if ed and await ed.is_visible():
                caption_editor = ed
                break
        if caption_editor:
            break

    if not caption_editor:
        await page.screenshot(path=f"{DEBUG}/{safe}-2-no-caption.png", full_page=True)
        return False, "no caption editor"

    # 3. Limpa e escreve caption
    try:
        await caption_editor.click(force=True)
        await page.wait_for_timeout(500)
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Delete")
        await page.wait_for_timeout(300)
        # Escreve caracter a caracter (TikTok usa ProseMirror, copy-paste pode falhar)
        await caption_editor.type(caption, delay=10)
        await page.wait_for_timeout(2000)
    except Exception as e:
        await page.screenshot(path=f"{DEBUG}/{safe}-3-caption-fail.png", full_page=True)
        return False, f"caption fail: {e}"

    # 4. Espera "Postar"/"Publicar"/"Post" ficar enabled
    post_btn = None
    for _ in range(60):  # até 60s para vídeo terminar de processar
        await page.wait_for_timeout(1000)
        await dismiss_modals(page)
        for sel in [
            'button[data-e2e="post_video_button"]',
            'button:has-text("Postar")',
            'button:has-text("Publicar")',
            'button:has-text("Post")',
        ]:
            btn = await page.query_selector(sel)
            if btn and await btn.is_visible():
                disabled = await btn.get_attribute("disabled")
                aria_dis = await btn.get_attribute("aria-disabled")
                if not disabled and aria_dis != "true":
                    post_btn = btn
                    break
        if post_btn:
            break

    if not post_btn:
        await page.screenshot(path=f"{DEBUG}/{safe}-4-no-post-btn.png", full_page=True)
        return False, "post button not enabled"

    await post_btn.click(force=True)
    print("postado, a verificar...", end=" ", flush=True)

    # 5. Verifica sucesso (toast ou redireciona para "Your video is being uploaded")
    success = False
    for _ in range(40):  # 40s
        await page.wait_for_timeout(1000)
        # URL muda para /tiktokstudio/content ou aparece toast
        if "/content" in page.url or "manage" in page.url:
            success = True
            break
        toast = await page.query_selector(
            'text=/postad|publicad|posted|published|enviad|uploaded|sucesso|success/i'
        )
        if toast and await toast.is_visible():
            success = True
            break

    if not success:
        await page.screenshot(path=f"{DEBUG}/{safe}-5-no-confirm.png", full_page=True)
        return False, "no confirmation"

    await page.screenshot(path=f"{DEBUG}/{safe}-OK.png", full_page=True)
    return True, "ok"


async def auto_post(n=1, file_name=None):
    state = load_state()
    done = set(v["file"] for v in state["videos"])
    candidatos = sorted([p for p in VIDEOS_DIR.glob("*.mp4") if p.name not in done])
    if not candidatos:
        print(f"✅ Sem vídeos novos em {VIDEOS_DIR}")
        return
    if file_name:
        alvo = [p for p in candidatos if p.name == file_name]
        if not alvo:
            print(f"⚠️ Vídeo não encontrado ou já publicado: {file_name}")
            return
    else:
        alvo = candidatos[:n]
    print(f"📺 {len(alvo)} vídeos a publicar no TikTok (de {len(candidatos)} pendentes)\n")

    async with async_playwright() as p:
        ctx = await launch(p, HEADLESS)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        # Anti-detect
        await page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )

        for i, v in enumerate(alvo, 1):
            meta_path = v.with_suffix(".json")
            meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
            print(f"  [{i}/{len(alvo)}]  — {meta.get('titulo', v.stem)[:50]} ...", end=" ", flush=True)
            ok, msg = await upload_one(page, v, meta)
            if ok:
                print("✓")
                state["videos"].append({
                    "file": v.name,
                    "ts": time.strftime("%Y-%m-%d %H:%M"),
                })
                save_state(state)
            else:
                print(f"⚠️ {msg}")
            if i < len(alvo):
                await page.wait_for_timeout(random.randint(20000, 40000))

        await ctx.close()
    print(f"\n✅ Concluído. Total uploads TikTok: {len(state['videos'])}")


def status():
    state = load_state()
    todos = list(VIDEOS_DIR.glob("*.mp4"))
    done = set(v["file"] for v in state["videos"])
    print(f"📺 {len(todos)} vídeos disponíveis")
    print(f"✅ {len(state['videos'])} já no TikTok")
    print(f"⏳ {len(todos) - len(done)} pendentes\n")
    for v in state["videos"][-5:]:
        print(f"  • {v['ts']}  {v['file']}")


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
        file_name = None
        n = 1
        if args and args[0].isdigit():
            n = int(args[0])
        for i, a in enumerate(args):
            if a == "--file" and i + 1 < len(args):
                file_name = args[i + 1]
        asyncio.run(auto_post(n, file_name=file_name))
