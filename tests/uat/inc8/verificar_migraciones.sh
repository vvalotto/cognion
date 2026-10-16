#!/usr/bin/env bash
# Verifica las migraciones Alembic contra una base DESCARTABLE propia (US-8.1.4).
# Crea la base, comprueba vacía→head, idempotencia y falla con base inaccesible; la borra al terminar.
# Nunca toca la base de desarrollo. Uso: tests/uat/inc8/verificar_migraciones.sh
set -euo pipefail
cd "$(dirname "$0")/../../.."

BASE="cognion_mig_$$"
# Credenciales y host salen del DATABASE_URL local (entorno o .env); solo cambia el nombre de la base.
ORIGEN="${DATABASE_URL:-$(grep -E '^DATABASE_URL=' .env | cut -d= -f2-)}"
leer() { python3 -c "from urllib.parse import urlparse; import sys; u=urlparse(sys.argv[1]); print({'u':u.username,'p':u.password,'h':u.hostname,'n':u.port or 5432}[sys.argv[2]])" "$ORIGEN" "$1"; }
USUARIO="$(leer u)"; CLAVE="$(leer p)"; HOST="$(leer h)"; PUERTO="$(leer n)"
URL="postgresql+asyncpg://${USUARIO}:${CLAVE}@${HOST}:${PUERTO}/${BASE}"
ALEMBIC=(.venv/bin/alembic)

# Crear/borrar la base requiere un rol con CREATEDB: por defecto el usuario del SO (PGADMIN_USER lo cambia).
admin() { psql -h "$HOST" -p "$PUERTO" ${PGADMIN_USER:+-U "$PGADMIN_USER"} -d postgres -qc "$1"; }
limpiar() { admin "DROP DATABASE IF EXISTS ${BASE}" >/dev/null 2>&1 || true; }
trap limpiar EXIT
ok() { echo "OK   $1"; }
fallo() { echo "FAIL $1"; exit 1; }

admin "CREATE DATABASE ${BASE} OWNER \"${USUARIO}\"" >/dev/null

export SECRET_KEY=verificacion
HEAD="$(DATABASE_URL="$URL" "${ALEMBIC[@]}" heads | awk '{print $1}')"

DATABASE_URL="$URL" "${ALEMBIC[@]}" upgrade head >/dev/null 2>&1 || fallo "1. upgrade head sobre base vacía"
ACTUAL="$(DATABASE_URL="$URL" "${ALEMBIC[@]}" current 2>/dev/null | awk '{print $1}')"
[ "$ACTUAL" = "$HEAD" ] && ok "1. base vacía → head ($HEAD)" || fallo "1. current=$ACTUAL, esperado $HEAD"

DATABASE_URL="$URL" "${ALEMBIC[@]}" upgrade head >/dev/null 2>&1 && ok "2. segunda corrida idempotente (exit 0)" || fallo "2. segunda corrida"

if DATABASE_URL="postgresql+asyncpg://${USUARIO}:${CLAVE}@${HOST}:5999/${BASE}" "${ALEMBIC[@]}" upgrade head >/dev/null 2>&1; then
  fallo "3. base inaccesible debería terminar con exit != 0"
else
  ok "3. base inaccesible → exit != 0 (el deploy se aborta)"
fi
echo "Migraciones verificadas."
