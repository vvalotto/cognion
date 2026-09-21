#!/usr/bin/env bash
# Guión de revisión manual — Iteración 2 del Incremento 6 "Sesión en vivo"
# (US-6.1.x y US-6.2.1 a US-6.2.8: RF-08 crear/unirse/iniciar, RF-09 dinámica en tiempo real,
#  RF-10 puntaje y ranking — backend únicamente, sin pantalla todavía)
#
# Está pensado para que Víctor lo corra y JUZGUE los resultados a ojo, viendo en vivo lo que
# recibe cada cliente conectado por WebSocket (un Docente y tres Estudiantes). Deja el backend
# corriendo y los datos sembrados al final para seguir explorando en Swagger UI
# (http://localhost:8000/docs).
#
# Uso: tests/uat/inc6/guion_manual_iteracion2.sh   (desde la raíz del repo)
#
# Al final imprime credenciales, ids y el comando de limpieza — nada se borra solo.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

PORT="${COGNION_UAT_PORT:-8000}"
BASE="http://localhost:${PORT}"
WS_BASE="ws://localhost:${PORT}"
DB_URL="postgresql://user:password@localhost:5432/cognion"
LOGDIR=$(mktemp -d -t cognion-uat-inc6)
LOG="${LOGDIR}/backend.log"
EMAIL_PREFIX="uat-inc6-$$"
PASSWORD="Password123!Uat"
STARTED_SERVER=0
CLIENT_PIDS=()

paso() {
  echo
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

revisar() {
  echo "  🔍 Revisar: $1"
}

json() {  # json <campo> — extrae un campo del JSON de stdin
  python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('$1',''))" 2>/dev/null
}

post() {  # post <token> <ruta> [body] — imprime "código cuerpo"
  local token="$1" ruta="$2" body="${3:-}"
  if [[ -n "$body" ]]; then
    curl -s -w ' [HTTP %{http_code}]\n' -X POST "${BASE}${ruta}" -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${token}" -d "$body"
  else
    curl -s -w ' [HTTP %{http_code}]\n' -X POST "${BASE}${ruta}" -H "Authorization: Bearer ${token}"
  fi
}

get() {  # get <token> <ruta>
  curl -s -w ' [HTTP %{http_code}]\n' "${BASE}$2" -H "Authorization: Bearer $1"
}

login() {  # login <email> — devuelve el token
  curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"$1\",\"password\":\"${PASSWORD}\"}" | json access_token
}

pregunta_actual() {  # pregunta_actual <token> <sesion_id> — pregunta_id de la pregunta actual
  curl -s "${BASE}/sesiones-en-vivo/$2" -H "Authorization: Bearer $1" \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['pregunta_actual']['pregunta_id'])"
}

mostrar_logs() {  # mostrar_logs — imprime lo recibido por cada cliente WebSocket
  sleep 0.6
  for f in "${LOGDIR}"/ws-*.log; do
    echo "  ── $(basename "$f" .log)"
    tail -n "${1:-2}" "$f" | sed 's/^/     /' | cut -c1-230
  done
}

lanzar_cliente() {  # lanzar_cliente <nombre> <token> <sesion_id>
  PYTHONPATH=. .venv/bin/python tests/uat/inc6/cliente_ws.py \
    "${WS_BASE}/sesiones-en-vivo/$3/canal" "$2" "$1" > "${LOGDIR}/ws-$1.log" 2>&1 &
  CLIENT_PIDS+=($!)
  echo "$!" > "${LOGDIR}/ws-$1.pid"
}

echo "== Postgres =="
pg_isready -q || { echo "Postgres no responde en localhost:5432 — arrancalo con: brew services start postgresql@16" >&2; exit 1; }
echo "OK"

echo "== Backend =="
if curl -s -o /dev/null "${BASE}/health"; then
  echo "Ya hay un backend corriendo en ${BASE} — lo reutilizo (no lo bajo al final)."
else
  echo "Arrancando backend en background (log: $LOG)..."
  .venv/bin/uvicorn src.app:app --port "$PORT" > "$LOG" 2>&1 &
  SERVER_PID=$!
  STARTED_SERVER=1
  for _ in $(seq 1 20); do
    curl -s -o /dev/null "${BASE}/health" && break
    sleep 0.5
  done
  curl -s -o /dev/null "${BASE}/health" || { echo "FAIL: el backend no respondió a tiempo"; cat "$LOG"; exit 1; }
  echo "OK (pid=$SERVER_PID)"
fi

paso "PASO 0 — Sembrar Administrador, Docente, Materia con 10 preguntas, Comisión y 3 Estudiantes"
ADMIN_EMAIL="${EMAIL_PREFIX}-admin@fiuner.edu.ar"
ADMIN_NOMBRE="UAT Admin" ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_PASSWORD="$PASSWORD" \
  .venv/bin/python scripts/seed_admin.py >/dev/null
admin_token=$(login "$ADMIN_EMAIL")

DOCENTE_EMAIL="${EMAIL_PREFIX}-docente@fiuner.edu.ar"
curl -s -X POST "${BASE}/identidad/autoregistro/docente" -H "Content-Type: application/json" \
  -d "{\"nombre\":\"UAT Docente\",\"email\":\"${DOCENTE_EMAIL}\",\"password\":\"${PASSWORD}\"}" >/dev/null
docente_token=$(login "$DOCENTE_EMAIL")

MATERIA_NOMBRE="${EMAIL_PREFIX}-materia"
materia=$(curl -s -X POST "${BASE}/materias" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" -d "{\"nombre\":\"${MATERIA_NOMBRE}\"}")
materia_id=$(echo "$materia" | json id)
banco_id=$(echo "$materia" | json banco_id)
for i in $(seq 1 10); do
  curl -s -X POST "${BASE}/preguntas/opcion-multiple" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"Pregunta UAT #${i}: ¿cuál es la opción B?\",\"opciones\":[{\"texto\":\"A\",\"es_correcta\":false},{\"texto\":\"B\",\"es_correcta\":true},{\"texto\":\"C\",\"es_correcta\":false},{\"texto\":\"D\",\"es_correcta\":false}],\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Tema UAT\",\"dificultad\":\"medio\",\"importancia\":\"alto\"}" >/dev/null
done

admin_id=$(psql "$DB_URL" -t -A -c "SELECT id FROM usuario WHERE email = '${ADMIN_EMAIL}';")
comision=$(curl -s -X POST "${BASE}/comisiones" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${admin_token}" \
  -d "{\"materia_id\":\"${materia_id}\",\"horario\":\"Lunes 18-22\",\"administrador_id\":\"${admin_id}\"}")
comision_id=$(echo "$comision" | json id)

for n in 1 2 3; do
  curl -s -X POST "${BASE}/identidad/autoregistro/estudiante" -H "Content-Type: application/json" \
    -d "{\"nombre\":\"UAT Estudiante ${n}\",\"email\":\"${EMAIL_PREFIX}-est${n}@fiuner.edu.ar\",\"password\":\"${PASSWORD}\",\"comision_id\":\"${comision_id}\"}" >/dev/null
  eval "est${n}_token=\$(login \"${EMAIL_PREFIX}-est${n}@fiuner.edu.ar\")"
done
echo "OK — Docente, 3 Estudiantes, materia con 10 preguntas y Comisión creados"

paso "PASO 1 — Docente crea la sesión en vivo (RF-08, US-6.1.2)"
echo "POST /sesiones-en-vivo (5 preguntas, 60 s por pregunta, para tener tiempo de mirar)"
sesion=$(curl -s -X POST "${BASE}/sesiones-en-vivo" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"comision_id\":\"${comision_id}\",\"cantidad_preguntas\":5,\"tiempo_limite_por_pregunta_segundos\":60}")
echo "  respuesta: $sesion"
sesion_id=$(echo "$sesion" | json id)
revisar "estado=EnEspera, cantidad_preguntas=5, sin pregunta_actual_indice"

paso "PASO 2 — Se conectan por WebSocket el Docente y los 3 Estudiantes"
lanzar_cliente docente "$docente_token" "$sesion_id"
lanzar_cliente est1 "$est1_token" "$sesion_id"
lanzar_cliente est2 "$est2_token" "$sesion_id"
lanzar_cliente est3 "$est3_token" "$sesion_id"
sleep 1.2
mostrar_logs 1
revisar "los 4 clientes dicen 'conectado'"

paso "PASO 3 — Los Estudiantes se unen; el Docente ve la sala de espera (US-6.1.3)"
for n in 1 2 3; do
  eval "t=\$est${n}_token"
  echo "POST /sesiones-en-vivo/${sesion_id}/unirse (est${n})"
  post "$t" "/sesiones-en-vivo/${sesion_id}/unirse" | cut -c1-200
done
echo "GET .../participantes (Docente):"
get "$docente_token" "/sesiones-en-vivo/${sesion_id}/participantes" | cut -c1-400
mostrar_logs 3
revisar "los participantes salen en el orden en que se unieron"
revisar "cada cliente conectado recibió 'participantes_actualizados' con la lista creciendo (1, 2 y 3)"

paso "PASO 4 — El Docente inicia: todos reciben el enunciado SIN opciones (US-6.1.4)"
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/iniciar" | cut -c1-300
mostrar_logs 1
revisar "los 4 clientes reciben 'pregunta_presentada' con el mismo enunciado y SIN opciones"
echo "GET estado como Estudiante (reconexión / entrar tarde):"
get "$est1_token" "/sesiones-en-vivo/${sesion_id}" | cut -c1-600
revisar "pregunta_actual con enunciado, opciones=null, respuesta_correcta=null, ya_respondio=false, puntaje_acumulado=0"

paso "PASO 5 — El Docente muestra las opciones (US-6.2.2)"
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/mostrar-opciones" | cut -c1-300
mostrar_logs 1
revisar "'opciones_mostradas' con las 4 opciones y SIN indicar cuál es la correcta"
pregunta_id=$(pregunta_actual "$docente_token" "$sesion_id")

paso "PASO 6 — Los Estudiantes responden: est1 y est2 aciertan (B), est3 falla (A) (US-6.2.4)"
for n in 1 2 3; do
  eval "t=\$est${n}_token"
  [[ "$n" == "3" ]] && opcion=0 || opcion=1
  echo "POST .../responder (est${n}, opción ${opcion})"
  post "$t" "/sesiones-en-vivo/${sesion_id}/responder" \
    "{\"pregunta_id\":\"${pregunta_id}\",\"contenido\":{\"opcion_indice\":${opcion}}}"
done
revisar "est1 y est2: es_correcta=true y puntaje entre 1500 y 3000 (dificultad medio × importancia alto); est3: es_correcta=false, puntaje=0"
revisar "el feedback NO trae ranking (solo tu puntaje) — el Estudiante no ve a los demás todavía"
echo "Repetir el POST de est1 (INV-AEV-07, una respuesta por pregunta):"
post "$est1_token" "/sesiones-en-vivo/${sesion_id}/responder" \
  "{\"pregunta_id\":\"${pregunta_id}\",\"contenido\":{\"opcion_indice\":1}}"
revisar "código 422 — ya respondió"
mostrar_logs 1
revisar "los clientes recibieron 'conteo_respuestas_actualizado' (total, sin desglose por opción)"

paso "PASO 7 — Cerrar la pregunta: un único mensaje con correcta + histograma + ranking (US-6.2.5)"
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/cerrar-pregunta" | cut -c1-300
mostrar_logs 1
revisar "'pregunta_cerrada' llega igual a los 4 clientes: respuesta_correcta, distribucion (B=2, A=1) y ranking con posiciones"
revisar "est1 y est2 arriba (el que respondió antes, más puntos), est3 último con 0"

paso "PASO 8 — El Estudiante NO ve el ranking hasta el final (RF-10, §17 punto 10)"
get "$est1_token" "/sesiones-en-vivo/${sesion_id}/ranking"
revisar "código 403 con un mensaje que dice que el ranking se publica al finalizar"
echo "El Docente sí lo ve en cualquier momento:"
get "$docente_token" "/sesiones-en-vivo/${sesion_id}/ranking" | cut -c1-400

paso "PASO 9 — Reconexión: est1 pierde la conexión y vuelve (US-6.2.8)"
kill "$(cat "${LOGDIR}/ws-est1.pid")" 2>/dev/null
sleep 0.5
echo "(est1 desconectado). Consulta el estado por HTTP:"
get "$est1_token" "/sesiones-en-vivo/${sesion_id}" | cut -c1-700
lanzar_cliente est1-reconectado "$est1_token" "$sesion_id"
sleep 0.8
revisar "recupera la pregunta actual, opciones_mostradas_en + tiempo límite, la respuesta correcta (ya está cerrada), ya_respondio=true y su puntaje_acumulado"
echo "POST .../unirse otra vez (idempotente):"
post "$est1_token" "/sesiones-en-vivo/${sesion_id}/unirse" | cut -c1-200
revisar "200 con la MISMA participación — no la perdió al desconectarse"

paso "PASO 10 — Avanzar a la siguiente pregunta (US-6.2.6): se presenta sin opciones"
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/avanzar" | cut -c1-300
mostrar_logs 1
revisar "'pregunta_presentada' con pregunta_actual_indice=1, sin opciones (incluido est1-reconectado: volvió a suscribirse)"
echo "Avanzar sin cerrar la pregunta (mostrar opciones y NO cerrar):"
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/mostrar-opciones" >/dev/null
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/avanzar"
revisar "código 422 PreguntaActualNoCerrada"
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/cerrar-pregunta" >/dev/null

paso "PASO 11 — Finalizar antes de agotar el set (US-6.2.7): todos reciben el ranking final"
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/finalizar" | cut -c1-300
mostrar_logs 1
revisar "'sesion_finalizada' con el ranking ordenado; la sesión pasa a Finalizada aunque quedaban 3 preguntas"
echo "Ahora el Estudiante sí ve el ranking:"
get "$est1_token" "/sesiones-en-vivo/${sesion_id}/ranking" | cut -c1-400
revisar "código 200 con el mismo ranking que recibieron por WebSocket"
echo "Después de finalizar, un Estudiante intenta unirse / el Docente finalizar de nuevo:"
post "$est1_token" "/sesiones-en-vivo/${sesion_id}/unirse" | cut -c1-200
post "$docente_token" "/sesiones-en-vivo/${sesion_id}/finalizar" | cut -c1-200
revisar "ambos 422 (SesionYaFinalizada), sin emitir ningún evento nuevo"

paso "PASO 12 — Casos de error de RBAC"
echo "Estudiante intenta finalizar / listar participantes:"
post "$est1_token" "/sesiones-en-vivo/${sesion_id}/finalizar"
get "$est1_token" "/sesiones-en-vivo/${sesion_id}/participantes"
revisar "ambos 403"
echo "Sesión inexistente:"
get "$docente_token" "/sesiones-en-vivo/00000000-0000-0000-0000-000000000000"
revisar "código 404"

paso "PASO 13 — Explorar libremente (opcional)"
echo "El backend sigue corriendo en ${BASE} — Swagger UI: ${BASE}/docs"
echo "Los clientes WebSocket siguen conectados: sus logs están en ${LOGDIR}/ws-*.log"

echo
echo "════════════════════════════════════════════════════════════════════════════"
echo "  RESUMEN — credenciales e ids de esta corrida (password de todas las cuentas: ${PASSWORD})"
echo "════════════════════════════════════════════════════════════════════════════"
echo "  Backend:     ${BASE}  (Swagger: ${BASE}/docs)"
echo "  Administrador: ${ADMIN_EMAIL}"
echo "  Docente:       ${DOCENTE_EMAIL}"
echo "  Estudiantes:   ${EMAIL_PREFIX}-est1/est2/est3@fiuner.edu.ar"
echo "  materia_id:    ${materia_id}"
echo "  comision_id:   ${comision_id}"
echo "  sesion_id:     ${sesion_id}"
echo "  logs WS:       ${LOGDIR}"
echo
if [[ "$STARTED_SERVER" == "1" ]]; then
  echo "  Este guión arrancó el backend (pid=$SERVER_PID, log=$LOG) — sigue corriendo."
  echo "  Para bajarlo: kill $SERVER_PID"
fi
echo "  Para cortar los clientes WebSocket: kill ${CLIENT_PIDS[*]}"
echo
echo "  Para limpiar los datos de esta corrida cuando termines de revisar:"
echo "  tests/uat/inc6/limpiar_uat.sh '${EMAIL_PREFIX}'"
echo
echo "  Anotá los hallazgos en quality/reports/uat/inc6/hallazgos-revision-manual.md"
echo "  (clasificación de severidad en docs/plans/PROCEDIMIENTO-UAT.md §8)"
