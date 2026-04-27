#!/usr/bin/env bash
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYBIN="$ROOT/.venv/bin/python"
[[ ! -x "$PYBIN" ]] && PYBIN="python3"

TRACKER="$ROOT/kdp-ebooks/kdp-pronto-upload/_lote-status.json"

if [[ ! -f "$TRACKER" ]]; then
  echo "❌ Tracker KDP não encontrado: $TRACKER"
  exit 1
fi

cd "$ROOT"
TARGET="$("$PYBIN" - <<'PY'
import json
from pathlib import Path
tracker = Path('kdp-ebooks/kdp-pronto-upload/_lote-status.json')
data = json.loads(tracker.read_text())
priority = ['blocked_limit', 'blocked_account', 'ready', 'uploading']
for st in priority:
    for b in sorted(data.get('books', []), key=lambda x: x.get('rank', 999)):
        if b.get('status') == st:
            print(b['id'])
            raise SystemExit(0)
print('')
PY
)"

if [[ -z "$TARGET" ]]; then
  echo "ℹ️ Nenhum livro elegível para tentativa KDP hoje."
  exit 0
fi

echo "🎯 Tentativa KDP diária: $TARGET"
"$PYBIN" "$ROOT/kdp-ebooks/atualizar-lote-kdp.py" "$TARGET" uploading >/dev/null 2>&1 || true

LOG_FILE="/tmp/kdp-tentativa-$(date +%Y-%m-%d)-$TARGET.log"

if command -v timeout >/dev/null 2>&1; then
  timeout 2700 "$PYBIN" -u "$ROOT/kdp-ebooks/kdp-auto-upload.py" "$TARGET" 2>&1 | tee "$LOG_FILE"
  RC=${PIPESTATUS[0]}
else
  "$PYBIN" -u "$ROOT/kdp-ebooks/kdp-auto-upload.py" "$TARGET" 2>&1 | tee "$LOG_FILE"
  RC=${PIPESTATUS[0]}
fi

if grep -qi "Clique de publicacao executado" "$LOG_FILE"; then
  "$PYBIN" "$ROOT/kdp-ebooks/atualizar-lote-kdp.py" "$TARGET" in_review >/dev/null 2>&1 || true
  echo "✅ $TARGET marcado como in_review"
  exit 0
fi

if grep -Eqi "Limite de criação de livros excedido|limite de livros" "$LOG_FILE"; then
  "$PYBIN" "$ROOT/kdp-ebooks/atualizar-lote-kdp.py" "$TARGET" blocked_limit >/dev/null 2>&1 || true
  echo "⚠️ $TARGET bloqueado por limite KDP"
  exit 0
fi

if grep -Eqi "Informações de conta incompletas|Ainda estamos configurando sua conta" "$LOG_FILE"; then
  "$PYBIN" "$ROOT/kdp-ebooks/atualizar-lote-kdp.py" "$TARGET" blocked_account >/dev/null 2>&1 || true
  echo "⚠️ $TARGET bloqueado por conta KDP"
  exit 0
fi

if [[ "$RC" -eq 124 ]]; then
  echo "⏱️ Tentativa KDP excedeu tempo limite (45 min)."
  exit 0
fi

if [[ "$RC" -ne 0 ]]; then
  echo "⚠️ Tentativa KDP terminou com erro (rc=$RC). Mantido status uploading."
fi

exit 0
