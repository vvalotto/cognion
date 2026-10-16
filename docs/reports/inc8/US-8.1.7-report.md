# Reporte — US-8.1.7: Cuenta SMTP resuelta por materia con fallback global

**Estado:** implementada en `feature/US-8.1.1-cors-configurable` (2026-10-16). PR diferido al cierre de la Iteración 1.
**Issue:** #534 · **Spec:** `docs/specs/inc8/US-8.1.7.md` · **Decisión:** `ADR-023`

## Qué se hizo
- `src/settings.py`: `CuentaSmtpMateria` y `smtp_cuentas_por_materia` (env `SMTP_CUENTAS_POR_MATERIA`, JSON con clave `materia_id` validada como UUID). En staging/producción cada cuenta se valida como la global (host no local, remitente distinto de `@cognion.local`).
- `src/shared/frameworks/smtp.py`: `resolver_cuenta_smtp` (cuenta de la materia, o la global si no tiene o no hay materia) y `enviar_email`. **Reemplaza el código `smtplib` que estaba duplicado** en `SmtpCanalEnvio` (Notificaciones) y `SmtpNotificador` (Identidad); lee `settings` al enviar, no al importar.
- `CanalEnvioPort.enviar` y `NotificadorPort.enviar_invitacion` ganan `materia_id: UUID | None = None`. Apertura, cierre e invitación envían con la materia; la recuperación de contraseña, sin materia, usa la global.
- Fakes y tests existentes actualizados (firma del puerto; ruta de parcheo de `smtplib` ahora en el módulo compartido).

## Verificación
10 tests nuevos (resolver, JSON de entorno, clave inválida, rechazo en producción sin filtrar la contraseña, envío con la cuenta correcta, invitación con la materia); suite unit 936/936. **Regresión real:** 43 tests de integración y BDD (invitaciones, recuperación de contraseña, notificaciones) contra una base descartable migrada, con servidor SMTP stub real: todos pasan; base borrada y base de desarrollo intacta.

## Decisiones propias (a confirmar)
- Una sola variable JSON en vez de una variable de entorno por materia (como decía el texto de `ADR-023`): un único secret, claves UUID validadas. Documentado en el ADR.
- Clave por `materia_id`, no por nombre. El operador obtiene el id de `GET /api/materias`.
- Se incluyó la invitación (no solo Notificaciones) porque la comisión ya conoce su materia y el costo era mínimo.

## Límites
- No hay cuentas reales cargadas: las credenciales de las cuentas institucionales las provee Víctor y quedan fuera del repo.
- No probado contra un servidor SMTP institucional real (starttls + login se verifican con un doble).
- Sin reintentos de envío (fuera de alcance).
