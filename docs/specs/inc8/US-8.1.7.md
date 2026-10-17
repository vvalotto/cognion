# US-8.1.7: Cuenta SMTP resuelta por materia con fallback global

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.1`
**Tipo**: `infra backend` (técnica — sin comando de negocio)
**Bounded Context**: transversal (`shared`), Notificaciones, Identidad
**Issue**: #534 · **Decisión**: `ADR-023`

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **que los emails de una materia salgan desde la cuenta institucional de esa materia**,
para **que lleguen desde una identidad legítima (SPF/DKIM) y el estudiante reconozca al remitente**.

---

## Contexto

Hoy hay una sola cuenta SMTP global (`SMTP_HOST/PORT/USER/PASSWORD/FROM`) y el código SMTP está **duplicado** en
`SmtpCanalEnvio` (Notificaciones) y `SmtpNotificador` (Identidad). `ADR-023` decidió resolver el remitente por materia,
con credenciales en variables de entorno (nunca en el dominio ni en la base) y la cuenta global como respaldo.

## Especificacion del comportamiento

- Nueva variable `SMTP_CUENTAS_POR_MATERIA`: JSON `{"<materia_id>": {"host", "port", "user", "password", "remitente"}}`
  (`port` default 25, `user`/`password` opcionales). Default `{}`. Las claves deben ser UUID: una clave inválida es
  error de configuración. Se carga como secret (`fly secrets set`).
- Módulo compartido `src/shared/frameworks/smtp.py` (reemplaza el SMTP duplicado de los dos adapters):
  - `resolver_cuenta_smtp(materia_id)` → la cuenta de esa materia si está configurada; si `materia_id` es `None` o no
    tiene cuenta propia → la cuenta global (`SMTP_*`). Lee `settings` al momento de enviar.
  - `enviar_email(materia_id, destinatario, asunto, cuerpo)` (en un thread, `smtplib` es bloqueante).
- `CanalEnvioPort.enviar(...)` y `NotificadorPort.enviar_invitacion(...)` ganan `materia_id: UUID | None = None`.
- Notificaciones (apertura y cierre) pasa la `materia_id` de la actividad. La invitación pasa la `materia_id` de la
  comisión. La recuperación de contraseña no tiene materia → cuenta global.
- En `staging`/`produccion` (`US-8.1.3`) cada cuenta por materia se valida como la global: `host` no local y
  `remitente` distinto de `@cognion.local`.
- Ningún mensaje de error, log ni excepción incluye `password`.

## Escenarios (BDD)

1. Materia con cuenta propia → el email sale con el `remitente` y el servidor de esa materia.
2. Materia sin cuenta propia → sale por la cuenta global.
3. Sin materia (recuperación de contraseña) → cuenta global.
4. `SMTP_CUENTAS_POR_MATERIA` con una clave que no es UUID → error al construir `Settings`.
5. En `produccion`, una cuenta por materia con host local → error que nombra la variable, sin la contraseña.
6. Apertura/cierre de una actividad y la invitación envían con la `materia_id` correcta.

## Fuera de alcance

Credenciales reales de las cuentas institucionales (las provee Víctor, fuera del repo); almacén de secretos para
más materias; reintentos de envío.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
