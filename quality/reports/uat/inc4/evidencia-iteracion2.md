# Evidencia UAT — Iteración 2 del Incremento 4 "Portal del estudiante y Analytics"

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc4/design-iteracion2.md` |
| Fecha ejecución | 2026-09-06 |
| Ejecutor | Sesión de Claude Code (Capa 1 + Capa 2 + recorrido automatizado en navegador real vía Claude Browser) |

---

## Capa 1 — pytest + Vitest

```
.venv/bin/pytest -q
1 failed, 851 passed, 71 warnings in 565.50s (0:09:25)
FAILED tests/step_defs/inc3/test_us_3_2_1_steps.py::test_rechazo_fuera_del_período_vigente
```

Única falla: la ya documentada en `CLAUDE.md` (ventana de tiempo ajustada entre creación de
actividad e inicio de evaluación en el propio setup del test, `task_471c8a04`) — confirmada
como preexistente, no una regresión de esta iteración. Sin ningún otro fallo.

```
cd frontend && npx vitest run
Test Files  46 passed (46) [en ejecución aislada del archivo con flake conocido]
     Tests  261 passed (261)
```

Al correr la suite completa en paralelo con `--coverage` se repitió el mismo flakiness por
timeout ya documentado en `US-4.2.5-quality.json`/`US-4.2.6-quality.json` (archivos no tocados
por esta iteración, siempre en verde en ejecución aislada) — no es una regresión.

---

## Capa 2 — HTTP vía `smoke.sh` extendido

`.claude/skills/run-cognion/smoke.sh` se extendió con la sección "Analytics — Iteración 2"
(`US-4.2.1`/`US-4.2.2`/`US-4.2.4`), inmediatamente después del bloque de Iteración 1. Corrida
completa, todos los pasos en verde:

```
== Flujo de Analytics — desempeño por alumno y por tema (Incremento 4, Iteración 2, RF-16/RF-17) ==
== GET /materias/{materia_id}/comisiones (docente, US-4.2.2) ==
OK (comisión encontrada)
== GET /comisiones/{comision_id}/estudiantes (docente, US-4.2.2) ==
OK (estudiante encontrado)
== GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno (docente elige al estudiante, US-4.2.1, RF-16) ==
OK (0 correctas, 2 incorrectas, igual que la vista del propio estudiante)
== GET /analytics/materias/{materia_id}/estudiantes/{id}/desempeno con id inexistente (esperado 404) ==
OK (404)
== GET /analytics/materias/{materia_id}/tasa-error-por-tema, toda la materia (docente, US-4.2.4, RF-17) ==
OK (Geografía y Arquitectura con tasa_error=1.0, 1 respuesta cada uno)
== GET /analytics/materias/{materia_id}/tasa-error-por-tema?comision_id={id} (acotado a la comisión, US-4.2.4) ==
OK (misma tasa acotada a la comisión sembrada)
== GET /analytics/materias/{materia_id}/tasa-error-por-tema con rol estudiante (esperado 403, RBAC) ==
OK (403)

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

El resto de la corrida (Identidad, Cuentas, Banco de Preguntas, Actividad Evaluativa, Analytics
Iteración 1) sigue en verde sin cambios.

---

## Verificación con datos sembrados a propósito — `guion_manual_iteracion2.sh`

Se corrió `tests/uat/inc4/guion_manual_iteracion2.sh`, que siembra una comisión con 2
estudiantes (Ana Pérez, Juan Gómez) y un banco de 3 preguntas (una por tema, severidad de error
distinta a propósito), respondidas en 2 actividades finalizadas por ambos. Verificado por HTTP
directo contra el backend real (no mockeado) tras la siembra:

| Consulta | Esperado (diseñado en el guión) | Obtenido |
|---|---|---|
| `GET /analytics/.../estudiantes/{ana}/desempeno` | 3 correctas / 3 incorrectas / 50% / 2 evaluaciones | ✅ idéntico |
| `GET /analytics/.../estudiantes/{juan}/desempeno` | 4 correctas / 2 incorrectas / 67% / 2 evaluaciones | ✅ idéntico |
| `GET /analytics/.../tasa-error-por-tema` (toda la materia) | Inversión de dependencias 100%, Bounded Contexts 25%, Ciclo de vida del software 0%, en ese orden | ✅ idéntico |

**Recorrido en navegador real (Claude Browser, sesión de Claude Code)** — login como Docente,
navegación directa a las dos pantallas nuevas:

- **"Desempeño por alumno"** (`/analytics/desempeno-por-alumno`): selectores en cascada
  Materia → Comisión → Estudiante funcionan; elegir "Ana Pérez" muestra 3/3/50%/2 con el
  detalle de las 2 evaluaciones (`Parcial 1`, `Parcial 2`) y su fecha — coincide exactamente
  con lo sembrado.
- **"Desempeño por tema"** (`/analytics/desempeno-por-tema`): elegir la Materia sin tocar
  Comisión (queda en "Toda la materia") muestra el listado ordenado por tasa de error
  descendente: "Inversión de dependencias" 100% en rojo, "Bounded Contexts" 25% en ámbar,
  "Ciclo de vida del software" 0% en verde — severidad por color exactamente como especifica
  el wireframe (§3.1, umbrales 50%/20%).

**Rechazo por rol (frontend):** login como Estudiante (Ana Pérez) e intento de acceder a
`/analytics/desempeno-por-tema` → pantalla "Acceso denegado — No tenés permiso para ver esta
pantalla" (`RequireRole`), sin llegar a ver el contenido del Docente.

Confirmación humana de Víctor sobre este mismo recorrido (o uno propio con
`guion_manual_iteracion2.sh`), pendiente — ver §3 más abajo.

---

## §3 — Revisión manual de Víctor

Guión de siembra: `tests/uat/inc4/guion_manual_iteracion2.sh` (imprime credenciales, ids y el
resultado esperado de cada pantalla al final). Revisado por Víctor en navegador real sobre los
datos sembrados por este guión (mismos datos verificados arriba por la sesión) — **sin
hallazgos nuevos**.

**Conclusión:** ✅ aprobado sin observaciones. Cierra completa la Iteración 2 del Incremento 4
(backend + frontend, RF-16/RF-17).

---

## Criterio de aceptación — resultado

- Capa 1 (pytest + Vitest): ✅ en verde, sin regresiones (851/852 backend, único fallo
  preexistente ya documentado; 261/261 frontend).
- Capa 2 (HTTP vía `smoke.sh` extendido): ✅ los 4 casos nuevos (comisiones/estudiantes de
  `US-4.2.2`, desempeño por alumno de `US-4.2.1` con 404 de estudiante inexistente, tasa de
  error por tema de `US-4.2.4` con y sin `comision_id`, rechazo por rol) responden con los
  valores esperados.
- Verificación con datos realistas y recorrido en navegador real: ✅ ambas pantallas muestran
  exactamente los valores sembrados, con severidad por color correcta.
- UAT visual de Víctor: ✅ aprobado sin observaciones (§3).

**Conclusión:** cierra completa la Iteración 2 del Incremento 4 (backend + frontend,
RF-16/RF-17). `docs/traceability/matrix.md` actualizado (RF-16/RF-17 → Implementado). Próximo
paso: evaluar el cierre de la baseline del Incremento 4 completo (Iteraciones 1 y 2 juntas).
