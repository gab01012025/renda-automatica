#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYBIN="$ROOT/.venv/bin/python"
[[ ! -x "$PYBIN" ]] && PYBIN="python3"

LOG_FILE="$(ls -1t /tmp/cron-renda-*.log 2>/dev/null | head -n1)"
STATE_DIR="/tmp/auto-recuperacao"
mkdir -p "$STATE_DIR"

COOLDOWN_MINUTES="${AUTO_RECOVERY_COOLDOWN_MINUTES:-90}"
NOW_EPOCH="$(date +%s)"

retry_allowed() {
  local key="$1"
  local f="$STATE_DIR/${key}.last"
  if [[ ! -f "$f" ]]; then
    return 0
  fi
  local last
  last="$(cat "$f" 2>/dev/null || echo 0)"
  local elapsed=$(( NOW_EPOCH - last ))
  local needed=$(( COOLDOWN_MINUTES * 60 ))
  [[ "$elapsed" -ge "$needed" ]]
}

mark_retry() {
  local key="$1"
  printf "%s" "$NOW_EPOCH" > "$STATE_DIR/${key}.last"
}

safe_run() {
  local key="$1"
  shift
  if ! retry_allowed "$key"; then
    echo "↺ Cooldown ativo para $key, sem retry agora"
    return 0
  fi
  echo "🛠️ Retry: $key"
  "$@" || echo "⚠️ Retry falhou: $key"
  mark_retry "$key"
}

# Se não houver log recente, aciona uma rodada completa para evitar buraco de execução.
if [[ -z "$LOG_FILE" ]]; then
  echo "ℹ️ Sem log de cron, acionando execução completa"
  safe_run "full_cron" /bin/bash "$ROOT/scripts/cron-diario.sh"
  exit 0
fi

LOG_MTIME="$(stat -c %Y "$LOG_FILE" 2>/dev/null || echo 0)"
MAX_LOG_AGE_H="${AUTO_RECOVERY_MAX_LOG_AGE_HOURS:-8}"
if [[ "$LOG_MTIME" -gt 0 ]]; then
  age_sec=$(( NOW_EPOCH - LOG_MTIME ))
  if [[ "$age_sec" -gt $(( MAX_LOG_AGE_H * 3600 )) ]]; then
    echo "ℹ️ Log muito antigo (${MAX_LOG_AGE_H}h+), acionando execução completa"
    safe_run "full_cron" /bin/bash "$ROOT/scripts/cron-diario.sh"
  fi
fi

# Verifica os últimos eventos do log para retries direcionados.
TAIL="$(tail -n 250 "$LOG_FILE" 2>/dev/null || true)"

if echo "$TAIL" | grep -qi "short falhou"; then
  safe_run "youtube_short" /bin/bash -lc "cd '$ROOT' && '$PYBIN' youtube-faceless/auto-shorts.py 1"
fi

if echo "$TAIL" | grep -qi "TikTok falhou"; then
  safe_run "tiktok" /bin/bash -lc "cd '$ROOT/tiktok-auto' && '$PYBIN' tiktok-auto-post.py 1"
fi

safe_run "tiktok_diario" /bin/bash "$ROOT/scripts/garantir-tiktok-diario.sh"

if echo "$TAIL" | grep -Eqi "pins falhou|auto-post Pinterest falhou"; then
  safe_run "pinterest" /bin/bash -lc "cd '$ROOT/pod-automatico/pinterest' && '$PYBIN' pinterest-auto-post.py 1"
fi

if echo "$TAIL" | grep -qi "métricas falhou"; then
  safe_run "metricas" /bin/bash -lc "cd '$ROOT' && '$PYBIN' scripts/metricas-diarias.py"
fi

if echo "$TAIL" | grep -qi "crosspost skip"; then
  safe_run "crosspost" /bin/bash -lc "cd '$ROOT' && node cross-post/cross-post.mjs"
fi

echo "✅ Auto-recuperação concluída"
