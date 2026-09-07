# Diseño de Pruebas UAT — Incremento 4-ADJ "Portal de Entrada y Validación E2E"

| Campo | Valor |
|-------|-------|
| Incremento | 4-ADJ |
| Baseline | BL-007 (a cerrar) |
| US cubiertas | `US-ADJ-31` — verifica de punta a punta el trabajo de `US-ADJ-21` a `US-ADJ-30` |
| Entorno | Propio |
| Fecha diseño | 2026-09-07 |

---

## Objetivo

Verificar el DoD completo del Incremento 4-ADJ en una sola corrida, no por iteración aislada:
un Administrador da de alta un Estudiante real de punta a punta desde la UI (Comisión →
Docente asignado → invitación → registro), y cualquier Docente/Estudiante/Administrador
autenticado navega por clic — sin URLs de memoria — desde el login hasta cualquier función de
su rol, atravesando los 4 BC (Identidad, Banco de Preguntas, Actividad Evaluativa, Analytics)
en un único guion realista.

A diferencia de todas las UAT anteriores (`quality/reports/uat/inc1/` a `inc4/`), que sembraban
la Comisión/invitación por script y arrancaban desde un endpoint o una URL conocida, esta es la
primera corrida que arranca desde el login real y no siembra nada por fuera de la UI salvo la
cuenta inicial del Administrador (ya sembrada por `US-1.1.0`/instalación).

---

## Estrategia

**Capa 1 (pytest + Vitest):** no aplica como verificación nueva — no hay código de producción
nuevo en esta US. Se corre igual como control de regresión antes de arrancar el guion manual.

**Capa 2 (navegador real, sin seeds):** es la capa central de esta US. Todo el escenario se
construye por clic, en el orden real que seguiría cada rol, usando Claude Browser contra el
entorno propio (backend `uvicorn` + frontend `vite dev`).

---

## Escenario DoD (guion E2E)

| # | Rol | Acción | Pantalla / ruta (por clic) |
|---|-----|--------|------------------------------|
| 1 | Administrador | Login | `/login` |
| 2 | Administrador | Da de alta al Docente | `/` → menú → Docentes |
| 3 | Docente | Login, crea una Materia nueva (Banco de Preguntas) | `/login` → menú → Banco de Preguntas → Materias |
| 4 | Docente | Carga 2 preguntas (1 opción múltiple, 1 V/F) | `/materias/:id/banco` → nueva pregunta |
| 5 | Docente | Crea una actividad de período abierto sobre esa materia | menú → Actividades → nueva |
| 6 | Administrador | Login, ve su Home, navega a Comisiones | `/login` → `/` → menú → Comisiones |
| 7 | Administrador | Crea una Comisión eligiendo la Materia ya creada | `/comisiones` → `/comisiones/nueva` |
| 8 | Administrador | Entra al detalle de la Comisión, asigna al Docente | `/comisiones/:id` |
| 9 | Docente | Login, navega a Actividades → Ver Comisiones de su Materia | `/login` → menú → Actividades → "Ver Comisiones" |
| 10 | Docente | Entra a la Comisión asignada, genera el link de invitación | `/actividad-evaluativa/materias/:id/comisiones` → detalle |
| 11 | Estudiante (nuevo) | Se registra con el link generado | `/registro?token=...` |
| 12 | Estudiante | Login | `/login` |
| 13 | Estudiante | Ve la actividad disponible, la inicia | Home Estudiante → Actividades |
| 14 | Estudiante | Responde una pregunta, suspende la evaluación | pantalla de evaluación |
| 15 | Estudiante | Reanuda, responde la segunda, finaliza | pantalla de evaluación |
| 16 | Estudiante | Ve la revisión completa | pantalla de revisión |
| 17 | Estudiante | Ve su propio desempeño (Analytics) | menú → Mi desempeño |
| 18 | Docente | Ve el desempeño de ese alumno elegido | menú → Desempeño por alumno |
| 19 | Docente | Ve la tasa de error por tema de la materia | menú → Desempeño por tema |

**Nota sobre el orden (corregida tras la primera corrida, ver `evidencia.md` §4):** una
Comisión referencia una Materia por `materia_id` (`US-2.1.2`) — el selector de "Nueva
Comisión" la exige, así que la Materia (con su banco de preguntas y actividad) debe existir
antes de que el Administrador pueda crear la Comisión. La tabla de arriba ya refleja el orden
real ejecutado, no el orden originalmente propuesto en
`docs/plans/inc4-adj/inc4-adj-candidatas.md`.

## Criterio de aceptación

Los 19 pasos completados sin ningún hallazgo 🔴 Bloqueante (un hallazgo que impida continuar
el guion o que revele un dato incorrecto en la UI). Hallazgos 🟡 Observación se registran igual
en `evidencia.md` y se clasifican por el criterio de `CLAUDE.md` §"Clasificación de hallazgos
en UAT" (formal si toca `src/`, informal si es solo `frontend/`). Confirmación final por
Víctor.
