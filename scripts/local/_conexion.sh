# Helper para `source` desde respaldar.sh y restaurar.sh (US-8.5.4): deja la conexión a la base local lista.
# Lee COGNION_LOCAL_ENV (default .env.local, creado por levantar.sh). Requiere haber hecho `cd` a la raíz.
ENV_LOCAL="${COGNION_LOCAL_ENV:-.env.local}"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }

[ -f "$ENV_LOCAL" ] || abortar "No existe $ENV_LOCAL." "Ejecutá primero scripts/local/levantar.sh (crea la base y la configuración)."
for cmd in pg_dump pg_restore psql pg_isready shasum python3; do
  command -v "$cmd" >/dev/null 2>&1 || abortar "Falta el comando '$cmd'." "Instalá las herramientas cliente de PostgreSQL (ej. 'brew install postgresql')."
done

ORIGEN="$(grep -E '^DATABASE_URL=' "$ENV_LOCAL" | cut -d= -f2-)"
[ -n "$ORIGEN" ] || abortar "$ENV_LOCAL no tiene DATABASE_URL."
_leer() { python3 -c "from urllib.parse import urlparse; import sys; u=urlparse(sys.argv[1]); print({'u':u.username or '','p':u.password or '','h':u.hostname or 'localhost','n':u.port or 5432,'b':u.path.lstrip('/')}[sys.argv[2]])" "$ORIGEN" "$1"; }
USUARIO="$(_leer u)"; CLAVE="$(_leer p)"; HOST="$(_leer h)"; PUERTO_PG="$(_leer n)"; BASE="$(_leer b)"
pg_isready -q -h "$HOST" -p "$PUERTO_PG" \
  || abortar "PostgreSQL no responde en $HOST:$PUERTO_PG." "Iniciálo (ej. 'brew services start postgresql') y volvé a ejecutar."

# `admin` opera sobre el catálogo (crear/borrar bases, rol con CREATEDB: PGADMIN_USER o el usuario del SO).
admin() { psql -h "$HOST" -p "$PUERTO_PG" ${PGADMIN_USER:+-U "$PGADMIN_USER"} -d postgres -qAt -c "$1"; }
# `en_base <base> <sql>` consulta una base con las credenciales de la app.
en_base() { PGPASSWORD="$CLAVE" psql -h "$HOST" -p "$PUERTO_PG" -U "$USUARIO" -d "$1" -qAt -c "$2"; }
