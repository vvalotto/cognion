#!/usr/bin/env bash
# Restaura un respaldo de Cognión (US-8.5.4). Por defecto es un ENSAYO: restaura en una base temporal, compara
# conteos contra la base actual y la borra. Solo con --sobre-local (y confirmando) reemplaza la base local.
#
# Uso: scripts/local/restaurar.sh <archivo.dump> [--sobre-local]
# Códigos de salida: 0 ok · 1 error (archivo corrupto, cancelado, etc.) · 3 los conteos difieren del origen.
set -euo pipefail
cd "$(dirname "$0")/../.."
. scripts/local/_conexion.sh

ARCHIVO="${1:-}"
SOBRE_LOCAL=0
[ "${2:-}" = "--sobre-local" ] && SOBRE_LOCAL=1
[ -n "$ARCHIVO" ] && [ -f "$ARCHIVO" ] || abortar "Indicá el archivo de respaldo a restaurar." "Uso: scripts/local/restaurar.sh <archivo.dump> [--sobre-local]"

# 1. Validación previa: ni el hash ni la lectura fallan → recién ahí se toca algo.
if [ -f "$ARCHIVO.sha256" ]; then
  ( cd "$(dirname "$ARCHIVO")" && shasum -a 256 -c "$(basename "$ARCHIVO").sha256" >/dev/null 2>&1 ) \
    || abortar "El archivo no coincide con su sha256: está corrupto o fue modificado." "No se tocó ninguna base."
else
  echo "AVISO: no hay $(basename "$ARCHIVO").sha256; no se puede comprobar la integridad por hash." >&2
fi
pg_restore --list "$ARCHIVO" >/dev/null 2>&1 \
  || abortar "El archivo no es un respaldo legible (corrupto o de otro formato)." "No se tocó ninguna base."

# 2. Confirmación (solo para reemplazar la base local).
if [ "$SOBRE_LOCAL" = "1" ]; then
  echo "Esto REEMPLAZA la base '$BASE' con el contenido de $(basename "$ARCHIVO")."
  read -r -p "Escribí RESTAURAR para continuar: " RESPUESTA || RESPUESTA=""
  [ "$RESPUESTA" = "RESTAURAR" ] || { echo "Cancelado: no se hizo nada."; exit 1; }
fi

# 3. Restauración a una base temporal (un respaldo defectuoso nunca toca la base local).
TEMPORAL="${BASE}_restaurada_$$"
ERR="$(mktemp)"
limpiar() { rm -f "$ERR"; admin "DROP DATABASE IF EXISTS \"${TEMPORAL}\"" >/dev/null 2>&1 || true; }
trap limpiar EXIT
admin "CREATE DATABASE \"${TEMPORAL}\" OWNER \"${USUARIO}\"" >/dev/null 2>&1 \
  || abortar "No pude crear la base temporal." "Hace falta un rol con CREATEDB: PGADMIN_USER=<rol> scripts/local/restaurar.sh ..."
if ! PGPASSWORD="$CLAVE" pg_restore --no-owner --exit-on-error -h "$HOST" -p "$PUERTO_PG" -U "$USUARIO" -d "$TEMPORAL" "$ARCHIVO" 2>"$ERR"; then
  tail -n 5 "$ERR" >&2
  abortar "pg_restore falló." "La base '$BASE' no se tocó."
fi

# 4. Comparación de conteos contra la base actual.
DIFIEREN=0
printf '%-22s %10s %10s\n' "tabla" "actual" "restaurada"
for tabla in usuario events pregunta_plantilla; do
  actual="$(en_base "$BASE" "SELECT count(*) FROM $tabla" 2>/dev/null || echo "-")"
  restaurada="$(en_base "$TEMPORAL" "SELECT count(*) FROM $tabla")"
  marca=""; [ "$actual" = "$restaurada" ] || { DIFIEREN=1; marca="  ≠"; }
  printf '%-22s %10s %10s%s\n' "$tabla" "$actual" "$restaurada" "$marca"
done

# 5. Reemplazo de la base local (solo con --sobre-local, ya confirmado).
if [ "$SOBRE_LOCAL" = "1" ]; then
  [ "$(admin "SELECT count(*) FROM pg_stat_activity WHERE datname='${BASE}'")" = "0" ] \
    || abortar "Hay conexiones abiertas a '$BASE'." "Detené el servidor (scripts/local/detener.sh) y volvé a ejecutar."
  admin "DROP DATABASE \"${BASE}\"" >/dev/null
  admin "ALTER DATABASE \"${TEMPORAL}\" RENAME TO \"${BASE}\"" >/dev/null
  echo "Base '$BASE' reemplazada con el respaldo."
  exit 0
fi

if [ "$DIFIEREN" = "1" ]; then
  echo "Los conteos difieren de la base actual (¿hubo actividad después del respaldo?). La temporal se borró." >&2
  exit 3
fi
echo "Ensayo OK: la restauración coincide con la base actual. La temporal se borró."
