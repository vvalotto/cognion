#!/usr/bin/env bash
# Restaura un respaldo de Cognión (US-10.2.2). Por defecto es un ENSAYO: restaura en una base temporal, muestra
# conteos contra la base actual y la borra. Con --reemplazar (y confirmando) reemplaza la base real.
#
#   ./restaurar.sh respaldos/cognion-20261111-030000.dump                 ensayo (no toca la base real)
#   ./restaurar.sh respaldos/cognion-20261111-030000.dump --reemplazar    reemplaza la base real
#
# Códigos de salida: 0 ok · 1 error (archivo corrupto, cancelado, falló la restauración).
set -euo pipefail
cd "$(dirname "$0")"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }
hash_sha256() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }
db() { docker compose exec -T db "$@"; }

ARCHIVO="${1:-}"
REEMPLAZAR=0
[ "${2:-}" = "--reemplazar" ] && REEMPLAZAR=1
[ -n "$ARCHIVO" ] && [ -f "$ARCHIVO" ] || abortar "Indicá el archivo de respaldo a restaurar." "Uso: ./restaurar.sh <archivo.dump> [--reemplazar]"
command -v docker >/dev/null 2>&1 || abortar "Falta docker."
[ -f .env ] || abortar "No existe deploy/servidor/.env." "Ejecutá ./preparar-env.sh primero."

# 1. Validación previa: ni el hash ni la lectura fallan → recién ahí se toca algo.
if [ -f "$ARCHIVO.sha256" ]; then
  ( cd "$(dirname "$ARCHIVO")" && hash_sha256 -c "$(basename "$ARCHIVO").sha256" >/dev/null 2>&1 ) \
    || abortar "El archivo no coincide con su sha256: está corrupto o fue modificado." "No se tocó ninguna base."
else
  echo "AVISO: no hay $(basename "$ARCHIVO").sha256; no se puede comprobar la integridad por hash." >&2
fi
db pg_restore --list < "$ARCHIVO" >/dev/null 2>&1 \
  || abortar "El archivo no es un respaldo legible (corrupto o de otro formato)." "No se tocó ninguna base."

contar() { db psql -U cognion -d "$1" -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"; }

if [ "$REEMPLAZAR" = "0" ]; then
  # 2a. Ensayo: base temporal, nunca la real.
  TEMPORAL="cognion_ensayo_$$"
  limpiar() { db dropdb -U cognion --if-exists "$TEMPORAL" >/dev/null 2>&1 || true; }
  trap limpiar EXIT
  db createdb -U cognion "$TEMPORAL" || abortar "No pude crear la base temporal."
  db pg_restore --no-owner --exit-on-error -U cognion -d "$TEMPORAL" < "$ARCHIVO" \
    || abortar "La restauración de ensayo falló." "La base real no se tocó."
  echo "Ensayo OK: el respaldo se restauró en una base temporal (ya borrada)."
  echo "Tablas restauradas: $(contar "$TEMPORAL") · Tablas en la base actual: $(contar cognion)"
  echo "Para reemplazar la base real: $0 $ARCHIVO --reemplazar"
  exit 0
fi

# 2b. Reemplazo: confirmación explícita, aplicación detenida, restauración en una sola transacción.
echo "Esto REEMPLAZA la base de Cognión con el contenido de $(basename "$ARCHIVO"). Se pierde lo que se cargó después de ese respaldo."
read -r -p "Escribí RESTAURAR para continuar: " RESPUESTA || RESPUESTA=""
[ "$RESPUESTA" = "RESTAURAR" ] || { echo "Cancelado: no se hizo nada."; exit 1; }

docker compose stop app
if db pg_restore --clean --if-exists --no-owner --single-transaction --exit-on-error -U cognion -d cognion < "$ARCHIVO"; then
  docker compose up -d --wait app
  echo "Base restaurada desde $(basename "$ARCHIVO") y aplicación levantada."
else
  docker compose up -d --wait app || true
  abortar "La restauración falló; como corre en una sola transacción, la base quedó como estaba." "Revisá: ./cognion.sh logs db"
fi
