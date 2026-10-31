#!/usr/bin/env bash
# Levanta Cognión para una prueba en la red local (US-8.5.3). Idempotente: volver a ejecutarlo reutiliza
# lo ya creado. Usa una base PROPIA (cognion_local), nunca la de desarrollo.
#
# Uso:  scripts/local/levantar.sh [--fondo]
#   --fondo   deja el servidor en segundo plano (se detiene con scripts/local/detener.sh)
#
# Variables opcionales (las usa la verificación para no tocar nada real):
#   COGNION_LOCAL_BASE   nombre de la base            (default cognion_local)
#   COGNION_LOCAL_PUERTO puerto del servidor          (default 8000)
#   COGNION_LOCAL_ENV    archivo de configuración     (default .env.local)
#   COGNION_LOCAL_LOGS   carpeta de logs y PID        (default logs/local)
#   PGADMIN_USER         rol con CREATEDB             (default: el usuario del SO)
#   ADMIN_NOMBRE/ADMIN_EMAIL/ADMIN_PASSWORD  datos del Administrador (si no, se piden por terminal)
set -euo pipefail
cd "$(dirname "$0")/../.."

FONDO=0
[ "${1:-}" = "--fondo" ] && FONDO=1
BASE="${COGNION_LOCAL_BASE:-cognion_local}"
PUERTO="${COGNION_LOCAL_PUERTO:-8000}"
ENV_LOCAL="${COGNION_LOCAL_ENV:-.env.local}"
LOGS="${COGNION_LOCAL_LOGS:-logs/local}"
PID_ARCHIVO="$LOGS/servidor.pid"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }
paso() { echo "• $1"; }

# 1. Prerrequisitos -----------------------------------------------------------------------------------
paso "Verificando prerrequisitos"
for cmd in node npm openssl caffeinate psql pg_isready curl; do
  command -v "$cmd" >/dev/null 2>&1 || abortar "Falta el comando '$cmd'." "Instalalo (ej. 'brew install ${cmd}') y volvé a ejecutar."
done
[ -x .venv/bin/python ] || abortar "No existe el entorno .venv." "Creálo con 'uv sync' y volvé a ejecutar."
if lsof -nP -iTCP:"$PUERTO" -sTCP:LISTEN >/dev/null 2>&1; then
  abortar "El puerto $PUERTO ya está en uso." "Si es un servidor anterior: scripts/local/detener.sh (o definí COGNION_LOCAL_PUERTO)."
fi

# URL de origen: la de .env.local si ya existe; si no, la de desarrollo (solo para tomar usuario, host y puerto).
if [ -f "$ENV_LOCAL" ]; then
  ORIGEN="$(grep -E '^DATABASE_URL=' "$ENV_LOCAL" | cut -d= -f2-)"
else
  ORIGEN="${DATABASE_URL:-$( (grep -E '^DATABASE_URL=' .env 2>/dev/null || true) | cut -d= -f2-)}"
  [ -n "$ORIGEN" ] || abortar "No encuentro un DATABASE_URL de origen." "Creá .env desde .env.example (se usa solo para tomar usuario y host de PostgreSQL)."
fi
leer() { python3 -c "from urllib.parse import urlparse; import sys; u=urlparse(sys.argv[1]); print({'u':u.username or '','p':u.password or '','h':u.hostname or 'localhost','n':u.port or 5432,'b':u.path.lstrip('/')}[sys.argv[2]])" "$ORIGEN" "$1"; }
USUARIO="$(leer u)"; CLAVE="$(leer p)"; HOST="$(leer h)"; PUERTO_PG="$(leer n)"

pg_isready -q -h "$HOST" -p "$PUERTO_PG" \
  || abortar "PostgreSQL no responde en $HOST:$PUERTO_PG." "Iniciálo (ej. 'brew services start postgresql') y volvé a ejecutar."
# La base de desarrollo es la del .env (o 'cognion'); la de .env.local es, por definición, la propia.
BASE_DEV="$( (grep -E '^DATABASE_URL=' .env 2>/dev/null || true) | cut -d= -f2- | sed 's|.*/||')"
[ "$BASE" != "$BASE_DEV" ] && [ "$BASE" != "cognion" ] \
  || abortar "La base '$BASE' es la de desarrollo." "Esta herramienta nunca la usa; elegí otro nombre con COGNION_LOCAL_BASE."

admin() { psql -h "$HOST" -p "$PUERTO_PG" ${PGADMIN_USER:+-U "$PGADMIN_USER"} -d postgres -qAt -c "$1"; }
en_base() { PGPASSWORD="$CLAVE" psql -h "$HOST" -p "$PUERTO_PG" -U "$USUARIO" -d "$BASE" -qAt -c "$1"; }

# 2. Base propia y .env.local (solo la primera vez) -------------------------------------------------------
paso "Preparando la base '$BASE'"
if [ -z "$(admin "SELECT 1 FROM pg_database WHERE datname='${BASE}'" 2>/dev/null || true)" ]; then
  admin "CREATE DATABASE \"${BASE}\" OWNER \"${USUARIO}\"" >/dev/null 2>&1 \
    || abortar "No pude crear la base '$BASE'." "Hace falta un rol con CREATEDB: PGADMIN_USER=<rol> scripts/local/levantar.sh"
fi
if [ ! -f "$ENV_LOCAL" ]; then
  paso "Creando $ENV_LOCAL (fuera de git)"
  URL_LOCAL="$(python3 -c "from urllib.parse import urlparse; import sys; print(urlparse(sys.argv[1])._replace(path='/'+sys.argv[2]).geturl())" "$ORIGEN" "$BASE")"
  umask 077
  {
    echo "ENTORNO=local"
    echo "EMAIL_MODO=consola"
    echo "SECRET_KEY=$(openssl rand -hex 32)"
    echo "DATABASE_URL=${URL_LOCAL}"
  } > "$ENV_LOCAL"
fi
case "$ENV_LOCAL" in /*) ENV_RUTA="$ENV_LOCAL" ;; *) ENV_RUTA="./$ENV_LOCAL" ;; esac
set -a; . "$ENV_RUTA"; set +a

# 3. Frontend compilado -------------------------------------------------------------------------------
if [ ! -f frontend/dist/index.html ] || [ -n "$(find frontend/src -newer frontend/dist/index.html -print -quit 2>/dev/null)" ]; then
  paso "Compilando el frontend (VITE_API_BASE_URL=/api)"
  [ -d frontend/node_modules ] || (cd frontend && npm ci --silent)
  (cd frontend && VITE_API_BASE_URL=/api npm run build --silent) >/dev/null \
    || abortar "Falló la compilación del frontend." "Corré 'cd frontend && VITE_API_BASE_URL=/api npm run build' para ver el error."
else
  paso "Frontend ya compilado y al día"
fi

# 4. Migraciones --------------------------------------------------------------------------------------
paso "Aplicando migraciones"
.venv/bin/alembic upgrade head >/dev/null 2>&1 \
  || abortar "Fallaron las migraciones." "Corré '.venv/bin/alembic upgrade head' con ese entorno para ver el detalle."

# 5. Administrador ------------------------------------------------------------------------------------
OPERATIVOS="$(en_base "SELECT count(*) FROM administrador a JOIN usuario u ON u.id = a.id WHERE NOT u.deshabilitada")"
if [ "$OPERATIVOS" = "0" ]; then
  paso "No hay un Administrador operativo: creando el primero"
  if [ -z "${ADMIN_NOMBRE:-}" ]; then read -r -p "  Nombre y apellido del Administrador: " ADMIN_NOMBRE; fi
  if [ -z "${ADMIN_EMAIL:-}" ]; then read -r -p "  Email del Administrador: " ADMIN_EMAIL; fi
  export ADMIN_NOMBRE ADMIN_EMAIL
  .venv/bin/python -m src.identidad.frameworks.cli.bootstrap_administrador \
    || abortar "No se creó el Administrador." "Revisá el mensaje de arriba (la contraseña pide 12+ caracteres con mayúscula, número y símbolo)."
else
  paso "Ya hay un Administrador operativo (no se toca)"
fi

# 6. Red local ----------------------------------------------------------------------------------------
IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
if [ -z "$IP" ]; then
  echo "AVISO: no detecté una IP de red local; el sistema solo será accesible desde esta máquina." >&2
  IP="127.0.0.1"
fi
NOMBRE_EQUIPO="$(scutil --get LocalHostName 2>/dev/null || hostname -s)"
export FRONTEND_URL="http://${IP}:${PUERTO}"
export CORS_ALLOWED_ORIGINS="http://${IP}:${PUERTO},http://${NOMBRE_EQUIPO}.local:${PUERTO}"

echo
echo "================================================================"
echo " Cognión local listo. Los alumnos deben entrar a:"
echo "   http://${IP}:${PUERTO}/"
echo "   http://${NOMBRE_EQUIPO}.local:${PUERTO}/   (alternativa por nombre)"
echo
echo " Antes de la clase, comprobá:"
echo "   - Los celulares están en la MISMA red que esta máquina (la red del aula puede aislar clientes)."
echo "   - El firewall de macOS permite conexiones entrantes a Python."
echo "   - Los emails NO se envían: los links (recuperar contraseña) quedan en el log."
echo " Log: ${LOGS}/uvicorn-$(date +%F).log"
echo "================================================================"
echo

# 7. Servidor -----------------------------------------------------------------------------------------
mkdir -p "$LOGS"
LOG="$LOGS/uvicorn-$(date +%F).log"
CMD=(caffeinate -dims .venv/bin/python -m uvicorn src.servidor:servidor --host 0.0.0.0 --port "$PUERTO")

if [ "$FONDO" = "1" ]; then
  nohup "${CMD[@]}" >>"$LOG" 2>&1 &
  echo $! > "$PID_ARCHIVO"
  for _ in $(seq 1 60); do
    curl -fs "http://127.0.0.1:${PUERTO}/api/health" >/dev/null 2>&1 && { echo "Servidor en segundo plano (PID $(cat "$PID_ARCHIVO")). Detenerlo: scripts/local/detener.sh"; exit 0; }
    kill -0 "$(cat "$PID_ARCHIVO")" 2>/dev/null || break
    sleep 0.5
  done
  tail -n 20 "$LOG" >&2
  abortar "El servidor no respondió a tiempo." "Revisá el log: $LOG"
fi
"${CMD[@]}" 2>&1 | tee -a "$LOG"
