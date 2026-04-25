#!/usr/bin/env bash
# Piloto automático total (instalação única)
# Uso:
#   bash scripts/piloto-automatico.sh --install
#   bash scripts/piloto-automatico.sh --status
#   bash scripts/piloto-automatico.sh --run-now
#   bash scripts/piloto-automatico.sh --uninstall

set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOCK_FILE="/tmp/piloto-automatico.lock"

run_main() {
  if command -v flock >/dev/null 2>&1; then
    flock -n "$LOCK_FILE" /bin/bash "$ROOT/scripts/cron-diario.sh"
  else
    /bin/bash "$ROOT/scripts/cron-diario.sh"
  fi
}

run_recovery() {
  if command -v flock >/dev/null 2>&1; then
    flock -n "$LOCK_FILE" /bin/bash "$ROOT/scripts/auto-recuperacao.sh"
  else
    /bin/bash "$ROOT/scripts/auto-recuperacao.sh"
  fi
}

install_cron() {
  local main_line="0 3,11,19 * * * /bin/bash '$ROOT/scripts/piloto-automatico.sh' --run-main >> /tmp/cron-renda-\$(date +\%Y-\%m-\%d).log 2>&1 # AUTOPILOT_MAIN"
  local recovery_line="*/30 * * * * /bin/bash '$ROOT/scripts/piloto-automatico.sh' --run-recovery >> /tmp/cron-renda-recovery-\$(date +\%Y-\%m-\%d).log 2>&1 # AUTOPILOT_RECOVERY"
  local heartbeat_line="55 23 * * * /bin/bash '$ROOT/scripts/piloto-automatico.sh' --heartbeat >> /tmp/cron-renda-heartbeat-\$(date +\%Y-\%m-\%d).log 2>&1 # AUTOPILOT_HEARTBEAT"

  ( crontab -l 2>/dev/null \
    | grep -v 'AUTOPILOT_MAIN' \
    | grep -v 'AUTOPILOT_RECOVERY' \
    | grep -v 'AUTOPILOT_HEARTBEAT' \
    | grep -v 'cron-diario.sh' \
    ; echo "$main_line"; echo "$recovery_line"; echo "$heartbeat_line" ) | crontab -

  echo "✅ Piloto automático instalado"
}

print_status() {
  echo "=== STATUS PILOTO AUTOMATICO ==="
  echo "Root: $ROOT"
  echo ""
  echo "Crontab ativo:"
  crontab -l 2>/dev/null | grep -E 'AUTOPILOT_|cron-diario.sh' || echo "(nenhuma entrada)"
  echo ""
  echo "Últimos logs principais:"
  ls -lht /tmp/cron-renda-*.log 2>/dev/null | head -5 || true
  echo ""
  echo "Últimos logs recovery:"
  ls -lht /tmp/cron-renda-recovery-*.log 2>/dev/null | head -5 || true
  echo ""
  echo "Últimos logs heartbeat:"
  ls -lht /tmp/cron-renda-heartbeat-*.log 2>/dev/null | head -5 || true
}

heartbeat() {
  local latest="$ROOT/scripts/relatorios/metricas-latest.json"
  if [[ -f "$latest" ]]; then
    echo "💓 Heartbeat $(date '+%Y-%m-%d %H:%M')"
    grep -E 'youtube_uploads_24h|tiktok_uploads_24h|sales_24h|revenue_24h_eur|total_clicks_24h|overall' "$latest" || true
  else
    echo "⚠️ Heartbeat: relatório não encontrado, gerando agora"
    local pybin="$ROOT/.venv/bin/python"
    [[ ! -x "$pybin" ]] && pybin="python3"
    "$pybin" "$ROOT/scripts/metricas-diarias.py" || true
  fi
}

case "${1:-}" in
  --install)
    install_cron
    /bin/bash "$ROOT/scripts/piloto-automatico.sh" --run-now
    print_status
    ;;
  --uninstall)
    crontab -l 2>/dev/null \
      | grep -v 'AUTOPILOT_MAIN' \
      | grep -v 'AUTOPILOT_RECOVERY' \
      | grep -v 'AUTOPILOT_HEARTBEAT' \
      | crontab -
    echo "✅ Piloto automático removido"
    ;;
  --status)
    print_status
    ;;
  --run-main)
    run_main
    ;;
  --run-recovery)
    run_recovery
    ;;
  --heartbeat)
    heartbeat
    ;;
  --run-now)
    run_main
    run_recovery
    heartbeat
    ;;
  *)
    echo "Uso: bash scripts/piloto-automatico.sh [--install|--uninstall|--status|--run-now]"
    exit 1
    ;;
esac
