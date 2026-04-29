#!/usr/bin/env bash
# Cron Noturno LOCAL — corre tudo no laptop do Gabriel
# Instalar: bash scripts/cron-diario.sh --install
# Testar:   bash scripts/cron-diario.sh
# Logs:     /tmp/cron-renda-YYYY-MM-DD.log

set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# ---------- INSTALL MODE ----------
if [[ "${1:-}" == "--install" ]]; then
  CRON_LINE="0 3,11,19 * * * /bin/bash '$ROOT/scripts/cron-diario.sh' >> /tmp/cron-renda-\$(date +\%Y-\%m-\%d).log 2>&1"
  ( crontab -l 2>/dev/null | grep -v 'cron-diario.sh' ; echo "$CRON_LINE" ) | crontab -
  echo "✅ Cron instalado (todos os dias 03:00, 11:00 e 19:00):"
  crontab -l | grep cron-diario.sh
  exit 0
fi

if [[ "${1:-}" == "--uninstall" ]]; then
  crontab -l 2>/dev/null | grep -v 'cron-diario.sh' | crontab -
  echo "✅ Cron removido"
  exit 0
fi

if [[ "${1:-}" == "--status" ]]; then
  echo "Cron atual:"
  crontab -l 2>/dev/null | grep -E 'cron-diario|^#' || echo "(nenhum)"
  echo ""
  echo "Últimos logs:"
  ls -lht /tmp/cron-renda-*.log 2>/dev/null | head -5
  exit 0
fi

# ---------- LOAD ENV ----------
for envf in "$ROOT/produtos-digitais/.env" "$ROOT/pod-automatico/.env" "$ROOT/.env"; do
  [[ -f "$envf" ]] && set -a && source "$envf" && set +a
done

LOG_PREFIX="[$(date '+%H:%M:%S')]"
# Cadência alvo €1300/mês: volume + diversidade + recorrência
PINS_DAILY="${PINS_DAILY:-5}"
SHORTS_DAILY="${SHORTS_DAILY:-2}"
SHORTS_ANIME_DAILY="${SHORTS_ANIME_DAILY:-2}"
TIKTOK_DAILY="${TIKTOK_DAILY:-5}"
POD_DESIGNS_PER_NICHO="${POD_DESIGNS_PER_NICHO:-5}"
POD_NICHOS_POR_RUN="${POD_NICHOS_POR_RUN:-2}"
echo ""
echo "=========================================="
echo "🌙 CRON NOTURNO — $(date '+%Y-%m-%d %H:%M')"
echo "=========================================="

# ---------- 1. DESIGNS POD (rotação multi-nicho por dia) ----------
NICHOS=("funny-puns-en" "vintage-retro-en" "cottagecore-botanical-en" "profession-humor-en" "y2k-nostalgia-en" "deutsch-spruche")
DIA=$(date +%d)
TOTAL=${#NICHOS[@]}
for k in $(seq 0 $((POD_NICHOS_POR_RUN - 1))); do
  IDX=$(( (10#$DIA + k) % TOTAL ))
  NICHO="${NICHOS[$IDX]}"
  echo "$LOG_PREFIX 🎯 Nicho [$((k+1))/$POD_NICHOS_POR_RUN]: $NICHO"
  echo "$LOG_PREFIX 📦 Gerar $POD_DESIGNS_PER_NICHO designs ($NICHO)..."
  ( cd pod-automatico && node gerador-designs/gerar.mjs "$NICHO" "$POD_DESIGNS_PER_NICHO" ) || echo "   ⚠️  designs falhou ($NICHO)"
  echo "$LOG_PREFIX 📤 Upload Printify ($NICHO)..."
  ( cd pod-automatico && node uploader-printify/upload.mjs "$NICHO" ) || echo "   ⚠️  upload falhou ($NICHO)"
done

# ---------- 3. PINS PINTEREST ----------
echo "$LOG_PREFIX 📌 [3/6] Gerar $PINS_DAILY pins Pinterest..."
PYBIN="$ROOT/.venv/bin/python"
[[ ! -x "$PYBIN" ]] && PYBIN="python3"
( cd pod-automatico/pinterest && "$PYBIN" gerar-pins.py "$PINS_DAILY" && "$PYBIN" gerar-descriptions.py ) || echo "   ⚠️  pins falhou"

# ---------- 3b. AUTO-PUBLICAR PINS NO PINTEREST ----------
echo "$LOG_PREFIX 📌 [3b] Auto-publicar $PINS_DAILY pins no Pinterest (Playwright)..."
( cd pod-automatico/pinterest && "$PYBIN" pinterest-auto-post.py "$PINS_DAILY" ) || echo "   ⚠️  auto-post Pinterest falhou (corre --login se sessão expirou)"

# ---------- 4. ARTIGO SEO ----------
echo "$LOG_PREFIX 📝 [4/6] Gerar artigo SEO..."
( cd afiliados-ia/gerador && node gerar-artigo.mjs ) || echo "   ⚠️  artigo falhou"

# ---------- 5. CROSS-POST ----------
echo "$LOG_PREFIX 📡 [5/6] Cross-post Medium/Devto/Hashnode..."
node cross-post/cross-post.mjs || echo "   ⚠️  crosspost skip"

# ---------- 6. YOUTUBE SHORT (gerar + upload) ----------
echo "$LOG_PREFIX 🎬 [6/6] YouTube Shorts — gerar + upload ($SHORTS_DAILY)..."
echo "$LOG_PREFIX 📈 [6a] Atualizar hints de performance (48h)..."
"$PYBIN" scripts/atualizar-hints-48h.py || echo "   ⚠️  hints 48h falhou"
"$PYBIN" youtube-faceless/auto-shorts.py "$SHORTS_DAILY" || echo "   ⚠️  short falhou (corre --auth se token expirou)"

# ---------- 6c. YOUTUBE ANIME (curiosidades, audiência maior) ----------
echo "$LOG_PREFIX 🎌 [6c] YouTube ANIME — gerar + upload ($SHORTS_ANIME_DAILY)..."
"$PYBIN" youtube-faceless/auto-shorts-anime.py "$SHORTS_ANIME_DAILY" || echo "   ⚠️  short anime falhou"

# ---------- 7. TIKTOK (reaproveita Short do YouTube) ----------
echo "$LOG_PREFIX 🎵 [7/7] TikTok — publicar $TIKTOK_DAILY vídeos..."
( cd tiktok-auto && "$PYBIN" tiktok-auto-post.py "$TIKTOK_DAILY" ) || echo "   ⚠️  TikTok falhou (corre --login se sessão expirou)"
echo "$LOG_PREFIX 🎯 [7b] Garantir meta diária do TikTok..."
/bin/bash "$ROOT/scripts/garantir-tiktok-diario.sh" || echo "   ⚠️  guardião TikTok falhou"
echo "$LOG_PREFIX 🎯 [1b] Garantir meta diária do POD..."
/bin/bash "$ROOT/scripts/garantir-pod-diario.sh" || echo "   ⚠️  guardião POD falhou"

# ---------- 7c. NOTION TEMPLATES (produto digital alta margem) ----------
NOTION_DAILY="${NOTION_DAILY:-1}"
echo "$LOG_PREFIX 📓 [7c] Notion templates — gerar $NOTION_DAILY..."
( cd produtos-digitais && node gerar-notion-templates.mjs "$NOTION_DAILY" ) || echo "   ⚠️  notion templates falhou"

# ---------- 7d. STOCK IMAGES IA (Adobe Stock / Shutterstock — passivo) ----------
STOCK_DAILY="${STOCK_DAILY:-5}"
echo "$LOG_PREFIX 📸 [7d] Stock images IA — gerar $STOCK_DAILY..."
"$PYBIN" stock-images/gerar-batch-stock.py "$STOCK_DAILY" || echo "   ⚠️  stock images falhou"

# ---------- 7e. AFILIADOS MULTI-IDIOMA (EN/DE/FR/ES — Amazon SEO) ----------
AFFIL_MULTILANG_DAILY="${AFFIL_MULTILANG_DAILY:-3}"
echo "$LOG_PREFIX 🌍 [7e] Afiliados multi-idioma — gerar $AFFIL_MULTILANG_DAILY artigos..."
( cd afiliados-ia/gerador && node gerar-artigo-multilang.mjs "$AFFIL_MULTILANG_DAILY" ) || echo "   ⚠️  afiliados multilang falhou"

# ---------- 7e2. AFILIADOS BR (Shopee + ML + AliExpress + Hotmart) ----------
AFFIL_BR_DAILY="${AFFIL_BR_DAILY:-3}"
echo "$LOG_PREFIX 🇧🇷 [7e2] Afiliados BR multi-marketplace — gerar $AFFIL_BR_DAILY artigos..."
( cd afiliados-ia/gerador && node gerar-artigo-br.mjs "$AFFIL_BR_DAILY" ) || echo "   ⚠️  afiliados BR falhou"

# ---------- 7f. ETSY DIGITAL DOWNLOADS (wall art + planners DE/FR/EN) ----------
ETSY_DIGITALS_DAILY="${ETSY_DIGITALS_DAILY:-5}"
echo "$LOG_PREFIX 🎨 [7f] Etsy digital downloads — gerar $ETSY_DIGITALS_DAILY..."
"$PYBIN" etsy-digitals/gerar-etsy-digitals.py "$ETSY_DIGITALS_DAILY" || echo "   ⚠️  etsy digitals falhou"

# ---------- 7f2. ETSY DIGITAL DOWNLOADS UPLOADER ----------
# DESATIVADO: o wizard Etsy PT-PT via Playwright não publica fiável.
# POD físico (camisas/posters) já está coberto por Printify acima (passo 1).
# Para digital downloads (PDF planners), próximo passo será Etsy API v3 oficial (OAuth).
# Para ativar via Playwright (rascunhos manuais): export ETSY_UPLOADER_ENABLED=1
if [[ "${ETSY_UPLOADER_ENABLED:-0}" == "1" ]]; then
  ETSY_UPLOAD_DAILY="${ETSY_UPLOAD_DAILY:-3}"
  ETSY_SESSION_DIR="$ROOT/etsy-digitals/.etsy-session"
  if [[ -d "$ETSY_SESSION_DIR" ]]; then
    echo "$LOG_PREFIX 📤 [7f2] Etsy uploader (manual) — subir $ETSY_UPLOAD_DAILY rascunhos..."
    "$PYBIN" etsy-digitals/etsy-uploader.py "$ETSY_UPLOAD_DAILY" || echo "   ⚠️  etsy uploader falhou"
  fi
else
  echo "$LOG_PREFIX 📤 [7f2] Etsy uploader Playwright — DESATIVADO (Printify trata POD físico)"
fi

# ---------- 7g. COLD EMAIL B2B PT (vende sites €390 a empresas locais) ----------
# Só corre 1x/dia (na execução das 11h) para não floodar inboxes
COLD_EMAIL_HOUR_FLAG="/tmp/cold-email-$(date +%Y-%m-%d).done"
# Warm-up automático: 5/dia primeira semana, depois sobe para 15
WARMUP_FILE="/tmp/cold-email-start-date"
[[ ! -f "$WARMUP_FILE" ]] && date +%s > "$WARMUP_FILE"
START_TS=$(cat "$WARMUP_FILE" 2>/dev/null || date +%s)
DAYS_SINCE=$(( ($(date +%s) - START_TS) / 86400 ))
if [[ $DAYS_SINCE -lt 7 ]]; then
  COLD_EMAIL_DAILY="${COLD_EMAIL_DAILY:-5}"
elif [[ $DAYS_SINCE -lt 14 ]]; then
  COLD_EMAIL_DAILY="${COLD_EMAIL_DAILY:-10}"
else
  COLD_EMAIL_DAILY="${COLD_EMAIL_DAILY:-15}"
fi
HOUR_NOW=$(date +%H)
if [[ "$HOUR_NOW" == "11" && ! -f "$COLD_EMAIL_HOUR_FLAG" ]]; then
  echo "$LOG_PREFIX 📧 [7g] Cold-email B2B PT — enviar $COLD_EMAIL_DAILY (warm-up dia $((DAYS_SINCE+1)))..."
  "$PYBIN" cold-email-pt/cold-email-pt.py "$COLD_EMAIL_DAILY" || echo "   ⚠️  cold-email falhou"
  touch "$COLD_EMAIL_HOUR_FLAG"
else
  echo "$LOG_PREFIX 📧 [7g] Cold-email — só corre às 11h (skip)"
fi

# ---------- 8. KDP (1 tentativa por dia) ----------
KDP_DAILY_FLAG="/tmp/kdp-tentativa-$(date +%Y-%m-%d).done"
if [[ ! -f "$KDP_DAILY_FLAG" ]]; then
  echo "$LOG_PREFIX 📚 [8/9] KDP — tentativa diária (1x/dia)..."
  /bin/bash "$ROOT/scripts/kdp-tentativa-diaria.sh" || echo "   ⚠️  tentativa KDP falhou"
  touch "$KDP_DAILY_FLAG"
else
  echo "$LOG_PREFIX 📚 [8/9] KDP — já tentado hoje (skip)"
fi

# ---------- 9. Métricas diárias ----------
echo "$LOG_PREFIX 📊 [9/9] Gerar métricas diárias..."
"$PYBIN" scripts/metricas-diarias.py || echo "   ⚠️  métricas falhou"
/bin/bash "$ROOT/scripts/diagnostico-receita.sh" || true

# ---------- DEPLOY VERCEL ----------
if command -v vercel >/dev/null 2>&1; then
  echo "$LOG_PREFIX 🚀 Deploy Vercel..."
  ( cd afiliados-ia/site && vercel deploy --prod --yes 2>&1 | tail -3 ) || echo "   ⚠️  deploy skip"
fi

# ---------- COMMIT LOCAL (sem push, evita problema GitHub) ----------
echo "$LOG_PREFIX 💾 Commit local..."
git add -A
if ! git diff --staged --quiet; then
  git commit -m "🤖 Cron local $(date +'%Y-%m-%d')" --quiet
  echo "   ✓ commit feito"
  # Push opcional (se gh auth funciona)
  git push 2>/dev/null && echo "   ✓ push GitHub" || echo "   ↺ push skip (offline ou repo full)"
else
  echo "   ↺ sem mudanças"
fi

echo "$LOG_PREFIX ✅ CRON CONCLUÍDO"
echo "=========================================="
