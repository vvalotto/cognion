# Plan de Implementación: US-6.3.3 - Estado completo de la sesión para reconectar la proyección

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** Cognion — BC Actividad Evaluativa

## Decisión de diseño (Fase 2)

- **Sin puertos nuevos:** `ObtenerEstadoSesionUseCase` suma `ProyeccionesEnVivoQueryPort`
  (ya existente, `US-6.2.3`), `ParticipantesSesionQueryPort` (ya existente, `US-6.1.3`) y
  `EstudianteConsultaPort` (ya existente, resolución de nombres de `US-6.3.1`) como
  dependencias nuevas — de 2 a 5. `cantidad_respuestas` usa el método homónimo del puerto de
  proyecciones (ya existe, no hay que sumar la distribución a mano).
- **CBO mitigado con funciones de módulo**, mismo patrón que `_pregunta_actual`/
  `_avance_del_estudiante` ya en el archivo: `_resultado_pregunta(sesion, proyecciones,
  estudiante_consulta)` nueva, no un método de la clase — la clase solo guarda las 5
  referencias a puertos en `__init__`, la lógica vive afuera.
- **`resultado_pregunta` solo para el Docente:** se calcula únicamente cuando `estudiante_id
  is None` (que en este endpoint solo ocurre para el rol Docente, `require_estudiante_o_docente`
  + el router solo pasa `estudiante_id` si el rol es Estudiante) — el Estudiante nunca ve el
  ranking antes del resultado final (`§17` punto 10).
- **`total_participantes`/`cantidad_respuestas` para ambos roles**, sin condicional de rol.

## Componentes a Implementar

### 1. Use Cases

- [x] `src/actividad_evaluativa/use_cases/obtener_estado_sesion.py`
  - `ResultadoPregunta` (nueva dataclass): `distribucion: list[OpcionDistribuida]`,
    `ranking: list[ParticipanteEnRanking]`
  - `EstadoSesion` gana `total_participantes: int`, `cantidad_respuestas: int`,
    `resultado_pregunta: ResultadoPregunta | None`
  - `_resultado_pregunta()` (función de módulo nueva)
  - `ObtenerEstadoSesionUseCase.__init__` gana `proyecciones`, `participantes`,
    `estudiante_consulta`
  - `execute()` calcula los 3 campos nuevos antes de armar el `EstadoSesion`

### 2. Frameworks

- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `OpcionDistribuidaResponse` (nuevo: `opcion: str`, `cantidad: int`)
  - `ResultadoPreguntaResponse` (nuevo: `distribucion: list[OpcionDistribuidaResponse]`,
    `ranking: list[RankingItemResponse]` — reutiliza el schema ya existente, ya tiene `nombre`)
  - `EstadoSesionEnVivoResponse` gana `total_participantes: int`, `cantidad_respuestas: int`,
    `resultado_pregunta: ResultadoPreguntaResponse | None`
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - `_a_estado_response()` arma los 3 campos nuevos
- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `ObtenerEstadoSesionUseCase(...)` en `get_sesiones_en_vivo_query_controller` recibe
    `SQLAlchemyProyeccionesEnVivoQuery(session)`, `SQLAlchemyParticipantesSesionQueryRepository(session)`,
    `EstudianteConsultaPortInProcess(session)` (los tres ya importados en ese archivo para otros
    use cases — se reutilizan las mismas clases de adapter)

### 3. Integración

- [x] `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.3.3*.feature` + step defs

**Estado:** 5/5 tareas completadas ✅

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-22

## Métricas de Tiempo

- **Tiempo real (tracker):** ~17 min hasta el cierre de Fase 7 (Fases 0 a 7)

## Lecciones aprendidas

- ✅ La mitigación de CBO por diseño (funciones de módulo en vez de métodos, decidida en Fase 2
  a partir del precedente de `US-6.3.2`) funcionó: `ObtenerEstadoSesionUseCase` llegó a 5
  dependencias sin marcar CRITICAL en el pre-push — a diferencia de `US-6.3.2`, acá no hizo
  falta ninguna corrección posterior.
- ✅ Reutilizar `RankingItemResponse` (ya tenía `nombre` desde `US-6.3.1`) para el ranking
  dentro de `ResultadoPreguntaResponse` evitó duplicar un schema.
- ✅ `cantidad_respuestas` ya existía como método del puerto (`ProyeccionesEnVivoQueryPort`,
  desde `US-6.2.3`) — no hubo que sumarlo a mano desde la distribución.
- 💡 Docstrings de `__init__` con muchas dependencias nuevas superan fácil el límite de 100
  caracteres de `ruff` (D205/línea) — conviene fijarse el largo exacto antes de escribirlos,
  no ajustar por prueba y error después.
