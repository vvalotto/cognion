# US-ADJ-66: El envío de email valida el certificado del servidor SMTP

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 8 — Despliegue en la nube (diferido)`
**Tipo**: `mejora de seguridad` backend (infraestructura compartida)
**Agregado principal afectado**: ninguno
**Bounded Context**: transversal (`shared`), lo consumen Notificaciones e Identidad
**Origen**: revisión del envío de emails al preparar el despliegue en GCP (2026-11-05, `docs/plans/DESPLIEGUE-GCP.md` Paso 11b).
**Issue**: [#586](https://github.com/vvalotto/cognion/issues/586)
**Interactúa con**: `ADR-023` (SMTP por materia), `US-8.1.7` (`src/shared/frameworks/smtp.py`), `US-ADJ-64` (logging), `scripts/probar_smtp.py`.

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar Cognión con emails reales**,
quiero **que la aplicación compruebe que el servidor de correo es de verdad el que dice ser antes de enviarle usuario, contraseña y mensajes**,
para **que nadie que controle la red entre la aplicación y el servidor de correo pueda leer las credenciales SMTP ni los links de recuperación de contraseña e invitación**.

---

## Contexto

`_enviar_sync` (`src/shared/frameworks/smtp.py`) abre la conexión y, si la cuenta tiene usuario, llama `servidor.starttls()` **sin contexto**. En
`smtplib`, eso cifra el canal pero **no valida la cadena de certificados ni que el nombre del certificado coincida con el servidor**. Un
intermediario en la red podría presentar un certificado propio, y la aplicación le entregaría `SMTP_USER`/`SMTP_PASSWORD` y después cada email
(con los tokens de recuperación de contraseña e invitación).

Se detectó al comprobar el envío real con Gmail: el mismo `smtplib`, usado con un contexto por defecto (`ssl.create_default_context()`), **sí**
falló con `CERTIFICATE_VERIFY_FAILED` en una Mac con Python de python.org (sin almacén de certificados del sistema), lo que muestra que la
validación depende de qué certificados raíz encuentre el intérprete.

Hoy el riesgo es bajo (prueba en una Mac o en una VM propia), pero debe cerrarse antes de enviar emails reales desde un servidor expuesto.

## Especificacion del comportamiento

- Al negociar STARTTLS, el envío usa un contexto TLS que **verifica el certificado y el nombre del servidor** (`SMTP_HOST` o el `host` de la cuenta de la materia).
- Si el certificado no es válido, el envío **falla** con un error claro (certificado no verificable) y **no se envían** usuario, contraseña ni mensaje.
- Solo cambia el caso con autenticación (cuenta con `user`), que es el único que ya usa STARTTLS. El envío sin usuario (servidor local de pruebas en `localhost:25`) **sigue igual**: no negocia TLS.
- Las cuentas por materia (`SMTP_CUENTAS_POR_MATERIA`) y la global se validan igual.
- `EMAIL_MODO=consola` no se ve afectado (no abre conexión).
- No se agrega ninguna variable para desactivar la validación.

## Escenarios (BDD)

1. **Certificado válido.** Servidor con un certificado firmado por una autoridad de confianza y nombre correcto → el email sale.
2. **Certificado autofirmado o de otra autoridad.** → el envío falla por certificado no verificable; el servidor no recibe `AUTH` ni el mensaje.
3. **Nombre que no coincide.** Certificado válido pero emitido para otro host → falla igual.
4. **Cuenta de materia.** Una materia con cuenta propia y certificado inválido → falla; otra materia con la cuenta global válida → sigue enviando.
5. **Sin usuario (servidor local).** `localhost:25` sin autenticación → sigue enviando sin TLS, sin regresión.
6. **`EMAIL_MODO=consola`.** → no abre conexión, sin cambios.
7. **Error visible.** Cuando falla por certificado, el log lo dice sin imprimir la contraseña ni el cuerpo del email.

## Fuera de alcance

SSL directo en el puerto 465 (el código solo implementa STARTTLS en el 587); autenticación por OAuth2; SPF/DKIM/DMARC del dominio remitente; fijar (pinning) el certificado de un proveedor concreto.

## Notas para `/implement-us`

- **Qué almacén de certificados usar es una decisión de diseño, no un detalle.** Con `ssl.create_default_context()` solo, el resultado depende del sistema: en la imagen Docker (Debian) hay `ca-certificates`, pero en una Mac con Python de python.org no, y los tests locales fallarían. Se propone `ssl.create_default_context(cafile=certifi.where())`, ya que `certifi` es dependencia transitiva (está en `uv.lock`) y da el mismo resultado en la Mac, en la imagen y en CI. Si se usa, declararlo como dependencia directa en `pyproject.toml`. Confirmar con Víctor al planificar.
- Los tests no deben depender de internet: usar un servidor SMTP de prueba con TLS y certificados generados en el test (uno válido contra una autoridad de prueba inyectada, uno autofirmado) en lugar de Gmail.
- Verificar que el fake SMTP de la UAT (`tests/uat`, Capa 2) usa `localhost:25` sin usuario; si alguno usa usuario, el caso 5 aplica y hay que revisarlo.
- Actualizar `docs/plans/DESPLIEGUE-GCP.md` Paso 11b (quitar el "límite conocido") y `scripts/probar_smtp.py` si compara con el comportamiento anterior.
- Mantener la sincronía de los `Fake*` de `tests/unit/` si se toca algún puerto (aquí no se espera).
