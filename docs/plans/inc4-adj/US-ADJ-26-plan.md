# Plan de Implementación: US-ADJ-26 - Docente genera el link de invitación de una Comisión

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion
**Bounded Context:** Identidad (backend) + Actividad Evaluativa (frontend, pantallas nuevas)
**Estado:** ✅ COMPLETADO — 9/9 tareas, quality gates APROBADO
(`quality/reports/inc4-adj/US-ADJ-26-quality.json`)

## Componentes a Implementar

### 1. Backend — ampliar `POST /comisiones/{id}/invitaciones` (Identidad)

- [x] `src/identidad/frameworks/api/schemas.py`
  - `GenerarInvitacionRequest.email_destinatario`: `str = Field(...)` → `str | None = None`
  - `InvitacionResponse`: agrega campo `token: str`
- [x] `src/identidad/use_cases/generar_invitacion.py`
  - `execute()`: solo llama a `self._notificador.enviar_invitacion(email_destinatario, invitacion.token)` si `email_destinatario is not None`
  - (incluye ajuste de tipo en `InvitacionesController.generar_invitacion`, mismo cambio de firma)
- [x] `src/identidad/frameworks/api/invitaciones_router.py`
  - Agrega `token=invitacion.token` al `InvitacionResponse` devuelto (`body.email_destinatario` ya llega opcional desde el schema, sin cambio de firma en el controller/use case más allá del tipo)

### 2. Frontend — cliente API (`identidad-comisiones-api.ts`)

- [x] `generarInvitacion(comisionId, docenteId, signal?): Promise<InvitacionResponse>`
  - `POST /comisiones/{comisionId}/invitaciones` con body `{ docente_id: docenteId }` (sin `email_destinatario`)
  - Mapea `InvitacionApiResponse` (snake_case: `id`, `comision_id`, `docente_id`, `expira_en`, `token`) → `InvitacionResponse` (camelCase)

### 3. Frontend — pantalla `ComisionesDeMateria.tsx` (Actividad Evaluativa, Docente)

- [x] `frontend/src/pages/actividad-evaluativa/ComisionesDeMateria.tsx`
  - Ruta `/actividad-evaluativa/materias/:materiaId/comisiones`
  - Reusa `listarComisionesPorMateria(materiaId)` (ya existente)
  - Breadcrumb: "Mis materias" (→ `/actividad-evaluativa/materias`) › `{materia.nombre}` › "Comisiones"
  - Tabla/lista simple: Horario + acción "Ver detalle" → navega a `/actividad-evaluativa/comisiones/{id}`
  - Estado vacío: "Todavía no hay comisiones creadas para esta materia." (misma redacción que `Actividades.tsx`)

### 4. Frontend — pantalla `ComisionDetalleDocente.tsx` (Actividad Evaluativa, Docente)

- [x] `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.tsx`
  - Ruta `/actividad-evaluativa/comisiones/:comisionId`
  - Carga `obtenerComision(comisionId)` (ya existente) para el horario y `materiaId` de vuelta no está disponible ahí — breadcrumb usa solo "Comisiones › {horario}" con botón "‹ Volver" a `history.back()` (mismo patrón que otras pantallas de detalle sin contexto de materia)
  - Botón "Generar link de invitación" → `generarInvitacion(comisionId, obtenerUsuarioId())`
  - Tras la respuesta: muestra recuadro con `${window.location.origin}/registro?token=${token}`, botón "Copiar" (`navigator.clipboard.writeText`), texto de ayuda "Válido por 7 días, un solo uso"
  - El botón principal cambia a "Generar un link nuevo" tras la primera generación exitosa
  - Tabla de Estudiantes inscriptos: reusa `listarEstudiantesDeComision(comisionId)` (ya existente), solo lectura
  - Manejo de error 422 (`DocenteNoAsignadoAComision`): mensaje de alerta en vez de crashear (defensa en profundidad — la UI no debería ofrecer llegar acá, pero el backend puede rechazar)

### 5. Frontend — entry point y rutas

- [x] `frontend/src/pages/actividad-evaluativa/Actividades.tsx`
  - Agrega botón "Ver Comisiones" junto a "+ Nueva actividad", navega a `/actividad-evaluativa/materias/${materiaId}/comisiones`
- [x] `frontend/src/router.tsx`
  - `/actividad-evaluativa/materias/:materiaId/comisiones` → `ComisionesDeMateria`, `RequireRole rol="docente"`
  - `/actividad-evaluativa/comisiones/:comisionId` → `ComisionDetalleDocente`, `RequireRole rol="docente"`

## Integración

- [ ] Sin cambios en `dependencies.py` de Identidad — reutiliza `GenerarInvitacionUseCase`,
  `InvitacionesController`, guard `require_docente` ya inyectados.
- [ ] Sin cambios en `dependencies.py` de Actividad Evaluativa — las pantallas nuevas consumen
  únicamente `identidad-comisiones-api.ts` (BC Identidad, ya expuesto al frontend) y
  `banco-preguntas-api.ts` (`listarMaterias`, ya usado por `Actividades.tsx`).

**Estado:** 0/9 tareas completadas
