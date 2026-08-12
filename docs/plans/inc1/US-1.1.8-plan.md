# Plan de Implementación: US-1.1.8 - Estudiante se registra desde la UI con link de invitación

**Patrón:** React 19 + TypeScript (frontend) + Clean Architecture (backend, ampliación mínima)
**Producto:** cognion
**Estado:** ✅ COMPLETADO

## Métricas de Tiempo (tracking real, `tracker_cli.py`)

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Validación de contexto | 23s |
| Fase 1 — BDD | 99s |
| Fase 2 — Plan | 224s |
| Fase 3 — Implementación (9 tareas) | 439s |
| Fase 4 — Tests unitarios | 332s |
| Fase 5 — Tests de integración | 89s |
| Fase 6 — Validación BDD | 30s |
| Fase 7 — Quality gates | 223s |

> No se compara contra estimaciones humanas (`PRIN-001`) — el tracking registra tiempo real
> de ejecución del agente, no varianza contra esfuerzo humano estimado.

## Lecciones Aprendidas

- ⚠️ El wireframe pedía mostrar el nombre de la comisión (materia), pero `RegistroResponse`
  solo exponía `comision_id` (UUID) — gap detectado en Fase 2, antes de escribir código.
  Consultado con Víctor antes de planificar: se amplió el backend (reutilizando
  `ComisionRepositoryPort.obtener_por_id`, puerto ya existente) en vez de degradar la UI.
  Documentado como adenda en la spec (`docs/specs/inc1/US-1.1.8.md`).
- 💡 Detectar gaps spec-vs-wireframe en Fase 2 (planificación) en vez de en Fase 3
  (implementación) evitó tener que rehacer trabajo — el plan ya reflejaba la decisión antes
  de escribir la primera línea de código.
- ✅ Cambiar la firma de `RegistrarEstudianteUseCase` rompió dos tests unitarios preexistentes
  (`US-1.1.2`) — se repararon en la misma Fase 4 en vez de dejarlos para después, evitando
  arrastrar suite roja entre US.

## Decisión de scope (ver adenda en `docs/specs/inc1/US-1.1.8.md`)

El wireframe (§2.5) pide mostrar el **nombre de la comisión** en la pantalla de éxito.
`RegistroResponse` solo devuelve `comision_id` (UUID) — se agrega `materia: str`, resuelta con
un lookup a `ComisionRepositoryPort.obtener_por_id` (puerto ya existente, sin decisión
arquitectónica nueva). El tag de comisión *antes* de enviar el formulario (§2.3) no es viable
sin un endpoint de preview de invitación — queda fuera de esta US, documentado en la spec.

## Componentes a Implementar

### 1. Backend — `materia` en `RegistroResponse`

- [x] `src/identidad/frameworks/api/schemas.py`
  - `RegistroResponse`: agregar campo `materia: str`
- [x] `src/identidad/use_cases/registrar_estudiante.py`
  - `RegistrarEstudianteUseCase.__init__`: agregar parámetro `comision_repositorio: ComisionRepositoryPort`
  - `execute`: después de crear el usuario, `comision = await self._comision_repositorio.obtener_por_id(invitacion.comision_id)` — la comisión existe siempre en este punto (invariante ya garantizado por la generación de la invitación, `US-1.1.1`), devolver `comision.materia` junto con `usuario` en la tupla de retorno (`tuple[Usuario, str, InvitacionAceptada, UsuarioRegistrado]`)
- [x] `src/identidad/interface_adapters/controllers/registro_controller.py`
  - `registrar_estudiante`: propagar el nuevo valor de retorno (`materia`) sin lógica adicional
- [x] `src/identidad/frameworks/api/registro_router.py`
  - Mapear `materia` recibido del controller a `RegistroResponse.materia`
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_registro_controller`: instanciar `SQLAlchemyComisionRepository(session)` e inyectarlo en `RegistrarEstudianteUseCase`

> **Nota:** `tests/unit/inc1/test_registrar_estudiante_use_case.py` y
> `tests/unit/inc1/test_registro_controller.py` (de `US-1.1.2`) quedan rotos por el cambio de
> firma — se actualizan en Fase 4 junto con los tests nuevos de esta US.

### 2. Frontend — Pantallas de registro

- [x] `frontend/src/pages/Registro.tsx`
  - Lee `token` de query param (`useSearchParams` de `react-router`)
  - Formulario: nombre, email, contraseña, confirmar contraseña (validación de cliente:
    coincidencia y mínimo 8 caracteres, INV-ID-11 — la regla de negocio la aplica el backend)
  - `POST /identidad/registro` vía `apiFetch` con `{ token, nombre, email, password }`
  - 201 → navega a `/registro/exito` pasando `materia` (via `navigate(..., { state })`, patrón consistente con SPA sin querystring de datos sensibles)
  - 422 (`ApiError`, cualquiera de los 3 casos de invitación) → navega a `/registro/error`
  - 409 (`ApiError`, email ya registrado) → error inline en el propio formulario (mismo patrón que `LoginError`, sin navegar)
  - Link secundario "¿Ya tenés cuenta? Iniciar sesión" → `/login`
- [x] `frontend/src/pages/RegistroError.tsx`
  - Pantalla completa (no inline) — mensaje genérico de link inválido/vencido/usado, sin
    distinguir motivo (§2.4). Sin formulario. Acción: volver a `/login`.
- [x] `frontend/src/pages/RegistroExito.tsx`
  - Pantalla completa — confirmación con nombre de la comisión (recibido por `location.state`,
    con fallback si se accede directo sin state). Acción primaria "Iniciar sesión" → `/login`.

### 3. Integración

- [x] `frontend/src/router.tsx`
  - Reemplazar `RegistroPlaceholder` en `/registro` por `<Registro />`
  - Agregar rutas `/registro/error` → `<RegistroError />`, `/registro/exito` → `<RegistroExito />`
  - Quitar el import/uso de `RegistroPlaceholder` de `_placeholders.tsx` (queda solo `InicioPlaceholder`)

**Estado:** 9/9 tareas completadas
