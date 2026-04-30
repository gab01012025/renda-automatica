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
VIDEOS_DIRS = [
    ROOT.parent / "ai-girls-shorts" / "videos",   # novo formato AI girls (prioridade)
    ROOT.parent / "youtube-faceless" / "videos",  # voiceover original
]
SESSION_DIR = Path.home() / ".cache" / "tiktok-chrome-profile"
CHROME_BIN = "/usr/bin/google-chrome"
PUBLISHED_FILE = ROOT / "_uploaded.json"
DEBUG = "/tmp/tiktok-debug"
Path(DEBUG).mkdir(exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)

HEADLESS = True
UPLOAD_URL = "https://www.tiktok.com/tiktokstudio/upload?from=upload"
CONTENT_URL = "https://www.tiktok.com/tiktokstudio/content"

BUNDLE_PRICE = os.environ.get("BUNDLE_PRICE", "29")
BUNDLE_URL = os.environ.get("GUMROAD_BUNDLE_URL", "https://barretovibes004.gumroad.com/l/sgppj")
BUNDLE_SHORT = os.environ.get("GUMROAD_BUNDLE_SHORT", BUNDLE_URL)


def load_state():
    if PUBLISHED_FILE.exists():
        return json.loads(PUBLISHED_FILE.read_text())
    return {"videos": []}


def save_state(d):
    PUBLISHED_FILE.write_text(json.dumps(d, indent=2, ensure_ascii=False))


def safe_name(s):
    return "".join(c if c.isalnum() else "_" for c in s)[:50]


def normalize_text(text):
    return " ".join((text or "").strip().lower().split())


def significant_words(text):
    words = []
    for raw in normalize_text(text).replace("#", " ").split():
        clean = "".join(ch for ch in raw if ch.isalnum())
        if len(clean) >= 4:
            words.append(clean)
    return words


def infer_ts_from_name(file_name):
    try:
        stamp = file_name.split("-", 2)
        if len(stamp) >= 2:
            return f"{stamp[0][:4]}-{stamp[0][4:6]}-{stamp[0][6:8]} {stamp[1][:2]}:{stamp[1][2:4]}"
    except Exception:
        pass
    return time.strftime("%Y-%m-%d %H:%M")


def load_meta_for_video(file_name):
    for d in VIDEOS_DIRS:
        meta_path = d / file_name.replace(".mp4", ".json")
        if meta_path.exists():
            try:
                return json.loads(meta_path.read_text())
            except Exception:
                return {}
    return {}


def video_matches_remote(file_name, remote_posts):
    meta = load_meta_for_video(file_name)
    candidates = [
        meta.get("titulo", ""),
        file_name.replace(".mp4", "").replace("-", " "),
        meta.get("topico", ""),
    ]
    candidate_words = set()
    for candidate in candidates:
        candidate_words.update(significant_words(candidate))

    if not candidate_words:
        return False

    for post in remote_posts:
        if any(normalize_text(candidate) and normalize_text(candidate) in post for candidate in candidates):
            return True
        post_words = set(significant_words(post))
        overlap = candidate_words & post_words
        if len(overlap) >= 3:
            return True
    return False


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


async def get_remote_content_text(page):
    try:
        await page.goto(CONTENT_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        await dismiss_modals(page)
        text = ""
        try:
            text = await page.locator("body").inner_text(timeout=10000)
        except Exception:
            text = await page.text_content("body") or ""
        return text or ""
    except Exception:
        return ""


async def verify_published_in_studio(page, title):
    remote_text = normalize_text(await get_remote_content_text(page))
    if not remote_text:
        return False

    normalized_title = normalize_text(title)
    probes = []
    if normalized_title:
        probes.append(normalized_title)
        if len(normalized_title) > 24:
            probes.append(normalized_title[:24])
        words = [word for word in normalized_title.split() if len(word) >= 4]
        if len(words) >= 3:
            probes.append(" ".join(words[:3]))

    for probe in probes:
        if probe and probe in remote_text:
            return True
    return False


async def fetch_remote_posts(page):
    remote_text = await get_remote_content_text(page)
    if not remote_text:
        return []
    lines = [normalize_text(line) for line in remote_text.splitlines() if line.strip()]
    posts = []
    seen = set()
    for line in lines:
        normalized = normalize_text(line)
        if len(normalized) < 12:
            continue
        if any(token in normalized for token in ["visualizações", "curtidas", "comentários", "postar", "publicar", "rascunho", "draft"]):
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        posts.append(normalized)
    return posts


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

    # Caption: titulo + CTA comercial com URL real + tags como hashtags
    hashtags = " ".join(f"#{t.replace(' ', '').lower()}" for t in tags[:8])
    cta = (
        f"💰 Bundle PRO + bônus por €{BUNDLE_PRICE}\n"
        f"👉 {BUNDLE_SHORT}\n"
        f"(também no link da bio)"
    )
    caption = f"{titulo}\n\n{cta}\n\n{hashtags} #fyp #foryou #shorts #ai #ia #chatgpt".strip()
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

    # 5. Verifica sucesso inicial (toast ou redireciona)
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

    # 6. Confirma no painel de conteúdo antes de marcar como publicado.
    if not await verify_published_in_studio(page, titulo):
        await page.screenshot(path=f"{DEBUG}/{safe}-6-not-in-content.png", full_page=True)
        return False, "posted toast seen, but not found in studio content"

    await page.screenshot(path=f"{DEBUG}/{safe}-OK.png", full_page=True)
    return True, "ok"


async def auto_post(n=1, file_name=None):
    state = load_state()
    done = set(v["file"] for v in state["videos"])
    candidatos = []
    for d in VIDEOS_DIRS:
        candidatos.extend(p for p in d.glob("*.mp4") if p.name not in done)
    candidatos.sort()
    if not candidatos:
        print(f"✅ Sem vídeos novos em {[str(d) for d in VIDEOS_DIRS]}")
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
    todos = []
    for d in VIDEOS_DIRS:
        todos.extend(d.glob("*.mp4"))
    done = set(v["file"] for v in state["videos"])
    print(f"📺 {len(todos)} vídeos disponíveis")
    print(f"✅ {len(state['videos'])} já no TikTok")
    print(f"⏳ {len(todos) - len(done)} pendentes\n")
    for v in state["videos"][-5:]:
        print(f"  • {v['ts']}  {v['file']}")


async def sync_remote_state(prune=False):
    state = load_state()
    existing_by_file = {item["file"]: item for item in state["videos"]}
    async with async_playwright() as p:
        ctx = await launch(p, HEADLESS)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )
        remote_posts = await fetch_remote_posts(page)
        await ctx.close()

    print(f"🌐 Entradas remotas encontradas no Studio: {len(remote_posts)}")
    if not remote_posts:
        print("⚠️ Não foi possível confirmar posts remotos no TikTok Studio.")
        return

    matched_files = []
    unmatched_files = []
    all_videos = []
    for d in VIDEOS_DIRS:
        all_videos.extend(d.glob("*.mp4"))
    for video_path in sorted(all_videos):
        if video_matches_remote(video_path.name, remote_posts):
            matched_files.append(video_path.name)
        else:
            unmatched_files.append(video_path.name)

    if prune:
        rebuilt = []
        for file_name in matched_files:
            rebuilt.append({
                "file": file_name,
                "ts": existing_by_file.get(file_name, {}).get("ts", infer_ts_from_name(file_name)),
            })
        state["videos"] = rebuilt
        save_state(state)
        print(f"✅ Estado local reconstruído com {len(rebuilt)} posts confirmados no Studio")
        if unmatched_files:
            print(f"⏳ Ainda não encontrados no Studio: {len(unmatched_files)}")
            for file_name in unmatched_files:
                print(f"  - {file_name}")
    else:
        print(f"✅ Remotos compatíveis: {len(matched_files)}")
        if unmatched_files:
            print(f"⚠️ Inconsistências detectadas: {len(unmatched_files)}")
            for file_name in unmatched_files:
                print(f"  - {file_name}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--show" in args or "--debug" in args:
        HEADLESS = False
        args = [a for a in args if a not in ("--show", "--debug")]
    if "--login" in args:
        asyncio.run(do_login())
    elif "--sync" in args:
        asyncio.run(sync_remote_state(prune="--prune" in args))
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
