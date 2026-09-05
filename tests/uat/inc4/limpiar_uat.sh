#!/usr/bin/env bash
# Limpia los datos sembrados por guion_manual_iteracion1.sh.
# Uso: tests/uat/inc4/limpiar_uat.sh <EMAIL_PREFIX>
# (el prefijo es el que el guión imprimió al final, ej. "uat-inc4-iter1-12345")
set -euo pipefail

PREFIX="${1:?Uso: limpiar_uat.sh <EMAIL_PREFIX> — ver el resumen que imprimió el guión}"
DB_URL="postgresql://user:password@localhost:5432/cognion"

psql "$DB_URL" -q -c "
  -- Borra TODOS los eventos de cada stream de Evaluacion afectado (no solo las filas cuyo
  -- propio payload trae actividad_id) — RespuestaRegistrada/Suspendida/etc. no llevan ese
  -- campo, así que filtrar por payload fila a fila deja huérfanos el resto del stream (bug
  -- detectado en la UAT de Analytics, Incremento 4 Iteración 1).
  DELETE FROM events WHERE aggregate_type = 'Evaluacion' AND aggregate_id IN (
    SELECT DISTINCT aggregate_id FROM events
    WHERE aggregate_type = 'Evaluacion' AND payload->>'actividad_id' IN (
      SELECT aggregate_id::text FROM events
      WHERE aggregate_type = 'ActividadEvaluativaPeriodoAbierto'
        AND payload->>'materia_id' IN (SELECT id::text FROM materia WHERE nombre LIKE '%${PREFIX}%')
    )
  );
  DELETE FROM events WHERE aggregate_type = 'ActividadEvaluativaPeriodoAbierto'
    AND payload->>'materia_id' IN (SELECT id::text FROM materia WHERE nombre LIKE '%${PREFIX}%');
  DELETE FROM invitacion WHERE comision_id IN (SELECT id FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${PREFIX}%'));
  DELETE FROM estudiante WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${PREFIX}%');
  DELETE FROM comision_docentes WHERE comision_id IN (SELECT id FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${PREFIX}%'));
  DELETE FROM comision WHERE administrador_id IN (SELECT id FROM usuario WHERE email LIKE '${PREFIX}%');
  DELETE FROM administrador WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${PREFIX}%');
  DELETE FROM docente WHERE id IN (SELECT id FROM usuario WHERE email LIKE '${PREFIX}%');
  DELETE FROM usuario WHERE email LIKE '${PREFIX}%';
  DELETE FROM pregunta_plantilla WHERE banco_id IN (SELECT id FROM banco WHERE materia_id IN (SELECT id FROM materia WHERE nombre LIKE '%${PREFIX}%'));
  DELETE FROM banco WHERE materia_id IN (SELECT id FROM materia WHERE nombre LIKE '%${PREFIX}%');
  DELETE FROM materia WHERE nombre LIKE '%${PREFIX}%';
"
echo "Datos de la corrida '${PREFIX}' limpiados."
