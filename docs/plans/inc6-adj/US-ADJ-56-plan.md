# Plan de Implementación: US-ADJ-56 - El desempeño del Estudiante incluye las sesiones en vivo

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Analytics, lee BC Actividad Evaluativa por puerto in-process — `ADR-006`)
**Estado:** ✅ Completado (Fases 0-8) — 2026-09-27

## Métricas de tiempo (tracker_cli)

| Fase | Minutos |
|------|---------|
| 0 — Validación de contexto | 2 |
| 1 — Escenarios BDD | 1 |
| 2 — Plan de implementación | 7 |
| 3 — Implementación (9 tareas) | 10 |
| 4 — Tests unitarios | 139 (incluye tiempo de espera de dos corridas completas de Vitest en background) |
| 5 — Tests de integración | 18 |
| 6 — Validación BDD | 12 |
| 7 — Quality gates | 7 |
| **Total efectivo** | **~197 min** |

## Lecciones aprendidas

- ✅ El diseño de dos capas de lectura (event store crudo para correctas/incorrectas/puntaje +
  `ranking_por_sesion` para posición) evitó reimplementar el desempate del ranking.
- ⚠️ Nunca correr dos suites de integración/BDD en paralelo contra la misma base de test: los
  `conftest.py` autouse (`DELETE FROM events`) de archivos no relacionados se pisan entre
  procesos y generan decenas de fallos que parecen regresiones y no lo son.
- 💡 Resolver el nombre de la comisión (`horario`) en el Use Case con el `ComisionConsultaPort`
  ya existente evitó que el Estudiante necesitara un permiso HTTP que no tiene
  (`GET /materias/{id}/comisiones` es solo Docente/Administrador).

## Diseño acordado (resumen de la exploración de código)

- El modo en vivo guarda todo lo necesario en dos streams del event store de Actividad
  Evaluativa: `ActividadEvaluativaEnVivo` (estado, `comision_id`, `materia_id`, cantidad de
  preguntas, fecha de `SesionEnVivoFinalizada`) y `ParticipacionEnVivo` (`respuestas` con
  `es_correcta`/`puntaje`, uno por par sesión-estudiante, id determinístico). La posición final
  y el total de participantes se leen de la tabla `ranking_por_sesion` (mismo orden que
  `ProyeccionesEnVivoQueryPort.ranking()`: puntaje desc, `ultima_actualizacion` asc,
  `estudiante_id` asc) — evita reimplementar el desempate.
- El nombre de la comisión (horario) se resuelve en el **Use Case**, no en el adapter nuevo, con
  el `ComisionConsultaPort` de Analytics que ya existe (`US-4.2.2`) — evita que el Estudiante
  necesite un permiso que hoy no tiene (`GET /materias/{id}/comisiones` exige
  `docente_o_administrador`) y evita mezclar Identidad dentro del adapter que lee Actividad
  Evaluativa (responsabilidad única, mismo criterio que `EvaluacionDesempenoConsultaPortInProcess`).
- **Sin endpoint nuevo:** `ObtenerDesempenoEstudianteUseCase` ya alimenta los dos únicos
  endpoints que necesita esta US (`mi-desempeno` del Estudiante y el equivalente del Docente,
  `US-4.2.1`) — ampliar su resultado alcanza. `DesempenoPorComisionDetalleEstudiante.tsx`
  (`US-ADJ-48`, RF-20) consume el mismo endpoint pero **no** pasa el nuevo prop al componente
  compartido — decisión de Víctor: RF-20 no incluye el vivo. Sin cambios en ese archivo.
- `DesempenoResumenDetalle.tsx` gana la sección "Sesiones en vivo" con dos props **opcionales**
  (`filasEnVivo`, `mensajeVacioEnVivo`) — sin ellos no se renderiza nada, así el tercer
  consumidor (`DesempenoPorComisionDetalleEstudiante.tsx`) queda intacto.

## Componentes a Implementar

### 1. Puerto nuevo de Analytics (`entities/ports/`)
- [x] `src/analytics/entities/ports/sesion_en_vivo_desempeno_consulta_port.py`
  - `SesionEnVivoDesempenoResumen` (DTO frozen): `sesion_id`, `comision_id`, `materia_id`,
    `finalizada_en`, `cantidad_preguntas`, `cantidad_correctas`, `cantidad_incorrectas`,
    `puntaje_final`, `posicion`, `total_participantes`
  - `SesionEnVivoDesempenoConsultaPort(ABC)` con `listar_sesiones_finalizadas(estudiante_id,
    materia_id: UUID | None) -> list[SesionEnVivoDesempenoResumen]` — solo sesiones
    `Finalizada`

### 2. Adapter in-process (`frameworks/adapters/`)
- [x] `src/analytics/frameworks/adapters/sesion_en_vivo_desempeno_consulta_port_in_process.py`
  - `SesionEnVivoDesempenoConsultaPortInProcess(SesionEnVivoDesempenoConsultaPort)`
  - Agrupa `EventoModel` de `aggregate_type="ParticipacionEnVivo"`, filtra por
    `estudiante_id` del primer evento (`EstudianteUnido`)
  - Carga los streams de `ActividadEvaluativaEnVivo` de los `sesion_id` resultantes,
    reconstruye con `ActividadEvaluativaEnVivo.reconstruir()`, descarta las que no están
    `Finalizada` y (si corresponde) no matchean `materia_id`
  - Reconstruye cada `ParticipacionEnVivo` con `.reconstruir()` para `puntaje_acumulado` y
    contar correctas/incorrectas
  - Lee `RankingPorSesionModel` filtrado por los `sesion_id` en juego, mismo `order_by` que
    `proyecciones_en_vivo_repository.ranking()`, para derivar `posicion`/`total_participantes`
  - Funciones de módulo (no métodos) para cada paso — mismo criterio de WMC que
    `EvaluacionDesempenoConsultaPortInProcess`

### 3. Use Case ampliado (`use_cases/`)
- [x] `src/analytics/use_cases/obtener_desempeno_estudiante.py`
  - Nuevo dataclass `SesionEnVivoDetalle` (frozen): `sesion_id`, `comision_horario`,
    `finalizada_en`, `cantidad_preguntas`, `cantidad_correctas`, `cantidad_incorrectas`,
    `puntaje_final`, `posicion`, `total_participantes`
  - `DesempenoEstudiante` gana el campo `sesiones_en_vivo: list[SesionEnVivoDetalle]` —
    `resumen` **no cambia** (decisión de Víctor: período abierto y vivo separados)
  - `ObtenerDesempenoEstudianteUseCase.__init__` recibe dos dependencias más:
    `sesion_en_vivo_desempeno_consulta: SesionEnVivoDesempenoConsultaPort` y
    `comision_consulta: ComisionConsultaPort`
  - `execute()`: arma `horario_por_comision` con
    `comision_consulta.listar_comisiones_por_materia(materia_id)`, ordena las sesiones en vivo
    por `finalizada_en` descendente (mismo criterio que las evaluaciones de período abierto)

### 4. Composition root (`frameworks/dependencies.py`)
- [x] `get_analytics_controller`: instancia `SesionEnVivoDesempenoConsultaPortInProcess(session)`
  y `ComisionConsultaPortInProcess(session)` (ya usado en otro controller, se repite la
  instancia — mismo patrón que el resto del archivo) y los pasa a
  `ObtenerDesempenoEstudianteUseCase`

### 5. Schemas de la API (`frameworks/api/schemas.py`)
- [x] `SesionEnVivoDetalleResponse(BaseModel)` con los mismos 9 campos del Use Case
- [x] `DesempenoEstudianteResponse` gana `sesiones_en_vivo: list[SesionEnVivoDetalleResponse]`

### 6. Router (`frameworks/api/analytics_router.py`)
- [x] `_a_response()` mapea también `desempeno.sesiones_en_vivo` — los dos endpoints existentes
  (`mi-desempeno`, `estudiantes/{id}/desempeno`) quedan cubiertos sin tocar las rutas

### 7. Frontend — cliente API (`frontend/src/lib/analytics-api.ts`)
- [x] `SesionEnVivoDesempenoResponse` (camelCase) + `SesionEnVivoDesempenoApiResponse`
  (snake_case) con los mismos 9 campos
- [x] `DesempenoEstudianteResponse` gana `sesionesEnVivo: SesionEnVivoDesempenoResponse[]`
- [x] `mapearDesempenoEstudiante` mapea el campo nuevo

### 8. Frontend — componente compartido (`frontend/src/pages/analytics/DesempenoResumenDetalle.tsx`)
- [x] `FilaSesionEnVivo` (interface) + `armarFilasEnVivo(desempeno)` (ordena desc por
  `finalizadaEn`, mismo criterio que `armarFilas`)
- [x] `DesempenoResumenDetalleProps` gana `filasEnVivo?: FilaSesionEnVivo[]` y
  `mensajeVacioEnVivo?: string` — **opcionales**
- [x] Sección "Sesiones en vivo" (título propio, sin paginación, sin `onClick`): comisión,
  fecha, cantidad de preguntas, correctas ✓, incorrectas ✗, puntaje final, posición
  ("`{posicion}° de {totalParticipantes}`") — se renderiza solo si `filasEnVivo` fue provisto

### 9. Frontend — pantallas consumidoras
- [x] `frontend/src/pages/analytics/MiDesempeno.tsx`: pasa `filasEnVivo`/`mensajeVacioEnVivo`
  ("Todavía no participaste en sesiones en vivo de esta materia.")
- [x] `frontend/src/pages/analytics/DesempenoPorAlumno.tsx`: idem, con el mensaje del Docente
  ("Este estudiante todavía no participó en sesiones en vivo de esta materia.")
- [x] `DesempenoPorComisionDetalleEstudiante.tsx`: **sin cambios** (decisión de alcance,
  verificado — el archivo no se tocó)

## Integración
- [x] Ninguna migración ni evento nuevo — solo lectura sobre datos ya persistidos
- [ ] `docs/traceability/matrix.md` y `BC-analytics-modelo.md` se actualizan en Fase 8
  (Documentación), no en Fase 3

**Estado:** 9/9 tareas de código completadas (la actualización documental de Fase 8 queda para
esa fase, no es parte de "Componentes a Implementar").

## Fase 4 — Tests unitarios

- [x] `tests/unit/inc4/test_sesion_en_vivo_desempeno_consulta_port.py` (DTO + ABC)
- [x] `tests/unit/inc4/test_sesion_en_vivo_desempeno_consulta_port_in_process.py` (funciones puras
  del adapter: `_streams_de_estudiante`, `_resumen_de_participacion`, `_resumenes`)
- [x] `tests/unit/inc4/test_obtener_desempeno_estudiante.py` ampliado con Fakes de los 2 puertos
  nuevos + clase `TestSesionesEnVivo` (6 tests)
- [x] `tests/unit/inc4/test_analytics_controller.py` — Fakes agregados para que el use case
  siga instanciando
- [x] Backend: 814/814 tests unitarios en verde (`pytest tests/unit/ -q`), 100% cobertura en
  `entities/ports/` y `use_cases/` de Analytics
- [x] Frontend: `MiDesempeno.test.tsx`/`DesempenoPorAlumno.test.tsx`/
  `DesempenoPorComisionDetalleEstudiante.test.tsx` — helper `desempeno()` ampliado con
  `sesiones_en_vivo: []`
- [x] `DesempenoResumenDetalle.test.tsx` ampliado con la sección "Sesiones en vivo" (7 tests
  nuevos) + tests de `armarFilasEnVivo`
- [x] `tsc -b` 0 errores; 27/27 tests de los 4 archivos de analytics en verde
- [x] `analytics-api.test.ts` ampliado con `sesiones_en_vivo` en los fixtures y una nueva
  aserción de mapeo completo (13/13 tests en verde)
- [x] Suite completa backend (814/814) y frontend re-verificadas tras el fix

## Fase 5 — Tests de integración

- [x] `tests/integration/inc4/conftest.py` ampliado: limpia también `ranking_por_sesion`
- [x] `tests/integration/inc4/test_sesion_en_vivo_desempeno_consulta_port.py` (8 tests, Postgres
  real vía `SQLAlchemyEventStore` + `SQLAlchemyProyeccionesEnVivo`)
- [x] `tests/integration/inc4/test_analytics_router.py` ampliado: `TestAnalyticsRouterSesionesEnVivo`
  (2 tests end-to-end reales: router → controller → use case → los 2 adapters → Postgres)
- [x] 12/12 tests de `test_analytics_router.py` en verde, sin regresiones en los pre-existentes
- [x] Suite completa de integración: 555/555 en verde en una corrida limpia y secuencial
  (las dos corridas anteriores mostraron ~111 fallos por interferencia entre dos procesos
  pytest concurrentes contra la misma base de test — error propio de la sesión, no una
  regresión: los fallos tocaban archivos ajenos como `ranking_preguntas_falladas`/`tasa_error`)

## Fase 6 — Validación BDD

- [x] `tests/step_defs/inc4/test_us_adj_56_steps.py` — steps para los 9 escenarios del
  `.feature` de Fase 1, resueltos contra el endpoint HTTP real (mismo criterio que
  `test_us_4_1_2_steps.py`); el texto literal del estado vacío lo verifica el frontend (Vitest)
- [x] 9/9 escenarios en verde tras corregir 2 steps que solo sembraban `ranking_por_sesion`
  sin el evento `RespuestaEnVivoRegistrada` real (el `puntaje_final` sale del stream de
  eventos, no de la tabla de ranking — la tabla solo resuelve posición/total)
- [x] Suite completa `tests/step_defs/`: 375/376 en verde — el único fallo
  (`test_rechazo_fuera_del_período_vigente`, inc3) es el flake preexistente ya documentado en
  `CLAUDE.md` (ventana de tiempo ajustada, no relacionado con esta US)

## Fase 7 — Quality Gates

- [x] `codeguard --analysis-type full` sobre los 6 archivos nuevos/modificados de `src/`:
  9/9 checks con resultados (`quality/reports/inc6-adj/US-ADJ-56-codeguard.json`) — 15
  "errors" son fallas de herramientas ausentes/timeout (`vulture`/`codespell` no instalados,
  mypy/pylint embebidos exceden su timeout interno), documentadas en observaciones
- [x] Pylint corrido directo sobre los 6 archivos: **9.74/10** (≥ 8.0) — el 7.54 que reportó
  CodeGuard para `schemas.py` es un falso valor de su pylint embebido por archivo aislado
- [x] Radon CC: máximo **8** (`_sesiones_finalizadas`), promedio 1.98 (≤ 10)
- [x] Radon MI: mínimo 57.88 (`sesion_en_vivo_desempeno_consulta_port_in_process.py`) (> 20)
- [x] Coverage backend (`src/analytics`, excluye `frameworks/` por `pyproject.toml`): **100%**
- [x] Frontend: oxlint 0 errores, `tsc -b` 0 errores, cobertura de
  `DesempenoResumenDetalle.tsx`/`MiDesempeno.tsx` al 100% statements/lines
- [x] `quality/reports/inc6-adj/US-ADJ-56-quality.json` generado, estado `APROBADO`
- [x] De paso, corregido el renombre pendiente de `SP-ADJ-02`→`Incremento 6-ADJ` en
  `tests/step_defs/` y `quality/reports/` (se había omitido en el PR #451 original)
