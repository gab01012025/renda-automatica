#!/usr/bin/env python3
"""
YouTube Shorts — Pipeline completa (gerar + upload).

Uso:
  python auto-shorts.py [N]   # default 1
"""
import asyncio, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
N = int(sys.argv[1]) if len(sys.argv) > 1 else 1

print(f"🎬 Pipeline YouTube Shorts ({N} vídeo{'s' if N > 1 else ''})\n")

# 1. Gera N vídeos novos
print("─── 1/2  Gerar vídeos ───")
r = subprocess.run([PYTHON, str(ROOT / "gerar-video.py"), str(N)], cwd=str(ROOT))
if r.returncode != 0:
    print("❌ Geração falhou")
    sys.exit(1)

# 2. Upload N pendentes
print("\n─── 2/2  Upload YouTube ───")
r = subprocess.run([PYTHON, str(ROOT / "upload-youtube.py"), "--pending", str(N)], cwd=str(ROOT))
sys.exit(r.returncode)
