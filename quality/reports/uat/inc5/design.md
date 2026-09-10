# Diseño de Pruebas UAT — Incremento 5 "Notificaciones"

| Campo | Valor |
|-------|-------|
| Incremento | 5 |
| Baseline | BL-009 (a abrir al cierre de esta UAT) |
| US cubiertas | US-5.0.1 (modelado), US-5.1.1 a US-5.1.3 (RF-14) |
| Entorno | Propio |
| Fecha diseño | 2026-09-10 |

## Objetivo

Verificar de punta a punta RF-14 (`RF_v1.md`): al crear una actividad de período abierto y al
cerrarla manualmente, los estudiantes de las comisiones correspondientes reciben un email real
(vía SMTP) con el contenido esperado — sin que el envío bloquee ni afecte la respuesta HTTP de
la operación de dominio. Cierra completa el Incremento 5 (mismo criterio que
`inc5-candidatas.md`: no hay Iteración 2 planificada, `US-5.1.3` cierra la única iteración).

Sin gate de diseño UX que verificar — RF-14 no tiene pantalla propia
(`docs/specs/inc5/US-5.1.1.md` a `US-5.1.3.md`, "Fuente de verdad UX: No aplica").

## Estrategia

**Capa 1 (pytest) + Capa 2 (HTTP, entorno propio).** Sin recorrido en navegador real — a
diferencia de los incrementos con frontend, acá no hay pantalla que navegar; la verificación
manual equivalente es la revisión directa del contenido de los emails capturados (ver
"Verificación manual" más abajo).

## Escenario DoD

Un Docente crea una Materia con una Comisión y un Estudiante inscripto (flujo real de
`US-1.1.1`/`US-1.1.8`, ya presente en `smoke.sh`), carga preguntas, crea una actividad de
período abierto sin restringir por comisión (dispara `notificar_apertura` a toda la materia,
que en este escenario es exactamente esa comisión) y luego la cierra manualmente antes de que
venza el período (dispara `notificar_cierre`). El estudiante recibe ambos emails.

## Capa 1 — Tests Automatizados

| ID | Test | Qué verifica |
|----|------|--------------|
| C1-1 | `pytest tests/unit/ tests/integration/ -q` | 757/757 en verde (backend completo, incluye `tests/unit/inc5/`, `tests/integration/inc5/`) |
| C1-2 | `pytest tests/step_defs/ -q` | 212/212 escenarios BDD en verde, incluidos los 4 de `US-5.1.2` y los 4 de `US-5.1.3` |

## Capa 2 — Verificación HTTP

`.claude/skills/run-cognion/smoke.sh` ya ejercita la creación (`POST /actividades`, `US-3.1.2`)
y el cierre manual (`POST /actividades/{id}/cerrar`, `US-3.3.2`) de una actividad, con un
estudiante real inscripto en la única comisión de esa materia — estos pasos ya existían por
otras US y ahora, con `US-5.1.2`/`US-5.1.3` mergeadas, disparan las notificaciones sin cambios
adicionales. Se extendió el script en dos puntos:

| ID | Verificación | Resultado esperado |
|----|--------------|---------------------|
| C2-1 | `fake_smtp.py` extendido para persistir cada mensaje capturado a un archivo (antes lo descartaba) | Log con el contenido real de cada email — headers + cuerpo |
| C2-2 | Assertion nueva inmediatamente después de `POST /actividades` | El log contiene `Subject: Nueva actividad disponible:` dirigido al email del estudiante sembrado |
| C2-3 | Assertion nueva inmediatamente después de `POST /actividades/{id}/cerrar` | El log contiene `Subject: Actividad cerrada:` dirigido al mismo estudiante |

## Verificación manual (sin recorrido de navegador — BC sin pantalla propia)

En vez de un recorrido de UI, la verificación manual consiste en revisar el contenido real de
los emails capturados por el fake SMTP durante la corrida de `smoke.sh` — ver
`evidencia.md` §3 para el log completo. Decisión de Víctor (2026-09-10): usar el log de texto
del fake SMTP existente en vez de instalar un catcher real (Mailhog) — no agrega cobertura
nueva para este alcance puntual.

## Criterio de aceptación

- Capa 1 en verde sin regresiones (757/757 unit+integration, 212/212 BDD).
- Capa 2 (`smoke.sh` extendido) en verde, con las dos assertions nuevas de notificación
  pasando.
- Contenido de los emails capturados revisado por Víctor, sin hallazgos 🔴 Bloqueantes.
