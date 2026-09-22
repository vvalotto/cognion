# Contexto de Ejecución — US-6.3.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc6/US-6.3.1.md`
- **Fuente Arquitectura:** Documento local — `CLAUDE.md` (§"Arquitectura interna") + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-6.3.1
- **Título:** Nombres de los Estudiantes en la sala de espera y el ranking
- **Tipo:** Mejora de comportamiento existente (cambio aditivo de contrato — amplía un puerto y 5 use cases ya cerrados para que HTTP/WebSocket transporten `nombre` además de `estudiante_id`)
- **Puntos:** 3
- **Prioridad:** Alta — bloquea a `US-6.3.3` y a todo el frontend (`US-6.3.5` a `US-6.3.9`)

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya trae escenarios Gherkin completos (7 escenarios) y el criterio de éxito es observable end-to-end (HTTP + WebSocket)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (histórico del proyecto: ≥ 9.0 en Incremento 6)
  - CC ≤ 10 (histórico del proyecto: ≤ 8)
  - MI ≥ 20 (histórico del proyecto: ≥ 40)
  - cobertura ≥ 95%
  - CBO ≤ 10 / WMC ≤ 25 (`pyproject.toml [tool.designreviewer]`, pre-push, bloqueante)

## Rutas de Artefactos
- Contexto: `docs/plans/inc6/US-6.3.1-context.md`
- BDD feature: `tests/features/inc6/US-6.3.1-nombres-estudiantes-sesion-en-vivo.feature`
- Plan: `docs/plans/inc6/US-6.3.1-plan.md`
- Reporte: `docs/reports/inc6/US-6.3.1-report.md`
- Quality report: `quality/reports/inc6/US-6.3.1-quality.json`

## Notas propias de esta US (no genéricas del template)
- **RNF a re-medir:** `CerrarPreguntaActual` debe seguir con p95 ≤ 100 ms tras sumar la resolución de nombres (`tests/uat/inc6/medir_rendimiento_cierre.py`, ya usado en `US-6.2.9`).
- **CBO a vigilar:** `UnirseASesionEnVivoUseCase` ya tiene 5 dependencias — la spec pide resolver por función de módulo o decorador del canal, no sumar una dependencia más a la clase.
- **Fakes:** actualizar `tests/unit/inc6/_fakes.py` y `tests/unit/inc3/_fakes.py` en el mismo commit que el puerto (regla de memoria del proyecto — evita que queden desactualizados sin correr pytest local).
