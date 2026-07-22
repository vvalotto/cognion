#!/usr/bin/env bash
# Driver de smoke test para el backend de Cognión (FastAPI + PostgreSQL).
# Levanta el server, ejercita el flujo real de alta de usuarios/comisión/
# asignación de docente, verifica el caso de error (email duplicado -> 409),
# limpia los datos de prueba y baja el server.
#
# Uso: .claude/skills/run-cognion/smoke.sh   (desde la raíz del repo)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PORT="${COGNION_SMOKE_PORT:-8000}"
BASE="http://localhost:${PORT}"
LOG=$(mktemp -t cognion-backend.XXXXXX.log)
DB_URL="postgresql://user:password@localhost:5432/cognion"
EMAIL_PREFIX="smoketest-$$"

cleanup() {
  local exit_code=$?
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
  # Best-effort: borrar cualquier dato de prueba de esta corrida.
  psql "$DB_URL" -q -c "
    DELETE FROM comision_docentes WHERE comision_id IN (SELECT id FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%'));
    DELETE FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%');
    DELETE FROM administrador WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%');
    DELETE FROM docente WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%');
    DELETE FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%';
  " >/dev/null 2>&1 || true
  exit "$exit_code"
}
trap cleanup EXIT

echo "== Postgres =="
pg_isready -q || { echo "Postgres no responde en localhost:5432 — arrancalo con: brew services start postgresql@16" >&2; exit 1; }
echo "OK"

echo "== Arrancando backend (puerto ${PORT}) =="
.venv/bin/uvicorn src.app:app --port "$PORT" > "$LOG" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 20); do
  if curl -s -o /dev/null "${BASE}/health"; then break; fi
  sleep 0.5
done

echo "== GET /health =="
code=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/health")
[[ "$code" == "200" ]] || { echo "FAIL: /health devolvió $code"; cat "$LOG"; exit 1; }
echo "OK ($code)"

echo "== POST /usuarios (administrador) =="
admin=$(curl -s -X POST "${BASE}/usuarios" -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL_PREFIX}-admin@fiuner.edu.ar\",\"password\":\"Password123!\",\"nombre\":\"Smoke Admin\",\"perfil\":\"administrador\"}")
admin_id=$(echo "$admin" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "OK (id=$admin_id)"

echo "== POST /usuarios (docente) =="
docente=$(curl -s -X POST "${BASE}/usuarios" -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL_PREFIX}-docente@fiuner.edu.ar\",\"password\":\"Password123!\",\"nombre\":\"Smoke Docente\",\"perfil\":\"docente\"}")
docente_id=$(echo "$docente" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "OK (id=$docente_id)"

echo "== POST /comisiones =="
comision=$(curl -s -X POST "${BASE}/comisiones" -H "Content-Type: application/json" \
  -d "{\"materia\":\"Smoke Test\",\"horario\":\"Lunes 18-22\",\"administrador_id\":\"${admin_id}\"}")
comision_id=$(echo "$comision" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "OK (id=$comision_id)"

echo "== POST /comisiones/{id}/docentes =="
code=$(curl -s -o /tmp/cognion-smoke-asignar.json -w '%{http_code}' -X POST "${BASE}/comisiones/${comision_id}/docentes" \
  -H "Content-Type: application/json" -d "{\"docente_id\":\"${docente_id}\"}")
[[ "$code" == "200" ]] || { echo "FAIL: asignar docente devolvió $code"; cat /tmp/cognion-smoke-asignar.json; exit 1; }
grep -q "$docente_id" /tmp/cognion-smoke-asignar.json || { echo "FAIL: docente no aparece en docentes_asignados"; exit 1; }
echo "OK ($code)"

echo "== POST /usuarios con email duplicado (esperado 409) =="
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/usuarios" -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL_PREFIX}-admin@fiuner.edu.ar\",\"password\":\"Password123!\",\"nombre\":\"Otro\",\"perfil\":\"docente\"}")
[[ "$code" == "409" ]] || { echo "FAIL: duplicado devolvió $code, esperado 409"; exit 1; }
echo "OK ($code)"

echo
echo "SMOKE TEST OK — server bajado y datos de prueba limpiados."