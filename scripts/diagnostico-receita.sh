#!/usr/bin/env bash
# Diagnostico de receita: imprime resumo + avisa quais tokens faltam para
# deslocar do "publicação cega" para "rastreamento + escala de receita".
set -uo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

for envf in "$ROOT/produtos-digitais/.env" "$ROOT/pod-automatico/.env" "$ROOT/.env"; do
  [[ -f "$envf" ]] && set -a && source "$envf" && set +a
done

LATEST="$ROOT/scripts/relatorios/metricas-latest.json"
echo "════════════════════════════════════════"
echo "💸 STATUS DE RECEITA — $(date '+%Y-%m-%d %H:%M')"
echo "════════════════════════════════════════"

if [[ -f "$LATEST" ]]; then
  python3 - <<'PY'
import json, pathlib
p = pathlib.Path('scripts/relatorios/metricas-latest.json')
d = json.loads(p.read_text())
t = d.get('traffic', {})
r = d.get('receita', {})
print(f"📈 Tráfego 24h: YT={t.get('youtube_uploads_24h',0)} | TT={t.get('tiktok_uploads_24h',0)}")
print(f"📈 Tráfego 48h: YT={t.get('youtube_uploads_48h',0)} | TT={t.get('tiktok_uploads_48h',0)}")
if r.get('enabled'):
    print(f"💶 Receita 24h: €{r.get('revenue_24h_eur',0):.2f} ({r.get('sales_24h',0)} vendas)")
    by = r.get('by_product', {}) or {}
    for k, v in by.items():
        print(f"   • {k}: €{v.get('revenue',0):.2f} ({v.get('sales',0)} vendas)")
else:
    print("💶 Receita: ❌ desativado (falta GUMROAD_ACCESS_TOKEN)")
PY
else
  echo "⚠️ Sem relatório ainda (corre métricas)."
fi

echo ""
echo "🔑 TOKENS — checklist para escalar até €1300/mês"
check() {
  local name="$1"; local val="${!name:-}"
  if [[ -n "$val" && "$val" != "XXXXX" ]]; then
    echo "  ✅ $name"
  else
    echo "  ❌ $name  ← bloqueia ${2:-funcionalidade}"
  fi
}
check GUMROAD_ACCESS_TOKEN "rastreio receita real"
check BITLY_TOKEN "rastreio cliques por canal"
check MEDIUM_TOKEN "amplificação cross-post Medium"
check DEVTO_TOKEN "amplificação cross-post Dev.to"
check HASHNODE_TOKEN "amplificação cross-post Hashnode"
check PRINTIFY_API_KEY "POD Etsy"
check PRINTIFY_SHOP_ID "POD Etsy"
check OPENAI_API_KEY "geração de tudo"

echo ""
echo "🎯 META: €1300/mês = ~€43/dia"
echo "   • POD Etsy ~€8/venda → 5/dia"
echo "   • Gumroad bundle €19 → 2/dia"
echo "   • KDP royalties → passivo"
echo "   • Affiliate site → passivo"
echo "════════════════════════════════════════"
