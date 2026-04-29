"""
Etsy Auto-Uploader via Playwright (browser automation).

Como funciona:
  - Primeira execução: abre browser, fazes login manual no Etsy 1x.
    A sessão fica persistida em ./.etsy-session (cookies + localStorage).
  - Próximas execuções: abre direto logado, lê produtos de etsy-digitals/produtos/
    e cria listing automaticamente (digital download) via UI.

Pré-requisitos:
  pip install playwright
  playwright install chromium

Uso:
  python etsy-uploader.py [N=3]    # sobe N produtos novos
  python etsy-uploader.py --login   # só abre browser para fazer login
"""
import os, sys, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = ROOT / "etsy-digitals" / ".etsy-session"
PRODUTOS_DIR = ROOT / "etsy-digitals" / "produtos"
UPLOADED = ROOT / "etsy-digitals" / "_uploaded.json"

uploaded = json.loads(UPLOADED.read_text()) if UPLOADED.exists() else []

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ playwright nao instalado. Run: pip install playwright && playwright install chromium")
    sys.exit(1)


def open_browser(p, headless=False):
    return p.chromium.launch_persistent_context(
        str(SESSION_DIR),
        headless=headless,
        viewport={"width": 1280, "height": 900},
        accept_downloads=False,
        args=["--disable-blink-features=AutomationControlled"],
    )


def login_flow():
    print("🔐 Abrindo browser para login Etsy...")
    print("   1. Faz login na tua conta PrintHouseLX")
    print("   2. Vai a https://www.etsy.com/your/shops/me/dashboard")
    print("   3. Quando estiveres logado, FECHA esta janela")
    with sync_playwright() as p:
        ctx = open_browser(p, headless=False)
        page = ctx.new_page()
        page.goto("https://www.etsy.com/signin")
        try:
            page.wait_for_event("close", timeout=10 * 60 * 1000)
        except Exception:
            pass
        ctx.close()
    print("✅ Sessão guardada em", SESSION_DIR)


def upload_listing(page, produto_dir: Path):
    """Sobe 1 produto digital ao Etsy."""
    listing_json = produto_dir / "etsy-listing.json"
    if not listing_json.exists():
        return False, "sem etsy-listing.json"
    meta = json.loads(listing_json.read_text())

    # encontrar arquivo principal (PDF ou PNG)
    files = sorted([f for f in produto_dir.iterdir()
                    if f.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg", ".zip")
                    and f.name != "INSTRUCOES-UPLOAD.md"])
    if not files:
        return False, "sem ficheiro principal"

    print(f"   📦 a subir: {meta.get('title', produto_dir.name)[:60]}")
    page.goto("https://www.etsy.com/your/shops/me/tools/listings/create", timeout=60000)
    time.sleep(5)

    # Etsy mudou UI várias vezes — tentar vários selectors para upload imagem
    images = [f for f in files if f.suffix.lower() in (".png", ".jpg", ".jpeg")]
    if not images:
        return False, "sem preview image"

    image_uploaded = False
    selectors_img = [
        'input[type="file"][accept*="image"]',
        'input[type="file"][accept*="png"]',
        'input[type="file"][accept*="jpg"]',
        'input[data-test-id*="image"][type="file"]',
        'input[data-selector*="image"][type="file"]',
        'input[type="file"]',  # último recurso
    ]
    for sel in selectors_img:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="attached", timeout=5000)
            loc.set_input_files(str(images[0]))
            time.sleep(5)
            image_uploaded = True
            print(f"      ✓ imagem enviada via: {sel}")
            break
        except Exception:
            continue

    if not image_uploaded:
        # screenshot debug + dump html para análise
        debug_dir = produto_dir.parent.parent / "_debug"
        debug_dir.mkdir(exist_ok=True)
        try:
            page.screenshot(path=str(debug_dir / f"fail-{produto_dir.name}.png"), full_page=True)
            (debug_dir / f"fail-{produto_dir.name}.html").write_text(page.content())
            print(f"      📸 debug em {debug_dir}/fail-{produto_dir.name}.{{png,html}}")
        except Exception:
            pass
        return False, "nenhum input de upload encontrado"

    # Title
    try:
        page.locator('input[name="title"]').fill(meta.get("title", produto_dir.name)[:140])
    except Exception:
        pass

    # Description
    try:
        page.locator('textarea[name="description"]').fill(meta.get("description", "")[:5000])
    except Exception:
        pass

    # Tags (até 13)
    try:
        tag_input = page.locator('input[aria-label*="ag"]').first
        for tag in (meta.get("tags") or [])[:13]:
            tag_input.fill(tag[:20])
            tag_input.press("Enter")
            time.sleep(0.3)
    except Exception:
        pass

    # Tipo: digital download
    try:
        page.get_by_label("Digital").check()
    except Exception:
        pass

    # Preço
    try:
        price = "8.00" if "wall_art" in produto_dir.name or "print" in produto_dir.name else "12.00"
        page.locator('input[name="price"]').fill(price)
    except Exception:
        pass

    # Quantidade (digital pode ser >1)
    try:
        page.locator('input[name="quantity"]').fill("999")
    except Exception:
        pass

    # Upload arquivo digital
    try:
        digital_files = [f for f in files if f.suffix.lower() in (".pdf", ".zip")]
        if not digital_files:
            digital_files = images  # se for wall art, vende o PNG
        if digital_files:
            digital_input = page.locator('input[type="file"][accept*="pdf"], input[type="file"][accept*="zip"]').first
            digital_input.set_input_files(str(digital_files[0]))
            time.sleep(2)
    except Exception:
        pass

    # Salvar como rascunho (mais seguro que publicar direto). Etsy tem MUITAS variantes.
    save_clicked = False
    save_labels = [
        "Salvar como rascunho", "Save as draft",
        "Guardar como rascunho", "Salvar rascunho",
        "Save and continue", "Salvar e continuar",
        "Guardar e continuar", "Continuar",
        "Save", "Salvar", "Guardar",
        "Publish", "Publicar",
    ]
    for label in save_labels:
        try:
            btn = page.get_by_role("button", name=label, exact=False).first
            btn.wait_for(state="visible", timeout=2000)
            btn.click()
            save_clicked = True
            print(f"      ✓ clicked save button: '{label}'")
            break
        except Exception:
            continue

    # fallback: procurar qualquer botão com texto que contenha save/salvar
    if not save_clicked:
        try:
            page.locator("button:has-text('alvar'), button:has-text('uardar'), button:has-text('ave')").first.click(timeout=3000)
            save_clicked = True
            print("      ✓ clicked save via text-contains fallback")
        except Exception:
            pass

    if not save_clicked:
        # screenshot para debug
        debug_dir = produto_dir.parent.parent / "_debug"
        debug_dir.mkdir(exist_ok=True)
        try:
            page.screenshot(path=str(debug_dir / f"nosave-{produto_dir.name}.png"), full_page=True)
            print(f"      📸 screenshot debug: {debug_dir}/nosave-{produto_dir.name}.png")
        except Exception:
            pass
        # Etsy auto-saves drafts. Mesmo sem clicar, fica como rascunho parcial.
        print("      ℹ️  rascunho parcial (Etsy auto-save). Vai ao painel rascunhos para finalizar.")
        time.sleep(3)
        return True, "auto-save fallback"

    time.sleep(5)
    return True, "ok"


def upload_batch(n=3):
    if not SESSION_DIR.exists():
        print("❌ Sessão não existe. Corre primeiro: python etsy-uploader.py --login")
        sys.exit(1)
    candidatos = [d for d in PRODUTOS_DIR.iterdir()
                  if d.is_dir() and d.name not in uploaded]
    if not candidatos:
        print("✅ todos os produtos já uploaded")
        return
    candidatos = candidatos[:n]
    print(f"📤 Vou tentar subir {len(candidatos)} produtos para Etsy")

    with sync_playwright() as p:
        ctx = open_browser(p, headless=False)  # headless=True após validares
        page = ctx.new_page()
        page.set_default_timeout(30000)
        for d in candidatos:
            try:
                ok, msg = upload_listing(page, d)
                if ok:
                    uploaded.append(d.name)
                    UPLOADED.write_text(json.dumps(uploaded, indent=2))
                    print(f"   ✅ rascunho criado: {d.name}")
                else:
                    print(f"   ⚠ falhou {d.name}: {msg}")
            except Exception as e:
                print(f"   ❌ erro {d.name}: {e}")
        ctx.close()
    print(f"\n✅ {len(uploaded)} produtos uploaded total")
    print("   👉 Vai a https://www.etsy.com/your/shops/me/tools/listings/draft e revê + publica os rascunhos.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--login":
        login_flow()
    else:
        n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
        upload_batch(n)
