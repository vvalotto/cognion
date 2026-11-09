# Reporte — US-ADJ-63: El hash de contraseñas no bloquea el event loop

**Estado:** implementada en `feature/inc-9-iter-1-correcciones` (2026-11-07), un commit por US; el PR sale al cierre de la Iteración 1.
**Issue:** [#562](https://github.com/vvalotto/cognion/issues/562) · **Spec:** `docs/specs/ajustes/US-ADJ-63.md` · **Origen:** prueba de despliegue en GCP, paso 13 (`US-8.6.3`)

## Qué se hizo
- `PasswordHasherPort` suma `hash_async`/`verificar_async` (abstractos); `hash`/`verificar` quedan como están.
- `BcryptPasswordHasher` implementa las asíncronas con `run_in_executor` sobre un `ThreadPoolExecutor` propio de `os.cpu_count()` hilos (`lru_cache`, `thread_name_prefix="bcrypt"`). Mismo algoritmo, costo (12) y formato de hash (`ADR-014`).
- Los 9 puntos de uso en 8 casos de uso de Identidad (`iniciar_sesion`, `cambiar_password` ×2, `crear_usuario`, `resetear_password`, `confirmar_nueva_password`, `autoregistrar_docente`, `autoregistrar_estudiante`, `registrar_estudiante`) pasan a `await self._hasher.<op>_async(...)`. Controllers, routers y `frontend/` no cambian.
- `FakePasswordHasher` implementa las dos formas asíncronas.

## Decisiones
- **Opción A2 en lugar de la A de la spec.** El puerto lo implementan solo dos clases, pero **144 llamadas en 58 archivos de tests** usan `hash`/`verificar` de forma síncrona para sembrar usuarios. En vez de volver `async` esos métodos, se agregaron las formas `*_async` y se conservaron las síncronas: los tests no cambian y un `await` olvidado no puede guardar una corrutina como hash. Una **guarda automática** (recorrido AST de `src/*/use_cases/`) falla si un caso de uso llama la forma síncrona o no espera la asíncrona.
- **Ejecutor propio** acotado a los núcleos, no el de `asyncio` por defecto (6 hilos en 2 vCPU), para que una ráfaga de logins no le quite CPU al hilo del event loop.
- Umbral de tiempo de **150 ms** (la spec decía 120) con hasta 3 intentos, para no depender de la carga del equipo.

## Hallazgos al probar
- **La primera versión de la prueba de tiempo no detectaba el bloqueo:** el último latido nunca se registraba si el bloqueo duraba hasta el final de la medición. Se descubrió probándola con el adaptador bloqueando; se agregó un latido final y se volvió a verificar.
- **bcrypt costo 12 tarda 414 ms** en la Mac de desarrollo (8 núcleos), más que los 250 a 325 ms previstos; la separación entre "libre" y "bloqueado" es amplia.
- **Un error mío al verificar:** en un experimento usé la variable de shell `U` para la ruta de `iniciar_sesion.py`, y el script de la base descartable también define `U` (el usuario de la base); al cargarlo la pisó y mi restauración copió el archivo a un `user` suelto en vez de al caso de uso, que quedó con la llamada síncrona. La guarda automática lo señaló de inmediato; se reaplicó el cambio y se borró el archivo suelto. Lección: no reutilizar nombres de variable entre un experimento y un script que se carga con `source`.
- Se registraron en `pyproject.toml` las etiquetas BDD nuevas de esta US y de `US-ADJ-68`.

## Calidad
13 unitarios (bcrypt real, sin base), 2 de integración con un `uvicorn` real y 6 escenarios BDD, todos en verde. **Regresión: 1359 tests pasan** contra una base descartable (toda la suite unitaria más la integración y el BDD de Identidad); la suite completa se corre una sola vez al cerrar la Iteración 1. Con el adaptador bloqueando fallan los 2 unitarios de tiempo (el event loop queda 1,5 s sin responder); con el login en la forma síncrona falla la guarda y `/health` tarda **1,163 s durante 3 logins** (umbral 0,35 s). `pylint` 10,00/10 en el puerto y el adaptador, `mypy` 0 errores (315 archivos), `ruff`/`black`/`isort` limpios, `bandit` sin problemas, CC promedio A (2,05), MI mínimo 100. Evidencia: `quality/reports/inc9/US-ADJ-63-quality.json`.

## Tiempo
Ver `.claude/tracking/US-ADJ-63-tracking.json`.

## Pendiente
- **Verificación en la VM de GCP** (fuera de esta US): repetir la ráfaga de 60 logins y medir el tiempo hasta el último y la latencia de un request ajeno (referencia: 19,5 s con el código anterior). La VM está pausada; la medición va con #597.
- Eliminar la base descartable `cognion_dg_descartable` al cerrar la iteración.
