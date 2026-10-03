# Plan de Implementación — US-ADJ-60

Spec: `docs/specs/ajustes/US-ADJ-60.md` · Contexto: `US-ADJ-60-context.md` · BDD: 11 escenarios.
Orden: dominio → persistencia → use cases → API → composition root → frontend → docs.

## Parte A — Backend

| # | Tarea | Archivos |
|---|-------|----------|
| T1 | `Usuario.bloqueada_hasta: datetime \| None`; `bloquear_por_intentos_fallidos(es_ultimo_administrador, ahora, duracion) -> bool` (política INV-ID-21: temporal solo para el último Administrador operativo); `es_administrador_operativo()`; `levantar_bloqueo_si_vencio(ahora) -> bool` (vencimiento perezoso); `resetear_password` limpia `bloqueada_hasta`; `registrar_fallo_cambio_password` pasa a solo contar y devolver si llegó al umbral (la política de bloqueo la aplica `bloquear_por_intentos_fallidos`) | `entities/usuario.py` |
| T2 | Errores `UltimoAdministradorOperativoError`, `CuentaBloqueadaTemporalmenteError(usuario_id, bloqueada_hasta)` con `segundos_restantes(ahora)` | `entities/errors.py` |
| T3 | Puerto `contar_administradores_operativos(excluyendo)`; retirar `tiene_comisiones_creadas` de `ComisionQueryPort` (queda sin uso) y de gateway y fakes | `entities/ports/usuario_repository_port.py`, `comision_query_port.py`, `gateways/*`, `tests/unit/inc1/_fakes.py`, `tests/unit/inc4/test_comisiones_query_controller.py`, `tests/integration/inc4/test_comision_query_repository.py` |
| T4 | Columna ORM `usuario.bloqueada_hasta` (timestamptz null) + migración Alembic (down_revision `a6c2d4f8b1e3`); gateway persiste/lee `bloqueada_hasta` y cuenta operativos (`administrador ⨝ usuario`, no deshabilitada, no bloqueada, excluyendo id) | `frameworks/db/models.py`, `migrations/versions/`, `gateways/usuario_repository.py` |
| T5 | `EliminarCuentaUseCase`: Administrador → siempre baja lógica; si es operativo y no hay otro → `UltimoAdministradorOperativoError`; ya deshabilitado/bloqueado → idempotente | `use_cases/eliminar_cuenta.py` |
| T6 | `IniciarSesionUseCase` y `CambiarPasswordUseCase`: vencimiento perezoso al inicio, bloqueo temporal vigente → `CuentaBloqueadaTemporalmenteError`, política en el 3.er fallo; reciben `duracion_bloqueo_temporal: timedelta` por constructor | `use_cases/iniciar_sesion.py`, `cambiar_password.py` |
| T7 | `settings.administrador_bloqueo_temporal_minutos = 15`, inyección en `get_auth_controller`/`get_perfil_controller` | `src/settings.py`, `frameworks/dependencies.py` |
| T8 | Routers: `DELETE /usuarios/{id}` → 409 estructurado; login y cambio de contraseña → 403 `cuenta_bloqueada_temporal` con `reintentar_en_segundos` | `api/cuentas_router.py`, `auth_router.py`, `perfil_router.py` |

## Parte B — Frontend (gate UX aprobado: wireframes §2.10/§2.11)

| # | Tarea | Archivos |
|---|-------|----------|
| T9 | `EliminarCuenta.tsx`: variante Administrador ("Deshabilitar cuenta", se puede reactivar), manejo del 409 mostrando el mensaje | `frontend/src/pages/cuentas/EliminarCuenta.tsx` |
| T10 | `Login.tsx`: alerta `cuenta_bloqueada_temporal` con minutos (redondeo hacia arriba, mín. 1), formulario habilitado; componente `LoginCuentaBloqueadaTemporalError.tsx` | `frontend/src/pages/identidad/` |

## Tests
- Unit (`tests/unit/inc7-adj/`): política y vencimiento en `Usuario`; los 3 use cases con fakes.
- Integration (`tests/integration/inc7-adj/`, base descartable): conteo de operativos, persistencia de `bloqueada_hasta`, endpoints 409/403, round-trip de la migración.
- BDD: `test_us_adj_60_steps.py`. Vitest: `EliminarCuenta`, `Login`, componente nuevo.

## Docs
`BC-identidad-modelo.md` (INV-ID-19/20/21, `bloqueada_hasta`, enmienda INV-ID-10), `.env.example` si lista settings, spec → "Implementada", reporte de la US.

## Riesgos
- CBO de `EliminarCuentaUseCase`: no suma colaboradores (el conteo va por el repositorio que ya recibe); retirar `tiene_comisiones_creadas` no cambia el conteo de dependencias.
- Condición de carrera entre dos Administradores que se deshabilitan a la vez: aceptada y documentada (spec).
- Tras T3, hay que correr todo `tests/unit` para detectar fakes desactualizados.
