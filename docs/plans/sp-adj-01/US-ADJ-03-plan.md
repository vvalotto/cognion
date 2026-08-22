# Plan de Implementación: US-ADJ-03 - Paginar el listado del banco de preguntas

**Patrón:** Clean Architecture BC-first (backend) + React 19/TypeScript/Vite (frontend)
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-22
**Tiempo real (tracker):** 81 min (Fases 0 a 8)

## Decisión de diseño (Fase 2, no cubierta explícitamente por la spec)

`GET /bancos/{id}/preguntas` lo consumen 5 pantallas: `Banco.tsx` (tabla paginada, único
caso que necesita paginación real) y `EditarPregunta.tsx`/`EliminarPregunta.tsx`/
`NuevaPreguntaOpcionMultiple.tsx`/`NuevaPreguntaVerdaderoFalso.tsx` (necesitan el banco
**completo** para buscar una pregunta por id o derivar sugerencias de unidad/tema). Decisión
confirmada con Víctor: **paginación opt-in** — `pagina`/`tamanio_pagina` son opcionales en
el puerto/endpoint; si el caller no los manda, se devuelven todas las preguntas que
matchean los filtros (comportamiento actual, sin truncar). El contrato de respuesta pasa a
ser siempre `{ preguntas: [...], total: n }` (antes `list[...]` plano) — las 4 pantallas
que no paginan solo necesitan leer `.preguntas` en vez de la lista directa; `total` no
existía antes y no las afecta.

Sin esta decisión, las 4 pantallas se romperían silenciosamente en bancos de más de 20
preguntas (exactamente el escenario — 71 preguntas — que motiva esta US), violando su
propio criterio de "sin regresión funcional".

## Componentes a Implementar

### 1. Gate UX (previo a tocar `frontend/`)

- [x] `docs/design/ux/wireframes-banco-preguntas.md` §2.3 — sección de paginación agregada
  (ya hecho en esta sesión, antes de este plan)

### 2. Backend — Entities

- [x] `src/banco_preguntas/entities/pregunta_plantilla.py`
  - `fecha_creacion: datetime` en `PreguntaPlantillaOpcionMultiple` y
    `PreguntaPlantillaVerdaderoFalso`
  - Fijado en `crear()` (`datetime.now(timezone.utc)`), **no tocado** por `editar()`
    (inmutable, sin invariante de negocio — es metadata de orden)

### 3. Backend — Migración

- [x] `migrations/versions/<rev>_pregunta_plantilla_fecha_creacion.py`
  - `op.add_column("pregunta_plantilla", sa.Column("fecha_creacion", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))`
  - Mismo patrón que `92b42288ef96_usuario_creado_en.py` — backfill con el timestamp único
    de la migración para las filas existentes, sin necesidad de un `UPDATE` manual

### 4. Backend — Port

- [x] `src/banco_preguntas/entities/ports/pregunta_repository_port.py`
  - `filtrar()` agrega `pagina: int | None = None`, `tamanio_pagina: int | None = None`
  - Retorno cambia de `list[...]` a `ResultadoPaginadoPreguntas` (dataclass nuevo:
    `preguntas: list[...]`, `total: int`)
  - Nuevo archivo `src/banco_preguntas/entities/resultado_paginado_preguntas.py` con el
    dataclass

### 5. Backend — Gateway

- [x] `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
  - `filtrar()`: `ORDER BY fecha_creacion, id` (desempate estable) siempre
  - Si `pagina`/`tamanio_pagina` vienen dados: aplica `LIMIT`/`OFFSET`; si no: sin límite
    (comportamiento actual)
  - `total`: query de conteo separada con los mismos filtros (sin `LIMIT`/`OFFSET`) —
    siempre se calcula, paginando o no
  - `_a_entidad()`: mapea `fecha_creacion` del modelo a la entidad
  - `guardar()`/`actualizar()`: persisten `fecha_creacion` (alta) / la dejan intacta (edición)
- [x] `src/banco_preguntas/frameworks/db/models.py`
  - `PreguntaPlantillaModel.fecha_creacion: Mapped[datetime]`

### 6. Backend — Use Cases

- [x] `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py` — sin cambios de
  código (fecha_creacion se fija dentro de `PreguntaPlantillaOpcionMultiple.crear()`)
- [x] `src/banco_preguntas/use_cases/cargar_pregunta_verdadero_falso.py` — ídem
- [x] `src/banco_preguntas/use_cases/filtrar_banco.py`
  - `execute()` agrega `pagina: int | None = None`, `tamanio_pagina: int | None = None`,
    pasa ambos al puerto, retorna `ResultadoPaginadoPreguntas`

### 7. Backend — Interface Adapters / Frameworks

- [x] `src/banco_preguntas/interface_adapters/controllers/bancos_controller.py`
  - `filtrar_preguntas()` agrega `pagina`/`tamanio_pagina`, devuelve
    `ResultadoPaginadoPreguntas`
- [x] `src/banco_preguntas/frameworks/api/schemas.py`
  - `PreguntasPaginadasResponse` nuevo: `preguntas: list[PreguntaOpcionMultipleResponse | PreguntaVerdaderoFalsoResponse]`, `total: int`
- [x] `src/banco_preguntas/frameworks/api/bancos_router.py`
  - Query params `pagina: int | None = None`, `tamanio_pagina: int | None = None`
  - `response_model=PreguntasPaginadasResponse`

### 8. Frontend

- [x] `frontend/src/components/ui/pagination.tsx` (nuevo, reusable — `US-ADJ-05` lo va a
  reusar para el listado de cuentas)
  - Props: `pagina`, `totalPaginas`, `onCambiarPagina`
  - Números de página + "Anterior"/"Siguiente"; no se renderiza (o queda deshabilitado) si
    `totalPaginas <= 1`
- [x] `frontend/src/lib/banco-preguntas-api.ts`
  - `filtrarBanco()` acepta `pagina?`/`tamanioPagina?` opcionales en `FiltrosBanco` (o
    parámetro separado); respuesta tipada como `{ preguntas: PreguntaResponse[]; total: number }`
  - Actualizar los 4 call-sites que no paginan (`EditarPregunta.tsx`, `EliminarPregunta.tsx`,
    `NuevaPreguntaOpcionMultiple.tsx`, `NuevaPreguntaVerdaderoFalso.tsx`) para leer
    `.preguntas` de la respuesta en vez de la lista directa — sin pasar `pagina`/
    `tamanioPagina`, siguen recibiendo todo
- [x] `frontend/src/pages/Banco.tsx`
  - Estado `pagina` (reset a 1 al cambiar cualquier filtro)
  - Pasa `pagina`/`tamanioPagina=20` a `filtrarBanco()`
  - Renderiza `<Pagination>` debajo de la tabla con `total` de la respuesta

### 9. Ajuste de tests existentes

- [x] Tests backend de `filtrar_banco`/`bancos_controller`/`bancos_router` (unit +
  integración) — agregar casos de paginación, ajustar los que asuman `list[...]` plano
- [x] `EditarPregunta.test.tsx`, `EliminarPregunta.test.tsx`,
  `NuevaPreguntaOpcionMultiple.test.tsx`, `NuevaPreguntaVerdaderoFalso.test.tsx` — ajustar
  mocks de `fetch` a la nueva forma de respuesta `{ preguntas, total }`
- [x] `Banco.test.tsx` — agregar casos de paginación (más de una página, cambiar de página,
  filtro reinicia paginación, una sola página)

**Estado:** 9/9 secciones completadas
