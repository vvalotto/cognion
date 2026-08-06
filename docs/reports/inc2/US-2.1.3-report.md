# Reporte de Implementación: US-2.1.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.3 - Docente carga una pregunta de opción múltiple en un banco
- **Puntos estimados:** 5
- **Tiempo real:** ~36 min (Fases 0–7, tracking de ejecución del agente — no comparable
  contra esfuerzo humano, nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-06

Tercera US de la Iteración 1 del Incremento 2 (BC Banco de Preguntas). Primer tipo de pregunta
implementado — establece el patrón de carga que `US-2.1.4` (Verdadero/Falso) sigue con su
propia estructura diferenciada, sin generalizar entre ambos tipos
(`BC-banco-preguntas-modelo.md` §4). Depende de `US-2.1.1` (`Banco` existente) como
precondición.

---

## Componentes Implementados

### Entities
- ✅ `src/banco_preguntas/entities/opcion.py` — value object `Opcion` (`texto`, `es_correcta`)
- ✅ `src/banco_preguntas/entities/dificultad.py`, `importancia.py` — `StrEnum`
  `Dificultad`/`Importancia` (Alto/Medio/Bajo), no desglosados como archivo aparte en el plan
  original pero requeridos por el aggregate según `BC-banco-preguntas-modelo.md` §4
- ✅ `src/banco_preguntas/entities/pregunta_plantilla.py` — aggregate
  `PreguntaPlantillaOpcionMultiple`; factory `crear()` valida INV-BP-02 (exactamente una
  opción correcta) e INV-BP-03 (mínimo 2 opciones) — invariantes puras de la estructura de
  `opciones`, validadas en la entidad sin necesidad de repositorio (mismo criterio que
  `Banco.crear`/`Materia.crear`)
- ✅ `src/banco_preguntas/entities/errors.py` (editado) — `OpcionesInvalidas`, `BancoNoExiste`
- ✅ `src/banco_preguntas/entities/eventos.py` (editado) — `PreguntaCargada`
- ✅ `src/banco_preguntas/entities/ports/pregunta_repository_port.py` —
  `PreguntaRepositoryPort.guardar()`
- ✅ `src/banco_preguntas/entities/ports/banco_repository_port.py` (editado) — agregado
  `obtener_por_id()`, necesario para validar la precondición de `banco_id` existente (mismo
  patrón que `MateriaRepositoryPort.obtener_por_id`, `US-2.1.2`)

### Use Cases
- ✅ `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py` —
  `CargarPreguntaOpcionMultipleUseCase.execute()`: verifica `Banco` existente (`BancoNoExiste`
  si no), delega INV-BP-02/03 a la entidad, persiste, devuelve `(pregunta, PreguntaCargada)`

### Interface Adapters
- ✅ `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` —
  `PreguntasController.cargar_pregunta_opcion_multiple()`
- ✅ `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` —
  `SQLAlchemyPreguntaRepository`
- ✅ `src/banco_preguntas/interface_adapters/gateways/banco_repository.py` (editado) —
  `obtener_por_id()` agregado a `SQLAlchemyBancoRepository` existente

### Frameworks
- ✅ `src/banco_preguntas/frameworks/db/models.py` (editado) — `PreguntaPlantillaModel`, tabla
  `pregunta_plantilla` con columna discriminadora `tipo` (`"opcion_multiple"` en esta US, deja
  lugar a `"verdadero_falso"` en `US-2.1.4`); `opciones` como `JSONB` en vez de tabla aparte,
  coherente con el event store JSONB append-only ya usado en el proyecto
- ✅ `src/banco_preguntas/frameworks/api/schemas.py` (editado) — `OpcionSchema`,
  `CargarPreguntaOpcionMultipleRequest`, `PreguntaOpcionMultipleResponse`
- ✅ `src/banco_preguntas/frameworks/api/preguntas_router.py` — `POST /preguntas/opcion-multiple`
- ✅ `src/banco_preguntas/frameworks/dependencies.py` (editado) — `get_preguntas_controller()`
- ✅ `src/app.py` (editado) — registrado `preguntas_router`

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| POST | `/preguntas/opcion-multiple` | Carga pregunta de opción múltiple; 201, 404 si `BancoNoExiste`, 422 si `OpcionesInvalidas` | ✅ `require_docente` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.37/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 6 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 56.40 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 99.0% (100% en código nuevo) | ≥ 95.0% | ✅ |

Fuente: `quality/reports/inc2/US-2.1.3-quality.json`. Coverage medido sobre
`entities`/`use_cases`/`interface_adapters` del BC `banco_preguntas` completo (250/250
statements relevantes); `frameworks/` excluido del gate por convención del proyecto
(`pyproject.toml`). Las 3 líneas sin cubrir (`materia_repository.py:40-42`) son código
preexistente de `US-2.1.1`, fuera del alcance de esta US. mypy sobre `src/` completo: sin
issues (117 archivos).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (11 nuevos) — `tests/unit/inc2/`
- `test_pregunta_plantilla.py` (4 tests) — factory `crear()`: creación válida, rechazo
  ninguna/más de una opción correcta, rechazo menos de 2 opciones
- `test_cargar_pregunta_opcion_multiple_use_case.py` (3 tests) — carga exitosa, `BancoNoExiste`,
  propagación de `OpcionesInvalidas` sin persistir
- `test_preguntas_controller.py` (1 test) — delegación al use case
- `_fakes.py` (editado) — `FakeBancoRepository.obtener_por_id`, `FakePreguntaRepository` nuevo

### Tests de Integración (11 nuevos) — `tests/integration/inc2/`
- `test_pregunta_repository_integration.py` (3 tests) — `SQLAlchemyBancoRepository.obtener_por_id`
  (existente/inexistente), `SQLAlchemyPreguntaRepository.guardar` contra PostgreSQL real
- `test_preguntas_api_integration.py` (7 tests) — flujo HTTP completo: carga exitosa, 3 rechazos
  por INV-BP-02/03, `BancoNoExiste`, sin autenticación, rol insuficiente
- `conftest.py` (editado) — limpieza de tabla `pregunta_plantilla`

### Escenarios BDD (4 nuevos) — `tests/features/inc2/US-2.1.3-cargar-pregunta-opcion-multiple.feature`
- Carga exitosa
- Rechazo por ninguna opción correcta
- Rechazo por más de una opción correcta
- Rechazo por menos de 2 opciones

`tests/step_defs/inc2/test_us_2_1_3_steps.py` — reutiliza `docente_headers()` de
`_auth_headers.py` (`US-2.1.1`).

**Todos los tests pasando:** ✅ 180/180 (suite completa del proyecto)

---

## Migraciones de Base de Datos

- ✅ `migrations/versions/b0e03a73f699_pregunta_plantilla.py`
  - Crea tabla `pregunta_plantilla`: `id`, `banco_id` (FK a `banco.id`), `tipo`, `texto`,
    `opciones` (`JSONB`, nullable), `unidad_tematica`, `tema`, `dificultad`, `importancia`,
    `activa`
  - Aplicada contra PostgreSQL local (`alembic upgrade head`)
  - Convención de ruta real del proyecto: `migrations/versions/` en la raíz, no
    `src/.../frameworks/db/migrations/` como sugería la spec original — se verificó contra
    `US-2.1.1`/`US-2.1.2` antes de generarla

---

## Decisión de Nomenclatura Resuelta en Fase 3

**`unidad_tematica` vs. `unidad`:** la spec de `US-2.1.3` usa `unidad` como shorthand en la
firma del comando `CargarPreguntaOpcionMultiple(banco_id, texto, opciones, unidad, tema,
dificultad, importancia)`, pero el modelo de dominio (`BC-banco-preguntas-modelo.md` §4,
tabla de atributos de `PreguntaPlantillaOpcionMultiple`) usa `unidad_tematica` como nombre
completo del atributo. Se usó `unidad_tematica` en entidad, use case, gateway, modelo
SQLAlchemy y schemas — mismo campo, nombre completo, consistente con la fuente de verdad del
modelo de dominio.

---

## Archivos Creados/Modificados

**Producción (nuevo):** `src/banco_preguntas/entities/opcion.py`, `dificultad.py`,
`importancia.py`, `pregunta_plantilla.py`,
`src/banco_preguntas/entities/ports/pregunta_repository_port.py`,
`src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py`,
`src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py`,
`src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`,
`src/banco_preguntas/frameworks/api/preguntas_router.py`,
`migrations/versions/b0e03a73f699_pregunta_plantilla.py`.

**Producción (editado):** `src/banco_preguntas/entities/errors.py`, `eventos.py`,
`entities/ports/banco_repository_port.py`,
`interface_adapters/gateways/banco_repository.py`, `frameworks/db/models.py`,
`frameworks/api/schemas.py`, `frameworks/dependencies.py`, `src/app.py`.

**Tests (nuevos):** `tests/unit/inc2/test_pregunta_plantilla.py`,
`test_cargar_pregunta_opcion_multiple_use_case.py`, `test_preguntas_controller.py`,
`tests/integration/inc2/test_pregunta_repository_integration.py`,
`test_preguntas_api_integration.py`,
`tests/features/inc2/US-2.1.3-cargar-pregunta-opcion-multiple.feature`,
`tests/step_defs/inc2/test_us_2_1_3_steps.py`.

**Tests (editados):** `tests/unit/inc2/_fakes.py`, `tests/integration/inc2/conftest.py`.

**Documentación:** `docs/plans/US-2.1.3-{context,plan}.md`,
`docs/reports/inc2/US-2.1.3-report.md` (este archivo),
`quality/reports/inc2/US-2.1.3-{quality,pylint,cc,mi,coverage}.json`, `CHANGELOG.md` (editado).

---

## Criterios de Aceptación

- [x] Carga exitosa — `PreguntaPlantillaOpcionMultiple` persistida con `activa = true`, evento
  `PreguntaCargada` emitido
- [x] Rechazo por ninguna opción correcta — `OpcionesInvalidas` (INV-BP-02)
- [x] Rechazo por más de una opción correcta — `OpcionesInvalidas` (INV-BP-02)
- [x] Rechazo por menos de 2 opciones — `OpcionesInvalidas` (INV-BP-03)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.1.4` — Docente carga una pregunta verdadero/falso (mismo patrón, tipo distinto,
  columna discriminadora `tipo` ya deja lugar en el modelo)
- [ ] RF-04/RF-05 permanecen "Especificado" en `docs/traceability/matrix.md` hasta que también
  cierre `US-2.1.4` (RF-04) y `US-2.1.4`/`US-2.1.5` (RF-05) — mismo criterio usado con
  RF-01/RF-02 en Identidad

---

## Lecciones Aprendidas

- ✅ Delegar la validación de INV-BP-02/03 al factory de la entidad
  (`PreguntaPlantillaOpcionMultiple.crear`) mantuvo el use case simple y concentró las
  invariantes estructurales en un solo punto de verdad, sin necesitar repositorio para
  validarlas.
- 💡 Verificar el nombre exacto de un atributo contra el modelo de dominio
  (`BC-banco-preguntas-modelo.md` §4) antes de copiar el shorthand de la firma del comando en
  la spec evitó introducir una inconsistencia de nombres (`unidad` vs. `unidad_tematica`) entre
  capas.
- ⚠️ La spec sugería `src/.../frameworks/db/migrations/` como ruta de la migración Alembic;
  la convención real del proyecto es `migrations/versions/` en la raíz. Verificar contra la US
  anterior en vez de confiar en el template de la spec (mismo hallazgo que
  `feedback_implement_us_rutas_incN` de memoria, aplicado ahora también a migraciones).

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-06
