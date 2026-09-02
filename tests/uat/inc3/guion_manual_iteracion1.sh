#!/usr/bin/env bash
# Guión de revisión manual — Iteración 1 del Incremento 3 "Actividad Evaluativa"
# (US-3.1.1 a US-3.1.3: crear actividad + iniciar evaluación con set fijo idempotente)
#
# A diferencia de smoke.sh (que solo verifica códigos HTTP y no deja nada corriendo), este
# guión está pensado para que Víctor lo corra y JUZGUE los resultados a ojo — deja el backend
# corriendo y los datos sembrados al final, para poder seguir explorando en Swagger UI
# (http://localhost:8000/docs) si quiere.
#
# Uso: tests/uat/inc3/guion_manual_iteracion1.sh   (desde la raíz del repo)
#
# Al final imprime credenciales, ids y el comando de limpieza — nada se borra solo.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

PORT="${COGNION_UAT_PORT:-8000}"
SMTP_PORT="${COGNION_UAT_SMTP_PORT:-2525}"
BASE="http://localhost:${PORT}"
DB_URL="postgresql://user:password@localhost:5432/cognion"
LOG=$(mktemp -t cognion-uat-inc3.XXXXXX.log)
EMAIL_PREFIX="uat-inc3-iter1-$$"
STARTED_SERVER=0
STARTED_SMTP=0

paso() {
  echo
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

revisar() {
  echo "  🔍 Revisar: $1"
}

echo "== Postgres =="
pg_isready -q || { echo "Postgres no responde en localhost:5432 — arrancalo con: brew services start postgresql@16" >&2; exit 1; }
echo "OK"

echo "== Backend =="
if curl -s -o /dev/null "${BASE}/health"; then
  echo "Ya hay un backend corriendo en ${BASE} — lo reutilizo (no lo bajo al final)."
  echo "  (si no arrancó con SMTP_PORT=${SMTP_PORT}, el paso de invitación al Estudiante puede fallar con 500 — en ese caso bajalo y volvé a correr este guión)"
else
  echo "Arrancando fake SMTP (puerto ${SMTP_PORT})..."
  python3 .claude/skills/run-cognion/fake_smtp.py "$SMTP_PORT" &
  SMTP_PID=$!
  STARTED_SMTP=1
  sleep 0.3
  echo "Arrancando backend en background (log: $LOG)..."
  SMTP_PORT="$SMTP_PORT" .venv/bin/uvicorn src.app:app --port "$PORT" > "$LOG" 2>&1 &
  SERVER_PID=$!
  STARTED_SERVER=1
  for _ in $(seq 1 20); do
    curl -s -o /dev/null "${BASE}/health" && break
    sleep 0.5
  done
  curl -s -o /dev/null "${BASE}/health" || { echo "FAIL: el backend no respondió a tiempo"; cat "$LOG"; exit 1; }
  echo "OK (pid=$SERVER_PID, smtp_pid=$SMTP_PID)"
fi

paso "PASO 0 — Sembrar Administrador, Docente y Estudiante"

ADMIN_EMAIL="${EMAIL_PREFIX}-admin@fiuner.edu.ar"
ADMIN_PASSWORD="Password123!"
ADMIN_NOMBRE="UAT Admin" ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  .venv/bin/python scripts/seed_admin.py >/dev/null
admin_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")
admin_token=$(echo "$admin_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

DOCENTE_EMAIL="${EMAIL_PREFIX}-docente@fiuner.edu.ar"
DOCENTE_PASSWORD="Password123!"
curl -s -X POST "${BASE}/usuarios" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"email\":\"${DOCENTE_EMAIL}\",\"password\":\"${DOCENTE_PASSWORD}\",\"nombre\":\"UAT Docente\",\"perfil\":\"docente\"}" >/dev/null
docente_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"${DOCENTE_EMAIL}\",\"password\":\"${DOCENTE_PASSWORD}\"}")
docente_token=$(echo "$docente_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

MATERIA_NOMBRE="${EMAIL_PREFIX}-materia"
materia=$(curl -s -X POST "${BASE}/materias" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"nombre\":\"${MATERIA_NOMBRE}\"}")
materia_id=$(echo "$materia" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
banco_id=$(echo "$materia" | python3 -c "import sys,json;print(json.load(sys.stdin)['banco_id'])")

admin_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${ADMIN_EMAIL}';")
comision=$(curl -s -X POST "${BASE}/comisiones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"materia_id\":\"${materia_id}\",\"horario\":\"Lunes 18-22\",\"administrador_id\":\"${admin_id}\"}")
comision_id=$(echo "$comision" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

docente_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${DOCENTE_EMAIL}';")
curl -s -X POST "${BASE}/comisiones/${comision_id}/docentes" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" -d "{\"docente_id\":\"${docente_id}\"}" >/dev/null

# El Estudiante se da de alta por invitación (US-1.1.1/1.1.8) — no hay alta directa. El token
# de la invitación no se expone en la respuesta de la API (solo se manda por email), así que
# para este guión se lee directo de la tabla, igual que hace smoke.sh.
ESTUDIANTE_EMAIL="${EMAIL_PREFIX}-estudiante@fiuner.edu.ar"
ESTUDIANTE_PASSWORD="Password123!"
invitacion=$(curl -s -X POST "${BASE}/comisiones/${comision_id}/invitaciones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"docente_id\":\"${docente_id}\",\"email_destinatario\":\"${ESTUDIANTE_EMAIL}\"}")
invitacion_id=$(echo "$invitacion" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
estudiante_token=""
if [[ -n "$invitacion_id" ]]; then
  invitacion_token=$(psql "$DB_URL" -t -A -c "SELECT token FROM invitacion WHERE id = '${invitacion_id}';")
  curl -s -X POST "${BASE}/identidad/registro" -H "Content-Type: application/json" \
    -d "{\"token\":\"${invitacion_token}\",\"nombre\":\"UAT Estudiante\",\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"${ESTUDIANTE_PASSWORD}\"}" >/dev/null
  estudiante_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"${ESTUDIANTE_PASSWORD}\"}")
  estudiante_token=$(echo "$estudiante_login" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
fi

if [[ -z "${estudiante_token:-}" ]]; then
  echo "  ⚠ FALLO sembrando el Estudiante (invitación: $invitacion) — revisá que el fake SMTP"
  echo "     esté arriba y que el backend haya arrancado con SMTP_PORT=${SMTP_PORT}."
  echo "     Los pasos 3+ no van a funcionar sin un token de Estudiante válido."
fi

echo "OK — Docente: ${DOCENTE_EMAIL} / ${DOCENTE_PASSWORD}"
echo "OK — Estudiante: ${ESTUDIANTE_EMAIL} / ${ESTUDIANTE_PASSWORD}"

paso "PASO 1 — Docente carga preguntas activas en el banco (RF-04/05)"
echo "POST /preguntas/verdadero-falso ×3"
for i in 1 2 3; do
  curl -s -X POST "${BASE}/preguntas/verdadero-falso" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"Pregunta UAT V/F #${i}\",\"respuesta_correcta\":true,\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Tema UAT\",\"dificultad\":\"medio\",\"importancia\":\"alto\"}" >/dev/null
done
echo "OK — 3 preguntas activas en el banco de \"${MATERIA_NOMBRE}\""
revisar "GET ${BASE}/bancos/${banco_id}/preguntas (con el header Authorization del docente) — deben aparecer las 3"

paso "PASO 2 — Docente crea una actividad de período abierto vigente (US-3.1.2)"
fecha_apertura=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat())")
fecha_cierre=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)+timedelta(days=7)).isoformat())")
echo "POST ${BASE}/actividades"
echo "  body: {\"materia_id\":\"${materia_id}\",\"fecha_apertura\":\"${fecha_apertura}\",\"fecha_cierre\":\"${fecha_cierre}\",\"cantidad_preguntas\":3,\"cantidad_intentos_permitidos\":1}"
actividad=$(curl -s -X POST "${BASE}/actividades" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"materia_id\":\"${materia_id}\",\"fecha_apertura\":\"${fecha_apertura}\",\"fecha_cierre\":\"${fecha_cierre}\",\"cantidad_preguntas\":3,\"cantidad_intentos_permitidos\":1}")
echo "  respuesta: $actividad"
actividad_id=$(echo "$actividad" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
revisar "código 201, cerrada_manualmente=false, cantidad_preguntas=3"

paso "PASO 3 — Estudiante inicia su evaluación (US-3.1.3, RF-12)"
echo "POST ${BASE}/evaluaciones"
echo "  body: {\"actividad_id\":\"${actividad_id}\"}"
evaluacion=$(curl -s -X POST "${BASE}/evaluaciones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${estudiante_token}" \
  -d "{\"actividad_id\":\"${actividad_id}\"}")
echo "  respuesta: $evaluacion"
evaluacion_id=$(echo "$evaluacion" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
revisar "código 200, estado=EnCurso, preguntas_asignadas trae exactamente 3 elementos, cada uno con pregunta_id + orden (0,1,2)"
revisar "los pregunta_id de preguntas_asignadas corresponden a las 3 preguntas cargadas en el Paso 1 (comparalas con el GET del banco)"

paso "PASO 4 — Reconexión: repetir el mismo POST /evaluaciones (INV-AE-05/06)"
echo "POST ${BASE}/evaluaciones (mismo body que el Paso 3)"
evaluacion_2=$(curl -s -X POST "${BASE}/evaluaciones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${estudiante_token}" \
  -d "{\"actividad_id\":\"${actividad_id}\"}")
echo "  respuesta: $evaluacion_2"
revisar "el 'id' debe ser IDÉNTICO al del Paso 3, y preguntas_asignadas debe ser el MISMO set en el MISMO orden — no un sorteo nuevo"

paso "PASO 5 — Caso de error: iniciar evaluación antes de la apertura"
apertura_futura=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)+timedelta(days=1)).isoformat())")
cierre_futuro=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)+timedelta(days=8)).isoformat())")
actividad_futura=$(curl -s -X POST "${BASE}/actividades" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"materia_id\":\"${materia_id}\",\"fecha_apertura\":\"${apertura_futura}\",\"fecha_cierre\":\"${cierre_futuro}\",\"cantidad_preguntas\":3,\"cantidad_intentos_permitidos\":1}")
actividad_futura_id=$(echo "$actividad_futura" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
echo "POST ${BASE}/evaluaciones con actividad_id de una actividad que abre mañana"
rechazo=$(curl -s -w '\n%{http_code}' -X POST "${BASE}/evaluaciones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${estudiante_token}" \
  -d "{\"actividad_id\":\"${actividad_futura_id}\"}")
echo "  respuesta: $rechazo"
revisar "código 422, el mensaje de error (\"detail\") debe ser entendible para un Estudiante — ¿le queda claro por qué lo rechazó?"

paso "PASO 6 — Caso de error: Docente intenta iniciar una evaluación (RBAC)"
echo "POST ${BASE}/evaluaciones con el token del Docente"
rechazo_rol=$(curl -s -w '\n%{http_code}' -X POST "${BASE}/evaluaciones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"actividad_id\":\"${actividad_id}\"}")
echo "  respuesta: $rechazo_rol"
revisar "código 403"

paso "PASO 7 — Explorar libremente (opcional)"
echo "El backend sigue corriendo en ${BASE} — Swagger UI: ${BASE}/docs"
echo "Podés pegar cualquiera de los tokens de abajo en el botón 'Authorize' y seguir probando"
echo "a mano (ej. actividad_id/estudiante_id inexistentes, cantidad_preguntas mayor a las"
echo "activas, fechas límite, etc.)."

echo
echo "════════════════════════════════════════════════════════════════════════════"
echo "  RESUMEN — credenciales e ids de esta corrida"
echo "════════════════════════════════════════════════════════════════════════════"
echo "  Backend:              ${BASE}  (Swagger: ${BASE}/docs)"
echo "  Administrador:        ${ADMIN_EMAIL} / ${ADMIN_PASSWORD}"
echo "  Docente:               ${DOCENTE_EMAIL} / ${DOCENTE_PASSWORD}"
echo "  Estudiante:            ${ESTUDIANTE_EMAIL} / ${ESTUDIANTE_PASSWORD}"
echo "  materia_id:            ${materia_id}"
echo "  banco_id:               ${banco_id}"
echo "  actividad_id (vigente): ${actividad_id}"
echo "  actividad_id (futura):  ${actividad_futura_id}"
echo "  evaluacion_id:           ${evaluacion_id}"
echo
if [[ "$STARTED_SERVER" == "1" ]]; then
  echo "  Este guión arrancó el backend (pid=$SERVER_PID, log=$LOG) — sigue corriendo."
  echo "  Para bajarlo: kill $SERVER_PID"
fi
echo
echo "  Para limpiar los datos de esta corrida cuando termines de revisar, corré:"
echo "  tests/uat/inc3/limpiar_uat.sh '${EMAIL_PREFIX}'"
echo
echo "  Anotá los hallazgos en quality/reports/uat/inc3/hallazgos-revision-manual.md"
echo "  (plantilla ya creada, clasificación de severidad en docs/plans/PROCEDIMIENTO-UAT.md §8)"
