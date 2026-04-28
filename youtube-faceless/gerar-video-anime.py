#!/usr/bin/env python3
"""
Pipeline YouTube Faceless — CURIOSIDADES ANIME em 60s (Shorts).
Mesma infra do gerar-video.py, mas:
  - Tópicos: curiosidades, lore, ranking, easter-eggs de animes populares
  - Imagens DALL-E estilo anime (sem usar imagens reais protegidas)
  - Hashtags + CTA otimizados para audiência anime PT/BR
  - Sem copyright: imagem original IA + script original

Uso:
    python gerar-video-anime.py [n_videos]
"""
import os, sys, json, random, asyncio, subprocess, urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "videos"
OUT.mkdir(exist_ok=True)

for env_path in [ROOT / ".env", ROOT.parent / "produtos-digitais" / ".env", ROOT.parent / "pod-automatico" / ".env"]:
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_KEY:
    print("❌ OPENAI_API_KEY missing"); sys.exit(1)

# 60+ tópicos de animes populares (rotação automática)
TOPICOS = [
    "5 curiosidades sobre Naruto que ninguém te contou",
    "o verdadeiro poder de Goku em Dragon Ball",
    "porque o Eren Yeager virou o vilão em Attack on Titan",
    "o segredo do sharingan em Naruto",
    "3 personagens de One Piece que ninguém esperava",
    "como Luffy se tornou Yonkou em One Piece",
    "porque Demon Slayer bateu recordes mundiais",
    "o significado real do nome Tanjiro",
    "a verdade sobre Light Yagami em Death Note",
    "5 mortes mais chocantes do anime",
    "porque Jujutsu Kaisen é o novo Naruto",
    "Gojo Satoru: o personagem mais OP do anime",
    "a teoria que muda tudo em Chainsaw Man",
    "Edward Elric e o preço da alquimia",
    "porque Hunter x Hunter é a obra-prima do Togashi",
    "5 animes que mudam a tua perspectiva sobre a vida",
    "o final secreto de Evangelion explicado",
    "como My Hero Academia revolucionou o gênero shonen",
    "o passado obscuro do All Might",
    "porque Berserk é o anime mais sombrio de todos",
    "Guts vs Griffith: a rivalidade definitiva",
    "5 animes que tens de ver antes de morrer",
    "o sistema de magia mais complexo dos animes",
    "como Spy x Family conquistou o mundo",
    "Anya: a personagem mais carismática do ano",
    "5 animes underrated que merecem mais atenção",
    "por que Studio Ghibli é insuperável",
    "o significado de Spirited Away explicado",
    "Howl no Castelo Animado e a crítica à guerra",
    "5 cenas de luta mais épicas do anime",
    "como Bleach voltou aos holofotes em 2024",
    "Ichigo Kurosaki: o shinigami mais incompreendido",
    "porque Tokyo Ghoul é uma alegoria sobre identidade",
    "Kaneki Ken: a metamorfose mais brutal",
    "5 animes que vão te fazer chorar",
    "Your Name: o anime que conquistou Hollywood",
    "Makoto Shinkai: o sucessor de Miyazaki",
    "como Frieren mudou o gênero isekai",
    "5 isekai que valem realmente a pena",
    "Re:Zero e o trauma do Subaru",
    "porque Mob Psycho 100 é genial",
    "a animação revolucionária de One Punch Man",
    "Saitama: o herói mais poderoso e mais triste",
    "5 vilões mais marcantes do anime",
    "Madara Uchiha: o mestre da manipulação",
    "porque Code Geass é uma lição de xadrez",
    "Lelouch Lamperouge: o anti-herói perfeito",
    "5 animes com finais perfeitos",
    "Steins;Gate e a teoria das linhas temporais",
    "Okabe Rintarou: o cientista louco favorito",
    "porque Vinland Saga é diferente de tudo",
    "Thorfinn: a busca pela verdadeira força",
    "5 protagonistas femininas mais fortes do anime",
    "Mikasa Ackerman: a guerreira definitiva",
    "como Kaguya-sama virou fenômeno mundial",
    "5 animes de comédia que vão te rir até chorar",
    "porque Cowboy Bebop é eterno",
    "Spike Spiegel e a melancolia do espaço",
    "5 trilhas sonoras mais icônicas do anime",
    "Yoko Kanno: a compositora dos sonhos",
    "como o anime conquistou a Netflix",
    "5 animes baseados em eventos reais",
]

ANIME_HASHTAGS = ["#anime", "#otaku", "#animes", "#shonen", "#mangá", "#manga", "#animeshorts", "#animecuriosidades", "#animebrasil", "#animept"]


def with_utm(url, source):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}utm_source={source}&utm_medium=organic_video&utm_campaign=anime_curiosidades"


# CTA mais leve para audiência anime (não promove "prompts ChatGPT" — não casa)
ANIME_CTA = (
    "\n\n👉 Segue para mais curiosidades de anime todos os dias!\n"
    "💬 Qual o teu anime favorito? Comenta!\n"
    "🔔 Ativa as notificações para não perder nenhum vídeo."
)


def gpt(prompt, system="És um criador de conteúdo viral em português europeu (PT-PT) e brasileiro (PT-BR neutro), especialista em animes japoneses. Escreves scripts curtos, virais, com hooks fortes, factos surpreendentes e zero spoilers grandes."):
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

Escreve um script de YouTube Shorts em português neutro (que funciona em PT e BR), 100-130 palavras (45-55 segundos lidos).

Estrutura obrigatória:
1. HOOK (5s): pergunta intrigante ou afirmação polémica sobre o anime
2. CORPO (40s): 2-3 factos verificados, lore profunda, ou teoria fundamentada
3. CTA (5s): "Segue para mais curiosidades", "Comenta o teu favorito", "Qual cena te marcou?"

Regras:
- Frases curtas, ritmo rápido, energia alta
- Sem emojis, sem hashtags no script (só texto narrado)
- Sem "olá pessoal", arranca direto ao tema
- NÃO faças spoilers gigantes (do tipo "o protagonista morre")
- Usa nomes japoneses corretos (Tanjiro, Goku, Luffy, etc.)
- Português neutro: nada de "fixe", "estás" ou "moleque"

Devolve APENAS o texto a narrar, sem títulos nem secções."""
    return gpt(prompt)


def gerar_titulo_e_desc(topico, script):
    prompt = f"""Para este YouTube Short sobre anime:

Tópico: {topico}
Script: {script[:300]}...

Gera (JSON válido):
{{
  "titulo": "título com 40-60 chars, chamativo, 1-2 emojis (🔥⚡💀🌸⚔️ funcionam bem em anime)",
  "descricao": "3-4 linhas com hook + breve resumo + 8 hashtags relevantes de anime",
  "tags": ["anime","nome-do-anime","curiosidades","otaku","shonen","manga","animes2026","tag-extra"]
}}

Devolve APENAS o JSON, sem markdown."""
    raw = gpt(prompt, system="És um especialista em SEO YouTube para nicho anime. Devolves sempre JSON válido.")
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"titulo": topico[:60], "descricao": script[:200], "tags": ["anime", "curiosidades", "otaku"]}


def aplicar_cta(meta):
    descricao = (meta.get("descricao") or "").strip()
    if "Segue para mais" not in descricao:
        descricao = f"{descricao}{ANIME_CTA}".strip()
    # Garante hashtags-base de anime
    tags = meta.get("tags") or []
    must_have = ["anime", "curiosidades", "otaku", "manga", "shonen", "animeshorts"]
    for t in must_have:
        if t not in [x.lower() for x in tags]:
            tags.append(t)
    meta["tags"] = tags[:15]
    meta["descricao"] = descricao
    return meta


async def tts(text, out_mp3):
    import edge_tts
    # Voz brasileira (mais energia para anime, audiência maior)
    voice = random.choice(["pt-BR-AntonioNeural", "pt-BR-FranciscaNeural", "pt-PT-DuarteNeural"])
    com = edge_tts.Communicate(text, voice, rate="+10%")
    await com.save(out_mp3)


def gerar_imagem_fundo(topico, slug):
    """Imagem 1024x1792 estilo anime (sem reproduzir personagens registados)."""
    prompt = (
        f"Vertical YouTube Shorts background, anime aesthetic style, generic anime atmosphere "
        f"inspired by the theme '{topico}'. Dynamic anime art style, vibrant colors, "
        f"cinematic lighting, action energy, mysterious vibe. NO TEXT in the image. "
        f"NO copyrighted characters — only generic stylized silhouettes or abstract anime backgrounds. "
        f"9:16 aspect ratio, dramatic composition."
    )
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


def montar_video(audio_mp3, imagem, slug):
    out_mp4 = OUT / f"{slug}.mp4"
    dur_raw = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(audio_mp3)],
        capture_output=True, text=True,
    ).stdout.strip()
    duration = float(dur_raw or "60")

    if imagem:
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(imagem), "-i", str(audio_mp3),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-t", str(duration), "-shortest", str(out_mp4),
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"color=c=0x0a0a14:s=1080x1920:d={duration}",
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
    slug = "anime-" + "".join(c if c.isalnum() else "-" for c in topico.lower())[:46].strip("-")
    timestamp = datetime.now().strftime("%Y%m%d-%H%M")
    slug = f"{timestamp}-{slug}"
    print(f"\n🎌 {topico}")
    print(f"   1/4 Script GPT-4o (anime mode)...", end=" ", flush=True)
    script = gerar_script(topico)
    print(f"✓ ({len(script)} chars)")

    print(f"   2/4 Metadata SEO anime...", end=" ", flush=True)
    meta = gerar_titulo_e_desc(topico, script)
    meta = aplicar_cta(meta)
    print(f"✓ {meta['titulo'][:50]}")

    print(f"   3/4 Áudio TTS...", end=" ", flush=True)
    audio = OUT / f"{slug}.mp3"
    await tts(script, str(audio))
    print(f"✓ {audio.stat().st_size//1024} KB")

    print(f"   4/4 Imagem DALL-E (anime style) + ffmpeg...", end=" ", flush=True)
    imagem = gerar_imagem_fundo(topico, slug)
    video = montar_video(audio, imagem, slug)
    if video:
        print(f"✓ {video.stat().st_size//1024} KB")
    else:
        print("✗"); return

    meta_path = OUT / f"{slug}.json"
    meta_path.write_text(json.dumps({
        "topico": topico,
        "tipo": "anime",
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
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    print(f"🎌 Gerando {n} YouTube Shorts ANIME\n")
    topicos = random.sample(TOPICOS, min(n, len(TOPICOS)))
    for t in topicos:
        try:
            await gerar_video(t)
        except Exception as e:
            print(f"   ❌ Erro: {e}")
    print(f"\n✅ Concluído. Pasta: {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
