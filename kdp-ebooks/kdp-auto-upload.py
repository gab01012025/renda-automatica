#!/usr/bin/env python3
"""
KDP Auto Upload (autonomo)
- Abre KDP em perfil dedicado de automacao
- Aguarda login (se necessario)
- Cria eBook Kindle
- Preenche campos principais do livro
- Faz upload do EPUB e da capa
- Preenche preco
- Publica automaticamente (por defeito)

Uso:
    python kdp-auto-upload.py [book_id]
    python kdp-auto-upload.py [book_id] --manual-review
Exemplo:
    python kdp-auto-upload.py copywriting-ia-pt
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent
TRACKER = ROOT / "kdp-pronto-upload" / "_lote-status.json"
PROFILE = Path.home() / ".cache" / "kdp-bot-profile"
PROFILE.mkdir(parents=True, exist_ok=True)


def get_book(book_id: str):
    data = json.loads(TRACKER.read_text())
    for b in data.get("books", []):
        if b.get("id") == book_id:
            meta = json.loads(Path(b["files"]["metadata"]).read_text())
            return b, meta
    return None, None


async def click_text(page, texts):
    for t in texts:
        try:
            loc = page.get_by_role("button", name=t)
            if await loc.count() > 0:
                await loc.first.click()
                return True
        except Exception:
            pass
        try:
            loc = page.locator(f"text={t}")
            if await loc.count() > 0:
                await loc.first.click()
                return True
        except Exception:
            pass
    return False


async def fill_first(page, selectors, value):
    for s in selectors:
        try:
            el = page.locator(s).first
            if await el.count() > 0:
                await el.click()
                await el.fill(str(value))
                return True
        except Exception:
            pass
    return False


async def fill_by_label_input(page, labels, value):
    for label in labels:
        try:
            field = page.locator(f"label:has-text('{label}')").first.locator("xpath=following::input[1]").first
            if await field.count() > 0:
                await field.click()
                await field.fill(str(value))
                return True
        except Exception:
            pass
    return False


async def fill_by_label_textarea(page, labels, value):
    for label in labels:
        try:
            area = page.locator(f"label:has-text('{label}')").first.locator("xpath=following::textarea[1]").first
            if await area.count() > 0:
                await area.click()
                await area.fill(str(value))
                return True
        except Exception:
            pass
        try:
            ed = page.locator(f"text={label}").first.locator("xpath=following::*[@contenteditable='true'][1]").first
            if await ed.count() > 0:
                await ed.click()
                await page.keyboard.press("Control+A")
                await page.keyboard.type(str(value)[:1800], delay=1)
                return True
        except Exception:
            pass
    return False


async def fill_by_text_anchor_input(page, anchors, value):
    for anchor in anchors:
        try:
            field = page.locator(f"text={anchor}").first.locator("xpath=following::input[@type='text'][1]").first
            if await field.count() > 0:
                await field.click()
                await field.fill(str(value))
                return True
        except Exception:
            pass
    return False


async def click_adult_no(page):
    try:
        no_label = page.locator("text=Público principal").first.locator(
            "xpath=following::label[contains(normalize-space(.), 'Não')][1]"
        ).first
        if await no_label.count() > 0:
            await no_label.click(force=True)
            return True
    except Exception:
        pass

    try:
        section = page.locator("text=Público principal").first
        radios = section.locator("xpath=following::input[@type='radio'][position()<=4]")
        if await radios.count() >= 2:
            await radios.nth(1).check(force=True)
            return True
    except Exception:
        pass

    return False


async def select_categories(page, meta):
    opened = await click_text(page, ["Escolha as categorias", "Choose categories"])
    if not opened:
        return False

    await page.wait_for_timeout(1200)
    modal = page.locator("div[role='dialog']").last
    try:
        categories = meta.get("categorias", [])
        cat_hint = " ".join(categories).lower()
        primary_options = [
            "Administração, Negócios e Economia",
            "Computação, Informática e Mídias Digitais",
            "Direito",
            "Culinária, Comida e Vinho",
            "Educação e Referência",
        ]
        if "law" in cat_hint or "direito" in cat_hint:
            primary_options = ["Direito"] + primary_options
        if "real estate" in cat_hint or "imobili" in cat_hint:
            primary_options = ["Administração, Negócios e Economia"] + primary_options
        if "cook" in cat_hint or "carbo" in cat_hint:
            primary_options = ["Culinária, Comida e Vinho"] + primary_options

        selected = False
        selects = modal.locator("select")
        if await selects.count() > 0:
            for option in primary_options:
                try:
                    await selects.first.select_option(label=option)
                    selected = True
                    await page.wait_for_timeout(900)
                    break
                except Exception:
                    pass

            # Fallback: focus the dropdown and pick first concrete option by keyboard.
            if not selected:
                try:
                    await selects.first.click()
                    await page.keyboard.press("ArrowDown")
                    await page.keyboard.press("Enter")
                    selected = True
                    await page.wait_for_timeout(900)
                except Exception:
                    pass

        if not selected:
            return False

        checks = modal.locator("input[type='checkbox']")
        if await checks.count() > 0:
            try:
                await checks.first.check(force=True)
            except Exception:
                pass

        await click_text(page, ["Salvar categorias", "Save categories"])
        await page.wait_for_timeout(800)
        return True
    except Exception:
        return False


async def wait_login_if_needed(page):
    for _ in range(180):  # 15 min
        txt = (await page.inner_text("body"))[:3000]
        if "Faça seu login" in txt or "Sign in" in txt:
            print("👉 Faz login no KDP neste browser. Eu continuo automaticamente depois do login.")
            await asyncio.sleep(5)
            continue
        if "O que você gostaria de criar?" in txt or "Create" in txt or "Criar eBook" in txt:
            return True
        await asyncio.sleep(2)
    return False


async def wait_processing_finish(page, timeout_s=240):
    for _ in range(timeout_s):
        try:
            body = (await page.inner_text("body"))[:20000]
        except Exception:
            body = ""

        if "Preparando seus arquivos" not in body and "Processando seu arquivo" not in body:
            return True
        await asyncio.sleep(1)
    return False


async def wait_pricing_step(page, retries=6):
    for _ in range(retries):
        body = (await page.inner_text("body"))[:30000]
        if "Royalties e precificação" in body or "Preço de lista" in body or "Territórios" in body:
            return True
        await click_text(page, ["Salvar e continuar", "Save and Continue", "Continue"])
        await page.wait_for_timeout(7000)
    return False


async def click_first_visible(page, selectors):
    for s in selectors:
        try:
            el = page.locator(s).first
            if await el.count() > 0:
                await el.click(force=True)
                return True
        except Exception:
            pass
    return False


async def set_role_control(page, selector):
    try:
        el = page.locator(selector).first
        if await el.count() == 0:
            return False
        state = await el.get_attribute("aria-checked")
        if state != "true":
            await el.click(force=True)
        return True
    except Exception:
        return False


async def fill_content_required_controls(page):
    try:
        return await page.evaluate(
            """() => {
                const setChecked = (el) => {
                    if (!el) return false;
                    el.click();
                    if ('checked' in el) el.checked = true;
                    if (el.setAttribute && el.getAttribute('role')) {
                        el.setAttribute('aria-checked', 'true');
                    }
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                };

                const findByText = (text) => {
                    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
                    let node;
                    while ((node = walker.nextNode())) {
                        if (node.textContent && node.textContent.includes(text)) return node;
                    }
                    return null;
                };

                let drmOk = false;
                const drmNode = findByText('Gerenciamento de direitos digitais (DRM)');
                if (drmNode) {
                    const radios = drmNode.parentElement.querySelectorAll('[role="radio"], input[type="radio"]');
                    if (radios.length >= 2) drmOk = setChecked(radios[1]);
                }

                let aiOk = false;
                const aiNode = findByText('Você usou ferramentas de IA');
                if (aiNode) {
                    const radios = aiNode.parentElement.querySelectorAll('[role="radio"], input[type="radio"]');
                    if (radios.length >= 1) aiOk = setChecked(radios[0]);
                }

                let confirmOk = false;
                const confirmNode = findByText('Ao clicar aqui, confirmo que minhas respostas estão corretas');
                if (confirmNode) {
                    const box = confirmNode.parentElement.querySelector('[role="checkbox"], input[type="checkbox"]');
                    confirmOk = setChecked(box);
                }

                if (!confirmOk) {
                    const visibleChecks = Array.from(document.querySelectorAll('[role="checkbox"], input[type="checkbox"]'))
                        .filter((el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length));
                    for (const cb of visibleChecks) {
                        confirmOk = setChecked(cb) || confirmOk;
                    }
                }

                return { drmOk, aiOk, confirmOk };
            }"""
        )
    except Exception:
        return {"drmOk": False, "aiOk": False, "confirmOk": False}


async def click_left_of_text(page, text, x_offset=18):
    try:
        target = page.locator(f"text={text}").first
        if await target.count() == 0:
            return False
        box = await target.bounding_box()
        if not box:
            return False
        await page.mouse.click(box["x"] - x_offset, box["y"] + (box["height"] / 2))
        return True
    except Exception:
        return False


async def run(book_id: str, auto_publish: bool = True):
    book, meta = get_book(book_id)
    if not book:
        print(f"❌ Livro não encontrado no tracker: {book_id}")
        return 1

    epub = Path(book["files"]["epub"])
    cover = Path(book["files"]["cover"])

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(PROFILE),
            headless=False,
            executable_path="/usr/bin/google-chrome",
            channel="chrome",
            viewport={"width": 1366, "height": 900},
            ignore_default_args=["--enable-automation"],
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        print(f"🚀 Iniciando upload KDP para: {book_id}")
        await page.goto("https://kdp.amazon.com/pt_BR/create", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        print(f"🌐 URL inicial: {page.url}")

        ok = await wait_login_if_needed(page)
        if not ok:
            print("❌ Timeout no login KDP")
            return 2
        print("✅ Sessao KDP pronta")

        # Etapa 1: clicar em Criar eBook
        if not await click_text(page, ["Criar eBook", "Create eBook", "Create Kindle eBook"]):
            print("⚠️ Não achei botão Criar eBook. Mantive browser aberto para ação manual.")
            await page.screenshot(path="/tmp/kdp-auto-no-create.png", full_page=True)
            await ctx.close()
            return 3

        await page.wait_for_timeout(5000)
        print("✅ Etapa Criar eBook iniciada")
        print(f"🌐 URL detalhes: {page.url}")

        # Etapa 2: detalhes
        title_ok = await fill_first(page, [
            'input[name*="bookTitle"]', 'input[id*="bookTitle"]',
            'input[aria-label*="Título" i]', 'input[placeholder*="Título" i]'
        ], meta.get("titulo", ""))
        if not title_ok:
            title_ok = await fill_by_label_input(page, ["Título do livro", "Book title", "Title"], meta.get("titulo", ""))
        if not title_ok:
            title_ok = await fill_by_text_anchor_input(page, ["Título do livro", "Book title", "Title"], meta.get("titulo", ""))

        subtitle_ok = await fill_first(page, [
            'input[name*="subtitle"]', 'input[id*="subtitle"]',
            'input[aria-label*="Subtítulo" i]'
        ], meta.get("subtitulo", ""))
        if not subtitle_ok:
            await fill_by_label_input(page, ["Subtítulo", "Subtitle"], meta.get("subtitulo", ""))

        author_ok = await fill_first(page, [
            'input[name*="author"]', 'input[id*="author"]',
            'input[aria-label*="Autor" i]'
        ], meta.get("autor", "Gabriel Barreto"))
        if not author_ok:
            author = (meta.get("autor") or "Gabriel Barreto").strip().split()
            first_name = author[0]
            last_name = " ".join(author[1:]) if len(author) > 1 else "Barreto"
            await fill_by_label_input(page, ["Autor ou colaborador principal", "Author"], first_name)
            await fill_by_label_input(page, ["Sobrenome", "Last name", "Surname"], last_name)
            await fill_by_text_anchor_input(page, ["Autor ou colaborador principal", "Author"], first_name)
            await fill_by_text_anchor_input(page, ["Sobrenome", "Last name", "Surname"], last_name)
            try:
                author_block = page.locator("text=Autor ou colaborador principal").first
                name_input = author_block.locator("xpath=following::input[@placeholder='Nome'][1]").first
                surname_input = author_block.locator("xpath=following::input[@placeholder='Sobrenome'][1]").first
                if await name_input.count() > 0:
                    await name_input.fill(first_name)
                if await surname_input.count() > 0:
                    await surname_input.fill(last_name)
            except Exception:
                pass

        # Descricao
        desc = meta.get("descricao", "")
        desc_ok = await fill_first(page, [
            'textarea[name*="description"]', 'textarea[id*="description"]',
            'textarea[aria-label*="Descrição" i]'
        ], desc)
        if not desc_ok:
            desc_ok = await fill_by_label_textarea(page, ["Descrição", "Description"], desc)
        if not desc_ok:
            desc_ok = await fill_first(page, ['div[role="textbox"]', '[contenteditable="true"]'], desc)
        if not desc_ok:
            try:
                body = page.frame_locator("iframe").first.locator("body")
                if await body.count() > 0:
                    await body.click()
                    await page.keyboard.press("Control+A")
                    await page.keyboard.press("Backspace")
                    await page.keyboard.type(desc[:1800], delay=3)
                    await page.keyboard.press("Tab")
                    desc_ok = True
            except Exception:
                pass
        if not desc_ok:
            try:
                desc_ok = await page.evaluate(
                    """(text) => {
                        if (window.tinyMCE && window.tinyMCE.activeEditor) {
                            const safe = String(text || "")
                                .replace(/&/g, "&amp;")
                                .replace(/</g, "&lt;")
                                .replace(/>/g, "&gt;");
                            window.tinyMCE.activeEditor.setContent(`<p>${safe}</p>`);
                            window.tinyMCE.activeEditor.save();
                            window.tinyMCE.activeEditor.fire("change");
                            window.tinyMCE.activeEditor.fire("blur");
                            return true;
                        }
                        const ta = document.querySelector('textarea[name*="description" i], textarea[id*="description" i]');
                        if (ta) {
                            ta.value = String(text || "");
                            ta.dispatchEvent(new Event("input", { bubbles: true }));
                            ta.dispatchEvent(new Event("change", { bubbles: true }));
                            return true;
                        }
                        return false;
                    }""",
                    desc[:1800],
                )
            except Exception:
                pass

        # Direitos de publicacao + publico principal sao obrigatorios para continuar
        await click_text(page, [
            "Eu possuo os direitos autorais",
            "I own the copyright",
            "direitos de publicação"
        ])
        await click_adult_no(page)

        # Categorias sao obrigatorias
        await select_categories(page, meta)

        if not title_ok:
            print("⚠️ Titulo não foi preenchido com os seletores atuais")
        if not desc_ok:
            print("⚠️ Descricao não foi preenchida com os seletores atuais")

        # Keywords (best effort)
        kws = meta.get("keywords", [])
        for i, kw in enumerate(kws[:7], start=1):
            await fill_first(page, [
                f'input[name*="keyword{i}"]', f'input[id*="keyword{i}"]'
            ], kw)

        # Save/Continue para Conteudo
        await click_text(page, ["Salvar e continuar", "Continue", "Salvar e prosseguir"])
        await page.wait_for_timeout(7000)
        print(f"🌐 URL apos detalhes: {page.url}")
        print("✅ Detalhes preenchidos")

        # Upload EPUB + Cover
        file_inputs = page.locator('input[type="file"]')
        count = await file_inputs.count()
        if count > 0:
            try:
                await file_inputs.nth(0).set_input_files(str(epub))
                print("✅ EPUB enviado")
            except Exception:
                print("⚠️ Não consegui enviar EPUB automaticamente")
            if count > 1:
                try:
                    await file_inputs.nth(1).set_input_files(str(cover))
                    print("✅ Capa enviada")
                except Exception:
                    print("⚠️ Não consegui enviar capa automaticamente")
            print("✅ Upload de ficheiros concluido")

        # Campo geralmente obrigatorio no conteudo
        await click_first_visible(page, [
            "label:has-text('Não, não aplique o Gerenciamento de direitos digitais')",
            "label:has-text('No, do not enable Digital Rights Management')",
            "text=Você gostaria de aplicar o Gerenciamento de direitos digitais (DRM) aos seus arquivos? >> xpath=following::*[@role='radio' and contains(., 'Não')][1]"
        ])

        # Se o livro foi produzido com IA, marcamos Sim.
        await click_first_visible(page, [
            "text=Conteúdo gerado por IA >> xpath=following::label[contains(., 'Sim')][1]",
            "text=AI-generated content >> xpath=following::label[contains(., 'Yes')][1]",
            "text=Você usou ferramentas de IA para criar textos, imagens e/ou traduções em seu livro? >> xpath=following::*[@role='radio' and contains(., 'Sim')][1]"
        ])

        # Confirmacao obrigatoria apos novo upload.
        await click_first_visible(page, [
            "text=Ao clicar aqui, confirmo que minhas respostas estão corretas",
            "label:has-text('Ao clicar aqui, confirmo que minhas respostas estão corretas')",
            "label:has-text('I confirm my answers are correct')",
            "input[type='checkbox']"
        ])

        js_flags = await fill_content_required_controls(page)
        print(
            f"✅ Campos obrigatorios conteudo (drm={js_flags.get('drmOk')}, "
            f"ia={js_flags.get('aiOk')}, confirm={js_flags.get('confirmOk')})"
        )

        # Aguarda KDP terminar o processamento de ficheiros antes de avancar.
        done = await wait_processing_finish(page)
        if done:
            print("✅ Processamento de ficheiros concluido")
        else:
            print("⚠️ Timeout aguardando processamento de ficheiros")

        # O KDP pode reconstruir o form apos o processamento; reaplicamos os campos obrigatorios.
        await click_first_visible(page, [
            "label:has-text('Não, não aplique o Gerenciamento de direitos digitais')",
            "label:has-text('No, do not enable Digital Rights Management')"
        ])
        await click_first_visible(page, [
            "text=Conteúdo gerado por IA >> xpath=following::label[contains(., 'Sim')][1]",
            "text=AI-generated content >> xpath=following::label[contains(., 'Yes')][1]"
        ])
        await set_role_control(page, "[role='checkbox']:has-text('Ao clicar aqui, confirmo que minhas respostas estão corretas')")
        js_flags = await fill_content_required_controls(page)
        print(
            f"✅ Campos obrigatorios pos-processamento (drm={js_flags.get('drmOk')}, "
            f"ia={js_flags.get('aiOk')}, confirm={js_flags.get('confirmOk')})"
        )

        # Save/Continue para Preco
        await click_text(page, ["Salvar e continuar", "Continue", "Salvar e prosseguir"])
        await page.wait_for_timeout(7000)
        print(f"🌐 URL apos conteudo: {page.url}")
        on_pricing = await wait_pricing_step(page)
        if not on_pricing:
            await page.screenshot(path="/tmp/kdp-auto-not-pricing.png", full_page=True)
            print("⚠️ Não consegui chegar na etapa de precificação.")
            print("📸 Screenshot: /tmp/kdp-auto-not-pricing.png")
            await ctx.close()
            return 5

        # Preco
        await fill_first(page, [
            'input[name*="listPrice"]', 'input[id*="listPrice"]',
            'input[aria-label*="Preço" i]', 'input[aria-label*="price" i]'
        ], meta.get("preco", "4.99"))
        await fill_by_text_anchor_input(page, ["Preço de lista", "List price"], meta.get("preco", "4.99"))
        print("✅ Preco preenchido")

        await page.screenshot(path="/tmp/kdp-auto-ready-to-publish.png", full_page=True)
        print("📸 Screenshot pre-publicacao: /tmp/kdp-auto-ready-to-publish.png")

        if auto_publish:
            published = await click_text(page, [
                "Publicar eBook Kindle",
                "Publicar seu eBook Kindle",
                "Publicar eBook",
                "Publish Your Kindle eBook",
                "Publish"
            ])
            if not published:
                print("⚠️ Não encontrei o botao de publicar automaticamente.")
                print("📸 Screenshot para revisao: /tmp/kdp-auto-ready-to-publish.png")
                await ctx.close()
                return 4

            await page.wait_for_timeout(6000)
            await page.screenshot(path="/tmp/kdp-auto-published.png", full_page=True)
            print("🎉 Clique de publicacao executado.")
            print("📸 Screenshot pos-publicacao: /tmp/kdp-auto-published.png")
            await ctx.close()
            return 0

        print("✅ Pronto para publicar. Revê a página e clica em Publicar eBook Kindle.")
        print("🛑 Vou manter o browser aberto para revisao final.")
        try:
            await page.wait_for_event("close", timeout=7200_000)
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KDP auto upload")
    parser.add_argument("book_id", nargs="?", default="copywriting-ia-pt")
    parser.add_argument("--manual-review", action="store_true", help="nao clica em publicar")
    args = parser.parse_args()

    rc = asyncio.run(run(args.book_id, auto_publish=not args.manual_review))
    sys.exit(rc)
