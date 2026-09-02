#!/usr/bin/env bash
# Guión de revisión manual — Iteración 4 del Incremento 3 "Actividad Evaluativa" (frontend)
# (US-3.4.1 a US-3.4.10/US-ADJ-09/10/11: DoD completo del incremento, backend + frontend)
#
# A diferencia de guion_manual_iteracion1.sh (que ejercita Swagger UI/HTTP), este guión siembra
# los datos y deja el backend corriendo para que Víctor navegue la aplicación REAL en el
# navegador (frontend Vite) y juzgue el resultado a ojo, checklist en mano.
#
# Uso: tests/uat/inc3/guion_manual_iteracion4.sh   (desde la raíz del repo)
#
# Al final imprime credenciales, ids, la URL del frontend y el checklist paso a paso.
# Nada se borra solo — usar tests/uat/inc3/limpiar_uat.sh al terminar.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"

PORT="${COGNION_UAT_PORT:-8000}"
SMTP_PORT="${COGNION_UAT_SMTP_PORT:-2525}"
BASE="http://localhost:${PORT}"
FRONTEND_URL="${COGNION_UAT_FRONTEND_URL:-http://localhost:5173}"
DB_URL="postgresql://user:password@localhost:5432/cognion"
LOG=$(mktemp -t cognion-uat-inc3-iter4.XXXXXX.log)
EMAIL_PREFIX="uat-inc3-iter4-$$"
STARTED_SERVER=0
STARTED_SMTP=0

paso() {
  echo
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "▶ $1"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
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

echo
echo "== Frontend =="
if curl -s -o /dev/null "${FRONTEND_URL}"; then
  echo "Ya hay un frontend corriendo en ${FRONTEND_URL} — lo reutilizo."
else
  echo "No respondió ${FRONTEND_URL} — arrancalo en otra terminal antes de navegar:"
  echo "  cd frontend && npm run dev"
fi

paso "PASO 0 — Sembrar Docente, Estudiante, materia con banco cargado y actividad vigente"

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

MATERIA_NOMBRE="Ingeniería de Software (UAT $$)"
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
    -d "{\"token\":\"${invitacion_token}\",\"nombre\":\"Juan Pérez\",\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"${ESTUDIANTE_PASSWORD}\"}" >/dev/null
  estudiante_login=$(curl -s -X POST "${BASE}/identidad/login" -H "Content-Type: application/json" \
    -d "{\"email\":\"${ESTUDIANTE_EMAIL}\",\"password\":\"${ESTUDIANTE_PASSWORD}\"}")
  estudiante_token=$(echo "$estudiante_login" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)
fi

if [[ -z "${estudiante_token:-}" ]]; then
  echo "  ⚠ FALLO sembrando el Estudiante (invitación: $invitacion) — revisá que el fake SMTP"
  echo "     esté arriba y que el backend haya arrancado con SMTP_PORT=${SMTP_PORT}."
  echo "     El recorrido del Estudiante (pasos 6+) no va a funcionar sin esto."
fi

echo "Cargando banco de preguntas (3 V/F + 1 opción múltiple)..."
for i in 1 2 3; do
  curl -s -X POST "${BASE}/preguntas/verdadero-falso" -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${docente_token}" \
    -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"Pregunta UAT V/F #${i}\",\"respuesta_correcta\":true,\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Tema UAT\",\"dificultad\":\"medio\",\"importancia\":\"alto\"}" >/dev/null
done
curl -s -X POST "${BASE}/preguntas/opcion-multiple" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"banco_id\":\"${banco_id}\",\"texto\":\"Pregunta UAT Opción Múltiple #1\",\"opciones\":[{\"texto\":\"Opción correcta\",\"es_correcta\":true},{\"texto\":\"Opción incorrecta A\",\"es_correcta\":false},{\"texto\":\"Opción incorrecta B\",\"es_correcta\":false}],\"unidad_tematica\":\"Unidad 1\",\"tema\":\"Tema UAT\",\"dificultad\":\"medio\",\"importancia\":\"alto\"}" >/dev/null
echo "OK — 4 preguntas activas en el banco de \"${MATERIA_NOMBRE}\""

echo "Creando actividad de período abierto vigente (2 preguntas, cierra en 7 días)..."
fecha_apertura=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)-timedelta(minutes=1)).isoformat())")
fecha_cierre=$(python3 -c "from datetime import datetime,timedelta,timezone;print((datetime.now(timezone.utc)+timedelta(days=7)).isoformat())")
actividad=$(curl -s -X POST "${BASE}/actividades" -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${docente_token}" \
  -d "{\"materia_id\":\"${materia_id}\",\"titulo\":\"Parcial 1 — Unidades 1 a 3\",\"fecha_apertura\":\"${fecha_apertura}\",\"fecha_cierre\":\"${fecha_cierre}\",\"cantidad_preguntas\":2,\"cantidad_intentos_permitidos\":1}")
actividad_id=$(echo "$actividad" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null)
echo "OK — actividad_id=${actividad_id}"

echo
echo "════════════════════════════════════════════════════════════════════════════"
echo "  RESUMEN — credenciales e ids de esta corrida"
echo "════════════════════════════════════════════════════════════════════════════"
echo "  Frontend:              ${FRONTEND_URL}"
echo "  Backend:               ${BASE}  (Swagger: ${BASE}/docs)"
echo "  Docente (María González):    ${DOCENTE_EMAIL} / ${DOCENTE_PASSWORD}"
echo "  Estudiante (Juan Pérez):     ${ESTUDIANTE_EMAIL} / ${ESTUDIANTE_PASSWORD}"
echo "  Materia:                ${MATERIA_NOMBRE}"
echo "  Actividad:               \"Parcial 1 — Unidades 1 a 3\" (actividad_id=${actividad_id})"
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
echo "  (clasificación de severidad en docs/plans/PROCEDIMIENTO-UAT.md §8)"
echo
echo "════════════════════════════════════════════════════════════════════════════"
echo "  CHECKLIST — recorrido en el navegador (${FRONTEND_URL})"
echo "════════════════════════════════════════════════════════════════════════════"
cat <<CHECKLIST

LADO DOCENTE
  [ ] 1. Login como Docente (${DOCENTE_EMAIL} / ${DOCENTE_PASSWORD})
  [ ] 2. Mis materias → entrar a "${MATERIA_NOMBRE}" → ver el banco con 4 preguntas
         (3 V/F + 1 opción múltiple)
  [ ] 3. Mis actividades → ver "Parcial 1 — Unidades 1 a 3" en el listado, badge "En curso"
  [ ] 4. Entrar al detalle de la actividad → "Extender plazo" → elegir una fecha de cierre
         posterior a la actual → confirmar → el detalle refleja el nuevo plazo de inmediato
  [ ] 5. Dejar esta pestaña en el detalle de la actividad (para cerrarla en el paso 13,
         DESPUÉS de que el Estudiante finalice)

LADO ESTUDIANTE (abrir una ventana/pestaña de incógnito o cerrar sesión del Docente)
  [ ] 6. Login como Estudiante (${ESTUDIANTE_EMAIL} / ${ESTUDIANTE_PASSWORD})
  [ ] 7. Mis materias ("1 pendiente") → Mis actividades → badge "Pendiente de responder",
         con el plazo extendido en el paso 4
  [ ] 8. "Rendir" → responder la primera pregunta → avanza a la 2/2
  [ ] 9. ⚠ CASO CLAVE — recargar la página (F5) en medio de la evaluación (simula una
         desconexión): al volver a cargar debe reaparecer LA MISMA pregunta pendiente,
         con la respuesta previa ya marcada, mismo set de preguntas (no debe volver a
         sortear ni perder lo respondido) — INV-AE-05/06
  [ ] 10. "Pausar y salir" → pantalla de evaluación suspendida ("Guardamos tus N
          respuestas") → "Continuar" → retoma exactamente en el mismo punto
  [ ] 11. Responder la última pregunta → "Confirmar y finalizar" → navega a la revisión
  [ ] 12. Revisión: verificar el resumen (Correctas/Incorrectas/Total), el texto de la
          propia respuesta y — en las incorrectas — la respuesta correcta. Las preguntas
          deben estar numeradas 1, 2 (no 0, 1 — si aparece "0." es el hallazgo ⚪ estético
          ya conocido, no hace falta reportarlo de nuevo)
  [ ] 13. Volver al listado de actividades → la tarjeta debe decir "Finalizada — ver
          revisión" y llevar directo a la revisión sin pasar por "Rendir" de nuevo

CIERRE (volver a la pestaña del Docente del paso 5)
  [ ] 14. "Cerrar actividad" (manual) → confirmar → el badge pasa a "Cerrada"
  [ ] 15. (Opcional) con un segundo Estudiante o el mismo ya finalizado, intentar entrar de
          nuevo a "Rendir" sobre la actividad ya cerrada → debe rechazarlo con un mensaje
          claro, no con una pantalla rota o colgada en blanco

Cualquier paso que no se comporte como se describe: anotalo en
quality/reports/uat/inc3/hallazgos-revision-manual.md con severidad
(🔴 Bloqueante / 🟡 Observación / ⚪ Estético, ver PROCEDIMIENTO-UAT.md §8).
CHECKLIST
