# Plan de Implementación: US-2.1.4 - Docente carga una pregunta de Verdadero/Falso

**Patrón:** Clean Architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Banco de Preguntas
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-08

## Métricas de Tiempo

| Fase | Tiempo real |
|------|-------------|
| 0 — Validación de Contexto | 5 min 29 s |
| 1 — Generación de Escenarios BDD | 1 min 32 s |
| 2 — Generación del Plan de Implementación | 7 min 43 s |
| 3 — Implementación Guiada por Tareas | 17 min 57 s |
| 4 — Tests Unitarios | 2 min 59 s |
| 5 — Tests de Integración | 2 min 18 s |
| 6 — Validación BDD | 1 min 50 s |
| 7 — Quality Gates | 8 min 15 s |
| **Total (fases 0-7)** | **48 min 03 s** |

> Nota (PRIN-001, `.claude/skills/implement-us/skill.md`): tiempos de ejecución del agente,
> no comparables a estimaciones de esfuerzo humano.

Segundo tipo de pregunta, mismo patrón que `US-2.1.3` (opción múltiple), reutilizando el
`PreguntaRepositoryPort`, la tabla `pregunta_plantilla` (columna discriminadora `tipo`) y el
router/controller existentes — se extienden, no se duplican.

## Componentes a Implementar

### 1. Entities
- [x] `src/banco_preguntas/entities/pregunta_plantilla.py`
  - Agregar `PreguntaPlantillaVerdaderoFalso` (dataclass): `id`, `banco_id`, `texto`,
    `respuesta_correcta: bool`, metadatos, `activa`
  - `staticmethod crear(...)` — sin invariantes de negocio adicionales (spec: `respuesta_correcta`
    obligatorio, ya garantizado por tipado, no por validación de dominio)
- [x] `src/banco_preguntas/entities/ports/pregunta_repository_port.py`
  - Ampliar el tipo de `guardar()` a `PreguntaPlantillaOpcionMultiple | PreguntaPlantillaVerdaderoFalso`

### 2. Use Cases
- [x] `src/banco_preguntas/use_cases/cargar_pregunta_verdadero_falso.py`
  - `CargarPreguntaVerdaderoFalsoUseCase` — mismo flujo que `CargarPreguntaOpcionMultipleUseCase`:
    valida `Banco` existente (`BancoNoExiste`), crea y persiste, emite `PreguntaCargada`

### 3. Interface Adapters
- [x] `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py`
  - Agregar método `cargar_pregunta_verdadero_falso`, recibiendo el nuevo use case por
    constructor (junto al de opción múltiple)
- [x] `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`
  - Agregar constante `TIPO_VERDADERO_FALSO`
  - `guardar()` distingue por tipo (`isinstance`) para mapear al modelo SQLAlchemy

### 4. Frameworks
- [x] `src/banco_preguntas/frameworks/db/models.py`
  - Agregar columna `respuesta_correcta: Mapped[bool | None]` (nullable — `None` para preguntas
    de opción múltiple) a `PreguntaPlantillaModel`
- [x] Migración Alembic — `alter_table pregunta_plantilla add column respuesta_correcta`
  (`migrations/versions/6f523d16bf1c_pregunta_plantilla_respuesta_correcta.py`, aplicada)
- [x] `src/banco_preguntas/frameworks/api/schemas.py`
  - `CargarPreguntaVerdaderoFalsoRequest`, `PreguntaVerdaderoFalsoResponse`
- [x] `src/banco_preguntas/frameworks/api/preguntas_router.py`
  - `POST /preguntas/verdadero-falso` (rol `docente`, 201, 404 si banco no existe)
- [x] `src/banco_preguntas/frameworks/dependencies.py`
  - `get_preguntas_controller` instancia también `CargarPreguntaVerdaderoFalsoUseCase`

### 5. Integración
- [x] Ninguna integración nueva fuera del BC — reutiliza `require_docente`, `SessionDep`,
  `BancoRepositoryPort` ya cableados desde `US-2.1.3`

**Estado:** 9/9 tareas completadas
