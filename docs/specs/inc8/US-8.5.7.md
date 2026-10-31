# US-8.5.7: Ensayo y prueba en red local con alumnos (UAT)

**Estado**: `Desestimada` (decisión de Víctor, 2026-10-18; no se implementa en este incremento)
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `UAT / verificación` (sin código de producción)
**Bounded Context**: transversal
**Issue**: #542

---

## Descripcion (lenguaje de negocio)

Como **docente**,
quiero **probar el sistema con alumnos reales conectados por la red del aula**,
para **saber qué falla con uso real antes de decidir dónde y cómo se despliega de forma definitiva**.

---

## Especificacion del comportamiento

Dos tramos, con Víctor presente; la sesión de Claude Code **no** contacta ni interactúa con los alumnos.

1. **Ensayo previo** (sin alumnos): con 2 o 3 dispositivos reales (iPhone, iPad, Android si hay) en la red elegida:
   levantar con `levantar.sh`, entrar por la URL impresa, hacer un respaldo y restaurarlo, completar el flujo de período
   abierto y una sesión en vivo corta. Se corrigen los hallazgos 🔴 antes de seguir.
2. **Prueba con alumnos**: se ejecuta el plan de `US-8.5.6`. Se respalda antes y después.

Artefactos en `quality/reports/uat/inc8-local/` (misma estructura que `inc7`): `registro-ejecuciones.md`,
`registro-hallazgos.md` (severidad 🔴 bloqueante / 🟡 observación / 🟢 mejora) y `plan-de-correccion.md`. El plan de
corrección **prioriza, no ejecuta**: cada hallazgo se clasifica en track informal (solo `frontend/`) o formal
(toca `src/`), según `CLAUDE.md`.

## Escenarios (BDD)

1. El ensayo previo con dispositivos reales termina sin hallazgos 🔴 abiertos.
2. La prueba con alumnos se ejecuta y queda registrada (cuántos alumnos, qué se hizo, qué falló).
3. Los respaldos de antes y después existen y el posterior se restaura en una base temporal.
4. Todos los hallazgos tienen severidad, track propuesto y estado.

## Definition of Done

Cierra la Iteración 5. La decisión de nube se retoma con la evidencia de esta prueba (capacidad percibida, latencia,
qué pidieron los alumnos) y con la respuesta de la Universidad sobre el convenio con Google.

## Fuente de verdad UX

No aplica — verificación de lo ya aprobado.
