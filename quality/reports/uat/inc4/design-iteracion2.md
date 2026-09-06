# Diseño de Pruebas UAT — Iteración 2 del Incremento 4 "Portal del estudiante y Analytics"

| Campo | Valor |
|-------|-------|
| Incremento / Iteración | 4 / Iteración 2 |
| Baseline | No aplica — cierra la Iteración 2 en `CLAUDE.md`. La baseline del Incremento 4 se abre al cierre completo (Iteraciones 1 y 2). |
| US cubiertas | `US-4.2.1` a `US-4.2.6` (RF-16: Docente ve el desempeño de un alumno elegido; RF-17: Docente ve la tasa de error por tema — backend + frontend) |
| Entorno | Propio |
| Fecha diseño | 2026-09-06 |

---

## Objetivo

Verificar de punta a punta RF-16 y RF-17 (`RF_v1.md`): el Docente elige un estudiante de una
comisión y ve su desempeño histórico (mismo dato que ve el propio estudiante, `US-4.2.1`), y
el Docente ve la tasa de error agregada por unidad/tema de una materia — de toda la materia o
acotada a una comisión (`US-4.2.4`) — tanto desde la API como desde las pantallas
"Desempeño por alumno" (`wireframes-analytics.md` §3.0, `#doc-desempeno-alumno`, `US-4.2.5`) y
"Desempeño por tema" (§3.1, `#doc-desempeno-tema`, `US-4.2.6`).

Mismo criterio que la Iteración 1: no se difiere el frontend — cierra RF-16/RF-17 de punta a
punta de una sola vez.

---

## Capas aplicables

**Capa 1 (pytest + Vitest): aplica.** Cubierta por la suite del proyecto — 852 tests backend
(unitarios + integración contra Postgres real + BDD/step_defs) + 261 tests frontend (Vitest +
React Testing Library). Se re-ejecuta como evidencia fresca de esta verificación, sin escribir
tests nuevos de UAT (ya cubierto por los tests de cada US).

**Capa 2 (HTTP, entorno propio): aplica.** `.claude/skills/run-cognion/smoke.sh` se extendió
con una sección nueva de Analytics — Iteración 2, inmediatamente después del bloque de
Iteración 1 (que deja una `Evaluacion` `Finalizada` conocida: 2 preguntas V/F con
`unidad_tematica="Unidad 1"`, `tema="Geografía"` y `tema="Arquitectura"` respectivamente, ambas
con `respuesta_correcta=false`, el estudiante contestó `true` a las dos → ambas incorrectas):

1. `GET /materias/{materia_id}/comisiones` (docente) → la comisión sembrada aparece (`US-4.2.2`)
2. `GET /comisiones/{comision_id}/estudiantes` (docente) → el estudiante sembrado aparece (`US-4.2.2`)
3. `GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno` (docente elige
   al estudiante) → mismo resultado que vio el propio estudiante en la Iteración 1 (0 correctas
   / 2 incorrectas) — confirma que no hay restricción de pertenencia a comisión (`US-4.2.1`, RF-16)
4. Mismo endpoint con un `estudiante_id` inexistente → 404 esperado
5. `GET /analytics/materias/{materia_id}/tasa-error-por-tema` sin `comision_id` (toda la
   materia) → Geografía y Arquitectura con `tasa_error=1.0`, 1 respuesta cada uno (`US-4.2.4`, RF-17)
6. Mismo endpoint con `comision_id` de la comisión sembrada → misma tasa, acotada
7. Mismo endpoint con rol `estudiante` → 403 esperado (RBAC, `require_docente`)

**UAT manual de Víctor en navegador real:** guión aparte,
`tests/uat/inc4/guion_manual_iteracion2.sh` siembra dos estudiantes en la misma comisión con
desempeño distinto y preguntas de 3 temas con severidad distinta (alta/media/baja), y deja el
backend + frontend corriendo para que Víctor navegue las pantallas "Desempeño por alumno" y
"Desempeño por tema" reales. Ver `evidencia-iteracion2.md` §3 para el checklist paso a paso y
la conclusión.

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** no aplica — mismo criterio que las
iteraciones anteriores, no hay entorno de staging desplegado.

---

## Criterio de aceptación

- Capa 1 (pytest + Vitest) en verde, sin regresiones nuevas (se acepta el flake ya documentado
  en `CLAUDE.md` de `test_rechazo_fuera_del_período_vigente`, ajeno a esta iteración).
- Capa 2 (HTTP vía `smoke.sh` extendido) responde con los códigos HTTP y los valores
  (comisiones/estudiantes listados, desempeño por alumno, tasa de error por tema con y sin
  `comision_id`) esperados, incluido el rechazo por rol y por id inexistente.
- UAT visual en navegador real (Víctor) sin hallazgos 🔴 Bloqueantes — clasificación de
  severidad según `PROCEDIMIENTO-UAT.md` §8.

---

## Evidencia

Ver `quality/reports/uat/inc4/evidencia-iteracion2.md` (Capa 1 + Capa 2, generada por la
sesión, y revisión manual a completar por Víctor).
