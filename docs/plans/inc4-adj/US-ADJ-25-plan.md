# Plan de Implementación: US-ADJ-25 - Administrador asigna un Docente a una Comisión

**Patrón:** Clean Architecture BC-First — backend (Identidad) + frontend
**Producto:** cognion (BC Identidad)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-07

## Componentes a Implementar

### 1. Backend — endpoint de consulta nuevo
- [x] `src/identidad/interface_adapters/controllers/comisiones_query_controller.py`
  - `obtener_comision(comision_id: UUID) -> Comision` — llama a
    `self._comision_repository.obtener_por_id(comision_id)` (puerto ya inyectado, usado hoy
    para validar existencia en `listar_estudiantes`); lanza `ComisionNoExiste` si es `None`.
    Sin Use Case dedicado (consulta de lectura simple, mismo criterio que el resto del
    controller).
- [x] `src/identidad/frameworks/api/comisiones_router.py`
  - `GET /comisiones/{comision_id}`, `response_model=ComisionResponse`, guard
    `require_docente_o_administrador` (ya existe en `dependencies.py`). 404 si
    `ComisionNoExiste`.

### 2. Frontend — cliente API
- [x] `frontend/src/lib/identidad-comisiones-api.ts`
  - `obtenerComision(comisionId: string, signal?: AbortSignal): Promise<ComisionDetalleResponse>`
    — `GET /comisiones/{id}`, mapea `docentes_asignados` (UUIDs) a `docentesAsignados: string[]`.
  - `asignarDocente(comisionId: string, docenteId: string, signal?: AbortSignal): Promise<ComisionDetalleResponse>`
    — `POST /comisiones/{id}/docentes` con `{ docente_id }`.

### 3. Frontend — pantalla de detalle
- [x] `frontend/src/pages/identidad/ComisionDetalle.tsx` (nuevo)
  - Carga `obtenerComision(comisionId)` + `listarCuentas({ rol: "docente" })` (resolver
    nombres, mismo patrón que `Comisiones.tsx`) + `listarEstudiantesDeComision(comisionId)`
    en paralelo.
  - Breadcrumb "Comisiones › {horario}" + botón "‹ Volver a Comisiones".
  - Alerta informativa si `docentesAsignados.length === 0`.
  - Select de Docentes disponibles + botón "Asignar" → `asignarDocente(...)` → actualiza el
    estado local con la respuesta (sin recargar la página).
  - Tabla de Estudiantes inscriptos (nombre, email si disponible) o estado vacío.
  - Mismo patrón de `AbortController` en `useEffect` que `NuevaComision.tsx`/`NuevaMateria.tsx`
    para el submit de "Asignar".

### 4. Integración
- [x] `frontend/src/router.tsx` — `/comisiones/:comisionId` usa `ComisionDetalle` en vez de
  `ComisionPlaceholder`.

### 5. Tests
- [x] Unitario backend: `tests/unit/inc4/test_comisiones_query_controller.py` — extendido con
  `TestObtenerComision` (existente, inexistente).
- [x] Integración backend: `tests/integration/inc4/test_comisiones_query_router.py` —
  extendido con `TestObtenerComision` (200 con/sin docente, 404, 403 Estudiante, regresión
  Docente). `POST /comisiones/{id}/docentes` ya estaba cubierto en
  `tests/integration/inc1/test_comisiones_api_integration.py` desde el Incremento 1, sin
  cambios.
- [x] BDD: `tests/step_defs/inc4-adj/test_us_adj_25_steps.py` — steps para el `.feature` ya
  escrito en Fase 1.
- [x] Frontend: `ComisionDetalle.test.tsx` (nuevo, 6 tests), `identidad-comisiones-api.test.ts`
  (+3 tests: `obtenerComision` ×2, `asignarDocente` ×1). Sin test nuevo en `router.test.tsx` —
  el guard de rol de `/comisiones/:comisionId` ya estaba cubierto desde `US-ADJ-23`, sin
  comportamiento nuevo que testear ahí.

**Estado:** 5/5 grupos completados.
