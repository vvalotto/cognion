#!/usr/bin/env bash
# Driver de smoke test para el backend de Cognión (FastAPI + PostgreSQL).
# Levanta el server, hace bootstrap del primer Administrador (ADR-016,
# scripts/seed_admin.py — POST /usuarios está protegido por RBAC desde
# US-1.1.5, no hay forma de crearlo vía HTTP sin loguearse primero), ejercita
# el flujo real de alta de usuarios/comisión/asignación de docente,
# invitación + registro de Estudiante (US-1.1.1/1.1.2/1.1.8), el flujo de
# Banco de Preguntas (US-2.1.1 a US-2.1.13: alta de materia, carga de pregunta
# de opción múltiple y de verdadero/falso, filtrado, edición y baja lógica),
# el flujo de gestión de cuentas (US-2.2.1 a US-2.2.5: bloqueo automático tras
# 3 intentos fallidos de login o de cambio de contraseña propio, listado/
# detalle/reseteo de cuentas por Administrador, desbloqueo), verifica casos
# de error (email duplicado -> 409, token vencido -> 422, opciones inválidas
# -> 422), limpia los datos de prueba y baja el server.
#
# Uso: .claude/skills/run-cognion/smoke.sh   (desde la raíz del repo)
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

PORT="${COGNION_SMOKE_PORT:-8000}"
SMTP_PORT="${COGNION_SMOKE_SMTP_PORT:-2525}"
BASE="http://localhost:${PORT}"
LOG=$(mktemp -t cognion-backend.XXXXXX.log)
DB_URL="postgresql://user:password@localhost:5432/cognion"
EMAIL_PREFIX="smoketest-$$"

cleanup() {
  local exit_code=$?
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
  if [[ -n "${SMTP_PID:-}" ]] && kill -0 "$SMTP_PID" 2>/dev/null; then
    kill "$SMTP_PID" 2>/dev/null || true
  fi
  # Best-effort: borrar cualquier dato de prueba de esta corrida.
  # Orden estricto por dependencias de FK — estudiante.comision_id referencia comision.id,
  # así que estudiante debe borrarse ANTES que comision (si no, la FK bloquea el DELETE de
  # comision y psql hace rollback de todo el bloque, aunque cada DELETE haya reportado éxito
  # — mismo gotcha documentado en run-cognion/SKILL.md).
  psql "$DB_URL" -q -c "
    DELETE FROM invitacion WHERE comision_id IN (SELECT id FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%'));
    DELETE FROM estudiante WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%');
    DELETE FROM comision_docentes WHERE comision_id IN (SELECT id FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%'));
    DELETE FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%');
    DELETE FROM administrador WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%');
    DELETE FROM docente WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%');
    DELETE FROM usuario WHERE email LIKE '${EMAIL_PREFIX}%';
    DELETE FROM pregunta_plantilla WHERE banco_id IN (SELECT id FROM banco WHERE materia_id IN (SELECT id FROM materia WHERE nombre LIKE '${EMAIL_PREFIX}%'));
    DELETE FROM banco WHERE materia_id IN (SELECT id FROM materia WHERE nombre LIKE '${EMAIL_PREFIX}%');
    DELETE FROM materia WHERE nombre LIKE '${EMAIL_PREFIX}%';
  " >/dev/null 2>&1 || true
  exit "$exit_code"
}
trap cleanup EXIT

echo "== Postgres =="
pg_isready -q || { echo "Postgres no responde en localhost:5432 — arrancalo con: brew services start postgresql@16" >&2; exit 1; }
echo "OK"

echo "== Arrancando fake SMTP (puerto ${SMTP_PORT}) =="
python3 .claude/skills/run-cognion/fake_smtp.py "$SMTP_PORT" &
SMTP_PID=$!
sleep 0.3
echo "OK"

echo "== Arrancando backend (puerto ${PORT}) =="
SMTP_PORT="$SMTP_PORT" .venv/bin/uvicorn src.app:app --port "$PORT" > "$LOG" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 20); do
  if curl -s -o /dev/null "${BASE}/health"; then break; fi
  sleep 0.5
done

echo "== GET /health =="
code=$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/health")
[[ "$code" == "200" ]] || { echo "FAIL: /health devolvió $code"; cat "$LOG"; exit 1; }
echo "OK ($code)"

echo "== Bootstrap Administrador (scripts/seed_admin.py, ADR-016) =="
ADMIN_EMAIL="${EMAIL_PREFIX}-admin@fiuner.edu.ar"
ADMIN_NOMBRE="Smoke Admin" ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_PASSWORD="Password123!" \
  .venv/bin/python scripts/seed_admin.py
echo "OK"

echo "== POST /identidad/login (administrador) =="
admin_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"Password123!\"}")
admin_token=$(echo "$admin_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "OK (token obtenido)"

echo "== POST /usuarios (docente) =="
docente=$(curl -s -X POST "${BASE}/usuarios" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"email\":\"${EMAIL_PREFIX}-docente@fiuner.edu.ar\",\"password\":\"Password123!\",\"nombre\":\"Smoke Docente\",\"perfil\":\"docente\"}")
docente_id=$(echo "$docente" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "OK (id=$docente_id)"

echo "== POST /identidad/login (docente) =="
docente_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL_PREFIX}-docente@fiuner.edu.ar\",\"password\":\"Password123!\"}")
docente_token=$(echo "$docente_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
echo "OK (token obtenido)"

MATERIA_NOMBRE="${EMAIL_PREFIX}-materia"

echo "== POST /materias (docente) =="
# Comisión referencia Materia por puerto desde US-2.1.2 — la materia (BC Banco de Preguntas)
# debe existir antes de poder crear la comisión que la referencia.
materia=$(curl -s -X POST "${BASE}/materias" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"nombre\":\"${MATERIA_NOMBRE}\"}")
materia_id=$(echo "$materia" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
banco_id=$(echo "$materia" | python3 -c "import sys,json;print(json.load(sys.stdin)['banco_id'])")
echo "OK (materia_id=$materia_id, banco_id=$banco_id)"

echo "== POST /comisiones =="
# admin_id no viene en LoginResponse — se resuelve por psql, es el único id que necesitamos
# de un Usuario creado fuera de la API (bootstrap, scripts/seed_admin.py).
admin_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${ADMIN_EMAIL}';")
comision=$(curl -s -X POST "${BASE}/comisiones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"materia_id\":\"${materia_id}\",\"horario\":\"Lunes 18-22\",\"administrador_id\":\"${admin_id}\"}")
comision_id=$(echo "$comision" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "OK (id=$comision_id)"

echo "== POST /comisiones/{id}/docentes =="
code=$(curl -s -o /tmp/cognion-smoke-asignar.json -w '%{http_code}' -X POST "${BASE}/comisiones/${comision_id}/docentes" \
  -H "Content-Type: application/json" -H "Authorization: Bearer ${admin_token}" \
  -d "{\"docente_id\":\"${docente_id}\"}")
[[ "$code" == "200" ]] || { echo "FAIL: asignar docente devolvió $code"; cat /tmp/cognion-smoke-asignar.json; exit 1; }
grep -q "$docente_id" /tmp/cognion-smoke-asignar.json || { echo "FAIL: docente no aparece en docentes_asignados"; exit 1; }
echo "OK ($code)"

echo "== POST /comisiones/{id}/invitaciones (docente) =="
# El use case manda el email de forma síncrona antes de devolver la invitación (US-1.1.1) —
# sin un SMTP disponible este paso fallaría con 500. fake_smtp.py (arrancado arriba) cubre eso
# para smoke testing local. Si por algún motivo no está disponible, el paso se reporta como
# omitido en vez de fallar todo el smoke test.
invitacion_code=$(curl -s -o /tmp/cognion-smoke-invitacion.json -w '%{http_code}' -X POST "${BASE}/comisiones/${comision_id}/invitaciones" \
  -H "Content-Type: application/json" -H "Authorization: Bearer ${docente_token}" \
  -d "{\"docente_id\":\"${docente_id}\",\"email_destinatario\":\"${EMAIL_PREFIX}-estudiante@fiuner.edu.ar\"}")

if [[ "$invitacion_code" == "201" ]]; then
  invitacion_id=$(python3 -c "import json;print(json.load(open('/tmp/cognion-smoke-invitacion.json'))['id'])")
  # El token no se expone en la respuesta de la API (solo se manda por email, US-1.1.1) — se
  # lee directo de la tabla para poder ejercitar el registro end-to-end.
  invitacion_token=$(psql "$DB_URL" -t -A -c "SELECT token FROM invitacion WHERE id = '${invitacion_id}';")
  echo "OK (id=$invitacion_id)"

  echo "== POST /identidad/registro con invitación vigente (US-1.1.8) =="
  registro=$(curl -s -X POST "${BASE}/identidad/registro" -H "Content-Type: application/json" \
    -d "{\"token\":\"${invitacion_token}\",\"nombre\":\"Smoke Estudiante\",\"email\":\"${EMAIL_PREFIX}-estudiante@fiuner.edu.ar\",\"password\":\"Password123!\"}")
  estudiante_materia=$(echo "$registro" | python3 -c "import sys,json;print(json.load(sys.stdin)['materia'])")
  [[ "$estudiante_materia" == "$MATERIA_NOMBRE" ]] || { echo "FAIL: materia devuelta '$estudiante_materia', esperada '$MATERIA_NOMBRE'"; exit 1; }
  echo "OK (materia=$estudiante_materia)"

  echo "== POST /identidad/registro con token ya usado (esperado 422) =="
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/identidad/registro" -H "Content-Type: application/json" \
    -d "{\"token\":\"${invitacion_token}\",\"nombre\":\"Otro\",\"email\":\"${EMAIL_PREFIX}-otro@fiuner.edu.ar\",\"password\":\"Password123!\"}")
  [[ "$code" == "422" ]] || { echo "FAIL: registro con token ya usado devolvió $code, esperado 422"; exit 1; }
  echo "OK ($code)"

  ESTUDIANTE_EMAIL="${EMAIL_PREFIX}-estudiante@fiuner.edu.ar"
  estudiante_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${ESTUDIANTE_EMAIL}';")

  echo "== Flujo de gestión de cuentas (Iteración 2, US-2.2.1 a US-2.2.5) =="

  echo "== POST /identidad/login (estudiante, password incorrecta, intento 1/3) =="
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"incorrecta\"}")
  [[ "$code" == "401" ]] || { echo "FAIL: login con password incorrecta devolvió $code, esperado 401"; exit 1; }
  echo "OK ($code)"

  echo "== POST /identidad/login (estudiante, password incorrecta, intento 2/3) =="
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"incorrecta\"}")
  [[ "$code" == "401" ]] || { echo "FAIL: login con password incorrecta devolvió $code, esperado 401"; exit 1; }
  echo "OK ($code)"

  echo "== POST /identidad/login (estudiante, password incorrecta, intento 3/3 — bloquea la cuenta) =="
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"incorrecta\"}")
  [[ "$code" == "401" ]] || { echo "FAIL: 3er intento fallido devolvió $code, esperado 401"; exit 1; }
  echo "OK ($code)"

  echo "== POST /identidad/login (estudiante, password CORRECTA, esperado 403 — cuenta bloqueada, INV-ID-10) =="
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"Password123!\"}")
  [[ "$code" == "403" ]] || { echo "FAIL: login con password correcta sobre cuenta bloqueada devolvió $code, esperado 403"; exit 1; }
  echo "OK ($code)"

  echo "== GET /usuarios?estado=bloqueada (administrador) — la cuenta debe aparecer (US-2.2.2) =="
  listado_json=$(curl -s "${BASE}/usuarios?estado=bloqueada" -H "Authorization: Bearer ${admin_token}")
  echo "$listado_json" | grep -q "$estudiante_id" || { echo "FAIL: cuenta bloqueada no aparece en el listado filtrado"; exit 1; }
  echo "OK"

  echo "== GET /usuarios/{id} (administrador) — detalle con bloqueada=true (US-2.2.3) =="
  detalle_json=$(curl -s "${BASE}/usuarios/${estudiante_id}" -H "Authorization: Bearer ${admin_token}")
  echo "$detalle_json" | grep -q '"bloqueada":true' || { echo "FAIL: detalle no refleja bloqueada=true"; exit 1; }
  echo "OK"

  echo "== POST /usuarios/{id}/resetear-password (administrador) — desbloquea (US-2.2.4) =="
  reset_json=$(curl -s -X POST "${BASE}/usuarios/${estudiante_id}/resetear-password" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${admin_token}" \
    -d '{"password_nueva":"Reseteada123!"}')
  echo "$reset_json" | grep -q '"bloqueada":false' || { echo "FAIL: reseteo no desbloqueó la cuenta"; exit 1; }
  echo "OK"

  echo "== POST /identidad/login (estudiante, password reseteada) — debe permitir login (desbloqueada) =="
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"Reseteada123!\"}")
  [[ "$code" == "200" ]] || { echo "FAIL: login tras reseteo devolvió $code, esperado 200"; exit 1; }
  echo "OK ($code)"

  echo "== PUT /usuarios/me/password (estudiante) — password_actual incorrecta, fallo 1/3 (US-2.2.5) =="
  estudiante_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"Reseteada123!\"}")
  estudiante_token=$(echo "$estudiante_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
  detalle_error=$(curl -s -o /tmp/cognion-smoke-cambiar-password.json -w '%{http_code}' -X PUT "${BASE}/usuarios/me/password" \
    -H "Content-Type: application/json" -H "Authorization: Bearer ${estudiante_token}" \
    -d '{"password_actual":"incorrecta","password_nueva":"Nueva123!"}')
  [[ "$detalle_error" == "401" ]] || { echo "FAIL: cambio con password_actual incorrecta devolvió $detalle_error, esperado 401"; exit 1; }
  grep -q '"intentos_restantes":2' /tmp/cognion-smoke-cambiar-password.json || { echo "FAIL: intentos_restantes no es 2 tras el 1er fallo"; cat /tmp/cognion-smoke-cambiar-password.json; exit 1; }
  echo "OK (401, intentos_restantes=2)"

  echo "== PUT /usuarios/me/password (estudiante) — password_actual incorrecta, fallo 2/3 =="
  code=$(curl -s -o /tmp/cognion-smoke-cambiar-password.json -w '%{http_code}' -X PUT "${BASE}/usuarios/me/password" \
    -H "Content-Type: application/json" -H "Authorization: Bearer ${estudiante_token}" \
    -d '{"password_actual":"incorrecta","password_nueva":"Nueva123!"}')
  [[ "$code" == "401" ]] || { echo "FAIL: 2do fallo devolvió $code, esperado 401"; exit 1; }
  grep -q '"intentos_restantes":1' /tmp/cognion-smoke-cambiar-password.json || { echo "FAIL: intentos_restantes no es 1 tras el 2do fallo"; cat /tmp/cognion-smoke-cambiar-password.json; exit 1; }
  echo "OK (401, intentos_restantes=1)"

  echo "== PUT /usuarios/me/password (estudiante) — password_actual incorrecta, fallo 3/3 (bloquea) =="
  code=$(curl -s -o /tmp/cognion-smoke-cambiar-password.json -w '%{http_code}' -X PUT "${BASE}/usuarios/me/password" \
    -H "Content-Type: application/json" -H "Authorization: Bearer ${estudiante_token}" \
    -d '{"password_actual":"incorrecta","password_nueva":"Nueva123!"}')
  [[ "$code" == "401" ]] || { echo "FAIL: 3er fallo devolvió $code, esperado 401"; exit 1; }
  grep -q '"bloqueada":true' /tmp/cognion-smoke-cambiar-password.json || { echo "FAIL: 3er fallo no marcó bloqueada=true"; cat /tmp/cognion-smoke-cambiar-password.json; exit 1; }
  echo "OK (401, bloqueada=true)"

  echo "== POST /identidad/login (estudiante) — confirma bloqueo cruzado por cambiar_password (esperado 403) =="
  code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"Reseteada123!\"}")
  [[ "$code" == "403" ]] || { echo "FAIL: login tras bloqueo por cambiar_password devolvió $code, esperado 403"; exit 1; }
  echo "OK ($code)"

  echo "== POST /usuarios/{id}/resetear-password (administrador) — desbloquea de nuevo, deja password conocida =="
  reset_json=$(curl -s -X POST "${BASE}/usuarios/${estudiante_id}/resetear-password" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${admin_token}" \
    -d '{"password_nueva":"Final123!"}')
  echo "$reset_json" | grep -q '"bloqueada":false' || { echo "FAIL: segundo reseteo no desbloqueó la cuenta"; exit 1; }
  echo "OK"

  echo "== PUT /usuarios/me/password (estudiante) — cambio exitoso con password_actual correcta =="
  estudiante_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"Final123!\"}")
  estudiante_token=$(echo "$estudiante_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
  code=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "${BASE}/usuarios/me/password" \
    -H "Content-Type: application/json" -H "Authorization: Bearer ${estudiante_token}" \
    -d '{"password_actual":"Final123!","password_nueva":"UltimaOk123!"}')
  [[ "$code" == "204" ]] || { echo "FAIL: cambio de contraseña exitoso devolvió $code, esperado 204"; exit 1; }
  echo "OK ($code)"
else
  echo "SKIPPED ($invitacion_code) — ver /tmp/cognion-smoke-invitacion.json y $LOG"
  echo "SKIPPED — depende de la invitación anterior"
fi

echo "== POST /usuarios con email duplicado (esperado 409) =="
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/usuarios" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"email\":\"${EMAIL_PREFIX}-docente@fiuner.edu.ar\",\"password\":\"Password123!\",\"nombre\":\"Otro\",\"perfil\":\"docente\"}")
[[ "$code" == "409" ]] || { echo "FAIL: duplicado devolvió $code, esperado 409"; exit 1; }
echo "OK ($code)"

echo "== POST /preguntas/opcion-multiple (banco de la materia creada arriba) =="
pregunta_om=$(curl -s -X POST "${BASE}/preguntas/opcion-multiple" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"¿Cuál es la capital de Entre Ríos?\",\"opciones\":[{\"texto\":\"Paraná\",\"es_correcta\":true},{\"texto\":\"Concordia\",\"es_correcta\":false}],\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Geografía\",\"dificultad\":\"bajo\",\"importancia\":\"medio\"}")
pregunta_om_id=$(echo "$pregunta_om" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "OK (id=$pregunta_om_id)"

echo "== POST /preguntas/verdadero-falso =="
pregunta_vf=$(curl -s -X POST "${BASE}/preguntas/verdadero-falso" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"FastAPI es síncrono por defecto.\",\"respuesta_correcta\":false,\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Arquitectura\",\"dificultad\":\"medio\",\"importancia\":\"alto\"}")
pregunta_vf_id=$(echo "$pregunta_vf" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
echo "OK (id=$pregunta_vf_id)"

echo "== GET /bancos/{id}/preguntas (sin filtro, deben aparecer ambas) =="
banco_json=$(curl -s "${BASE}/bancos/${banco_id}/preguntas" -H "Authorization: Bearer ${docente_token}")
echo "$banco_json" | grep -q "$pregunta_om_id" || { echo "FAIL: pregunta opción múltiple no aparece en el banco"; exit 1; }
echo "$banco_json" | grep -q "$pregunta_vf_id" || { echo "FAIL: pregunta verdadero/falso no aparece en el banco"; exit 1; }
echo "OK (2 preguntas)"

echo "== PUT /preguntas/{id} (editar texto de la pregunta de opción múltiple) =="
editada=$(curl -s -X PUT "${BASE}/preguntas/${pregunta_om_id}" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"texto\":\"¿Cuál es la capital de la provincia de Entre Ríos?\",\"opciones\":[{\"texto\":\"Paraná\",\"es_correcta\":true},{\"texto\":\"Concordia\",\"es_correcta\":false}],\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Geografía\",\"dificultad\":\"bajo\",\"importancia\":\"medio\"}")
texto_editado=$(echo "$editada" | python3 -c "import sys,json;print(json.load(sys.stdin)['texto'])")
[[ "$texto_editado" == "¿Cuál es la capital de la provincia de Entre Ríos?" ]] || { echo "FAIL: texto editado no se reflejó, devolvió '$texto_editado'"; exit 1; }
echo "OK (texto actualizado)"

echo "== DELETE /preguntas/{id} (baja lógica de la pregunta V/F) =="
code=$(curl -s -o /dev/null -w '%{http_code}' -X DELETE "${BASE}/preguntas/${pregunta_vf_id}" \
  -H "Authorization: Bearer ${docente_token}")
[[ "$code" == "204" ]] || { echo "FAIL: eliminar pregunta devolvió $code, esperado 204"; exit 1; }
echo "OK ($code)"

echo "== GET /bancos/{id}/preguntas (la pregunta eliminada ya no debe aparecer, INV-BP-04) =="
banco_json=$(curl -s "${BASE}/bancos/${banco_id}/preguntas" -H "Authorization: Bearer ${docente_token}")
echo "$banco_json" | grep -q "$pregunta_vf_id" && { echo "FAIL: pregunta eliminada sigue apareciendo en el banco"; exit 1; }
echo "$banco_json" | grep -q "$pregunta_om_id" || { echo "FAIL: pregunta opción múltiple ya no aparece tras la baja de la otra"; exit 1; }
echo "OK (1 pregunta activa)"

echo "== POST /preguntas/opcion-multiple con opciones inválidas (0 correctas, esperado 422) =="
code=$(curl -s -o /dev/null -w '%{http_code}' -X POST "${BASE}/preguntas/opcion-multiple" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"Pregunta inválida\",\"opciones\":[{\"texto\":\"A\",\"es_correcta\":false},{\"texto\":\"B\",\"es_correcta\":false}],\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Geografía\",\"dificultad\":\"bajo\",\"importancia\":\"medio\"}")
[[ "$code" == "422" ]] || { echo "FAIL: opciones inválidas devolvió $code, esperado 422"; exit 1; }
echo "OK ($code)"

echo
echo "SMOKE TEST OK — server bajado y datos de prueba limpiados."
