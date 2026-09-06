#!/usr/bin/env bash
# Guión de revisión manual — Iteración 2 del Incremento 4 "Portal del estudiante y Analytics"
# (US-4.2.1 a US-4.2.6: RF-16 Docente ve el desempeño de un alumno elegido, RF-17 Docente ve la
# tasa de error por tema — backend + frontend)
#
# Siembra una materia con una comisión de 2 estudiantes, un banco de 3 preguntas V/F (una por
# tema, con severidad de error distinta a propósito: Alto=100%, Medio=25%, Bajo=0%) y 2
# actividades de período abierto ya finalizadas por ambos estudiantes, con desempeño individual
# distinto entre ellos. Deja el backend + frontend corriendo para que Víctor navegue las
# pantallas "Desempeño por alumno" (US-4.2.5) y "Desempeño por tema" (US-4.2.6) reales.
#
# Uso: tests/uat/inc4/guion_manual_iteracion2.sh   (desde la raíz del repo)
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
LOG=$(mktemp -t cognion-uat-inc4-iter2.XXXXXX.log)
EMAIL_PREFIX="uat-inc4-iter2-$$"
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
echo "== Sembrando Administrador, Docente, 1 materia, 1 comisión y 2 Estudiantes =="

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

MATERIA_NOMBRE="Ingeniería de Software (${EMAIL_PREFIX})"
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

# Ambos estudiantes en la MISMA comisión — a diferencia de la Iteración 1 (donde el segundo
# estudiante necesitaba una materia aparte por la limitación de comision_id único), acá
# "Desempeño por alumno" (US-4.2.5) necesita 2+ estudiantes reales de la misma comisión para
# poder elegir entre ellos en el selector.
invitar_y_registrar() {
  local email="$1" nombre="$2"
  local invitacion invitacion_id token
  invitacion=$(curl -s -X POST "${BASE}/comisiones/${comision_id}/invitaciones" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"docente_id\":\"${docente_id}\",\"email_destinatario\":\"${email}\"}")
  invitacion_id=$(echo "$invitacion" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
  if [[ -z "$invitacion_id" ]]; then
    echo "  ⚠ FALLO invitando a ${email}: $invitacion" >&2
    exit 1
  fi
  token=$(psql "$DB_URL" -t -A -c "SELECT token FROM invitacion WHERE id = '${invitacion_id}';")
  curl -s -X POST "${BASE}/identidad/registro" -H "Content-Type: application/json" \
    -d "{\"token\":\"${token}\",\"nombre\":\"${nombre}\",\"email\":\"${email}\",\"password\":\"Password123!\"}" >/dev/null
}

ANA_EMAIL="${EMAIL_PREFIX}-ana@fiuner.edu.ar"
JUAN_EMAIL="${EMAIL_PREFIX}-juan@fiuner.edu.ar"
invitar_y_registrar "$ANA_EMAIL" "Ana Pérez"
invitar_y_registrar "$JUAN_EMAIL" "Juan Gómez"

ana_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"${ANA_EMAIL}\",\"password\":\"Password123!\"}")
ana_token=$(echo "$ana_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
ana_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${ANA_EMAIL}';")

juan_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
  -d "{\"email\":\"${JUAN_EMAIL}\",\"password\":\"Password123!\"}")
juan_token=$(echo "$juan_login" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
juan_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${JUAN_EMAIL}';")

echo "OK — Docente, 1 materia, 1 comisión y 2 Estudiantes (Ana, Juan) sembrados."

echo
echo "== Cargando 3 preguntas V/F, una por tema, respuesta_correcta=true en las 3 =="
declare -a temas=("Inversión de dependencias" "Bounded Contexts" "Ciclo de vida del software")
declare -a unidades=("Unidad 3 — Principios SOLID" "Unidad 2 — Arquitectura" "Unidad 1 — Fundamentos")
declare -a pregunta_ids=()
for i in 0 1 2; do
  pregunta=$(curl -s -X POST "${BASE}/preguntas/verdadero-falso" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"Pregunta de ${temas[$i]}\",\"respuesta_correcta\":true,\"unidad_tematica\":\"${unidades[$i]}\",\"tema\":\"${temas[$i]}\",\"dificultad\":\"medio\",\"importancia\":\"alto\"}")
  pregunta_ids[$i]=$(echo "$pregunta" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
done
echo "OK — 3 preguntas activas: [Alto=${temas[0]}, Medio=${temas[1]}, Bajo=${temas[2]}]"

crear_actividad_y_responder() {
  # $1=titulo, $2..$4=respuestas de Ana (alto,medio,bajo como true/false), $5..$7=respuestas de Juan
  local titulo="$1" ana_alto="$2" ana_medio="$3" ana_bajo="$4" juan_alto="$5" juan_medio="$6" juan_bajo="$7"
  local fecha_apertura fecha_cierre actividad_json actividad_id
  fecha_apertura=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat())")
  fecha_cierre=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)+timedelta(days=7)).isoformat())")
  actividad_json=$(curl -s -X POST "${BASE}/actividades" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"materia_id\":\"${materia_id}\",\"titulo\":\"${titulo}\",\"fecha_apertura\":\"${fecha_apertura}\",\"fecha_cierre\":\"${fecha_cierre}\",\"cantidad_preguntas\":3,\"cantidad_intentos_permitidos\":1}")
  actividad_id=$(echo "$actividad_json" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

  responder_y_finalizar() {
    local token="$1" r_alto="$2" r_medio="$3" r_bajo="$4"
    local evaluacion_json evaluacion_id
    evaluacion_json=$(curl -s -X POST "${BASE}/evaluaciones" -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${token}" -d "{\"actividad_id\":\"${actividad_id}\"}")
    evaluacion_id=$(echo "$evaluacion_json" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
    curl -s -X POST "${BASE}/evaluaciones/${evaluacion_id}/respuestas" -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${token}" \
      -d "{\"pregunta_id\":\"${pregunta_ids[0]}\",\"contenido\":{\"valor\":${r_alto}}}" >/dev/null
    curl -s -X POST "${BASE}/evaluaciones/${evaluacion_id}/respuestas" -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${token}" \
      -d "{\"pregunta_id\":\"${pregunta_ids[1]}\",\"contenido\":{\"valor\":${r_medio}}}" >/dev/null
    curl -s -X POST "${BASE}/evaluaciones/${evaluacion_id}/respuestas" -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${token}" \
      -d "{\"pregunta_id\":\"${pregunta_ids[2]}\",\"contenido\":{\"valor\":${r_bajo}}}" >/dev/null
    curl -s -X POST "${BASE}/evaluaciones/${evaluacion_id}/finalizar" -H "Authorization: Bearer ${token}" >/dev/null
  }

  responder_y_finalizar "$ana_token" "$ana_alto" "$ana_medio" "$ana_bajo"
  responder_y_finalizar "$juan_token" "$juan_alto" "$juan_medio" "$juan_bajo"
  echo "$actividad_id"
}

echo
echo "== Actividad 1 — Ana: Alto=incorrecta, Medio=correcta, Bajo=correcta | Juan: igual =="
actividad1_id=$(crear_actividad_y_responder "Parcial 1 — Unidades 1 a 3" \
  "false" "true" "true" \
  "false" "true" "true")
echo "OK — actividad_id=${actividad1_id}"

echo "== Actividad 2 — Ana: Alto=incorrecta, Medio=incorrecta, Bajo=correcta | Juan: Alto=incorrecta, Medio=correcta, Bajo=correcta =="
actividad2_id=$(crear_actividad_y_responder "Parcial 2 — Repaso" \
  "false" "false" "true" \
  "false" "true" "true")
echo "OK — actividad_id=${actividad2_id}"

echo
echo "════════════════════════════════════════════════════════════════════════════"
echo "  RESUMEN — credenciales e ids de esta corrida"
echo "════════════════════════════════════════════════════════════════════════════"
echo "  Frontend:              ${FRONTEND_URL}"
echo "  Backend:               ${BASE}  (Swagger: ${BASE}/docs)"
echo "  Docente (María González):    ${DOCENTE_EMAIL} / Password123!"
echo "  Materia:                     ${MATERIA_NOMBRE}"
echo "  Comisión:                    Lunes 18-22"
echo
echo "  Estudiante 1 — Ana Pérez:    ${ANA_EMAIL} / Password123!"
echo "    Acumulado esperado en 'Desempeño por alumno': 3 correctas / 3 incorrectas / 6 total / 50% acierto / 2 evaluaciones"
echo "  Estudiante 2 — Juan Gómez:   ${JUAN_EMAIL} / Password123!"
echo "    Acumulado esperado en 'Desempeño por alumno': 4 correctas / 2 incorrectas / 6 total / 67% acierto / 2 evaluaciones"
echo
echo "  'Desempeño por tema' — toda la materia, esperado ordenado por tasa de error descendente:"
echo "    ${temas[0]} (${unidades[0]}): 4 respuestas, 4 incorrectas → 100% (alta, rojo)"
echo "    ${temas[1]} (${unidades[1]}): 4 respuestas, 1 incorrecta  → 25%  (media, ámbar)"
echo "    ${temas[2]} (${unidades[2]}): 4 respuestas, 0 incorrectas → 0%   (baja, verde)"
echo
if [[ "$STARTED_SERVER" == "1" ]]; then
  echo "  Este guión arrancó el backend (pid=$SERVER_PID, log=$LOG) — sigue corriendo."
  echo "  Para bajarlo: kill $SERVER_PID"
fi
echo
echo "  Para limpiar los datos de esta corrida cuando termines de revisar, corré:"
echo "  tests/uat/inc4/limpiar_uat.sh '${EMAIL_PREFIX}'"
echo
echo "  Anotá los hallazgos en quality/reports/uat/inc4/evidencia-iteracion2.md §3"
echo "  (clasificación de severidad en docs/plans/PROCEDIMIENTO-UAT.md §8)"
echo "════════════════════════════════════════════════════════════════════════════"
