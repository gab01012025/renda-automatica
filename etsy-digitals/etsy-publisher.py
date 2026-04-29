"""
Etsy Auto-Publisher v2 — fluxo completo até PUBLICAR (não rascunho).

Fluxo:
  1. abre create-listing
  2. preenche TODOS os campos obrigatórios (com screenshots a cada passo)
  3. clica Publish (ou Salvar e continuar até chegar a Publish)

Uso: python etsy-publisher.py [N=1]
"""
import os, sys, json, time, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SESSION_DIR = ROOT / "etsy-digitals" / ".etsy-session"
PRODUTOS_DIR = ROOT / "etsy-digitals" / "produtos"
UPLOADED = ROOT / "etsy-digitals" / "_uploaded.json"
DEBUG_DIR = ROOT / "etsy-digitals" / "_debug"
DEBUG_DIR.mkdir(exist_ok=True)

uploaded = json.loads(UPLOADED.read_text()) if UPLOADED.exists() else []

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("❌ pip install playwright && playwright install chromium")
    sys.exit(1)


def screenshot(page, name):
    try:
        path = DEBUG_DIR / f"{name}.png"
        page.screenshot(path=str(path), full_page=True)
        print(f"      📸 {path.name}")
    except Exception as e:
        print(f"      ⚠ screenshot fail: {e}")


def safe_click(page, selectors, timeout=4000, label=""):
    """Tenta vários selectors até um clicar."""
    for sel in selectors:
        try:
            if isinstance(sel, dict):
                if sel.get("role"):
                    loc = page.get_by_role(sel["role"], name=sel.get("name", ""), exact=False).first
                elif sel.get("text"):
                    loc = page.get_by_text(sel["text"], exact=False).first
                else:
                    continue
            else:
                loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=timeout)
            loc.click()
            print(f"      ✓ click {label or sel}")
            return True
        except Exception:
            continue
    return False


def safe_fill(page, selectors, value, label=""):
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            loc.wait_for(state="visible", timeout=3000)
            loc.fill(value)
            return True
        except Exception:
            continue
    return False


def publish_listing(page, produto_dir: Path):
    listing_json = produto_dir / "etsy-listing.json"
    if not listing_json.exists():
        return False, "sem etsy-listing.json"
    meta = json.loads(listing_json.read_text())

    files = sorted([f for f in produto_dir.iterdir()
                    if f.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg", ".zip")])
    images = [f for f in files if f.suffix.lower() in (".png", ".jpg", ".jpeg")]
    digital_files = [f for f in files if f.suffix.lower() in (".pdf", ".zip")]
    if not digital_files:
        digital_files = images  # se for wall art, vende o PNG mesmo

    if not images:
        return False, "sem imagem preview"

    title = meta.get("title", produto_dir.name)[:140]
    description = meta.get("description", "Beautiful digital download.")[:5000]
    tags = (meta.get("tags") or [])[:13]

    print(f"\n   📦 {title[:60]}")

    page.goto("https://www.etsy.com/your/shops/me/tools/listings/create", timeout=60000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    screenshot(page, f"01-create-{produto_dir.name}")

    # ---- 1. UPLOAD IMAGEM ----
    img_uploaded = False
    for sel in ['input[type="file"][accept*="image"]', 'input[data-test-id*="photo"]', 'input[type="file"]']:
        try:
            page.locator(sel).first.set_input_files(str(images[0]), timeout=8000)
            page.wait_for_timeout(5000)
            img_uploaded = True
            break
        except Exception:
            continue
    if not img_uploaded:
        screenshot(page, f"02-no-img-{produto_dir.name}")
        return False, "upload imagem falhou"
    print("      ✓ imagem")
    screenshot(page, f"02-after-img-{produto_dir.name}")

    # ---- 2. TÍTULO ----
    safe_fill(page, [
        'input[name="title"]',
        'input[id*="title"]',
        'textarea[name="title"]',
        'input[aria-label*="ítulo"]',
        'input[aria-label*="itle"]',
    ], title, "title")

    # ---- 3. CATEGORIA (input de pesquisa) ----
    cat_query = "Decoração de parede" if ("print" in produto_dir.name or "wall" in produto_dir.name) else "Cadernos e diários"
    for sel in [
        'input[placeholder*="exemplo" i]',
        'input[placeholder*="aneis" i]',
        'input[aria-label*="ategoria"]',
        'input[name*="taxonomy"]',
    ]:
        try:
            inp = page.locator(sel).first
            inp.wait_for(state="visible", timeout=3000)
            inp.click()
            inp.fill(cat_query)
            page.wait_for_timeout(1500)
            # clica primeira sugestão
            try:
                page.locator('[role="option"], [role="listbox"] li, [data-test-id*="suggestion"]').first.click(timeout=3000)
                print(f"      ✓ categoria: {cat_query}")
            except Exception:
                inp.press("Enter")
            break
        except Exception:
            continue

    # Tipo: Ficheiros digitais
    safe_click(page, [
        {"role": "radio", "name": "Ficheiros digitais"},
        {"role": "radio", "name": "Digital files"},
        'input[value="download"]',
        'input[name="listing_type"][value="download"]',
    ], label="tipo=digital")

    # Quando foi feito (select nativo)
    for sel in ['select[name="when_made"]', 'select#when-made', 'select']:
        try:
            el = page.locator(sel).first
            el.wait_for(state="visible", timeout=2000)
            # tenta vários valores
            picked = False
            for value in ["made_to_order", "2020_2025", "2020_2024"]:
                try:
                    el.select_option(value=value)
                    print(f"      ✓ when_made: {value}")
                    picked = True
                    break
                except Exception:
                    continue
            if not picked:
                # tenta primeiro option não-vazio
                el.evaluate("e => { e.selectedIndex = 1; e.dispatchEvent(new Event('change', {bubbles:true})); }")
                print("      ✓ when_made: index 1")
            break
        except Exception:
            continue

    # Quem o fez: "Fui eu"
    safe_click(page, [
        {"role": "radio", "name": "Fui eu"},
        {"role": "radio", "name": "I did"},
        'input[value="i_did"]',
        'input[name="who_made"][value="i_did"]',
    ], label="who_made=fui eu")

    # O que é: "Um produto acabado"
    safe_click(page, [
        {"role": "radio", "name": "Um produto acabado"},
        {"role": "radio", "name": "A finished product"},
        'input[value="false"][name="is_supply"]',
        'input[name="is_supply"][value="false"]',
    ], label="is_supply=acabado")

    page.wait_for_timeout(1500)

    # ---- 4. DESCRIÇÃO ----
    safe_fill(page, [
        'textarea[name="description"]',
        'div[contenteditable="true"][aria-label*="escri"]',
        'div[contenteditable="true"]',
    ], description, "description")

    # ---- 5. TAGS ----
    tag_selectors = [
        'input[placeholder*="Forma" i]',
        'input[placeholder*="estilo" i]',
        'input[aria-label*="tiqueta" i][type="text"]',
        'input[aria-label*="ag"][type="text"]',
        'input[name="tags"]',
    ]
    for sel in tag_selectors:
        try:
            tag_input = page.locator(sel).first
            tag_input.wait_for(state="visible", timeout=3000)
            for tag in tags:
                tag_input.fill(tag[:20])
                tag_input.press(",")
                page.wait_for_timeout(300)
            print(f"      ✓ {len(tags)} tags")
            break
        except Exception:
            continue

    # ---- 7. PREÇO ----
    is_wall = "wall" in produto_dir.name or "print" in produto_dir.name
    price = "8.00" if is_wall else "12.00"
    safe_fill(page, [
        'input[name="price"]',
        'input[id*="price"]',
        'input[aria-label*="reço"]',
        'input[aria-label*="rice"]',
    ], price, "price")

    # ---- 8. QUANTIDADE ----
    safe_fill(page, [
        'input[name="quantity"]',
        'input[id*="quantity"]',
        'input[aria-label*="uantidade"]',
        'input[aria-label*="uantity"]',
    ], "999", "quantity")

    # ---- 9. UPLOAD FICHEIRO DIGITAL ----
    for sel in [
        'input[type="file"][accept*="pdf"]',
        'input[type="file"][accept*="zip"]',
        'input[data-test-id*="digital"]',
        'input[data-selector*="digital-file"]',
    ]:
        try:
            page.locator(sel).first.set_input_files(str(digital_files[0]), timeout=5000)
            page.wait_for_timeout(3000)
            print(f"      ✓ digital file: {digital_files[0].name}")
            break
        except Exception:
            continue

    page.wait_for_timeout(2000)
    screenshot(page, f"03-filled-{produto_dir.name}")

    # ---- 10. PUBLICAR (não rascunho!) ----
    publish_clicked = safe_click(page, [
        {"role": "button", "name": "Publicar"},
        {"role": "button", "name": "Publish"},
        {"role": "button", "name": "Publicar agora"},
        {"role": "button", "name": "Publish now"},
        'button:has-text("Publicar")',
        'button:has-text("Publish")',
    ], label="PUBLISH")

    if not publish_clicked:
        # tenta "Pré-visualizar" + depois publicar do preview
        safe_click(page, [
            {"role": "button", "name": "Pré-visualizar"},
            {"role": "button", "name": "Preview"},
        ], label="preview")
        page.wait_for_timeout(3000)
        publish_clicked = safe_click(page, [
            {"role": "button", "name": "Publicar"},
            {"role": "button", "name": "Publish"},
        ], label="PUBLISH (after preview)")

    page.wait_for_timeout(5000)
    screenshot(page, f"04-after-publish-{produto_dir.name}")

    # confirmar dialog se aparecer
    safe_click(page, [
        {"role": "button", "name": "Sim, publicar"},
        {"role": "button", "name": "Yes, publish"},
        {"role": "button", "name": "Confirmar"},
        {"role": "button", "name": "Confirm"},
        {"role": "button", "name": "Continuar"},
        {"role": "button", "name": "Continue"},
    ], label="confirm dialog")

    page.wait_for_timeout(8000)
    screenshot(page, f"05-final-{produto_dir.name}")

    # verificar se URL mudou para /listings (sucesso) ou ainda em /create (falha)
    url = page.url
    if "/listings/create" in url or "/draft" in url:
        return False, f"ainda em wizard ({url})"
    return True, "publicado"


def main():
    if not SESSION_DIR.exists():
        print("❌ Corre primeiro: python etsy-uploader.py --login")
        sys.exit(1)
    candidatos = [d for d in PRODUTOS_DIR.iterdir()
                  if d.is_dir() and d.name not in uploaded][: int(sys.argv[1]) if len(sys.argv) > 1 else 1]
    if not candidatos:
        print("✅ todos uploaded")
        return
    print(f"📤 publicar {len(candidatos)} produtos")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(SESSION_DIR), headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.new_page()
        page.set_default_timeout(20000)
        for d in candidatos:
            try:
                ok, msg = publish_listing(page, d)
                if ok:
                    uploaded.append(d.name)
                    UPLOADED.write_text(json.dumps(uploaded, indent=2))
                    print(f"   ✅ PUBLICADO: {d.name} — {msg}")
                else:
                    print(f"   ⚠ {d.name}: {msg}")
            except Exception as e:
                print(f"   ❌ erro {d.name}: {e}")
                screenshot(page, f"99-exception-{d.name}")
        ctx.close()


if __name__ == "__main__":
    main()
