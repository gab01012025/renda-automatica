#!/usr/bin/env bash
# 💰 BOOST MANUAL — força ciclo completo POD agora (gerar→upload→pin)
# Uso: bash scripts/boost-pod-now.sh [N=3]
# Roda em background, output em /tmp/boost-pod-$(date).log
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
N="${1:-3}"
LOG="/tmp/boost-pod-$(date +%Y-%m-%d-%H%M).log"
NICHOS=("retro-sunset-en" "vintage-animal-en" "halloween-spooky-en" "christmas-funny-en" "mental-health-en" "deutsch-spruche")

echo "💰 BOOST POD — gerar $N designs × 6 nichos = $((N*6)) designs novos"
echo "📝 Log: $LOG"
echo ""

(
  echo "=== START $(date) ==="
  cd "$ROOT/pod-automatico/gerador-designs"
  for n in "${NICHOS[@]}"; do
    echo ""
    echo "━━━ GERAR $n ($N designs) ━━━"
    node gerar.mjs "$n" "$N" 2>&1 || echo "⚠ gerar $n falhou"
  done

  cd "$ROOT/pod-automatico/uploader-printify"
  for n in "${NICHOS[@]}"; do
    pendentes=$(ls "$ROOT/pod-automatico/designs/$n"/*.png 2>/dev/null | wc -l)
    if [[ "$pendentes" -gt 0 ]]; then
      echo ""
      echo "━━━ UPLOAD $n ($pendentes designs) ━━━"
      node upload.mjs "$n" 2>&1 || echo "⚠ upload $n falhou"
    fi
  done

  cd "$ROOT"
  echo ""
  echo "━━━ PINTEREST PINS ━━━"
  PYBIN=$(command -v python3)
  "$PYBIN" pod-automatico/pinterest/gerar-pins.py 2>&1 || echo "⚠ pins falharam"

  echo ""
  echo "=== END $(date) ==="
) > "$LOG" 2>&1 &

PID=$!
echo "✅ Boost a correr em background (PID=$PID)"
echo "   Acompanhar:  tail -f $LOG"
echo "   Status:      ps -p $PID && echo VIVO || echo TERMINADO"
