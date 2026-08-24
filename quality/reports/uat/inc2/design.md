# Diseño de Pruebas UAT — Iteración 1 del Incremento 2 "Banco de Preguntas"

| Campo | Valor |
|-------|-------|
| Incremento / Iteración | 2 / Iteración 1 |
| Baseline | No aplica — no cierra BL-003. BL-003 se abre recién al cierre completo del Incremento 2 (incluye Iteración 2, RF-03, todavía sin modelar). Esta verificación cierra solo la Iteración 1 en `CLAUDE.md`. |
| US cubiertas | `US-2.1.1` a `US-2.1.13` (backend RF-04/05/06, Iteración 1 + frontend, Iteración 1 completa) |
| Entorno | Propio |
| Fecha diseño | 2026-08-17 |

---

## Objetivo

Verificar de punta a punta que un Docente puede armar y mantener el banco de preguntas de
una materia — crearla, cargar preguntas de ambos tipos, filtrarlas, editarlas y eliminarlas
(baja lógica) — según la primera mitad del Hito del Incremento 2 (`PLAN_v1.md`):

> El docente arma y mantiene el banco de preguntas completo, filtrable por
> materia/unidad/tema/dificultad/importancia.

(La segunda mitad del Hito — *"el administrador resuelve problemas de cuentas sin depender
del docente"*, RF-03/Iteración 2 — queda fuera de este UAT, no implementada todavía.)

---

## Capas aplicables

**Capa 1 (pytest + Vitest): aplica.** Ya cubierta por la suite del proyecto — 270/270 tests
backend (unitarios + integración contra Postgres real + BDD/step_defs, incluye Identidad y
Banco de Preguntas) + 103/103 tests frontend (Vitest + React Testing Library). Se re-ejecuta
como evidencia fresca de esta verificación, sin escribir tests nuevos.

**Capa 2 (HTTP, entorno propio): aplica.** `smoke.sh` (`.claude/skills/run-cognion/smoke.sh`)
hoy solo cubre el flujo de Identidad. Se extiende con el flujo real de Banco de Preguntas,
reutilizando el `docente_token` que el script ya obtiene tras asignar el Docente a una
Comisión:

1. `POST /materias` — Docente crea una materia (banco vacío creado en el mismo flujo)
2. `POST /preguntas/opcion-multiple` — carga una pregunta de Opción Múltiple
3. `POST /preguntas/verdadero-falso` — carga una pregunta de Verdadero/Falso
4. `GET /bancos/{id}/preguntas` — filtra el banco, verifica que ambas preguntas aparecen
5. `PUT /preguntas/{id}` — edita el texto de una pregunta, verifica el cambio en el `GET`
6. `DELETE /preguntas/{id}` — elimina (baja lógica) una pregunta
7. `GET /bancos/{id}/preguntas` — verifica que la pregunta eliminada ya no aparece (INV-BP-04)
8. Caso de error: `POST /preguntas/opcion-multiple` con opciones inválidas (0 o 2+ marcadas
   como correctas) → 422 esperado

**UAT manual en navegador real:** Víctor recorre el flujo completo en su navegador contra el
backend real (no `fetch` mockeado) — mismo criterio que `BL-002`, aplicado proactivamente al
cierre de la iteración (no reactivo, como fue en `BL-002`):

1. Login como Docente
2. Crear una materia nueva
3. Cargar una pregunta de Opción Múltiple
4. Cargar una pregunta de Verdadero/Falso
5. Filtrar el banco (unidad, tema, dificultad, importancia)
6. Editar una pregunta existente
7. Eliminar una pregunta con confirmación — verificar que el mensaje aclara la baja lógica y
   que la pregunta desaparece de la tabla tras confirmar

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** no aplica — no es uno de los
checkpoints nombrados y no hay entorno de staging desplegado (mismo ítem abierto que
`BL-001`/`BL-002`).

---

## Criterio de aceptación

- Capa 1 (pytest + Vitest) en verde, sin regresiones.
- Capa 2 (HTTP vía `smoke.sh` extendido) responde con los códigos HTTP esperados en el flujo
  completo y en el caso de error, sin pérdida de datos.
- UAT visual en navegador real sin hallazgos 🔴 Bloqueantes — clasificación de severidad según
  `PROCEDIMIENTO-UAT.md` §8.

---

## Evidencia

Ver `quality/reports/uat/inc2/evidencia.md` (a generar tras la ejecución).
