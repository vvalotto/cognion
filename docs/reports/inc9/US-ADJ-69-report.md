# Reporte — US-ADJ-69: El login avisa "te queda 1 intento" tras el 2.º fallo

**Estado:** implementada en `feature/inc-9-iter-2-link-grupal` (2026-11-08), un commit por US; el PR sale al cierre de la Iteración 2.
**Issue:** [#604](https://github.com/vvalotto/cognion/issues/604) (cierra [#502](https://github.com/vvalotto/cognion/issues/502) al mergear) · **Spec:** `docs/specs/ajustes/US-ADJ-69.md` · **Origen:** observación O-1 de la UAT del 7-ADJ; decisión de Víctor del 2026-11-08

## Qué se hizo
- **Entidad:** `CredencialesInvalidas.intentos_restantes` (`None` por defecto). Su docstring declara el trade-off: el aviso solo aparece en cuentas existentes.
- **Caso de uso:** `IniciarSesionUseCase` fija `intentos_restantes = 1` cuando el contador llega a `_INTENTOS_MAXIMOS - 1`, es decir, solo en el 2.º fallo. El 1.º y el 3.º (el que bloquea) responden como siempre.
- **Router:** `POST /identidad/login` devuelve `detail = {"mensaje": ..., "intentos_restantes": 1}` solo cuando hay aviso; sin aviso el `detail` sigue siendo texto. Ningún status cambia (3.er fallo `401`, siguiente `403`).
- **Frontend:** `LoginError` muestra "Te queda 1 intento antes del bloqueo de la cuenta." y el link "recuperala por email" a `/recuperar-password`; `Login` lee `detail.intentos_restantes`.
- **Documentación:** enmiendas en `US-2.2.1`, `US-ADJ-60` y `BC-identidad-modelo.md` (`INV-ID-10`).

## Decisiones
- El aviso se fija en el caso de uso y no en el router: es una regla de la política de bloqueo, no un detalle de presentación.
- Solo "queda 1": no se informa 2 ni 0, para revelar lo mínimo.
- Un email inexistente nunca lleva el aviso. Consecuencia aceptada por Víctor: el aviso permite distinguir las cuentas reales; el bloqueo del 4.º intento ya lo hacía.

## Hallazgo al probar
`apiFetch` descartaba el `detail` estructurado cuando la respuesta era `401` (solo lo conservaba para los demás status), así que `Login` nunca habría visto el aviso. El test de `Login` lo destapó; corregido y cubierto con un test propio en `api-client.test.ts`.

## Calidad
7 unitarios (sin base), 4 de integración por HTTP con base descartable, 6 escenarios BDD y, en frontend, 3 de `LoginError`, 2 de `Login` y 1 de `api-client`, todos en verde. 235 tests de regresión de login, bloqueo y Administrador pasan; 113 de frontend en identidad y `api-client` también. Con el código anterior fallan los 7 unitarios, 2 de los 4 de integración y 2 de los 6 BDD (los demás verifican lo que no cambia). `pylint` 9,94/10 (línea base de los tres archivos 9,87), `mypy` 0 errores (315 archivos), `ruff`/`black`/`isort` limpios, `tsc -b` sin errores. La suite completa se corre una sola vez al cerrar la Iteración 2. Evidencia: `quality/reports/inc9/US-ADJ-69-quality.json`.

## Tiempo
Ver `.claude/tracking/US-ADJ-69-tracking.json`.

## Pendiente
- Verificar en navegador real, al cierre de la iteración: tres fallos seguidos y el aviso en el segundo.
- Eliminar la base descartable `cognion_adj69_descartable` al cerrar la iteración.
