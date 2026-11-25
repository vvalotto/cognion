# ADR-029 — Errores de dominio con categoría y traducción a HTTP en un solo lugar

**Estado:** Aceptado
**Fecha:** 2026-11-25
**Origen:** Issue [#667](https://github.com/vvalotto/cognion/issues/667), hallazgo `IM-02` de la revisión de diseño (`docs/revision-diseno-2026-11/`); decidido con Víctor en la Iteración 2 del Incremento 12. Relacionado con `ADR-017` y `ADR-019` (qué puede vivir en `shared/`) y con `ADR-028` (unidad de trabajo). Lo implementa `US-12.2.2` (Issue [#669](https://github.com/vvalotto/cognion/issues/669)).

---

## Contexto

Hay 78 clases de error en los `entities/errors.py` de los cinco contextos (Actividad Evaluativa 39, Identidad 25, Banco 8, Analytics 4 y 2 en `shared`) y **todas heredan directamente de `Exception`**, sin una base común. Son 69 nombres distintos: cinco nombres se repiten como clases separadas en varios contextos (`MateriaNoAutorizada` en 4, `ComisionNoAutorizada` en 3, `MateriaNoExiste` en 3, `ActividadNoExiste` y `ComisionNoExiste` en 2). Ningún `exception_handler` está registrado en `app.py`. Cada router repite el `try/except` con la lista de errores que su autor recordó y los traduce a mano: 136 `raise HTTPException` en 19 routers, 134 de ellos dentro de un `except`.

Medición del 2026-11-25 (AST sobre `src/*/frameworks/api/`):

| Código HTTP | Traducciones | Clases de error que lo reciben |
|---|---|---|
| 404 | 48 | 16 |
| 403 | 38 | 10 |
| 422 | 36 | 37 |
| 409 | 10 | 5 |
| 401 | 2 | 2 |
| sin traducción en ningún router | — | 8 |

(Cada router se resolvió contra el contexto del que importa la clase, porque hay nombres repetidos entre contextos.)

- **Casi no hay inconsistencia entre endpoints:** solo dos clases reciben dos códigos, ambas de Identidad: `ComisionNoExiste` (10 veces 404 y 1 vez 422) y `MateriaNoExiste` (1 vez 404 y 1 vez 422). El 422 es cuando el id viene en el cuerpo del pedido (`autoregistrar_estudiante`, `crear_comision`) y el 404 cuando viene en la URL: una distinción legítima.
- **El contrato de la respuesta importa:** 128 de las 136 traducciones usan `detail=str(exc)`; 8 usan un objeto estructurado con `codigo` (`auth_router`, `perfil_router`, `cuentas_router`), que el frontend lee desde `US-ADJ-67` para no interpretar el texto. Dos módulos ya centralizan parte de eso (`errores_invitacion.py` y `bloqueo_temporal.py`). Ninguna traducción agrega cabeceras.
- **Los 8 errores sin traducción en un router** tienen otro camino: las invitaciones y el bloqueo temporal pasan por esos dos módulos y los de JWT por la autenticación; `ConcurrenciaOptimistaError` la capturan los casos de uso.
- **No se midió** que "un error de dominio que nadie listó salga como 500", como infiere el informe: es plausible, pero no se comprobó.

## Opciones Consideradas

| Opción | Qué es | Costo y riesgo |
|---|---|---|
| **A. Base y categorías en el dominio** | Una base `ErrorDeDominio` en `shared/entities/` con categorías; cada error hereda de la suya; un manejador en `app.py` traduce por categoría | Re-clasificar 78 clases (mecánico, deriva de la tabla de arriba, sin cambio de comportamiento) y borrar ~134 `try/except`. La historia más grande de la iteración, partible por contexto |
| **B. Tabla central en `frameworks/`** | Un diccionario `error → (status, codigo)` y un manejador, sin tocar las clases | Más barato de adoptar y un test puede exigir que toda clase esté en la tabla, pero la clasificación no vive en el dominio y quedan dos lugares que editar |
| **C. Decorador por endpoint** | Reduce líneas, no la decisión por endpoint | No resuelve la consistencia |
| **D. Estado HTTP dentro del error** | Cada clase lleva su código | El dominio pasaría a conocer HTTP; contradice la arquitectura |

## Decisión

**Todo error de dominio hereda de `ErrorDeDominio` (en `shared/entities/errors.py`) a través de una de cinco categorías —`NoEncontrado`, `NoAutorizado`, `NoAutenticado`, `ReglaViolada` y `Conflicto`— y un único manejador registrado en `app.py` las traduce a 404, 403, 401, 422 y 409. Un router solo conserva un `except` propio cuando el código depende del endpoint y no del error.**

## Justificación

- **Resuelve la causa, no el síntoma:** el código HTTP de cada error se decide una vez, junto con su categoría, en vez de endpoint por endpoint; y un error nuevo se clasifica al definirlo.
- **No cambia ningún comportamiento.** La categoría de cada una de las 78 clases se deriva del código que hoy recibe: 37 `ReglaViolada`, 16 `NoEncontrado`, 10 `NoAutorizado`, 5 `Conflicto` y 2 `NoAutenticado`; las 8 sin traducción en un router se deciden una por una en `US-12.2.2`. Los tests que ya verifican códigos de estado protegen la migración.
- **La clasificación es del dominio y el HTTP es de `frameworks/`:** "no existe", "no autorizado", "regla violada" y "conflicto" son conceptos del dominio que también sirven al canal WebSocket y a las CLI; el mapa de categoría a código vive en `frameworks/`. Por eso se descarta D.
- **Se descarta B** porque deja la clasificación fuera del dominio y en dos lugares, y **C** porque no resuelve la inconsistencia.
- **Los dos casos con código según el endpoint** (`ComisionNoExiste` en `autoregistrar_estudiante` y `MateriaNoExiste` en `crear_comision`, ambos en el cuerpo del pedido: 422) conservan un `except` local, que queda en la lista de excepciones de la guarda de `HTTPException`. Es el cambio mínimo; las alternativas (un error nuevo `ReferenciaInvalida`, o unificar todo en 404) tocan los casos de uso o el comportamiento del frontend por 2 endpoints.

## Impacto en Configuración

- `src/shared/entities/errors.py`: `ErrorDeDominio` con un `codigo` opcional y un método `detalle()` (devuelve `str(self)` y, si el error tiene `codigo`, el objeto `{codigo, mensaje, …}` que el frontend ya espera), más las cinco categorías.
- `src/shared/frameworks/api/errores.py` (nuevo) y `src/app.py`: el manejador y el mapa categoría → código (404, 403, 401, 422, 409).
- Los `entities/errors.py` de los cinco contextos: cada clase hereda de su categoría.
- Los 19 routers: se borran los `try/except` de traducción (134). Los errores con datos propios (`CuentaBloqueadaTemporalmenteError` con `reintentar_en_segundos`, `intentos_restantes`) sobrescriben `detalle()`; los dos módulos auxiliares (`errores_invitacion.py`, `bloqueo_temporal.py`) se absorben.
- `tests/unit/inc12/test_guardas_con_excepciones.py`: el conteo de `raise HTTPException` baja de 136 a un objetivo de **4** (los 2 `except` locales y los 2 `raise` directos de `analytics_router`, que `US-12.2.2` puede convertir en `NoEncontrado` para llegar a 2). Además, un test nuevo exige que toda clase de un `errors.py` herede de `ErrorDeDominio`.
- `pyproject.toml`: un contrato de `import-linter` que prohíbe a `frameworks/api/` importar `entities/errors.py` para traducir (criterio de salida de la iteración), con los dos `except` locales como únicas excepciones declaradas.
- `docs/architecture/` (vista transversal) y `docs/design/domain/`.

## Consecuencias

- ✅ El mismo error ya no puede ser 404 en un endpoint y 422 en otro por descuido, y un error nuevo se clasifica al nacer.
- ✅ Los routers pierden ~134 `try/except`: es la causa de buena parte de los métodos largos que DesignReviewer marca en `frameworks/`, y baja la presión sobre el umbral de CBO de `US-12.2.6`.
- ✅ La clasificación queda disponible para el canal WebSocket y las CLI.
- ⚠️ **Un error nuevo sin categoría sale como 500.** Lo evita el test que exige que toda clase de un `errors.py` herede de `ErrorDeDominio`.
- ⚠️ **Clasificar mal una clase cambia su código HTTP.** Se mitiga derivando cada categoría de la traducción actual y con los tests de estado existentes; `US-12.2.2` debe correr la suite completa y Playwright.
- ⚠️ **Puede cambiar el comportamiento donde hoy un error de dominio no estaba listado en un endpoint** y salía como 500: pasará a ser un 4xx. Es una mejora deliberada, pero `US-12.2.2` debe listar los casos que encuentre, porque podrían estar tapando un defecto.
- ⚠️ La migración se puede partir por contexto: 39 clases de Actividad Evaluativa, 25 de Identidad, 8 de Banco y 4 de Analytics, más las 2 de `shared`.
- ⚠️ **Los nombres repetidos entre contextos** (`MateriaNoAutorizada` en 4, `ComisionNoAutorizada` y `MateriaNoExiste` en 3, `ActividadNoExiste` y `ComisionNoExiste` en 2) son clases distintas que significan lo mismo: al re-clasificarlas conviene que `US-12.2.2` decida si se unifican en una sola de `shared/`. Se anota como oportunidad, no como parte de esta decisión.

## Enmienda 2026-11-25 (al escribir `US-12.2.2`)

Al revisar cada traducción para la spec apareció algo que la medición original no vio: **no son 2 las clases cuya traducción depende del endpoint, son 6**, todas de Identidad. La medición solo buscaba clases con distinto código; también hay clases con distinta **forma del `detail`**, y el frontend usa esos campos (`bloqueada`, `codigo`, `intentos_restantes`):

| Clase | Qué cambia según el endpoint |
|---|---|
| `ComisionNoExiste`, `MateriaNoExiste` | El código: 422 si el id viene en el cuerpo, 404 si viene en la URL (los 2 casos del texto original) |
| `CuentaBloqueadaError` | 403 con texto en `auth_router`; 403 con `{mensaje, bloqueada: true}` en `perfil_router` |
| `InvitacionInvalida` | 404 con texto en `invitaciones_grupales_router`; 404 o 422 con `{codigo, mensaje}` en `errores_invitacion.py` |
| `PasswordDemasiadoCorta`, `PasswordSinComplejidadSuficiente` | Texto en 4 routers; `{mensaje}` en `perfil_router`; `{codigo: "password_invalida", mensaje}` en `errores_invitacion.py` |

**La decisión no cambia, se amplía su excepción:** el criterio "un router solo conserva un `except` propio cuando la respuesta depende del endpoint y no del error" se aplica a estos 6 casos, no a 2, y unificarlos cambiaría una respuesta que el frontend lee. Por eso el objetivo de `raise HTTPException` en los routers deja de ser 4: la estimación es de **6 a 8**, y la guarda de `US-12.2.2` lo fija exacto tras clasificar los casos en la Fase 0.
