#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYBIN="$ROOT/.venv/bin/python"
[[ ! -x "$PYBIN" ]] && PYBIN="python3"

MIN_DAILY="${TIKTOK_MIN_DAILY:-3}"
MAX_BURST="${TIKTOK_MAX_BURST_PER_RUN:-2}"
VIDEOS_DIR="$ROOT/youtube-faceless/videos"
STATE_FILE="$ROOT/tiktok-auto/_uploaded.json"
TODAY="$(date +%Y-%m-%d)"

count_today() {
  "$PYBIN" - <<'PY'
import json
from pathlib import Path
from datetime import datetime
path = Path('tiktok-auto/_uploaded.json')
if not path.exists():
    print(0)
    raise SystemExit
try:
    data = json.loads(path.read_text()).get('videos', [])
except Exception:
    print(0)
    raise SystemExit
prefix = datetime.now().strftime('%Y-%m-%d')
print(sum(1 for item in data if str(item.get('ts','')).startswith(prefix)))
PY
}

count_pending() {
  "$PYBIN" - <<'PY'
import json
from pathlib import Path
videos = sorted(Path('youtube-faceless/videos').glob('*.mp4'))
state_path = Path('tiktok-auto/_uploaded.json')
done = set()
if state_path.exists():
    try:
        done = {item.get('file') for item in json.loads(state_path.read_text()).get('videos', [])}
    except Exception:
        done = set()
print(sum(1 for video in videos if video.name not in done))
PY
}

ensure_supply() {
  local pending="$1"
  if [[ "$pending" -gt 0 ]]; then
    return 0
  fi
  echo "🎬 Sem vídeos pendentes para TikTok; gerando 1 short extra"
  (cd "$ROOT" && "$PYBIN" youtube-faceless/auto-shorts.py 1) || echo "⚠️ Falhou ao gerar short extra para TikTok"
}

posted_today="$(count_today)"
pending_before="$(count_pending)"

echo "📊 TikTok hoje: ${posted_today}/${MIN_DAILY} | pendentes=${pending_before}"

if [[ "$posted_today" -ge "$MIN_DAILY" ]]; then
  echo "✅ Meta diária do TikTok já cumprida"
  exit 0
fi

ensure_supply "$pending_before"
pending_after_supply="$(count_pending)"
if [[ "$pending_after_supply" -le 0 ]]; then
  echo "⚠️ Ainda sem vídeos pendentes após tentativa de geração"
  exit 0
fi

needed=$(( MIN_DAILY - posted_today ))
if [[ "$needed" -gt "$MAX_BURST" ]]; then
  needed="$MAX_BURST"
fi
if [[ "$needed" -gt "$pending_after_supply" ]]; then
  needed="$pending_after_supply"
fi

if [[ "$needed" -le 0 ]]; then
  echo "✅ Nada a publicar agora"
  exit 0
fi

echo "🚀 Forçando publicação TikTok: ${needed} vídeo(s)"
(cd "$ROOT/tiktok-auto" && "$PYBIN" tiktok-auto-post.py "$needed") || echo "⚠️ Publicação TikTok via guardião falhou"

posted_today_after="$(count_today)"
pending_after="$(count_pending)"
echo "📈 TikTok após guardião: ${posted_today_after}/${MIN_DAILY} | pendentes=${pending_after}"
