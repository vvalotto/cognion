# Plan de Implementación: US-3.4.2 - Docente ve sus materias y el listado de actividades de una materia

**Patrón:** Clean Architecture BC-first (backend) + React 19/TypeScript (frontend)
**Producto:** actividad_evaluativa
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-30

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de contexto | 317s |
| 1 — Escenarios BDD | 73s |
| 2 — Plan de implementación | 116s |
| 3 — Implementación | 463s |
| 4 — Tests unitarios | 316s |
| 5 — Tests de integración | 228s |
| 6 — Validación BDD | 51s |
| 7 — Quality Gates | 220s |
| **Total (fases 0-7)** | **~30 min** |

> Sin comparación contra estimación humana (PRIN-001).

## Lecciones Aprendidas

- ✅ Verificar el dominio contra el prototipo HTML **antes** de tocar código (Fase 0/2) detectó
  dos gaps reales (`titulo` inexistente, conteo de finalizadas no cubierto por el puerto
  existente) que de otro modo hubiesen aparecido recién en UAT — mismo principio que
  `feedback_prototipo_html_autoridad`, aplicado esta vez a nivel de dominio, no solo de texto.
- ✅ Decidir `titulo` como campo **opcional** (no requerido) limitó el blast radius a 0 tests
  rotos de las Iteraciones 1-3 (25+ archivos que crean actividades sin ese campo) — verificado
  corriendo la suite completa (664/664) antes de dar por cerrada la Fase 3.
- ✅ Separar `ActividadesQueryController` de `ActividadesController` desde el diseño (Fase 2)
  evitó repetir el patrón de CRITICAL de CBO ya visto 5 veces en el proyecto
  (`US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.1.7`/`US-2.2.2`).
- ✅ Reutilizar `ActividadEvaluativaPeriodoAbierto.reconstruir()` dentro del gateway de
  consulta (en vez de duplicar la lógica de reconstrucción, como hizo
  `SQLAlchemyEvaluacionActivaQueryRepository` con su propio `_resumen_de_stream`) mantuvo el
  nuevo repositorio más simple — posible porque acá se necesitan todos los campos del
  aggregate, no un resumen liviano.

## Alcance y gaps resueltos (ver `US-3.4.2-context.md` para el detalle)

1. `titulo: str = ""` opcional agregado a `ActividadEvaluativaPeriodoAbierto` — no rompe
   fixtures de `US-3.1.2` a `US-3.3.2`.
2. `ActividadQueryPort` (nuevo) calcula conteo de evaluaciones activas **y** finalizadas por
   actividad con su propia consulta sobre `events`, sin ensanchar `EvaluacionActivaQueryPort`.
3. `#doc-materias` simplificado: solo nombre de materia (sin comisión ni conteo).

## Componentes a Implementar

### Backend

#### 1. Dominio — campo `titulo`
- [x] `entities/actividad_evaluativa_periodo_abierto.py`: agregar `titulo: str = field(default="")`
  al dataclass; `crear(..., titulo: str = "")`; `reconstruir()` lee `payload.get("titulo", "")`
- [x] `entities/eventos.py`: `ActividadEvaluativaCreada.titulo: str = ""`
- [x] `use_cases/crear_actividad_periodo_abierto.py`: `execute(..., titulo: str = "")`, incluir
  `titulo` en el payload persistido
- [x] `frameworks/api/schemas.py`: `CrearActividadRequest.titulo: str = ""`,
  `ActividadResponse.titulo: str`
- [x] `interface_adapters/controllers/actividades_controller.py`: `crear_actividad(..., titulo)`
- [x] `frameworks/api/actividades_router.py`: pasar `body.titulo`, incluir en `_a_response`

#### 2. Query de listado — nuevo puerto y Use Case
- [x] `entities/ports/actividad_query_port.py` (nuevo)
  - `ActividadResumen` (frozen dataclass): `id`, `materia_id`, `titulo`, `fecha_apertura`,
    `fecha_cierre`, `cantidad_preguntas`, `cantidad_intentos_permitidos`, `cerrada_manualmente`,
    `cantidad_evaluaciones_activas`, `cantidad_evaluaciones_finalizadas`
  - `ActividadQueryPort(ABC)` — `listar_por_materia(materia_id) -> list[ActividadResumen]`
- [x] `use_cases/listar_actividades.py` (nuevo) — `ListarActividadesUseCase`, delega en el
  puerto sin lógica propia (mismo nivel de indirección que `FiltrarBancoUseCase`)

#### 3. Gateway — SQLAlchemy
- [x] `frameworks/adapters/actividad_query_repository.py` (nuevo) —
  `SQLAlchemyActividadQueryRepository`:
  - Reconstruye cada `ActividadEvaluativaPeriodoAbierto` agrupando su stream en memoria
    (reutiliza `ActividadEvaluativaPeriodoAbierto.reconstruir()` — no duplica esa lógica),
    filtra por `materia_id`
  - Cuenta evaluaciones activas/finalizadas agrupando el stream de `Evaluacion` por
    `actividad_id` (mismo patrón "agrupar en memoria" de
    `SQLAlchemyEvaluacionActivaQueryRepository`, `US-3.2.4`, sin tocar ese archivo)

#### 4. Controller y endpoint — separados de `ActividadesController` (command)
- [x] `interface_adapters/controllers/actividades_query_controller.py` (nuevo) —
  `ActividadesQueryController.listar_actividades(materia_id)`. Separado de
  `ActividadesController` a propósito: ese ya tiene 3 use cases inyectados — agregar un 4°
  arriesga el mismo CRITICAL de CBO que `US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.1.7`/`US-2.2.2`
  (mismo criterio de separación command/query ya aplicado en `BancosController`)
- [x] `frameworks/api/actividades_router.py`: nuevo `GET ""` con query param `materia_id`
  (`UUID`, requerido), rol `docente`, response `list[ActividadResumenResponse]`
- [x] `frameworks/api/schemas.py`: `ActividadResumenResponse` (incluye `estado: str`, calculado
  en el router — no persiste, INV de la spec)
- [x] `frameworks/dependencies.py`: `get_actividades_query_controller(session)`

#### 5. Estado derivado (función pura, sin persistir)
- [x] Función `_estado_actividad(resumen, ahora) -> Literal["en_curso","programada","cerrada"]`
  en `actividades_router.py` (mismo nivel que `_a_response`) — `cerrada` si
  `cerrada_manualmente` o `fecha_cierre <= ahora`; `programada` si `fecha_apertura > ahora`;
  si no, `en_curso`

### Frontend

#### 6. Cliente API
- [x] `actividad-evaluativa-api.ts`: agregar `titulo` a `ActividadResponse`/`CrearActividadBody`
  (camelCase, mapeo snake_case↔camelCase igual que el resto del archivo); nueva función
  `listarActividades(materiaId)` → `GET /actividades?materia_id={id}`, tipos
  `ActividadResumenResponse`/`EstadoActividad`

#### 7. Badge — nuevas variantes
- [x] `components/ui/badge.tsx`: agregar `estado-en-curso` (verde, reutiliza colores de
  `estado-activa`), `estado-programada` (ámbar), `estado-cerrada` (rojo, reutiliza colores de
  `estado-bloqueada`) — mismos tokens de color que el resto del sistema, sin inventar paleta

#### 8. Pantallas
- [x] `pages/MateriasActividades.tsx` (nueva, `#doc-materias`) — reutiliza `listarMaterias()`
  (`banco-preguntas-api.ts`, `US-2.1.9`) sin cambios; tarjeta por materia (solo nombre), navega
  a `/actividad-evaluativa/materias/:materiaId/actividades`
- [x] `pages/Actividades.tsx` (nueva, `#doc-actividades`) — `listarActividades(materiaId)` +
  `listarMaterias()` (para resolver nombre de materia del breadcrumb, mismo patrón que
  `Banco.tsx`); tarjeta por actividad (`titulo` con fallback `"Actividad del {fecha apertura
  formateada}"` si viene vacío, ventana de fechas, `Badge` de estado, conteo de evaluaciones
  según el estado); botón "+ Nueva actividad" → `/actividad-evaluativa/materias/:materiaId/actividades/nueva`
  (todavía placeholder, la reemplaza `US-3.4.3`); grilla vacía con la acción visible si no hay
  actividades

#### 9. Routing
- [x] `router.tsx`: reemplazar `ActividadEvaluativaPlaceholder` por `MateriasActividades` en
  `/actividad-evaluativa/materias` y por `Actividades` en
  `/actividad-evaluativa/materias/:materiaId/actividades` (rutas ya creadas en `US-3.4.1`,
  `RequireRole rol="docente"` sin cambios)

**Estado:** 9/9 tareas completadas
