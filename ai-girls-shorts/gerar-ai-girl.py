#!/usr/bin/env python3
"""
AI-Girls Shorts — Pipeline 100% GRÁTIS para vídeos virais TikTok/YouTube.

Estilo: thirst-trap / motivacional / POV — formato que viraliza em 2026.

Stack:
  1. Pollinations.ai Flux (imagem hiper-realista mulher AI) — GRÁTIS
  2. edge-tts (voz feminina jovem PT-BR) — GRÁTIS
  3. ffmpeg Ken Burns (zoom/pan dinâmico) + legendas burned-in
  4. Output 1080x1920 9:16 pronto para TikTok + YouTube Shorts

Uso:
  python gerar-ai-girl.py [N=1]    # gera N vídeos
"""
import os, sys, json, random, asyncio, subprocess, urllib.request, urllib.parse, hashlib, time
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "videos"
OUT.mkdir(exist_ok=True)
TMP = ROOT / "_tmp"
TMP.mkdir(exist_ok=True)

# ─────────── CHARACTERS (consistência via seed Pollinations) ───────────
# Cada character = mesma seed → mesma "pessoa" entre frames
CHARACTERS = [
    {
        "name": "Sofia",
        "seed": 42001,
        "base": "ultra realistic photo portrait, beautiful 23 year old brunette woman with long wavy hair, hazel eyes, natural makeup, soft smile, warm golden hour lighting, instagram aesthetic, shallow depth of field, 85mm lens, photorealistic, hyperrealistic skin texture",
    },
    {
        "name": "Luna",
        "seed": 42002,
        "base": "ultra realistic photo portrait, stunning 22 year old blonde woman with straight long hair, blue eyes, soft natural makeup, gentle smile, dreamy sunset lighting, beach background bokeh, instagram model aesthetic, photorealistic, hyperrealistic",
    },
    {
        "name": "Maya",
        "seed": 42003,
        "base": "ultra realistic photo portrait, gorgeous 24 year old latina woman with wavy chestnut hair, brown eyes, soft glam makeup, confident smile, warm sunset lighting, tropical greenery background, instagram aesthetic, 85mm lens, photorealistic",
    },
    {
        "name": "Aria",
        "seed": 42004,
        "base": "ultra realistic photo portrait, beautiful 23 year old asian woman with long black hair, soft brown eyes, minimal makeup, sweet smile, soft window lighting, cozy indoor setting bokeh background, instagram aesthetic, photorealistic, hyperrealistic skin",
    },
    {
        "name": "Julia",
        "seed": 42005,
        "base": "ultra realistic photo portrait, beautiful 22 year old brazilian woman with long curly dark hair, brown eyes, glowing tan skin, soft smile, golden hour beach lighting, palm tree bokeh background, instagram aesthetic, photorealistic, hyperrealistic",
    },
]

# ─────────── SCENES (variações de pose para mesmo character) ───────────
SCENES = [
    "looking directly at camera with soft smile, neutral background bokeh",
    "looking slightly to the side, hair gently moving, soft natural light",
    "smiling warmly, head tilted slightly, dreamy bokeh background",
    "soft gaze towards camera, gentle expression, golden hour glow",
    "looking up dreamily, soft lips, warm sunset lighting",
    "side profile portrait, hair flowing, soft warm light",
]

# ─────────── SCRIPTS POR FORMATO (PT-BR viral 2026) ───────────
SCRIPTS = [
    # Motivacional feminino
    {"tema": "motivacional", "voz_genero": "F", "linhas": [
        "Você não precisa ser perfeita.",
        "Você só precisa ser você.",
        "E isso já é mais do que suficiente.",
        "Lembre-se disso hoje.",
    ]},
    {"tema": "motivacional", "voz_genero": "F", "linhas": [
        "Tem dia que parece que nada vai dar certo.",
        "Mas você ainda está aqui.",
        "Isso já é uma vitória.",
        "Continue.",
    ]},
    {"tema": "motivacional", "voz_genero": "F", "linhas": [
        "Pare de pedir desculpa por existir.",
        "Pare de se diminuir.",
        "Você nasceu pra brilhar.",
        "Lembra disso.",
    ]},
    # POV / sedução leve
    {"tema": "pov", "voz_genero": "F", "linhas": [
        "POV: ela percebeu que merece mais.",
        "Mais respeito.",
        "Mais carinho.",
        "Mais de tudo.",
    ]},
    {"tema": "pov", "voz_genero": "F", "linhas": [
        "POV: você finalmente parou de aceitar pouco.",
        "E o universo te respondeu.",
        "Veio em dobro.",
        "Veja só.",
    ]},
    # Reflexões relacionamento
    {"tema": "reflexao", "voz_genero": "F", "linhas": [
        "Quem te ama de verdade não te faz duvidar.",
        "Não te faz esperar.",
        "Não te faz se sentir pouco.",
        "Pensa nisso.",
    ]},
    {"tema": "reflexao", "voz_genero": "F", "linhas": [
        "Cura é quando você lembra dele e não dói mais.",
        "Quando o nome dele é só uma palavra.",
        "Esse dia chega.",
        "Confia.",
    ]},
    # Mindset
    {"tema": "mindset", "voz_genero": "F", "linhas": [
        "Sua vida muda quando você muda.",
        "Quando você para de esperar.",
        "Quando você começa a fazer.",
        "Hoje é o dia.",
    ]},
    {"tema": "mindset", "voz_genero": "F", "linhas": [
        "Energia atrai energia.",
        "Suba sua frequência.",
        "Cuide de você primeiro.",
        "O resto vem.",
    ]},
    # Dicas curtas
    {"tema": "dica", "voz_genero": "F", "linhas": [
        "Três coisas que mudam sua vida em trinta dias.",
        "Acordar mais cedo.",
        "Beber mais água.",
        "Sair menos com quem te suga.",
    ]},
]

VOICES_F = ["pt-BR-FranciscaNeural", "pt-BR-ThalitaNeural"]

# ─────────── helper ───────────
def carregar_env():
    for envf in [ROOT / ".env", ROOT.parent / ".env",
                 ROOT.parent / "youtube-faceless" / ".env"]:
        if envf.exists():
            for line in envf.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

carregar_env()

def gerar_imagem_pollinations(prompt, seed, out_path, w=1080, h=1920):
    """Pollinations Flux — grátis ilimitado."""
    enc = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{enc}?width={w}&height={h}&model=flux&nologo=true&seed={seed}"
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
                if len(data) > 5000:
                    out_path.write_bytes(data)
                    return True
        except Exception as e:
            wait = 8 * (attempt + 1)
            print(f"   ⏳ Pollinations retry em {wait}s ({e.__class__.__name__})", flush=True)
            time.sleep(wait)
    return False

async def gerar_audio(text, out_mp3, voice):
    import edge_tts
    com = edge_tts.Communicate(text, voice, rate="-5%", pitch="+2Hz")
    await com.save(str(out_mp3))

def get_audio_duration(mp3_path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_path)],
        capture_output=True, text=True
    )
    try:
        return float(r.stdout.strip())
    except Exception:
        return 8.0

def montar_video(imagens, audio_mp3, legendas, out_mp4):
    """
    ffmpeg: várias imagens com Ken Burns (zoom in/out lento) + crossfade,
    audio overlay, legendas burned-in (drawtext) sincronizadas.
    """
    duracao_total = get_audio_duration(audio_mp3)
    n = len(imagens)
    dur_por = duracao_total / n + 0.3   # leve overlap para crossfade

    # 1) cada imagem → clip MP4 com Ken Burns
    clips = []
    for i, img in enumerate(imagens):
        clip = TMP / f"clip_{i}_{int(time.time())}.mp4"
        # zoompan effect — zoom suave de 1.0 → 1.15 ao longo da duração
        # 30 fps, 1080x1920
        fps = 30
        frames = int(dur_por * fps)
        zoom_expr = f"zoom+0.0008"   # zoom incremental por frame
        zoompan = (
            f"scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='min({zoom_expr},1.18)':d={frames}:s=1080x1920:fps={fps}"
        )
        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(img),
            "-vf", zoompan,
            "-t", f"{dur_por:.3f}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
            "-r", str(fps),
            str(clip),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"   ⚠️  clip {i} falhou: {r.stderr[-200:]}")
            return False
        clips.append(clip)

    # 2) concatenar clips (sem crossfade para simplicidade — rápido)
    list_file = TMP / f"list_{int(time.time())}.txt"
    list_file.write_text("\n".join(f"file '{c.absolute()}'" for c in clips))

    video_sem_audio = TMP / f"sem_audio_{int(time.time())}.mp4"
    cmd_concat = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(video_sem_audio),
    ]
    r = subprocess.run(cmd_concat, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"   ⚠️  concat falhou: {r.stderr[-300:]}")
        return False

    # 3) construir filter drawtext para legendas sincronizadas
    n_leg = len(legendas)
    seg = duracao_total / n_leg
    # Escapar caracteres especiais ffmpeg
    def esc(s):
        return s.replace("\\", "\\\\").replace("'", "\u2019").replace(":", "\\:").replace(",", "\\,")
    drawtexts = []
    for i, leg in enumerate(legendas):
        start = i * seg
        end = (i + 1) * seg
        txt = esc(leg)
        drawtexts.append(
            f"drawtext=text='{txt}':"
            f"fontsize=64:fontcolor=white:borderw=4:bordercolor=black:"
            f"x=(w-text_w)/2:y=h-h/3:"
            f"enable='between(t,{start:.2f},{end:.2f})'"
        )
    vf_legendas = ",".join(drawtexts)

    # 4) juntar audio + legendas burned-in
    cmd_final = [
        "ffmpeg", "-y", "-i", str(video_sem_audio), "-i", str(audio_mp3),
        "-vf", vf_legendas,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        str(out_mp4),
    ]
    r = subprocess.run(cmd_final, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"   ⚠️  final falhou: {r.stderr[-400:]}")
        return False

    # cleanup
    for c in clips:
        try: c.unlink()
        except: pass
    try: video_sem_audio.unlink(); list_file.unlink()
    except: pass

    return True

# ─────────── main ───────────
async def gerar_um_video(idx):
    char = random.choice(CHARACTERS)
    script = random.choice(SCRIPTS)
    voice = random.choice(VOICES_F)
    n_frames = len(script["linhas"])

    ts = int(time.time()) + idx
    print(f"\n🎬 [{idx+1}] {char['name']} ({script['tema']}) — voz: {voice}")

    # 1) gerar N imagens da mesma personagem (mesma seed, scenes diferentes)
    imagens = []
    scenes = random.sample(SCENES, min(n_frames, len(SCENES)))
    for i, scene in enumerate(scenes):
        prompt = f"{char['base']}, {scene}"
        img = TMP / f"img_{ts}_{i}.png"
        print(f"   📸 frame {i+1}/{n_frames}...", end=" ", flush=True)
        ok = gerar_imagem_pollinations(prompt, char["seed"] + i * 7, img)
        if not ok:
            print("FALHOU")
            return None
        print("OK")
        imagens.append(img)

    # 2) gerar audio
    print(f"   🎤 TTS edge-tts...", end=" ", flush=True)
    texto = " ".join(script["linhas"])
    audio = TMP / f"audio_{ts}.mp3"
    await gerar_audio(texto, audio, voice)
    print("OK")

    # 3) montar video
    print(f"   🎞️  Montagem ffmpeg...", end=" ", flush=True)
    out_mp4 = OUT / f"ai-girl-{char['name'].lower()}-{script['tema']}-{ts}.mp4"
    ok = montar_video(imagens, audio, script["linhas"], out_mp4)
    if not ok:
        print("FALHOU")
        return None
    print("OK")

    # 4) cleanup imagens tmp
    for img in imagens:
        try: img.unlink()
        except: pass
    try: audio.unlink()
    except: pass

    # 5) metadata para upload
    meta = {
        "video": str(out_mp4),
        "titulo": gerar_titulo(script["tema"]),
        "descricao": gerar_descricao(script),
        "tags": gerar_tags(script["tema"]),
        "tema": script["tema"],
        "character": char["name"],
        "criado": datetime.now().isoformat(),
    }
    meta_file = out_mp4.with_suffix(".json")
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    print(f"   ✅ {out_mp4.name}  ({out_mp4.stat().st_size//1024} KB)")
    return out_mp4

def gerar_titulo(tema):
    titulos = {
        "motivacional": ["Você precisava ouvir isso", "Lembrete pra você hoje", "Pare e leia isso", "Era pra você ver isso hoje"],
        "pov": ["POV: você merece mais", "POV: o universo te ouviu", "POV: era hora", "POV: ela acordou"],
        "reflexao": ["Pensa nisso hoje", "Era pra você ler isso", "Deixa marinar", "Reflita sobre isso"],
        "mindset": ["Mindset que muda tudo", "Lê isso 3 vezes", "A virada está aqui", "Energia que atrai"],
        "dica": ["Faz isso por 30 dias", "Mude sua vida assim", "Truque que mudou minha vida", "3 coisas pra hoje"],
    }
    return random.choice(titulos.get(tema, ["Veja isso"])) + " 💫 #shorts"

def gerar_descricao(script):
    return (
        " ".join(script["linhas"]) + "\n\n"
        "Te ajudou? Salve, compartilhe e siga pra mais 💕\n\n"
        f"#shorts #motivacional #{script['tema']} #fy #foryou #viral"
    )

def gerar_tags(tema):
    base = ["shorts", "viral", "fy", "foryou", "motivacional", "feminino", "mulher"]
    extra = {
        "motivacional": ["motivacao", "mindset", "autoestima"],
        "pov": ["pov", "ela", "girlsthatglow"],
        "reflexao": ["reflexao", "amorproprio", "cura"],
        "mindset": ["mindset", "lei", "atracao"],
        "dica": ["dica", "rotina", "habitos"],
    }.get(tema, [])
    return base + extra

async def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"🎬 AI-Girls Shorts — vou gerar {n} vídeo(s)\n")
    sucessos = []
    for i in range(n):
        try:
            v = await gerar_um_video(i)
            if v: sucessos.append(v)
        except Exception as e:
            print(f"   ❌ erro: {e}")
    print(f"\n✅ {len(sucessos)}/{n} vídeo(s) gerado(s) em {OUT}")
    return 0 if sucessos else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
