#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/produtos-digitais/.env"

usage() {
  cat <<'EOF'
Uso:
  bash scripts/preencher-env-metricas.sh \
    --gumroad-token "TOKEN" \
    --bitly-token "TOKEN" \
    --bitly-dev "https://bit.ly/..." \
    --bitly-mkt "https://bit.ly/..." \
    --bitly-bundle "https://bit.ly/..." \
    [--bundle-price "29"]

Se algum argumento for omitido, o valor atual do .env é preservado.
EOF
}

get_current() {
  local key="$1"
  local cur
  cur=$(grep -E "^${key}=" "$ENV_FILE" | head -n1 | cut -d'=' -f2- || true)
  printf '%s' "$cur"
}

set_kv() {
  local key="$1"
  local value="$2"
  if grep -qE "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf "%s=%s\n" "$key" "$value" >> "$ENV_FILE"
  fi
}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ .env não encontrado em $ENV_FILE"
  exit 1
fi

GUMROAD_TOKEN="$(get_current GUMROAD_ACCESS_TOKEN)"
BITLY_TOKEN="$(get_current BITLY_TOKEN)"
BUNDLE_PRICE="$(get_current BUNDLE_PRICE)"
BITLY_DEV=""
BITLY_MKT=""
BITLY_BUNDLE=""

# Read current JSON mapping if present
RAW_JSON="$(get_current BITLY_LINKS_JSON)"
if [[ -n "$RAW_JSON" ]]; then
  BITLY_DEV="$(python3 - <<PY
import json
s = '''$RAW_JSON'''
try:
    d = json.loads(s)
    print(d.get('prompts-chatgpt-programadores',''))
except Exception:
    print('')
PY
)"
  BITLY_MKT="$(python3 - <<PY
import json
s = '''$RAW_JSON'''
try:
    d = json.loads(s)
    print(d.get('prompts-marketing-pt',''))
except Exception:
    print('')
PY
)"
  BITLY_BUNDLE="$(python3 - <<PY
import json
s = '''$RAW_JSON'''
try:
    d = json.loads(s)
    print(d.get('bundle-prompts-ai-pt',''))
except Exception:
    print('')
PY
)"
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gumroad-token) GUMROAD_TOKEN="${2:-}"; shift 2 ;;
    --bitly-token) BITLY_TOKEN="${2:-}"; shift 2 ;;
    --bitly-dev) BITLY_DEV="${2:-}"; shift 2 ;;
    --bitly-mkt) BITLY_MKT="${2:-}"; shift 2 ;;
    --bitly-bundle) BITLY_BUNDLE="${2:-}"; shift 2 ;;
    --bundle-price) BUNDLE_PRICE="${2:-29}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "❌ Argumento desconhecido: $1"; usage; exit 1 ;;
  esac
done

[[ -z "$BUNDLE_PRICE" ]] && BUNDLE_PRICE="29"

BITLY_JSON=$(python3 - <<PY
import json
print(json.dumps({
  'prompts-chatgpt-programadores': '$BITLY_DEV',
  'prompts-marketing-pt': '$BITLY_MKT',
  'bundle-prompts-ai-pt': '$BITLY_BUNDLE'
}, ensure_ascii=False, separators=(',',':')))
PY
)

set_kv BUNDLE_PRICE "$BUNDLE_PRICE"
set_kv GUMROAD_ACCESS_TOKEN "$GUMROAD_TOKEN"
set_kv BITLY_TOKEN "$BITLY_TOKEN"
set_kv BITLY_LINKS_JSON "$BITLY_JSON"

echo "✅ .env atualizado via CLI"

MISSING=0
if [[ -z "$GUMROAD_TOKEN" ]]; then echo "⚠️ Falta GUMROAD_ACCESS_TOKEN"; MISSING=1; fi
if [[ -z "$BITLY_TOKEN" ]]; then echo "⚠️ Falta BITLY_TOKEN"; MISSING=1; fi
if [[ -z "$BITLY_DEV" || -z "$BITLY_MKT" || -z "$BITLY_BUNDLE" ]]; then
  echo "⚠️ Falta preencher um ou mais links em BITLY_LINKS_JSON"
  MISSING=1
fi

if [[ "$MISSING" -eq 0 ]]; then
  echo "🎯 Métricas por produto prontas para rodar automaticamente."
else
  echo "ℹ️ Completa os campos faltantes para ativar cliques+conversão por produto."
fi
