#!/usr/bin/env bash
# Guión de revisión manual — Iteración 1 del Incremento 4 "Portal del estudiante y Analytics"
# (US-4.1.1 a US-4.1.3: RF-15, Estudiante ve su desempeño — backend + frontend)
#
# Siembra los datos (materia con banco de 4 preguntas V/F, 2 actividades de período abierto ya
# finalizadas con resultado conocido, y una segunda materia sin evaluaciones) y deja el backend
# corriendo para que Víctor navegue la pantalla "Mi desempeño" real (frontend Vite) y confirme
# que los números mostrados coinciden con lo sembrado.
#
# Uso: tests/uat/inc4/guion_manual_iteracion1.sh   (desde la raíz del repo)
#
# Al final imprime credenciales, ids, la URL del frontend y el checklist paso a paso.
# Nada se borra solo — usar tests/uat/inc4/limpiar_uat.sh al terminar.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

PORT="${COGNION_UAT_PORT:-8000}"
SMTP_PORT="${COGNION_UAT_SMTP_PORT:-2525}"
BASE="http://localhost:${PORT}"
FRONTEND_URL="${COGNION_UAT_FRONTEND_URL:-http://localhost:5173}"
DB_URL="postgresql://user:password@localhost:5432/cognion"
LOG=$(mktemp -t cognion-uat-inc4-iter1.XXXXXX.log)
EMAIL_PREFIX="uat-inc4-iter1-$$"
STARTED_SERVER=0
STARTED_SMTP=0

echo "== Postgres =="
pg_isready -q || { echo "Postgres no responde en localhost:5432 — arrancalo con: brew services start postgresql@16" >&2; exit 1; }
echo "OK"

echo "== Backend =="
if curl -s -o /dev/null "${BASE}/health"; then
  echo "Ya hay un backend corriendo en ${BASE} — lo reutilizo (no lo bajo al final)."
  echo "  (si no arrancó con SMTP_PORT=${SMTP_PORT}, el paso de invitación a los Estudiantes puede fallar con 500 — en ese caso bajalo y volvé a correr este guión)"
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

echo
echo "== Frontend =="
if curl -s -o /dev/null "${FRONTEND_URL}"; then
  echo "Ya hay un frontend corriendo en ${FRONTEND_URL} — lo reutilizo."
else
  echo "No respondió ${FRONTEND_URL} — arrancalo en otra terminal antes de navegar:"
  echo "  cd frontend && npm run dev"
fi

echo
echo "== Sembrando Administrador, Docente, 2 materias y el Estudiante =="

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
  -d "{\"email\":\"${DOCENTE_EMAIL}\",\"password\":\"${DOCENTE_PASSWORD}\",\"nombre\":\"María González\",\"perfil\":\"docente\"}" >/dev/null
docente_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"${DOCENTE_EMAIL}\",\"password\":\"${DOCENTE_PASSWORD}\"}")
docente_token=$(echo "$docente_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# Materia 1: banco de 4 preguntas V/F, se usan 2 actividades ya finalizadas para dejar un
# resultado conocido en "Mi desempeño". Materia 2: sin ninguna actividad — verifica el estado
# vacío del selector.
MATERIA_1_NOMBRE="Ingeniería de Software (${EMAIL_PREFIX})"
materia1=$(curl -s -X POST "${BASE}/materias" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"nombre\":\"${MATERIA_1_NOMBRE}\"}")
materia1_id=$(echo "$materia1" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
banco1_id=$(echo "$materia1" | python3 -c "import sys,json;print(json.load(sys.stdin)['banco_id'])")

MATERIA_2_NOMBRE="Gestión de Proyectos (${EMAIL_PREFIX})"
materia2=$(curl -s -X POST "${BASE}/materias" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"nombre\":\"${MATERIA_2_NOMBRE}\"}")
materia2_id=$(echo "$materia2" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

admin_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${ADMIN_EMAIL}';")

comision1=$(curl -s -X POST "${BASE}/comisiones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"materia_id\":\"${materia1_id}\",\"horario\":\"Lunes 18-22\",\"administrador_id\":\"${admin_id}\"}")
comision1_id=$(echo "$comision1" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

comision2=$(curl -s -X POST "${BASE}/comisiones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"materia_id\":\"${materia2_id}\",\"horario\":\"Martes 18-22\",\"administrador_id\":\"${admin_id}\"}")
comision2_id=$(echo "$comision2" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

docente_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${DOCENTE_EMAIL}';")
curl -s -X POST "${BASE}/comisiones/${comision1_id}/docentes" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" -d "{\"docente_id\":\"${docente_id}\"}" >/dev/null
curl -s -X POST "${BASE}/comisiones/${comision2_id}/docentes" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" -d "{\"docente_id\":\"${docente_id}\"}" >/dev/null

# El Estudiante se da de alta por invitación (US-1.1.1/1.1.8) — no hay alta directa. El token
# de la invitación no se expone en la respuesta de la API (solo se manda por email), así que
# para este guión se lee directo de la tabla, igual que hace smoke.sh.
ESTUDIANTE_EMAIL="${EMAIL_PREFIX}-estudiante@fiuner.edu.ar"
ESTUDIANTE_PASSWORD="Password123!"
invitacion1=$(curl -s -X POST "${BASE}/comisiones/${comision1_id}/invitaciones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"docente_id\":\"${docente_id}\",\"email_destinatario\":\"${ESTUDIANTE_EMAIL}\"}")
invitacion1_id=$(echo "$invitacion1" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
estudiante_token=""
if [[ -n "$invitacion1_id" ]]; then
  invitacion1_token=$(psql "$DB_URL" -t -A -c "SELECT token FROM invitacion WHERE id = '${invitacion1_id}';")
  curl -s -X POST "${BASE}/identidad/registro" -H "Content-Type: application/json" \
    -d "{\"token\":\"${invitacion1_token}\",\"nombre\":\"Juan Pérez\",\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"${ESTUDIANTE_PASSWORD}\"}" >/dev/null
  estudiante_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"${ESTUDIANTE_PASSWORD}\"}")
  estudiante_token=$(echo "$estudiante_login" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
fi

if [[ -z "${estudiante_token:-}" ]]; then
  echo "  ⚠ FALLO sembrando el Estudiante (invitación: $invitacion1) — revisá que el fake SMTP"
  echo "     esté arriba y que el backend haya arrancado con SMTP_PORT=${SMTP_PORT}."
  echo "     El recorrido del Estudiante no va a funcionar sin esto."
  exit 1
fi

# La Materia 2 (sin evaluaciones) necesita un SEGUNDO estudiante, no el mismo — el dominio
# actual liga a un Estudiante con una única comisión (`estudiante.comision_id`, sin
# muchos-a-muchos), así que una segunda invitación a la misma persona no lo inscribe en otra
# materia (detectado en la UAT de Analytics, Incremento 4 Iteración 1). El selector de
# materia de "Mi desempeño" (US-4.1.3) solo aparece con 2+ materias del MISMO estudiante, algo
# que hoy no es alcanzable — el caso "materia sin evaluaciones" se prueba con esta segunda
# cuenta en una sesión aparte.
ESTUDIANTE2_EMAIL="${EMAIL_PREFIX}-estudiante2@fiuner.edu.ar"
ESTUDIANTE2_PASSWORD="Password123!"
invitacion2=$(curl -s -X POST "${BASE}/comisiones/${comision2_id}/invitaciones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"docente_id\":\"${docente_id}\",\"email_destinatario\":\"${ESTUDIANTE2_EMAIL}\"}")
invitacion2_id=$(echo "$invitacion2" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
if [[ -n "$invitacion2_id" ]]; then
  invitacion2_token=$(psql "$DB_URL" -t -A -c "SELECT token FROM invitacion WHERE id = '${invitacion2_id}';")
  curl -s -X POST "${BASE}/identidad/registro" -H "Content-Type: application/json" \
    -d "{\"token\":\"${invitacion2_token}\",\"nombre\":\"Ana López\",\"email\":\"${ESTUDIANTE2_EMAIL}\",\"password\":\"${ESTUDIANTE2_PASSWORD}\"}" >/dev/null
fi

echo "OK — Docente, 2 materias y 2 Estudiantes sembrados."

echo
echo "== Cargando 4 preguntas V/F en el banco de \"${MATERIA_1_NOMBRE}\" (respuesta correcta conocida) =="
# Orden y respuesta_correcta fijos — con cantidad_preguntas=4 (todo el banco) IniciarEvaluacion
# asigna siempre las 4, sin depender del sorteo aleatorio, así el resultado es 100% predecible.
declare -a preguntas_texto=(
  "Buenos Aires es la capital de Argentina."
  "El Sol gira alrededor de la Tierra."
  "PostgreSQL es una base de datos relacional."
  "Python es un lenguaje compilado."
)
declare -a preguntas_correcta=("true" "false" "true" "false")
declare -a pregunta_ids=()
for i in 0 1 2 3; do
  pregunta=$(curl -s -X POST "${BASE}/preguntas/verdadero-falso" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"banco_id\":\"${banco1_id}\",\"texto\":\"${preguntas_texto[$i]}\",\"respuesta_correcta\":${preguntas_correcta[$i]},\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Repaso\",\"dificultad\":\"medio\",\"importancia\":\"alto\"}")
  pregunta_ids[$i]=$(echo "$pregunta" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
done
echo "OK — 4 preguntas activas (respuestas correctas: V, F, V, F, en ese orden)"

crear_actividad_finalizada() {
  local titulo="$1"; shift
  local -a respuestas=("$@")
  local fecha_apertura fecha_cierre actividad_json actividad_id evaluacion_json evaluacion_id
  fecha_apertura=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat())")
  fecha_cierre=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)+timedelta(days=7)).isoformat())")
  actividad_json=$(curl -s -X POST "${BASE}/actividades" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"materia_id\":\"${materia1_id}\",\"titulo\":\"${titulo}\",\"fecha_apertura\":\"${fecha_apertura}\",\"fecha_cierre\":\"${fecha_cierre}\",\"cantidad_preguntas\":4,\"cantidad_intentos_permitidos\":1}")
  actividad_id=$(echo "$actividad_json" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

  evaluacion_json=$(curl -s -X POST "${BASE}/evaluaciones" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${estudiante_token}" \
    -d "{\"actividad_id\":\"${actividad_id}\"}")
  evaluacion_id=$(echo "$evaluacion_json" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

  for i in 0 1 2 3; do
    curl -s -X POST "${BASE}/evaluaciones/${evaluacion_id}/respuestas" -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${estudiante_token}" \
      -d "{\"pregunta_id\":\"${pregunta_ids[$i]}\",\"contenido\":{\"valor\":${respuestas[$i]}}}" >/dev/null
  done
  curl -s -X POST "${BASE}/evaluaciones/${evaluacion_id}/finalizar" \
    -H "Authorization: Bearer ${estudiante_token}" >/dev/null
  echo "$actividad_id"
}

echo
echo "== Actividad 1 — Estudiante responde V,V,V,V → 2 correctas (Q1,Q3) / 2 incorrectas (Q2,Q4) =="
actividad1_id=$(crear_actividad_finalizada "Parcial 1 — Unidades 1 a 2" "true" "true" "true" "true")
echo "OK — actividad_id=${actividad1_id}, Evaluacion Finalizada (2 correctas / 2 incorrectas)"

echo "== Actividad 2 — Estudiante responde F,F,F,F → 2 correctas (Q2,Q4) / 2 incorrectas (Q1,Q3) =="
actividad2_id=$(crear_actividad_finalizada "Parcial 2 — Unidades 3 a 4" "false" "false" "false" "false")
echo "OK — actividad_id=${actividad2_id}, Evaluacion Finalizada (2 correctas / 2 incorrectas)"

echo
echo "════════════════════════════════════════════════════════════════════════════"
echo "  RESUMEN — credenciales e ids de esta corrida"
echo "════════════════════════════════════════════════════════════════════════════"
echo "  Frontend:              ${FRONTEND_URL}"
echo "  Backend:               ${BASE}  (Swagger: ${BASE}/docs)"
echo "  Docente (María González):    ${DOCENTE_EMAIL} / ${DOCENTE_PASSWORD}"
echo "  Estudiante 1 (Juan Pérez):   ${ESTUDIANTE_EMAIL} / ${ESTUDIANTE_PASSWORD}"
echo "    Materia (con desempeño):   ${MATERIA_1_NOMBRE}"
echo "    Parcial 1 (id=${actividad1_id}) → 2 correctas / 2 incorrectas"
echo "    Parcial 2 (id=${actividad2_id}) → 2 correctas / 2 incorrectas"
echo "    Acumulado esperado:        4 correctas / 4 incorrectas / 8 total / 50% acierto / 2 evaluaciones"
echo "  Estudiante 2 (Ana López):    ${ESTUDIANTE2_EMAIL} / ${ESTUDIANTE2_PASSWORD}"
echo "    Materia (sin evaluaciones): ${MATERIA_2_NOMBRE}"
echo
if [[ "$STARTED_SERVER" == "1" ]]; then
  echo "  Este guión arrancó el backend (pid=$SERVER_PID, log=$LOG) — sigue corriendo."
  echo "  Para bajarlo: kill $SERVER_PID"
fi
echo
echo "  Para limpiar los datos de esta corrida cuando termines de revisar, corré:"
echo "  tests/uat/inc4/limpiar_uat.sh '${EMAIL_PREFIX}'"
echo
echo "  Anotá los hallazgos en quality/reports/uat/inc4/guion-manual-iteracion1.md"
echo "  (clasificación de severidad en docs/plans/PROCEDIMIENTO-UAT.md §8)"
echo "════════════════════════════════════════════════════════════════════════════"
