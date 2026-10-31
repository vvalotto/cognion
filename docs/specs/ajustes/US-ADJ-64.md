# US-ADJ-64: Logging local — los emails de consola se ven y los tokens no quedan completos en el log

**Estado**: `Implementada`
**Iteracion / Sprint**: `Incremento 8 — Despliegue y operación`, Iteración 8 (ajustes de la UAT de `v0.9.0`)
**Tipo**: `fix` backend (configuración de logging, infraestructura transversal)
**Agregado principal afectado**: ninguno
**Bounded Context**: transversal (`src/shared/frameworks/`)
**Origen**: UAT `US-8.7.2`, hallazgos #2 y #9 (`quality/reports/uat/inc8/registro-hallazgos.md`).
**Issue**: [#570](https://github.com/vvalotto/cognion/issues/570)
**Interactúa con**: `US-8.5.2` (`EMAIL_MODO=consola`), `US-6.1.1` (el canal WebSocket autentica por parámetro `token`), `US-ADJ-26`/`US-1.1.1` (links de invitación).

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **Docente que usa Cognión en su propia máquina, sin servidor de correo**,
quiero **ver en el log del servidor los emails que el sistema "enviaría" (recuperar contraseña, invitaciones, avisos de actividad)**
y **que ese mismo log no guarde completos los tokens de acceso de las personas**,
para **poder recuperar una cuenta sin depender del correo y que nadie que lea el log pueda reutilizar una sesión**.

---

## Contexto

### Problema 1 (hallazgo #2, 🔴): el modo consola no escribe nada

`src/shared/frameworks/smtp.py:82` deja el email completo con `logger.info(...)`. La aplicación **no configura el logging**: no hay
`basicConfig` ni `dictConfig` en `src/`, y `uvicorn` solo configura sus propios loggers. Los `INFO` de la aplicación se descartan, así que
la recuperación de contraseña, los links de invitación por email y las notificaciones de apertura y cierre (RF-14) no se ven en ningún lado,
contra lo que prometen la spec de `US-8.5.2`, el aviso de `levantar.sh` y `DESPLIEGUE-LOCAL.md` §7. El test de `US-8.5.2` pasaba porque
`caplog` captura el mensaje aunque el servidor real no lo muestre.

### Problema 2 (hallazgo #9, 🟡): tokens completos en el log de acceso

`uvicorn` registra la URL completa de cada pedido. Quedan escritos **el JWT de sesión** (`.../canal?token=<JWT>`, 98 líneas en la UAT) y **el
token de invitación** (`GET /registro?token=…`). El JWT es válido 60 minutos y la invitación, 7 días o hasta usarse.

### Decisión de diseño

Un módulo `src/shared/frameworks/logging_config.py` con `configurar_logging()`, invocado una sola vez al importar la aplicación
(`src/app.py`, que usan tanto `src.app:app` como `src.servidor:servidor`):
- nivel `INFO` para los loggers de `src` (configurable con la variable `LOG_LEVEL`, por defecto `INFO`) con el mismo formato que usa uvicorn;
- un filtro sobre `uvicorn.access` y `uvicorn.error` que reemplaza el valor de `token=` por `token=***` en el mensaje y en los argumentos;
- no se toca el nivel de las bibliotecas de terceros (SQLAlchemy y demás siguen en `WARNING`).

El contenido del email de consola **conserva el link completo**: es el objetivo del modo consola. Solo se enmascaran las URL de acceso.

---

## Especificacion del comportamiento

- Con `EMAIL_MODO=consola`, cada email que el sistema "envía" aparece en la salida del servidor con destinatario, asunto y cuerpo (links incluidos).
- Ninguna línea del log de acceso contiene el valor de un parámetro `token`: se escribe `token=***`.
- El formato y el resto de las líneas de uvicorn no cambian.
- `LOG_LEVEL` (opcional, `DEBUG|INFO|WARNING|ERROR`) ajusta el nivel de los loggers de `src`; un valor inválido falla al arrancar con un mensaje claro.
- Aplica igual con `ENTORNO=local`, `staging` y `produccion`.

## Escenarios (BDD)

1. **Recuperar contraseña en modo consola.** Servidor real (proceso `uvicorn src.servidor:servidor` contra una base descartable, con `EMAIL_MODO=consola`); un `POST /identidad/recuperar-password/solicitar` con el email de una cuenta existente → la salida del proceso contiene `Email (modo consola)`, el destinatario y el link `/recuperar-password/<token>`.
2. **Invitación por email en modo consola.** Generar una invitación indicando `email_destinatario` → su token aparece en la salida (el email trae el token suelto, no un link: se verificó al implementar).
3. **Aviso de actividad.** Crear una actividad con comisiones → el aviso de apertura aparece en la salida (RF-14).
4. **El JWT no queda en el log.** Abrir un WebSocket con token → la línea de acceso contiene `token=***` y no el JWT.
5. **La invitación y el link de recuperación no quedan en el log.** `GET /registro?token=<token>` → la línea de acceso contiene `token=***`; `GET /recuperar-password/<token>` → `/recuperar-password/***` (ampliación decidida en la Fase 2).
6. **Lo demás no cambia.** Un `GET /api/health` se registra con el mismo formato de siempre.
7. **`LOG_LEVEL` inválido.** `LOG_LEVEL=ruidoso` → el arranque falla con un mensaje que lista los valores válidos.
8. **Sin fugas por otras rutas.** Con un error de autenticación del WebSocket (token inválido) tampoco aparece el valor del token en la línea de rechazo.

## Fuera de alcance

Cambiar el mecanismo de autenticación del WebSocket (enviar el token en un subprotocolo en vez de la URL); rotación o envío de logs a un servicio externo; el formato JSON estructurado de logs.

## Notas para `/implement-us`

- El test del escenario 1 **no puede usar `caplog`**: debe leer la salida real de un proceso `uvicorn`.
- Ejecutar las pruebas de integración y BDD solo contra una base descartable (`DATABASE_URL` inline), nunca `cognion_local` ni `cognion_uat`.
- Actualizar `docs/plans/DESPLIEGUE-LOCAL.md` §7 con el resultado verificado.
