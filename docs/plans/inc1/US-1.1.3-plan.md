# Plan de Implementación: US-1.1.3 - Estudiante intenta registrarse con link vencido o inválido

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** identidad
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-07-23

> **Nota de alcance:** esta US no crea componentes nuevos — refina el camino de rechazo de
> `RegistrarEstudianteUseCase` (`US-1.1.2`). Todos los archivos abajo ya existen; el trabajo es
> modificarlos.
>
> **Nota de nomenclatura:** la spec (`docs/specs/inc1/US-1.1.3.md`) referencia
> `src/identidad/entities/excepciones.py`, pero el archivo real de excepciones del BC es
> `src/identidad/entities/errors.py` (usado por `EmailYaRegistrado`, `UsuarioNoEsDocente`, etc.
> desde `US-1.1.0`). Se sigue la convención del código existente, no la ruta de la spec.

## Componentes a Implementar

### 1. Excepciones específicas (`entities`)
- [x] `src/identidad/entities/errors.py`
  - Reemplazar `InvitacionNoValida` (genérica) por tres excepciones específicas:
    `InvitacionInvalida` (token no corresponde a ninguna invitación),
    `InvitacionVencida` (`expira_en` ya pasado), `InvitacionYaUsada` (`usada_en` no null)
  - Mismo formato que las excepciones existentes: guardan el dato en conflicto (`token`) y arman
    un mensaje descriptivo
  - Se elimina `InvitacionNoValida` — no queda ningún otro consumidor tras este cambio (verificado:
    solo `invitacion.py`, `registrar_estudiante.py`, `registro_router.py` y sus tests la usan)

### 2. Invitación — distinguir el motivo del rechazo (`entities`)
- [x] `src/identidad/entities/invitacion.py`
  - Agregar `verificar_vigente(ahora: datetime) -> None`: lanza `InvitacionYaUsada` si
    `usada_en is not None`, o `InvitacionVencida` si `ahora >= expira_en`; no lanza nada si
    la invitación es vigente (INV-ID-01, INV-ID-03)
  - `aceptar(ahora)` delega en `verificar_vigente(ahora)` antes de marcar `usada_en`
  - `es_vigente(ahora) -> bool` se mantiene sin cambios (sigue usándose en los tests existentes)
  - Actualizar el import de `InvitacionNoValida` → `InvitacionVencida`, `InvitacionYaUsada`

### 3. Caso de uso — distinguir token inexistente (`use_cases`)
- [x] `src/identidad/use_cases/registrar_estudiante.py`
  - `_buscar_invitacion_vigente(token)`: si `obtener_por_token(token)` devuelve `None`, lanza
    `InvitacionInvalida(token)`; si existe, delega la validación de vigencia en
    `invitacion.verificar_vigente(ahora)` (reutiliza la lógica de la Entity, no la duplica)
  - Actualizar el docstring de `execute()` para listar las tres excepciones posibles
  - Actualizar imports

### 4. Mapeo HTTP — 422 para las tres excepciones (`frameworks`)
- [x] `src/identidad/frameworks/api/registro_router.py`
  - `except (InvitacionInvalida, InvitacionVencida, InvitacionYaUsada) as exc:` → mismo
    `HTTPException(422, detail=str(exc))` que hoy (la spec exige el mismo status/mensaje de
    cara al Estudiante para los tres casos; el backend distingue internamente solo para logging)
  - Actualizar imports y docstring del endpoint

### 5. Interface Adapters
- [x] `src/identidad/interface_adapters/controllers/registro_controller.py` — **sin cambios**,
  solo delega en el use case; verificado, no requiere modificación

## Integración

- [x] No hay cambios de DI (`frameworks/dependencies.py`) — mismos repos y hasher que `US-1.1.2`
- [x] No hay endpoint nuevo — mismo `POST /identidad/registro`
- [x] Impacto en tests existentes: `tests/unit/inc1/test_invitacion.py` y
  `tests/unit/inc1/test_registrar_estudiante_use_case.py` actualizados a las excepciones
  específicas; `tests/integration/inc1/test_registro_api_integration.py` con test nuevo de
  invitación ya usada; `tests/step_defs/inc1/test_us_1_1_3_steps.py` nuevo

## Frontend

- [x] Diferido — ver `docs/plans/inc1/US-1.1.3-context.md` §Decisión de alcance — frontend.
  No se crea `RegistroError.tsx` en esta US.

**Estado:** 4/4 tareas de código completadas (Componentes 1–4 + verificación de Componente 5).

## Métricas de Tiempo

| Fase | Real |
|------|------|
| Fase 0 — Validación de Contexto | 1 min 15s |
| Fase 1 — Escenarios BDD | 32s |
| Fase 2 — Plan de Implementación | 1 min 41s |
| Fase 3 — Implementación | 1 min 46s |
| Fase 4 — Tests Unitarios | 57s |
| Fase 5 — Tests de Integración | 30s |
| Fase 6 — Validación BDD | 2 min 36s |
| Fase 7 — Quality Gates | 1 min 13s |

> Nota (PRIN-001): tiempos reales de ejecución del agente, no comparables con estimación
> humana en puntos de historia.

## Resultado final

- 85/85 tests verdes (unit + integration + step_defs, excluyendo el escenario `@ux` diferido)
- Quality gates APROBADO: pylint 9.91/10, CC máx 3, MI mín 73.54, coverage 100%
- `InvitacionNoValida` eliminada; refinada en `InvitacionInvalida`, `InvitacionVencida`,
  `InvitacionYaUsada` — sin código obsoleto remanente en `src/`
