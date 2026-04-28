#!/usr/bin/env python3
"""
Pipeline ANIME: gera N vídeos curiosidades de anime + faz upload no YouTube.
Usa o mesmo token.json (mesmo canal por agora — podes split depois).
"""
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
N = int(sys.argv[1]) if len(sys.argv) > 1 else 2

print(f"🎌 Pipeline ANIME ({N} vídeo{'s' if N > 1 else ''})\n")

print("─── 1/2  Gerar vídeos anime ───")
r = subprocess.run([PYTHON, str(ROOT / "gerar-video-anime.py"), str(N)], cwd=str(ROOT))
if r.returncode != 0:
    print("❌ Geração anime falhou"); sys.exit(1)

print("\n─── 2/2  Upload YouTube ───")
r = subprocess.run([PYTHON, str(ROOT / "upload-youtube.py"), "--pending", str(N)], cwd=str(ROOT))
sys.exit(r.returncode)
