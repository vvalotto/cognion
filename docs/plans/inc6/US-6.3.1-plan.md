# Plan de Implementación: US-6.3.1 - Nombres de los Estudiantes en la sala de espera y el ranking

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** Cognion — BC Actividad Evaluativa (con un puerto hacia Identidad)

## Decisión de diseño (Fase 2)

`ParticipanteResumen` (`participantes_sesion_query_port.py`) y `ParticipanteEnRanking`
(`proyecciones_en_vivo_port.py`) son read models **locales** de Actividad Evaluativa — sus
adapters (`SQLAlchemyParticipantesSesionQueryRepository`, `SQLAlchemyProyeccionesEnVivoQuery`)
consultan tablas propias del BC y no tienen forma de conocer `nombre` (vive en Identidad). Para
no romper esa frontera:

- Ambas dataclasses ganan `nombre: str = ""` (default — los adapters existentes quedan **sin
  cambios**, siguen construyendo las instancias sin ese campo).
- La resolución real ocurre en el **use case**, con un helper compartido nuevo
  (`resolver_nombres`) que llama a `EstudianteConsultaPort.obtener_nombres()` (una sola
  consulta por lote) y devuelve un `dict[UUID, str]` con `"Estudiante sin nombre"` para los ids
  sin cuenta resoluble. Cada use case arma la lista final con `dataclasses.replace(item,
  nombre=nombres[item.estudiante_id])` antes de devolverla o transmitirla.

Esto evita una dependencia nueva en `UnirseASesionEnVivoUseCase` (ya tiene `estudiante_consulta`
inyectado desde `US-6.1.3` — se reutiliza tal cual, sin sumar el 6° parámetro que preocupa la
spec) y mantiene los 4 use cases restantes en +1 dependencia cada uno (dentro del umbral de CBO
observado en incrementos anteriores).

## Componentes a Implementar

### 1. Puerto y adapter (Entities / Frameworks)

- [x] `src/actividad_evaluativa/entities/ports/estudiante_consulta_port.py`
  - Nuevo método abstracto `obtener_nombres(ids: list[UUID]) -> dict[UUID, str]`
- [x] `src/actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py`
  - Implementación: una sola `SELECT id, nombre FROM usuarios WHERE id IN (...)` (batch, no una
    consulta por Estudiante) contra `UsuarioModel` de Identidad — mismo criterio de
    acoplamiento consciente (`ADR-006`) que el resto del adapter
- [x] `src/actividad_evaluativa/use_cases/_resolucion_nombres.py` (módulo nuevo, compartido)
  - `NOMBRE_SIN_RESOLVER = "Estudiante sin nombre"`
  - `async def resolver_nombres(consulta: EstudianteConsultaPort, ids: Iterable[UUID]) -> dict[UUID, str]`
    — de-duplica `ids`, llama al puerto una vez, completa los faltantes con `NOMBRE_SIN_RESOLVER`

### 2. Read models (Entities)

- [x] `src/actividad_evaluativa/entities/ports/participantes_sesion_query_port.py`
  - `ParticipanteResumen` gana `nombre: str = ""`
- [x] `src/actividad_evaluativa/entities/ports/proyecciones_en_vivo_port.py`
  - `ParticipanteEnRanking` gana `nombre: str = ""`

### 3. Use Cases (resolución de nombres antes de responder/transmitir)

- [x] `src/actividad_evaluativa/use_cases/unirse_a_sesion_en_vivo.py`
  - `_mensaje_participantes` recibe `nombres: dict[UUID, str]` y arma `"nombre"` por participante
  - `execute()` resuelve `nombres` con el `estudiante_consulta` ya inyectado antes de publicar
- [x] `src/actividad_evaluativa/use_cases/listar_participantes.py`
  - Nueva dependencia `estudiante_consulta: EstudianteConsultaPort`
  - `execute()` enriquece la lista antes de devolverla
- [x] `src/actividad_evaluativa/use_cases/cerrar_pregunta_actual.py`
  - Nueva dependencia `estudiante_consulta: EstudianteConsultaPort`
  - `_mensaje_cierre` recibe el ranking ya enriquecido
- [x] `src/actividad_evaluativa/use_cases/finalizar_sesion_en_vivo.py`
  - Nueva dependencia `estudiante_consulta: EstudianteConsultaPort`
  - `_mensaje_final` recibe el ranking ya enriquecido
- [x] `src/actividad_evaluativa/use_cases/obtener_ranking.py`
  - Nueva dependencia `estudiante_consulta: EstudianteConsultaPort`
  - `execute()` enriquece la lista antes de devolverla

### 4. Interface Adapters / Frameworks (contrato HTTP)

- [x] `src/actividad_evaluativa/frameworks/api/schemas.py`
  - `ParticipanteResponse` y `RankingItemResponse` ganan `nombre: str`
- [x] `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`
  - Las 2 construcciones de response (`listar_participantes`, `obtener_ranking`) pasan `nombre=p.nombre`/`r.nombre`

### 5. Composition root

- [x] `src/actividad_evaluativa/frameworks/dependencies.py`
  - `get_conduccion_en_vivo_controller`: `CerrarPreguntaActualUseCase` y `FinalizarSesionEnVivoUseCase` reciben `EstudianteConsultaPortInProcess(session)`
  - `get_sesiones_en_vivo_query_controller`: `ListarParticipantesUseCase` y `ObtenerRankingUseCase` reciben `EstudianteConsultaPortInProcess(session)`
  - `get_sesiones_en_vivo_controller`: sin cambios (`UnirseASesionEnVivoUseCase` ya lo recibía)

### 6. Integración

- [x] `tests/unit/inc6/_fakes.py`, `tests/unit/inc3/_fakes.py`
  - `FakeEstudianteConsultaPort` (única definición, en `inc3/_fakes.py` — `inc6` la reutiliza) gana `obtener_nombres` **en el mismo commit** que el puerto
- [x] Re-medir el RNF: `tests/uat/inc6/medir_rendimiento_cierre.py` contra `CerrarPreguntaActualUseCase` con la resolución de nombres sumada — **CUMPLE**, p95 = 79.09 ms (umbral 100 ms), 60 participantes, 30 cierres — evidencia en `quality/reports/uat/inc6/rendimiento-cierre.json`

**Estado:** 13/13 tareas completadas ✅

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-22

## Métricas de Tiempo

- **Tiempo real (tracker):** ~48 min hasta el cierre de Fase 7 (Fases 0 a 7)
- Tracking corrido con `.venv/bin/python .claude/tracking/tracker_cli.py` — sin estimación humana previa en la spec (US técnica sin story points de referencia comparables directos).

## Lecciones aprendidas

- ✅ Reutilizar el `EstudianteConsultaPort` ya inyectado en `UnirseASesionEnVivoUseCase`
  (desde `US-6.1.3`) evitó sumar una 6ª dependencia a esa clase — el diseño de Fase 2
  (dar default `""` a `nombre` en los read models locales y resolver en el use case) se
  sostuvo sin cambios durante la implementación.
- ⚠️ `codeguard` sin activar el `.venv` en el `PATH` reporta `vulture`/`codespell` como "no
  instalados" y hace timeout en mypy/pylint — falso negativo de entorno, no del código.
  Activar `.venv/bin/activate` antes de correrlo evita el ruido.
- 💡 mypy encontró un error real de tipos (`dict()` sobre `Sequence[Row]` en vez de un dict
  comprehension) que ni pylint ni los tests habían detectado — confirma que el hook mypy
  dedicado sigue siendo necesario como fuente de verdad de tipos (nota ya documentada en
  `CLAUDE.md` sobre el bug de `codeguard`/mypy).
