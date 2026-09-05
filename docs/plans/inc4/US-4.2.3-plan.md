# Plan de Implementación: US-4.2.3 - PreguntaMetadatoConsultaPort hacia Banco de Preguntas

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Analytics (consumidor), Banco de Preguntas (dato existente)

## Componentes a Implementar

### 1. Port de consulta (entities)
- [ ] `src/analytics/entities/ports/pregunta_metadato_consulta_port.py`
  - `MetadatoPreguntaResumen`: `@dataclass(frozen=True)` con `unidad_tematica: str`, `tema: str` — copia propia de Analytics, no reexporta `MetadatosPregunta` de Banco de Preguntas (mismo criterio que `ComisionResumen`/`EstudianteResumen`, `US-4.2.2`)
  - `PreguntaMetadatoConsultaPort(ABC)`: único método `async def obtener_metadatos(self, pregunta_ids: list[UUID]) -> dict[UUID, MetadatoPreguntaResumen]`

### 2. Adapter in-process (frameworks)
- [ ] `src/analytics/frameworks/adapters/pregunta_metadato_consulta_port_in_process.py`
  - `PreguntaMetadatoConsultaPortInProcess(PreguntaMetadatoConsultaPort)`
  - Recibe `AsyncSession` compartida (mismo patrón que `ComisionConsultaPortInProcess`/`EvaluacionDesempenoConsultaPortInProcess`)
  - `obtener_metadatos`: lote vacío → `{}` sin consultar la base; si no, una sola query `select(PreguntaPlantillaModel).where(PreguntaPlantillaModel.id.in_(pregunta_ids))` (sin filtrar por `activa` — INV-BP no aplica al metadato) y arma el `dict` mapeando cada fila encontrada; ids sin fila correspondiente simplemente no aparecen
  - Único punto de Analytics que importa `src.banco_preguntas.frameworks.db.models.PreguntaPlantillaModel` — mismo criterio de acoplamiento consciente (`ADR-006`) que los adapters de `US-4.1.1`/`US-4.2.2`

### 3. Integración (composition root)
- [x] `src/analytics/frameworks/dependencies.py`
  - Agregar `get_pregunta_metadato_consulta_port(session: SessionDep) -> PreguntaMetadatoConsultaPort`, cableado contra `PreguntaMetadatoConsultaPortInProcess`
  - Sin consumidor todavía — lo cablea `US-4.2.4` (mismo criterio que `get_comision_consulta_port`, dejado documentado en su propio docstring)

**Estado:** 3/3 tareas completadas

## Tests

- Unitarios: `tests/unit/inc4/test_pregunta_metadato_consulta_port.py` (3 tests — DTO inmutable, ABC no instanciable)
- Integración: `tests/integration/inc4/test_pregunta_metadato_consulta_port_in_process.py` (4 tests contra PostgreSQL real)
- BDD: `tests/step_defs/inc4/test_us_4_2_3_steps.py` (4 escenarios de `US-4.2.3-pregunta-metadato-query-port.feature`)
- Suite completa: 821/821 tests (unit + integration + step_defs) — sin regresiones.

## Estado

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-05

## Quality Gates

- pylint 9.60/10, CC máx 3, MI mín 60.90, coverage 100% (`entities/ports/`, `frameworks/*` excluido del gate por `pyproject.toml`)
- codeguard: 9/9 checks corridos en modo `full`, 0 issues reales (ver observaciones en `quality/reports/inc4/US-4.2.3-quality.json`)
- Estado: **APROBADO**

## Lecciones Aprendidas

- ⚠️ Los tests de integración/BDD que insertan filas en `pregunta_plantilla`/`banco`/`materia` necesitan limpieza local propia (autouse fixture) — `tests/integration/inc4/conftest.py` solo limpia la tabla `events`, no las tablas de Banco de Preguntas. Sin esa limpieza, filas huérfanas rompen tests de otros BCs (violación de FK al correr la suite completa) — mismo patrón ya usado por `tests/step_defs/inc4/test_us_4_2_2_steps.py`, ahora replicado también en el test de integración.
- 💡 Correr la suite completa (no solo los tests nuevos) antes de cerrar Fase 7 fue lo que detectó la contaminación cruzada — los tests de la propia US pasaban aislados sin problema.
