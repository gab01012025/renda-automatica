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
PINS_DAILY="${PINS_DAILY:-3}"
SHORTS_DAILY="${SHORTS_DAILY:-2}"
TIKTOK_DAILY="${TIKTOK_DAILY:-2}"
echo ""
echo "=========================================="
echo "🌙 CRON NOTURNO — $(date '+%Y-%m-%d %H:%M')"
echo "=========================================="

# ---------- 1. DESIGNS POD (nicho rotativo) ----------
NICHOS=("mundial-futebol-pt" "memes-portugal" "cafe-lisboa" "frases-motivacionais" "pets-engracados" "programadores-br" "casamento-pt" "profissoes-pt" "astrologia-signos" "maternidade-pt" "aniversarios-pt")
DIA=$(date +%d)
IDX=$(( 10#$DIA % ${#NICHOS[@]} ))
NICHO="${NICHOS[$IDX]}"
echo "$LOG_PREFIX 🎯 Nicho do dia: $NICHO"

echo "$LOG_PREFIX 📦 [1/6] Gerar 3 designs..."
( cd pod-automatico && node gerador-designs/gerar.mjs "$NICHO" 3 ) || echo "   ⚠️  designs falhou"

echo "$LOG_PREFIX 📤 [2/6] Upload Printify..."
( cd pod-automatico && node uploader-printify/upload.mjs "$NICHO" ) || echo "   ⚠️  upload falhou"

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

# ---------- 7. TIKTOK (reaproveita Short do YouTube) ----------
echo "$LOG_PREFIX 🎵 [7/7] TikTok — publicar $TIKTOK_DAILY vídeos..."
( cd tiktok-auto && "$PYBIN" tiktok-auto-post.py "$TIKTOK_DAILY" ) || echo "   ⚠️  TikTok falhou (corre --login se sessão expirou)"

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
