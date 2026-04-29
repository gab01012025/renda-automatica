#!/usr/bin/env bash
# Health-check diário — corre 1x/dia, escreve resumo em /tmp/health-renda-YYYY-MM-DD.txt
# Avisa se: OpenAI sem créditos, sessões expiradas, contas suspensas, módulos a falhar
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
DATE=$(date +%Y-%m-%d)
OUT="/tmp/health-renda-$DATE.txt"

{
  echo "════════════════════════════════════════"
  echo "🩺 HEALTH CHECK — $DATE $(date +%H:%M)"
  echo "════════════════════════════════════════"

  # 1) Cron ativo?
  echo ""
  echo "[1] CRON"
  if crontab -l 2>/dev/null | grep -q "piloto-automatico"; then
    echo "  ✅ Cron AUTOPILOT ativo"
  else
    echo "  ❌ CRON NÃO INSTALADO — correr: bash scripts/piloto-automatico.sh --install"
  fi

  # 2) Logs hoje
  echo ""
  echo "[2] LOGS HOJE"
  for tipo in cron-renda cron-renda-recovery; do
    f="/tmp/${tipo}-${DATE}.log"
    if [[ -f "$f" ]]; then
      lines=$(wc -l < "$f")
      err=$(grep -cE "❌|FAIL|Error " "$f" 2>/dev/null)
      err=${err:-0}
      echo "  📄 $tipo: $lines linhas, $err erros"
    else
      echo "  ⚠ $tipo: SEM LOG hoje"
    fi
  done

  # 3) OpenAI quota
  echo ""
  echo "[3] OPENAI"
  today_log="/tmp/cron-renda-${DATE}.log"
  if [[ -f "$today_log" ]] && grep -q "insufficient_quota" "$today_log" 2>/dev/null; then
    echo "  ❌ QUOTA ESGOTADA hoje — recarregar em https://platform.openai.com/settings/organization/billing"
  else
    echo "  ✅ OK (sem erros hoje)"
  fi

  # 4) YouTube
  echo ""
  echo "[4] YOUTUBE"
  if [[ -f "$today_log" ]] && grep -q "uploadLimitExceeded" "$today_log" 2>/dev/null; then
    echo "  ⚠ LIMITE DIÁRIO atingido hoje (normal, reseta em 24h)"
  else
    echo "  ✅ OK"
  fi

  # 5) TikTok
  echo ""
  echo "[5] TIKTOK"
  tt_cookies="$HOME/.cache/tiktok-chrome-profile/Default/Cookies"
  if [[ -f "$tt_cookies" ]]; then
    age_days=$(( ($(date +%s) - $(stat -c %Y "$tt_cookies")) / 86400 ))
    if [[ "$age_days" -lt 14 ]]; then
      echo "  ✅ Sessão OK (atualizada há ${age_days}d)"
    else
      echo "  ⚠ Sessão antiga (${age_days}d) — talvez expire em breve"
    fi
  else
    echo "  ❌ SEM SESSÃO — correr: cd tiktok-auto && python tiktok-auto-post.py --login"
  fi

  # 6) Pinterest
  echo ""
  echo "[6] PINTEREST"
  pin_cookies="$HOME/.cache/pinterest-chrome-profile/Default/Cookies"
  if [[ -f "$pin_cookies" ]]; then
    age_days=$(( ($(date +%s) - $(stat -c %Y "$pin_cookies")) / 86400 ))
    if [[ "$age_days" -lt 14 ]]; then
      echo "  ✅ Sessão OK (atualizada há ${age_days}d)"
    else
      echo "  ⚠ Sessão antiga (${age_days}d) — talvez expire em breve"
    fi
  else
    echo "  ❌ SEM SESSÃO — correr: python pod-automatico/pinterest/pinterest-auto-post.py --login"
  fi

  # 7) Printify
  echo ""
  echo "[7] PRINTIFY"
  err500=$(grep -hE "Printify.*500|Internal Server Error" /tmp/cron-renda-*.log 2>/dev/null | wc -l)
  err400=$(grep -hE "Printify.*400|Validation failed" /tmp/cron-renda-*.log 2>/dev/null | wc -l)
  echo "  📊 erros 500 (transientes): $err500 | erros 400 (validação): $err400"
  if [[ "${err400:-0}" -gt 5 ]]; then
    echo "  ⚠ MUITOS erros 400 — investigar payload"
  fi

  # 8) Afiliados ativos
  echo ""
  echo "[8] AFILIADOS"
  env_file="$ROOT/afiliados-ia/.env"
  for var in SHOPEE_AFF_ID ML_AFF_TAG ALIEXPRESS_AFF_ID HOTMART_AFF_ID AMZ_TAG_DE; do
    val=$(grep "^$var=" "$env_file" 2>/dev/null | cut -d= -f2)
    if [[ -n "$val" && "$val" != "XXXXX" ]]; then
      echo "  ✅ $var configurado"
    else
      echo "  ⚠ $var VAZIO"
    fi
  done

  # 9) SMTP cold-email
  echo ""
  echo "[9] COLD EMAIL"
  smtp_user=$(grep -h "^SMTP_USER=" "$ROOT/cold-email-pt/.env" "$ROOT/.env" 2>/dev/null | head -1 | cut -d= -f2)
  smtp_pass=$(grep -h "^SMTP_PASS=" "$ROOT/cold-email-pt/.env" "$ROOT/.env" 2>/dev/null | head -1 | cut -d= -f2)
  if [[ -n "$smtp_user" && -n "$smtp_pass" ]]; then
    echo "  ✅ SMTP configurado ($smtp_user)"
  else
    echo "  ⚠ SMTP DRY-RUN — adicionar SMTP_USER/SMTP_PASS a cold-email-pt/.env"
  fi

  # 10) Inventário
  echo ""
  echo "[10] INVENTÁRIO POD"
  for n in retro-sunset-en vintage-animal-en halloween-spooky-en christmas-funny-en mental-health-en deutsch-spruche; do
    pend=$(ls "$ROOT/pod-automatico/designs/$n/"*.png 2>/dev/null | wc -l)
    feitos=$(ls "$ROOT/pod-automatico/designs/$n/feitos/"*.png 2>/dev/null | wc -l)
    echo "  📦 $n: $pend pendentes, $feitos publicados"
  done

  echo ""
  echo "════════════════════════════════════════"
  echo "Resumo guardado em: $OUT"
} | tee "$OUT"
