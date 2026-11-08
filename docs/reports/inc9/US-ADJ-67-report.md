# Reporte — US-ADJ-67: El Docente genera un link de invitación grupal con vencimiento corto

**Estado:** implementada en `feature/inc-9-iter-2-link-grupal` (2026-11-08), un commit por US; el PR sale al cierre de la Iteración 2.
**Issue:** [#590](https://github.com/vvalotto/cognion/issues/590) · **Spec:** `docs/specs/ajustes/US-ADJ-67.md` · **ADR:** `ADR-027` · **Origen:** prueba real con estudiantes sobre la VM de GCP (2026-11-06)

## Qué se hizo
- **Agregado `Invitacion`:** `grupal`, `usos` y `revocada_en`; estados vigente, vencida, revocada y usada; `crear_grupal` con duración 15, 60 (por defecto) o 1440 minutos; `revocar` idempotente. La individual no cambia (un uso, 7 días).
- **Casos de uso nuevos:** `GenerarInvitacionGrupal` (revoca el link vigente anterior y guarda el nuevo en una sola transacción), `RevocarInvitacionGrupal` y `ObtenerUltimaInvitacionGrupal`. La autorización "Docente asignado" se extrajo a `autorizacion_comision.py`.
- **Registro:** con un link grupal cada registro suma un uso con `UPDATE usos = usos + 1`; un registro rechazado (email repetido, contraseña inválida) no cuenta.
- **API:** `POST /comisiones/{id}/invitaciones-grupales`, `GET .../ultima`, `POST .../{id}/revocar`. El preview y el registro devuelven `detail = {"codigo", "mensaje"}` (`invitacion_invalida`, `invitacion_vencida`, `invitacion_revocada`, `invitacion_usada`, `password_invalida`); los status no cambian.
- **Persistencia:** migración `f7a3c9d15e82_invitacion_grupal` (tres columnas, `downgrade` verificado).
- **Frontend:** tarjeta de invitación del Docente (duración, link, copiar, vigencia, registrados con refresco cada 15 s, desactivar, avisos de vencido y desactivado), `RegistroError` con cuatro motivos por `?motivo=` y `Registro` que muestra la contraseña rechazada en el formulario.
- **Documentación:** `ADR-027`, nota en `ADR-012`, `BC-identidad-modelo.md` (`Invitación`, `INV-ID-01`, `INV-ID-03`, `INV-ID-22`, `INV-ID-23`).

## Decisiones
- El contador `usos` de la grupal no vive en el agregado: con registros simultáneos lo suma la base; el agregado solo lo fija en la individual.
- El mapeo error → código HTTP vive en `frameworks` (`errores_invitacion.py`), no en las entidades.
- Controller nuevo para el link grupal, separado del de la individual (CBO).
- El endpoint individual se conserva; solo desaparece de la pantalla.

## Hallazgos al implementar
- Dos registros del mismo email a la vez terminaban en un `500` (violación de la restricción única): `SQLAlchemyUsuarioRepository.guardar` lo traduce ahora a `EmailYaRegistrado` (`409`).
- Un contador en memoria perdía cuentas con registros simultáneos: se pasó a una sola sentencia SQL, probado con 20 registros a la vez.
- La autorización "Docente asignado" estaba copiada en tres casos de uso (pylint R0801): extraída a un helper.

## Calidad
42 unitarios nuevos, 18 de integración (incluye 20 registros simultáneos, el mismo email en paralelo y las filas anteriores a la migración), 15 casos BDD y, en frontend, los de `ComisionDetalleDocente`, `RegistroError`, `Registro` y `api-client`, todos en verde. 233 tests de regresión de invitaciones, registro, login y bloqueo pasan contra una base descartable; `verificar_migraciones.sh` en verde. Cobertura 100 % en lo nuevo o modificado. `pylint` 9,93/10 (quedan R0903 y R0902 como en el resto), `mypy` 0 errores (322 archivos), `ruff`/`black`/`isort` limpios, `tsc -b` sin errores, ninguna función con complejidad B o mayor. La suite completa se corre una sola vez al cerrar la Iteración 2. Evidencia: `quality/reports/inc9/US-ADJ-67-quality.json`.

## Tiempo
Ver `.claude/tracking/US-ADJ-67-tracking.json`.

## Pendiente
- Verificar en navegador real, al cierre de la iteración y con celular: abrir el link con tres estudiantes, vencerlo y desactivarlo.
- Eliminar la base descartable `cognion_adj69_descartable` al cerrar la iteración.
- Si se despliega en GCP, correr la migración y repetir la ráfaga de registros con la clase real (#597).
