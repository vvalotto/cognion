# Plan de Implementación: US-ADJ-08 - Estudiante ve la materia/comisión de la invitación antes de registrarse

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC Identidad)
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-30

## Resultado

847/847 tests unitarios backend, 570/571 integración (único fallo confirmado como colisión de
concurrencia ajena, no regresión — ver `docs/reports/inc6-adj/US-ADJ-08-report.md`), 5/5
escenarios BDD, 800/800 tests frontend. Quality gates APROBADO
(`quality/reports/inc6-adj/US-ADJ-08-quality.json`): pylint 10.00/10, CC máx 4, MI mín 59.36,
coverage 100% en los módulos medibles del gate (`entities`/`use_cases`/`interface_adapters`).

## Componentes a Implementar

### 1. Query — `ObtenerInvitacionUseCase` (use_cases)
- [x] `src/identidad/use_cases/obtener_invitacion.py`
  - `InvitacionPreview` (dataclass): `materia: str`, `horario: str` — DTO de solo lectura, sin `docente_id` ni datos sensibles
  - `ObtenerInvitacionUseCase(invitacion_repositorio, comision_repositorio, materia_port)`
  - `execute(token: str) -> InvitacionPreview`:
    1. Busca la invitación por token (`InvitacionRepositoryPort.obtener_por_token`) → `InvitacionInvalida` si no existe
    2. `invitacion.verificar_vigente(datetime.now(UTC))` → reutiliza el método existente de `Invitacion` (no muta estado, a diferencia de `aceptar()`) → lanza `InvitacionVencida`/`InvitacionYaUsada` si corresponde
    3. Resuelve la comisión (`ComisionRepositoryPort.obtener_por_id`) y la materia (`MateriaPort.obtener`) — mismo patrón que `RegistroController.registrar_estudiante`
    4. Devuelve `InvitacionPreview(materia=materia.nombre, horario=comision.horario)`
  - Sin cambios en `Invitacion` (entities) ni en las excepciones existentes (`InvitacionInvalida`/`InvitacionVencida`/`InvitacionYaUsada` ya cubren los 3 casos de error)

### 2. Controller — extender `InvitacionesController`
- [x] `src/identidad/interface_adapters/controllers/invitaciones_controller.py`
  - Agrega segunda dependencia: `obtener_invitacion: ObtenerInvitacionUseCase`
  - Nuevo método `async def obtener_invitacion(self, token: str) -> InvitacionPreview` — delega en el use case
  - Se reutiliza el controller existente (ya dedicado al aggregate `Invitacion`) en vez de crear uno nuevo — mismo criterio que `US-2.2.3` (command/query en el mismo controller cuando no hay riesgo de CBO)

### 3. Schema — `InvitacionPreviewResponse`
- [x] `src/identidad/frameworks/api/schemas.py`
  - `InvitacionPreviewResponse(BaseModel)`: `materia: str`, `horario: str` — mismo patrón que `RegistroResponse`

### 4. Endpoint — `GET /identidad/invitaciones/{token}`
- [x] `src/identidad/frameworks/api/registro_router.py`
  - Nuevo endpoint público (sin `Depends(get_current_user)`, mismo criterio que `POST /identidad/registro`) en el router con `prefix="/identidad"` → path final `/identidad/invitaciones/{token}`
  - Errores: `InvitacionInvalida` → 404; `InvitacionVencida`/`InvitacionYaUsada` → 422 (a diferencia de `POST /registro`, aquí sí puede distinguirse 404 de 422 porque no hay riesgo de filtrar información sobre invitaciones ajenas — es una consulta anónima por token, no una enumeración de recursos)
  - Usa `Depends(get_invitaciones_controller)` (ya existente)

### 5. Composition root
- [x] `src/identidad/frameworks/dependencies.py`
  - `get_invitaciones_controller`: agrega `comision_repo` (ya se instancia) y `materia_port = MateriaPortInProcess(session)` como argumentos de `ObtenerInvitacionUseCase(invitacion_repo, comision_repo, materia_port)`, pasado como segundo argumento a `InvitacionesController(...)`

## Integración

- [x] Frontend: `frontend/src/pages/identidad/Registro.tsx`
  - `useEffect` al montar: `apiFetch<InvitacionPreviewResponse>("/identidad/invitaciones/" + token)` (nuevo `AbortController` propio para el fetch de montaje, no reutilizar el de submit — mismo criterio de `US-ADJ-20`/gap de `US-4.1.x`)
  - Estados: `cargando` (spinner/skeleton corto), `preview` (materia + horario), `tokenInvalido` (404/422 → navega a `/registro/error`, reutilizando la pantalla ya existente — mismo criterio "no distinguir el motivo" de `US-1.1.3`)
  - Chip `.comision-tag` (Tailwind, sin componente nuevo) antes del formulario: "● Te vas a unir a **{materia} — {horario}**" — usa `horario` en vez de la letra de comisión inexistente en el dominio (nota de diseño de la spec)
  - El formulario no se muestra mientras `cargando` o si el token ya es inválido (evita que el Estudiante lo complete para descubrir el rechazo recién en el submit)

**Estado:** 6/6 tareas completadas
