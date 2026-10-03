# Reporte de Implementación: US-ADJ-60

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-60 — El sistema siempre conserva al menos un Administrador operativo
- **Iteración:** `Incremento 7-ADJ — Ciclo de vida de la cuenta y ajustes de la UAT v1` (segunda US)
- **Puntos estimados:** 5
- **Tiempo real:** ver `.claude/tracking/US-ADJ-60-tracking.json` (PRIN-001)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-10-03
- **Origen:** UAT manual de cierre de alcance v1, hallazgo **#4** 🔴 (`quality/reports/uat/inc7/registro-hallazgos.md`)
- **Aporta:** el sistema ya no puede quedar sin Administrador que lo opere: un Administrador nunca se borra, no se puede deshabilitar al último operativo, y el bloqueo automático del último es temporal.

## Componentes Implementados

### Entities
- ✅ `usuario.py` — `bloqueada_hasta`, `es_administrador_operativo()`, `bloquear_por_intentos_fallidos()` (política INV-ID-21 en un único método), `tiene_bloqueo_temporal_vigente()`, `levantar_bloqueo_si_vencio()` (vencimiento perezoso); `resetear_password` limpia `bloqueada_hasta`; `registrar_fallo_cambio_password` solo cuenta (la política la aplica el use case)
- ✅ `errors.py` — `CuentaBloqueadaTemporalmenteError`, `UltimoAdministradorOperativoError`
- ✅ `ports/usuario_repository_port.py` — `contar_administradores_operativos(excluyendo)`; se retiró `tiene_comisiones_creadas` de `ComisionQueryPort` (sin usos)

### Use Cases
- ✅ `eliminar_cuenta.py` — Administrador: siempre baja lógica, `409` si es el último operativo
- ✅ `iniciar_sesion.py`, `cambiar_password.py` — bloqueo temporal / permanente y vencimiento perezoso, duración inyectada
- ✅ `politica_bloqueo.py` (nuevo) — `es_ultimo_administrador_operativo` y `rechazar_si_bloqueada`, compartidos por ambos use cases

### Interface Adapters y Frameworks
- ✅ `gateways/usuario_repository.py` — conteo `administrador ⨝ usuario` y persistencia de `bloqueada_hasta`
- ✅ `db/models.py` + migración `c4d1f9a27b60` (`usuario.bloqueada_hasta timestamptz NULL`, round-trip verificado)
- ✅ `settings.administrador_bloqueo_temporal_minutos` (15), inyectado desde `dependencies.py`
- ✅ Routers: `DELETE /usuarios/{id}` → `409` `ultimo_administrador_operativo`; login y cambio de contraseña → `403` `cuenta_bloqueada_temporal` con `reintentar_en_segundos` (`api/bloqueo_temporal.py`)

### Frontend (gate UX aprobado 2026-10-03, wireframes §2.10 y §2.11)
- ✅ `EliminarCuenta.tsx` — variante Administrador ("Deshabilitar cuenta") y manejo del `409`
- ✅ `Login.tsx` + `LoginCuentaBloqueadaTemporalError.tsx` — alerta con minutos, formulario habilitado

### Documentación
- ✅ `BC-identidad-modelo.md` (INV-ID-19/20/21, `bloqueada_hasta`, enmienda a INV-ID-10), wireframes §2.10/§2.11 + prototipo (pantallas 9 a 11), spec en "Implementada"

## Tests

| Nivel | Resultado |
|-------|-----------|
| Unit backend | 875/875 ✅ (nuevos: `tests/unit/inc7-adj/`) |
| Integración + BDD | 984/984 ✅ suite completa contra base descartable; 12 de integración y 10 de BDD nuevos |
| Frontend (Vitest) | 813/813 ✅ — statements 93,53 %, branches 85,97 % |

Verificación: `mypy` 0 errores, `ruff` 0 en `src`, `pylint` 9,54, CC ≤ B, MI mín. 49,72. CodeGuard `--analysis-type full` (9 checks); sus errores son tooling (herramientas no instaladas, timeouts), ver `quality/reports/inc7-adj/US-ADJ-60-quality.json`.

## Incidente propio (transparencia)

Un comando de BDD corrió sin `DATABASE_URL` y **vació las tablas de identidad de la base de desarrollo `cognion`** (tenía 6 usuarios de UAT). No afecta producción ni datos reales. A partir de ahí, todo comando de integración/BDD lleva `DATABASE_URL` hacia una base descartable en la misma línea. La base de desarrollo necesita `alembic upgrade head` y, si se quiere, reponer el Administrador y los datos de UAT.

## Decisiones y notas

- La política de bloqueo salió de `registrar_fallo_cambio_password` (que bloqueaba siempre) hacia `bloquear_por_intentos_fallidos`: se actualizó un test existente de la entidad.
- Condición de carrera entre dos Administradores que se deshabilitan a la vez: aceptada y documentada (INV-ID-20).
- `US-ADJ-62` (recuperar contraseña desbloquea) deberá limpiar también `bloqueada_hasta`.
