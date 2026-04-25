#!/usr/bin/env python3
"""
Pipeline YouTube Faceless — Curiosidades IA em 60s (Shorts)
1. GPT-4o gera script (45-55s narrados em PT-PT)
2. edge-tts converte para áudio MP3
3. ffmpeg combina áudio + imagem fixa (DALL-E ou cor sólida com texto) → MP4 9:16
4. Output pronto a fazer upload manual no YouTube Studio (ou via API depois)

Uso:
    python gerar-video.py [n_videos]
"""
import os, sys, json, random, asyncio, subprocess, urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "videos"
OUT.mkdir(exist_ok=True)

# Carregar OPENAI_API_KEY
for env_path in [ROOT / ".env", ROOT.parent / "produtos-digitais" / ".env", ROOT.parent / "pod-automatico" / ".env"]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_KEY:
    print("❌ OPENAI_API_KEY missing")
    sys.exit(1)

TOPICOS = [
    "uma curiosidade pouco conhecida sobre o ChatGPT",
    "como o GPT-4 aprende",
    "o que é uma rede neural em 60 segundos",
    "porque a IA não pode mentir intencionalmente",
    "o maior erro de quem usa ChatGPT",
    "3 prompts que mudam a tua vida",
    "como ganhar dinheiro com IA em 2026",
    "o que é AGI e quando chega",
    "por que a OpenAI vale mais que a Tesla",
    "o que ChatGPT NÃO te diz sobre si próprio",
    "Claude vs ChatGPT vs Gemini: qual escolher",
    "como detectar texto escrito por IA",
    "o futuro da programação com Copilot",
    "porque devemos aprender prompt engineering",
    "1 truque ChatGPT que poucos conhecem",
]

GUMROAD_CTA = (
    "\n\n💰 Packs de prompts em PT (compra direta):\n"
    "• Devs (100 prompts): https://barretovibes004.gumroad.com/l/pisbx\n"
    "• Marketing (150 prompts): https://barretovibes004.gumroad.com/l/kzclrq\n"
    "• Bundle 250 prompts (€19): https://barretovibes004.gumroad.com/l/sgppj\n"
    "\nSe quiseres o bundle com desconto, começa pelo de €19."
)

def gpt(prompt, system="És um criador de conteúdo viral em português europeu para YouTube Shorts. Escreves scripts curtos (45-55 segundos quando lidos), começam com hook forte, terminam com CTA."):
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps({
            "model": "gpt-4o",
            "temperature": 0.9,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"]

def gerar_script(topico):
    prompt = f"""Tópico: {topico}

Escreve um script de YouTube Shorts em português europeu, com 100-130 palavras (45-55 segundos lidos).

Estrutura:
1. HOOK (primeiros 5 segundos): pergunta ou afirmação chocante
2. CORPO (40 segundos): 2-3 factos surpreendentes ou passos práticos
3. CTA (5 segundos): "Segue para mais", "Comenta o que achaste", etc.

Regras:
- Frases curtas, ritmo rápido
- Sem emojis, sem hashtags no script (só texto narrado)
- Sem "olá pessoal", arranca direto ao tema
- Português de Portugal (pt-PT) natural

Devolve APENAS o texto a narrar, sem títulos nem secções."""
    return gpt(prompt)

def gerar_titulo_e_desc(topico, script):
    prompt = f"""Para este YouTube Short:

Tópico: {topico}
Script: {script[:300]}...

Gera (JSON):
{{
  "titulo": "título com 40-60 caracteres, chamativo, 1-2 emojis no máximo",
  "descricao": "3-4 linhas com hooks, depois 8 hashtags relevantes",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"]
}}

Devolve APENAS o JSON, sem markdown."""
    raw = gpt(prompt, system="És um especialista em SEO YouTube. Devolves sempre JSON válido.")
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"titulo": topico[:60], "descricao": script[:200], "tags": ["IA","ChatGPT","tecnologia"]}


def aplicar_cta(meta):
    descricao = (meta.get("descricao") or "").strip()
    if "barretovibes004.gumroad.com" not in descricao:
        descricao = f"{descricao}{GUMROAD_CTA}".strip()
    meta["descricao"] = descricao
    tags = meta.get("tags") or []
    if "Prompts" not in tags:
        tags.append("Prompts")
    if "NegociosDigitais" not in tags:
        tags.append("NegociosDigitais")
    meta["tags"] = tags[:15]
    return meta

async def tts(text, out_mp3):
    import edge_tts
    # Voz portuguesa de Portugal
    voice = "pt-PT-DuarteNeural"  # ou "pt-PT-RaquelNeural"
    com = edge_tts.Communicate(text, voice, rate="+8%")
    await com.save(out_mp3)

def gerar_imagem_fundo(topico, slug):
    """Gera imagem 1024x1792 (vertical) via DALL-E 3."""
    prompt = f"Vertical YouTube Shorts background image for video about '{topico}'. Modern, eye-catching, abstract tech style. Bold colors. NO TEXT in the image. Cinematic lighting. 9:16 aspect ratio."
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps({"model": "dall-e-3", "prompt": prompt, "n": 1, "size": "1024x1792", "quality": "standard"}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            url = json.loads(r.read())["data"][0]["url"]
        img_path = OUT / f"{slug}-bg.png"
        urllib.request.urlretrieve(url, img_path)
        return img_path
    except Exception as e:
        print(f"   ⚠️  DALL-E falhou: {e}")
        return None

def montar_video(audio_mp3, imagem, slug, legenda_texto=None):
    """ffmpeg: imagem + audio → MP4 9:16 (1080x1920)."""
    out_mp4 = OUT / f"{slug}.mp4"
    # Pega duração do áudio
    dur_raw = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(audio_mp3)],
        capture_output=True, text=True,
    ).stdout.strip()
    duration = float(dur_raw or "60")

    if imagem:
        # Imagem + áudio, redimensionada para 1080x1920
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(imagem), "-i", str(audio_mp3),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration), "-shortest", str(out_mp4),
        ]
    else:
        # Fallback: cor sólida + texto
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x1a1a2e:s=1080x1920:d={duration}",
            "-i", str(audio_mp3),
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", str(out_mp4),
        ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"   ⚠️  ffmpeg erro: {r.stderr[-300:]}")
        return None
    return out_mp4

async def gerar_video(topico):
    slug = "".join(c if c.isalnum() else "-" for c in topico.lower())[:50].strip("-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    slug = f"{timestamp}-{slug}"
    print(f"\n🎬 {topico}")
    print(f"   1/4 Script GPT-4o...", end=" ", flush=True)
    script = gerar_script(topico)
    print(f"✓ ({len(script)} chars)")

    print(f"   2/4 Metadata SEO...", end=" ", flush=True)
    meta = gerar_titulo_e_desc(topico, script)
    meta = aplicar_cta(meta)
    print(f"✓ {meta['titulo'][:50]}")

    print(f"   3/4 Áudio TTS (edge-tts pt-PT)...", end=" ", flush=True)
    audio = OUT / f"{slug}.mp3"
    await tts(script, str(audio))
    print(f"✓ {audio.stat().st_size//1024} KB")

    print(f"   4/4 Imagem DALL-E + montagem ffmpeg...", end=" ", flush=True)
    imagem = gerar_imagem_fundo(topico, slug)
    video = montar_video(audio, imagem, slug)
    if video:
        print(f"✓ {video.stat().st_size//1024} KB")
    else:
        print("✗")
        return

    # Salva metadata
    meta_path = OUT / f"{slug}.json"
    meta_path.write_text(json.dumps({
        "topico": topico,
        "script": script,
        "titulo": meta["titulo"],
        "descricao": meta["descricao"],
        "tags": meta["tags"],
        "video": str(video.name),
        "audio": str(audio.name),
        "criado_em": datetime.now().isoformat(),
    }, ensure_ascii=False, indent=2))
    print(f"   ✅ Pronto: {video.name}")
    print(f"      Título: {meta['titulo']}")

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print(f"🚀 Gerando {n} YouTube Shorts faceless\n")
    topicos = random.sample(TOPICOS, min(n, len(TOPICOS)))
    for t in topicos:
        try:
            await gerar_video(t)
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    print(f"\n✅ Concluído. Pasta: {OUT}")
    print(f"📤 Upload manual em https://studio.youtube.com → criar Short → upload .mp4")
    print(f"   (metadata em .json para copiar título/descrição/tags)")

if __name__ == "__main__":
    asyncio.run(main())
