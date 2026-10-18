#!/usr/bin/env bash
# Verifica scripts/local/levantar.sh y detener.sh (US-8.5.3) contra una base y un puerto DESCARTABLES propios.
# No toca .env.local ni la base cognion_local ni la de desarrollo (se comprueba con una huella antes/después).
# Uso: tests/uat/inc8/verificar_levantar_local.sh   (requiere PostgreSQL local y un rol con CREATEDB)
set -euo pipefail
cd "$(dirname "$0")/../../.."

BASE="cognion_lv_$$"
PUERTO=$((18000 + $$ % 1000))
TMP="$(mktemp -d)"
export COGNION_LOCAL_BASE="$BASE" COGNION_LOCAL_PUERTO="$PUERTO"
export COGNION_LOCAL_ENV="$TMP/env.local" COGNION_LOCAL_LOGS="$TMP/logs"
CLAVE_ADMIN="Local#Prueba-2026"
export ADMIN_NOMBRE="Admin Local" ADMIN_EMAIL="admin-local@ejemplo.edu.ar" ADMIN_PASSWORD="$CLAVE_ADMIN"

ORIGEN="${DATABASE_URL:-$(grep -E '^DATABASE_URL=' .env | cut -d= -f2-)}"
leer() { python3 -c "from urllib.parse import urlparse; import sys; u=urlparse(sys.argv[1]); print({'u':u.username,'p':u.password or '','h':u.hostname,'n':u.port or 5432,'b':u.path.lstrip('/')}[sys.argv[2]])" "$ORIGEN" "$1"; }
USUARIO="$(leer u)"; CLAVE="$(leer p)"; HOST="$(leer h)"; PUERTO_PG="$(leer n)"; BASE_DEV="$(leer b)"
admin() { psql -h "$HOST" -p "$PUERTO_PG" ${PGADMIN_USER:+-U "$PGADMIN_USER"} -d postgres -qAt -c "$1"; }
en() { PGPASSWORD="$CLAVE" psql -h "$HOST" -p "$PUERTO_PG" -U "$USUARIO" -d "$1" -qAt -c "$2"; }
limpiar() { scripts/local/detener.sh >/dev/null 2>&1 || true; admin "DROP DATABASE IF EXISTS \"${BASE}\"" >/dev/null 2>&1 || true; rm -rf "$TMP"; }
trap limpiar EXIT
ok() { echo "OK   $1"; }
fallo() { echo "FAIL $1"; exit 1; }
huella() { en "$BASE_DEV" "SELECT (SELECT string_agg(version_num,',') FROM alembic_version) || '|' || (SELECT count(*) FROM usuario)" 2>/dev/null || echo "sin-base-dev"; }

ANTES="$(huella)"

# 1. Máquina sin .env.local ni base → quedan creados y el sistema responde.
scripts/local/levantar.sh --fondo >"$TMP/salida1.txt" 2>&1 || { cat "$TMP/salida1.txt"; fallo "1. levantar.sh --fondo"; }
[ -f "$COGNION_LOCAL_ENV" ] && [ -n "$(admin "SELECT 1 FROM pg_database WHERE datname='${BASE}'")" ] \
  && ok "1a. se crearon .env.local y la base propia" || fallo "1a. creación"
grep -q "ENTORNO=local" "$COGNION_LOCAL_ENV" && grep -q "EMAIL_MODO=consola" "$COGNION_LOCAL_ENV" \
  && [ "$(grep -E '^SECRET_KEY=' "$COGNION_LOCAL_ENV" | cut -d= -f2- | wc -c)" -ge 64 ] && ok "1b. .env.local con ENTORNO=local, consola y secreto aleatorio" || fallo "1b. contenido de .env.local"
[ "$(stat -f %Lp "$COGNION_LOCAL_ENV")" = "600" ] && ok "1c. .env.local con permisos 600" || fallo "1c. permisos"
curl -fs "http://127.0.0.1:${PUERTO}/" | grep -qi "<html" && ok "1d. la interfaz responde en /" || fallo "1d. /"
curl -fs "http://127.0.0.1:${PUERTO}/api/health" >/dev/null && ok "1e. /api/health responde" || fallo "1e. health"
CODIGO="$(curl -s -o /dev/null -w '%{http_code}' -X POST "http://127.0.0.1:${PUERTO}/api/identidad/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${CLAVE_ADMIN}\"}")"
[ "$CODIGO" = "200" ] && ok "1f. el login del Administrador creado funciona" || fallo "1f. login ($CODIGO)"
grep -q "http://" "$TMP/salida1.txt" && grep -q "alumnos deben entrar" "$TMP/salida1.txt" && ok "1g. imprime las URLs para los alumnos" || fallo "1g. URLs"

# 5. Acceso por la IP de la red local desde esta misma máquina (sustituye al otro dispositivo).
IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
if [ -n "$IP" ]; then
  curl -fs "http://${IP}:${PUERTO}/api/health" >/dev/null && ok "5. responde por la IP local ${IP}" || fallo "5. IP local"
else
  echo "SKIP 5. sin IP de red local detectada"
fi

# 2. Segunda ejecución: no pisa .env.local ni el Administrador.
HASH1="$(shasum "$COGNION_LOCAL_ENV" | awk '{print $1}')"
scripts/local/detener.sh >/dev/null
scripts/local/levantar.sh --fondo >"$TMP/salida2.txt" 2>&1 || { cat "$TMP/salida2.txt"; fallo "2. segunda ejecución"; }
[ "$HASH1" = "$(shasum "$COGNION_LOCAL_ENV" | awk '{print $1}')" ] && [ "$(en "$BASE" "SELECT count(*) FROM administrador")" = "1" ] \
  && ok "2. segunda ejecución: .env.local y Administrador intactos" || fallo "2. pisó algo"
scripts/local/detener.sh >/dev/null
sleep 1
curl -fs "http://127.0.0.1:${PUERTO}/api/health" >/dev/null 2>&1 && fallo "detener.sh no detuvo el servidor" || ok "2b. detener.sh detiene el servidor"

# 3. PostgreSQL inaccesible → mensaje claro, exit != 0, sin traza.
printf 'ENTORNO=local\nEMAIL_MODO=consola\nSECRET_KEY=%s\nDATABASE_URL=postgresql+asyncpg://u:p@127.0.0.1:5999/x\n' "$(openssl rand -hex 32)" > "$TMP/env.caido"
if COGNION_LOCAL_ENV="$TMP/env.caido" scripts/local/levantar.sh --fondo >"$TMP/salida3.txt" 2>&1; then
  fallo "3. debería terminar con exit != 0"
elif grep -q "ERROR: PostgreSQL no responde" "$TMP/salida3.txt" && ! grep -q "Traceback" "$TMP/salida3.txt"; then
  ok "3. Postgres apagado → mensaje claro, exit != 0, sin traza"
else
  cat "$TMP/salida3.txt"; fallo "3. mensaje"
fi

# 4. La base de desarrollo no se modificó.
[ "$ANTES" = "$(huella)" ] && ok "4. la base de desarrollo quedó intacta" || fallo "4. cambió la base de desarrollo"
echo "Despliegue local verificado."
