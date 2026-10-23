#!/usr/bin/env sh
# Exporta el esquema OpenAPI de cada servicio a docs/api/<servicio>.yaml
# Uso: PYTHON=ruta/al/python scripts/export_openapi.sh
set -eu
PYTHON="${PYTHON:-python}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
for svc in auth pedidos tracking chatbot; do
  (cd "$ROOT/services/$svc" && USE_SQLITE=true "$PYTHON" manage.py spectacular --validate \
    --file "$ROOT/docs/api/$svc.yaml")
  echo "docs/api/$svc.yaml"
done
