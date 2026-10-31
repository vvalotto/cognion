#!/usr/bin/env bash
# Verifica scripts/local/respaldar.sh y restaurar.sh (US-8.5.4) contra una base DESCARTABLE con datos sembrados.
# No toca cognion_local, la base de desarrollo ni ~/CognionRespaldos (usa una carpeta temporal).
# Uso: tests/uat/inc8/verificar_respaldo_local.sh   (requiere PostgreSQL local y un rol con CREATEDB)
set -euo pipefail
cd "$(dirname "$0")/../../.."

BASE="cognion_rs_$$"
TMP="$(mktemp -d)"
export COGNION_LOCAL_ENV="$TMP/env.local" COGNION_RESPALDOS="$TMP/respaldos"
unset COGNION_RESPALDOS_N

ORIGEN="${DATABASE_URL:-$(grep -E '^DATABASE_URL=' .env | cut -d= -f2-)}"
leer() { python3 -c "from urllib.parse import urlparse; import sys; u=urlparse(sys.argv[1]); print({'u':u.username,'p':u.password or '','h':u.hostname,'n':u.port or 5432,'b':u.path.lstrip('/')}[sys.argv[2]])" "$ORIGEN" "$1"; }
USUARIO="$(leer u)"; CLAVE="$(leer p)"; HOST="$(leer h)"; PUERTO_PG="$(leer n)"; BASE_DEV="$(leer b)"
URL="postgresql+asyncpg://${USUARIO}:${CLAVE}@${HOST}:${PUERTO_PG}/${BASE}"
admin() { psql -h "$HOST" -p "$PUERTO_PG" ${PGADMIN_USER:+-U "$PGADMIN_USER"} -d postgres -qAt -c "$1"; }
en() { PGPASSWORD="$CLAVE" psql -h "$HOST" -p "$PUERTO_PG" -U "$USUARIO" -d "$1" -qAt -c "$2"; }
limpiar() { admin "DROP DATABASE IF EXISTS \"${BASE}\"" >/dev/null 2>&1 || true; for b in $(admin "SELECT datname FROM pg_database WHERE datname LIKE '${BASE}\_restaurada\_%'" 2>/dev/null); do admin "DROP DATABASE \"$b\"" >/dev/null 2>&1 || true; done; rm -rf "$TMP"; }
trap limpiar EXIT
ok() { echo "OK   $1"; }
fallo() { echo "FAIL $1"; exit 1; }
temporales() { admin "SELECT count(*) FROM pg_database WHERE datname LIKE '${BASE}\_restaurada\_%'"; }
conteo() { en "$BASE" "SELECT (SELECT count(*) FROM usuario)||'/'||(SELECT count(*) FROM events)||'/'||(SELECT count(*) FROM pregunta_plantilla)"; }
[ "$BASE" != "$BASE_DEV" ] || fallo "la base de prueba coincide con la de desarrollo"

# Preparación: base descartable migrada y con datos.
admin "CREATE DATABASE \"${BASE}\" OWNER \"${USUARIO}\"" >/dev/null
printf 'ENTORNO=local\nEMAIL_MODO=consola\nSECRET_KEY=%s\nDATABASE_URL=%s\n' "$(openssl rand -hex 32)" "$URL" > "$COGNION_LOCAL_ENV"
export SECRET_KEY=verificacion
DATABASE_URL="$URL" .venv/bin/alembic upgrade head >/dev/null 2>&1 || fallo "preparación: migraciones"
DATABASE_URL="$URL" ADMIN_NOMBRE="Admin Resp" ADMIN_EMAIL="resp@ejemplo.edu.ar" ADMIN_PASSWORD="Resp#Prueba-2026" \
  .venv/bin/python -m src.identidad.frameworks.cli.bootstrap_administrador >/dev/null 2>&1 || fallo "preparación: administrador"
en "$BASE" "INSERT INTO events (id, aggregate_type, aggregate_id, sequence_number, event_type, payload, occurred_at)
  VALUES (gen_random_uuid(), 'Prueba', gen_random_uuid(), 1, 'Probado', '{}', now());
  INSERT INTO materia (id, nombre, activa) VALUES ('11111111-1111-1111-1111-111111111111', 'Materia de prueba', true);
  INSERT INTO banco (id, materia_id) VALUES ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111');
  INSERT INTO pregunta_plantilla (id, banco_id, tipo, texto, unidad_tematica, tema, dificultad, importancia, activa)
  VALUES (gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'opcion_multiple', 'Texto', 'U1', 'T1', 'BAJA', 'BAJA', true)" >/dev/null
ORIGINAL="$(conteo)"
[ "$ORIGINAL" = "1/1/1" ] && ok "preparación: base con datos (usuarios/eventos/preguntas = $ORIGINAL)" || fallo "preparación: datos $ORIGINAL"

# 1. Respaldo no vacío, legible y con sha256.
scripts/local/respaldar.sh >"$TMP/r1.txt" 2>&1 || { cat "$TMP/r1.txt"; fallo "1. respaldar.sh"; }
DUMP="$(ls -1 "$COGNION_RESPALDOS"/"${BASE}"-*.dump | head -n 1)"
[ -s "$DUMP" ] && pg_restore --list "$DUMP" >/dev/null && ( cd "$COGNION_RESPALDOS" && shasum -a 256 -c "$(basename "$DUMP").sha256" >/dev/null ) \
  && ok "1. respaldo no vacío, legible por pg_restore --list y con sha256 válido" || fallo "1. contenido del respaldo"
[ "$(stat -f %Lp "$COGNION_RESPALDOS")" = "700" ] && ok "1b. carpeta de respaldos con permisos 700" || fallo "1b. permisos"

# 2. Ensayo: restaura a una base temporal, mismos conteos, temporal eliminada.
scripts/local/restaurar.sh "$DUMP" >"$TMP/r2.txt" 2>&1 || { cat "$TMP/r2.txt"; fallo "2. restaurar.sh (ensayo)"; }
grep -q "Ensayo OK" "$TMP/r2.txt" && [ "$(temporales)" = "0" ] && [ "$(conteo)" = "$ORIGINAL" ] \
  && ok "2. ensayo: mismos conteos que el origen y base temporal eliminada" || { cat "$TMP/r2.txt"; fallo "2. ensayo"; }

# 3. Rotación: con N=2 quedan los 2 más recientes.
sleep 1.1; scripts/local/respaldar.sh >/dev/null 2>&1
sleep 1.1; COGNION_RESPALDOS_N=2 scripts/local/respaldar.sh >/dev/null 2>&1
[ "$(ls -1 "$COGNION_RESPALDOS"/*.dump | wc -l | tr -d ' ')" = "2" ] && [ "$(ls -1 "$COGNION_RESPALDOS"/*.sha256 | wc -l | tr -d ' ')" = "2" ] \
  && [ ! -e "$DUMP" ] && ok "3. rotación: se conservan los 2 más recientes (con sus sha256)" || fallo "3. rotación"
DUMP="$(ls -1 "$COGNION_RESPALDOS"/"${BASE}"-*.dump | tail -n 1)"

# 3b. El nombre lleva el de la base y la rotación no toca los respaldos de otra base (hallazgo #10 de la UAT).
case "$(basename "$DUMP")" in "${BASE}"-*.dump) ok "3b. el respaldo se llama como la base respaldada ($(basename "$DUMP" | cut -c1-30)…)" ;; *) fallo "3b. nombre del respaldo" ;; esac
touch "$COGNION_RESPALDOS/otra_base-20200101-000000.dump" "$COGNION_RESPALDOS/otra_base-20200101-000000.dump.sha256"
sleep 1.1; COGNION_RESPALDOS_N=1 scripts/local/respaldar.sh >/dev/null 2>&1
[ -e "$COGNION_RESPALDOS/otra_base-20200101-000000.dump" ] && [ "$(ls -1 "$COGNION_RESPALDOS"/"${BASE}"-*.dump | wc -l | tr -d ' ')" = "1" ] \
  && ok "3c. con N=1 rota solo los respaldos de esta base: el de otra base queda intacto" || fallo "3c. rotación mezclada"
rm -f "$COGNION_RESPALDOS"/otra_base-*
DUMP="$(ls -1 "$COGNION_RESPALDOS"/"${BASE}"-*.dump | tail -n 1)"

# 4. Archivo corrupto: falla con mensaje claro y no toca nada.
head -c 300 "$DUMP" > "$TMP/truncado.dump"
if scripts/local/restaurar.sh "$TMP/truncado.dump" >"$TMP/r4.txt" 2>&1; then fallo "4a. un archivo truncado debería fallar"
elif grep -q "^ERROR:" "$TMP/r4.txt" && [ "$(temporales)" = "0" ] && [ "$(conteo)" = "$ORIGINAL" ] && ! grep -q Traceback "$TMP/r4.txt"; then
  ok "4a. archivo truncado → error claro, base intacta, sin temporales"
else cat "$TMP/r4.txt"; fallo "4a. mensaje"; fi
cp "$DUMP" "$TMP/alterado.dump"; cp "$DUMP.sha256" "$TMP/alterado.dump.sha256"; sed -i '' "s/$(basename "$DUMP")/alterado.dump/" "$TMP/alterado.dump.sha256"
printf 'x' >> "$TMP/alterado.dump"
if scripts/local/restaurar.sh "$TMP/alterado.dump" >"$TMP/r4b.txt" 2>&1; then fallo "4b. sha256 alterado debería fallar"
elif grep -q "sha256" "$TMP/r4b.txt" && [ "$(conteo)" = "$ORIGINAL" ]; then ok "4b. archivo que no coincide con su sha256 → rechazado"
else cat "$TMP/r4b.txt"; fallo "4b. mensaje"; fi

# 5. --sobre-local sin confirmación no hace nada.
en "$BASE" "DELETE FROM pregunta_plantilla" >/dev/null
MODIFICADO="$(conteo)"
if echo "no" | scripts/local/restaurar.sh "$DUMP" --sobre-local >"$TMP/r5.txt" 2>&1; then fallo "5a. sin confirmación debería salir con exit != 0"
elif grep -q "Cancelado" "$TMP/r5.txt" && [ "$(conteo)" = "$MODIFICADO" ]; then ok "5a. --sobre-local sin confirmación → no hace nada"
else cat "$TMP/r5.txt"; fallo "5a. cancelación"; fi

# Extra: si la base cambió después del respaldo, el ensayo lo informa (exit 3).
set +e; scripts/local/restaurar.sh "$DUMP" >"$TMP/r5b.txt" 2>&1; CODIGO=$?; set -e
[ "$CODIGO" = "3" ] && ok "5b. el ensayo detecta que la base actual difiere del respaldo (exit 3)" || { cat "$TMP/r5b.txt"; fallo "5b. exit $CODIGO"; }

# Extra: con confirmación, --sobre-local sí reemplaza la base.
echo "RESTAURAR" | scripts/local/restaurar.sh "$DUMP" --sobre-local >"$TMP/r5c.txt" 2>&1 || { cat "$TMP/r5c.txt"; fallo "5c. --sobre-local confirmado"; }
[ "$(conteo)" = "$ORIGINAL" ] && [ "$(temporales)" = "0" ] && ok "5c. --sobre-local confirmado → la base vuelve al estado del respaldo" || fallo "5c. contenido"
echo "Respaldo y restauración verificados."
