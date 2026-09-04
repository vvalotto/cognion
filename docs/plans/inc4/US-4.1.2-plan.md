# Plan de Implementación: US-4.1.2 - Estudiante consulta su propio desempeño en una materia

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** Analytics
**Estado:** ✅ COMPLETADO — quality gates APROBADO (`quality/reports/inc4/US-4.1.2-quality.json`)

## Métricas de Tiempo

| Fase | Duración real |
|------|---------------|
| 0 — Validación de Contexto | 48s |
| 1 — Escenarios BDD | 18min 22s |
| 2 — Plan de Implementación | 1min 47s |
| 3 — Implementación (5 tareas) | 2min 17s |
| 4 — Tests Unitarios | 1min 04s |
| 5 — Tests de Integración | 3min 31s |
| 6 — Validación BDD | 4min 08s |
| 7 — Quality Gates | 10min 13s |
| **Total (Fases 0-7)** | **~42 min** |

Nota: PRIN-001 — estos tiempos son de ejecución del agente, no comparables contra estimación
humana en story points.

## Componentes a Implementar

### 1. Use Case (`use_cases`)
- [x] `src/analytics/use_cases/obtener_desempeno_estudiante.py`
  - `EvaluacionDetalle` (dataclass): `evaluacion_id, actividad_id, finalizada_en, cantidad_correctas, cantidad_incorrectas`
  - `ResumenDesempeno` (dataclass): `total_correctas, total_incorrectas, porcentaje_acierto, cantidad_evaluaciones`
  - `DesempenoEstudiante` (dataclass): `evaluaciones: list[EvaluacionDetalle], resumen: ResumenDesempeno`
  - `ObtenerDesempenoEstudianteUseCase.execute(estudiante_id, materia_id) -> DesempenoEstudiante`
    - Llama `EvaluacionDesempenoConsultaPort.listar_evaluaciones_finalizadas(estudiante_id, materia_id)` una sola vez
    - Ordena el detalle por `finalizada_en` descendente
    - Suma correctas/incorrectas del conjunto completo, calcula `porcentaje_acierto` redondeado (`round`) sobre el total de respuestas — `0` si no hay evaluaciones, sin dividir por cero (INV de la spec)

### 2. Interface Adapters (`interface_adapters`)
- [x] `src/analytics/interface_adapters/controllers/analytics_controller.py`
  - `AnalyticsController.obtener_mi_desempeno(estudiante_id, materia_id) -> DesempenoEstudiante`
  - Delega directo en el Use Case, mismo patrón mínimo que `ActividadesEstudianteController`

### 3. Frameworks (`frameworks`)
- [x] `src/analytics/frameworks/api/schemas.py` (nuevo — primer schema del BC)
  - `EvaluacionDetalleResponse`, `ResumenDesempenoResponse`, `DesempenoEstudianteResponse` (Pydantic, mapean 1:1 los dataclasses del Use Case)
- [x] `src/analytics/frameworks/api/analytics_router.py` (extiende el router existente)
  - `GET /analytics/materias/{materia_id}/mi-desempeno`, `dependencies=[Depends(require_estudiante)]`
  - `estudiante_id` resuelto de `get_current_user` (JWT), nunca de la URL
- [x] `src/analytics/frameworks/dependencies.py` (extiende)
  - `require_estudiante = require_rol([TipoPerfil.ESTUDIANTE], get_current_user)` (mismo patrón que `actividad_evaluativa/frameworks/dependencies.py`)
  - `get_analytics_controller(session) -> AnalyticsController`, cablea `ObtenerDesempenoEstudianteUseCase(EvaluacionDesempenoConsultaPortInProcess(session))`

### 4. Integración
- [x] Verificar que `analytics_router` ya está registrado en `src/app.py` (confirmado: sí, línea 88) — sin cambios ahí; `from src.app import app` importa sin errores con el endpoint nuevo
- [x] Sin migración de base de datos — el Use Case solo lee vía el puerto existente de `US-4.1.1`

**Estado:** 5/5 tareas completadas
