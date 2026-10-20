# ADR-025 — Despliegue de prueba en GCP: VM gratuita con la aplicación y PostgreSQL juntos

**Estado:** Propuesto (borrador de `US-8.6.1`, Issue #545) — se completa decisión por decisión y pasa a Aceptado al cerrar el spike
**Fecha:** 2026-10-20
**Origen:** `US-8.6.1`, Iteración 6 del Incremento 8. Relacionado con `ADR-021` y `ADR-024` (Fly.io, en revisión), `ADR-022` (backup) y `ADR-023` (SMTP).

---

## Contexto

Víctor eligió el 2026-10-19 desplegar una **prueba de uso** en una VM `e2-micro` de la capa gratuita de GCP, con su cuenta
personal, con la aplicación y PostgreSQL juntos (opción A de `docs/plans/inc8/inc8-candidatas.md` §Iteración 6). Cuatro
cuestiones condicionan el resto de la iteración y se resuelven una por una, con Víctor presente.

## Decisión 1 — Dominio y HTTPS: subdominio gratuito de DuckDNS (2026-10-20)

**Opciones consideradas:**
- **`sslip.io`** (el nombre contiene la IP): descartada. Los certificados de Let's Encrypt comparten el límite entre todos
  los usuarios de ese dominio y hay reportes de bloqueos.
- **Túnel de Cloudflare**: descartada. Sin dominio propio la URL cambia en cada reinicio; con URL estable exige un dominio, y
  suma otro proceso en 1 GB de RAM. No se verificó el paso de WebSockets.
- **Dominio propio**: viable y la más estable, pero Víctor no tiene uno ni quiere pagarlo para una prueba.
- **Subdominio gratuito de DuckDNS**: elegida.

**Decisión:** la prueba se publica bajo un subdominio de DuckDNS, con certificado automático de Let's Encrypt gestionado por
el proxy HTTPS de la VM.

**Justificación:** costo cero, nombre estable y fácil de dictar a los alumnos, y la VM tiene IP pública estática, así que la
validación por HTTP funciona con los puertos 80/443 abiertos. El riesgo de depender de un servicio gratuito de terceros es
aceptable en una prueba acotada.

**Notas y límites:**
- Sin HTTPS no se usa con alumnos reales: contraseñas y tokens viajarían sin cifrar y el botón "Copiar link" de invitación
  (`navigator.clipboard`, solo en contexto seguro) probablemente fallaría. Con `http://<IP>` se puede probar para uso propio.
- No se verificó si `duckdns.org` comparte el límite de certificados que sí afectó a `sslip.io`; con un solo certificado es
  poco probable que moleste. Si se migra a un dominio propio, el cambio es de configuración, no de código.
- La URL de la prueba alimenta `FRONTEND_URL` y `CORS_ALLOWED_ORIGINS` (mismo origen, `US-8.1.6`).

## Decisión 2 — Modo de email y `ENTORNO`: emails en el log, `ENTORNO=local` (2026-10-20)

**Opciones consideradas:**
- **Emails reales con SMTP y `ENTORNO=staging`**: descartada para esta primera prueba. Exige una cuenta SMTP y verificar que
  la VM pueda enviar: según el conocimiento general (no verificado en esta sesión) GCP bloquea por defecto el puerto 25
  saliente, el código solo implementa STARTTLS en el puerto 587 con usuario y clave (no SSL directo en el 465), y no se sabe
  si el servidor institucional de `ADR-023` acepta conexiones desde una IP de Google.
- **Emails en el log con `EMAIL_MODO=consola` y `ENTORNO=local`**: elegida.

**Decisión:** la VM corre con `ENTORNO=local` y `EMAIL_MODO=consola`. Ningún email sale; su contenido (con los links de token)
queda en el log INFO de la aplicación.

**Justificación:** no depende de una cuenta SMTP ni del bloqueo de puertos, y la configuración ya está probada en la máquina
de Víctor (`US-8.5.1`/`8.5.2`). La primera prueba se hace con cuentas de prueba o un grupo chico.

**Consecuencias asumidas:**
- Los alumnos **no pueden recuperar su contraseña por su cuenta**: Víctor lee el link en el log por SSH y se lo pasa.
- **No llegan los avisos de actividad** nueva o cerrada (RF-14); solo quedan en el log.
- Las **invitaciones** siguen funcionando: la pantalla muestra el link y, con HTTPS (decisión 1), el botón "Copiar link" anda.
- Los **tokens quedan en el log**: solo los lee quien entra a la VM. Por eso esta configuración no se usa con una cuenta
  abierta a terceros ni se comparte el log.
- `ENTORNO=local` valida solo el secreto (≥32 caracteres, distinto del ejemplo), no las URLs ni CORS. La base de datos puede
  estar en `localhost`, lo que deja abierta la decisión 3 (PostgreSQL nativo o en contenedor).
- Pasar a emails reales (`ENTORNO=staging` + SMTP) queda como mejora para una segunda prueba; es cambio de configuración, no
  de código, salvo que el servidor institucional exija SSL directo.

## Decisión 3 — Contenedores o procesos nativos en 1 GB de RAM

*Pendiente.*

## Decisión 4 — Alcance de datos y cuenta de la prueba

*Pendiente.*

## Impacto en Configuración

*Se completa al cerrar las cuatro decisiones.*
