#!/usr/bin/env bash
# Limpia los datos sembrados por guion_manual_iteracion2.sh.
# Uso: tests/uat/inc6/limpiar_uat.sh <EMAIL_PREFIX>
# (el prefijo es el que el guión imprimió al final, ej. "uat-inc6-12345")
set -euo pipefail

PREFIX="${1:?Uso: limpiar_uat.sh <EMAIL_PREFIX> — ver el resumen que imprimió el guión}"
DB_URL="postgresql://user:password@localhost:5432/cognion"

psql "$DB_URL" -q -c "
  CREATE TEMP TABLE sesiones_uat AS
    SELECT DISTINCT aggregate_id FROM events
    WHERE aggregate_type = 'ActividadEvaluativaEnVivo'
      AND payload->>'materia_id' IN (SELECT id::text FROM materia WHERE nombre LIKE '%${PREFIX}%');
  DELETE FROM ranking_por_sesion WHERE sesion_id IN (SELECT aggregate_id FROM sesiones_uat);
  DELETE FROM distribucion_por_pregunta WHERE sesion_id IN (SELECT aggregate_id FROM sesiones_uat);
  DELETE FROM events WHERE aggregate_type = 'ParticipacionEnVivo'
    AND payload->>'sesion_id' IN (SELECT aggregate_id::text FROM sesiones_uat);
  DELETE FROM events WHERE aggregate_type = 'ActividadEvaluativaEnVivo'
    AND aggregate_id IN (SELECT aggregate_id FROM sesiones_uat);
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
