#!/usr/bin/env bash
# Garante que pelo menos POD_MIN_DAILY designs foram gerados+enviados ao Printify hoje.
# Se ficou abaixo, gera mais nichos rotativos até atingir a meta.
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

for envf in "$ROOT/produtos-digitais/.env" "$ROOT/pod-automatico/.env" "$ROOT/.env"; do
  [[ -f "$envf" ]] && set -a && source "$envf" && set +a
done

POD_MIN_DAILY="${POD_MIN_DAILY:-6}"
POD_DESIGNS_PER_NICHO="${POD_DESIGNS_PER_NICHO:-5}"
POD_MAX_BURST="${POD_MAX_BURST_PER_RUN:-3}"

NICHOS=("funny-puns-en" "vintage-retro-en" "cottagecore-botanical-en" "profession-humor-en" "y2k-nostalgia-en" "deutsch-spruche")

# Conta designs criados hoje em todos os feitos/
TODAY_GLOB="$(date +%Y-%m-%d)"
COUNT=0
while IFS= read -r f; do COUNT=$((COUNT+1)); done < <(find pod-automatico/designs -type f -name '*.png' -newermt "$TODAY_GLOB 00:00" 2>/dev/null)

PEND=$((POD_MIN_DAILY - COUNT))
echo "📊 POD hoje: $COUNT/$POD_MIN_DAILY designs"

if (( PEND <= 0 )); then
  echo "✅ Meta diária POD já cumprida"
  exit 0
fi

DIA=$(date +%d)
TOTAL=${#NICHOS[@]}
RUNS=0
# Cada run gera POD_DESIGNS_PER_NICHO; capamos por POD_MAX_BURST nichos
while (( PEND > 0 )) && (( RUNS < POD_MAX_BURST )); do
  IDX=$(( (10#$DIA + RUNS + COUNT) % TOTAL ))
  NICHO="${NICHOS[$IDX]}"
  echo "🎯 Catch-up nicho: $NICHO ($POD_DESIGNS_PER_NICHO designs)"
  ( cd pod-automatico && node gerador-designs/gerar.mjs "$NICHO" "$POD_DESIGNS_PER_NICHO" ) || echo "   ⚠️  gerar falhou ($NICHO)"
  ( cd pod-automatico && node uploader-printify/upload.mjs "$NICHO" ) || echo "   ⚠️  upload falhou ($NICHO)"
  RUNS=$((RUNS+1))
  PEND=$((PEND - POD_DESIGNS_PER_NICHO))
done

echo "🏁 POD catch-up: +$RUNS nicho(s) processado(s)"
