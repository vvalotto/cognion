# US-8.5.2: Canal de email por consola para uso sin SMTP

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `infra backend` (técnica — sin comando de negocio)
**Bounded Context**: transversal (`src/shared/frameworks/smtp.py`, `src/settings.py`)
**Issue**: #537

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba con alumnos**,
quiero **que el sistema funcione sin un servidor de correo, dejando a la vista el contenido de los emails**,
para **poder completar flujos que dependen de un link por email (recuperar contraseña) sin configurar SMTP**.

---

## Contexto

Sin SMTP configurado, `smtplib` intenta conectarse a `localhost:25`, falla, y: Notificaciones lo registra y sigue
(`BC-notificaciones-modelo.md` §6); pero la **recuperación de contraseña** y la **invitación por email** quedan
sin entregar. La invitación se puede evitar copiando el link desde la interfaz (`US-ADJ-26`); la recuperación no.

## Especificacion del comportamiento

- Nueva setting `email_modo: Literal["smtp", "consola"]` (env `EMAIL_MODO`, default `smtp`).
- En modo `consola`, `enviar_email` (`src/shared/frameworks/smtp.py`) **no abre ninguna conexión**: escribe en el log
  de la aplicación, a nivel INFO, el destinatario, el asunto y el cuerpo completo (incluye los links con token).
- En `staging` y `produccion` el modo `consola` se rechaza al arrancar (el cuerpo contiene tokens de recuperación y
  no deben quedar en logs de un servidor expuesto); el error nombra `EMAIL_MODO`.
- `smtp` (default) conserva el comportamiento actual, incluida la cuenta por materia (`US-8.1.7`).
- `.env.example` documenta la variable.

## Escenarios (BDD)

1. `EMAIL_MODO=consola` → un envío escribe destinatario, asunto y cuerpo en el log y no llama a `smtplib`.
2. `EMAIL_MODO=smtp` (o sin definir) → el envío usa la cuenta resuelta, como hasta ahora.
3. `EMAIL_MODO=consola` con `ENTORNO=produccion` → error de configuración que nombra `EMAIL_MODO`.
4. Solicitar recuperación de contraseña en modo `consola` → el link queda en el log y el endpoint responde igual
   que siempre (sin revelar si el email existe, `INV-ID-17`).

## Fuera de alcance

Un buzón de pruebas con interfaz (tipo Mailpit); reintentos de envío.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
