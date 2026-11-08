# US-8.3.3: Observabilidad mínima — logs estructurados y healthcheck de readiness

**Estado**: `Implementada`
**Iteracion / Sprint**: `Incremento 9 — Correcciones y robustez`, Iteración 3 (nació en el Incremento 8, Iteración 3, y se movió porque no depende de la nube)
**Tipo**: `mejora de operación` backend (infraestructura compartida)
**Agregado principal afectado**: ninguno
**Bounded Context**: transversal (`shared`) y la aplicación (`src/app.py`)
**Origen**: plan del Incremento 8 (`docs/plans/inc8/inc8-candidatas.md`); decisiones de Víctor del 2026-11-08 sobre el formato de los logs y la convivencia con `/health`.
**Issue**: [#526](https://github.com/vvalotto/cognion/issues/526)
**Interactúa con**: `US-ADJ-64` y `US-ADJ-68` (enmascarado de tokens en el log), `US-8.5.2` (email por consola, se lee en el log), `deploy/gcp/` (`docker-compose.yml`, `cognion.sh estado`).

---

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar Cognión**,
quiero **saber si la aplicación está viva y si realmente puede atender pedidos, y poder leer sus logs con una herramienta**,
para **distinguir "el proceso está en pie" de "la base de datos no responde", y diagnosticar un incidente sin leer texto suelto a ojo**.

---

## Contexto

Hoy `GET /health` solo responde `{"status": "ok"}`: dice que el proceso está vivo, pero no mira la base de datos. Si PostgreSQL se cae, `/health` sigue en `ok` y el operador se entera por los usuarios. `docker-compose.yml` de GCP lo usa como healthcheck de la app y `cognion.sh estado` también lo consulta.

Los logs son texto (`INFO:     mensaje`), cómodos en la terminal local (el modo consola de emails depende de leerlos ahí), pero difíciles de filtrar o procesar con una herramienta cuando la aplicación esté desplegada.

## Decisiones tomadas (Víctor, 2026-11-08)

- **`/health` no cambia.** Sigue siendo el chequeo de que el proceso está vivo, sin tocar la base; el healthcheck de Docker y el arranque de Caddy siguen igual.
- **Endpoint nuevo `GET /health/ready`** que comprueba la base de datos. `cognion.sh estado` muestra los dos.
- **Logs: variable `LOG_FORMAT=texto|json`, por defecto `texto`.** En local nada cambia; en un despliegue se activa con una variable de entorno.
- Sin identificador de pedido ni métricas en esta US.

## Especificacion del comportamiento

**Readiness.**
- `GET /health/ready` ejecuta un `SELECT 1` contra la base con un tiempo máximo corto (2 s).
- Con la base disponible responde `200` con `{"status": "ok", "base_de_datos": "ok"}`.
- Si la base no responde, falla o supera el tiempo, responde `503` con `{"status": "error", "base_de_datos": "no disponible"}`. El cuerpo **no** incluye el motivo, la URL ni credenciales; el error real se escribe en el log (`ERROR`) sin la contraseña.
- No requiere autenticación, igual que `/health` (el healthcheck de Docker y el operador no tienen JWT). Bajo `/api` en el servidor integrado (`/api/health/ready`).
- `/health` y `/health/ready` no cambian ningún otro endpoint.

**Logs estructurados.**
- Nueva variable `LOG_FORMAT` con valores `texto` (por defecto) y `json`; cualquier otro valor hace fallar el arranque con un mensaje claro (como el resto de `settings`).
- Con `texto` el comportamiento es exactamente el actual.
- Con `json` cada registro sale como **un objeto JSON por línea** con `ts` (ISO 8601, UTC), `nivel`, `logger` y `mensaje`; si el registro trae una excepción, además `excepcion` con el traceback como texto (sigue siendo una sola línea JSON).
- El formato alcanza a los logs de la aplicación (`src.*`) y a los de `uvicorn` (`uvicorn.access` y `uvicorn.error`).
- **El enmascarado de tokens se conserva en ambos formatos**: ningún JWT, token de invitación o de recuperación aparece en una línea JSON, ni en `mensaje` ni en `excepcion`.
- `.env.example`, `deploy/gcp/.env.example` y las guías de despliegue documentan la variable.

## Escenarios (BDD)

1. **`/health` no cambia.** Responde `200 {"status": "ok"}` sin tocar la base, incluso con la base caída.
2. **Readiness con la base disponible.** `GET /health/ready` responde `200` con `base_de_datos: ok`.
3. **Readiness con la base caída.** Responde `503` con `base_de_datos: no disponible`, sin el motivo, la URL ni la contraseña; el error queda en el log.
4. **Readiness sin credenciales.** Responde igual sin `Authorization`.
5. **Formato `texto` por defecto.** Sin `LOG_FORMAT`, las líneas son las de hoy (`INFO:     ...`).
6. **Formato `json`.** Con `LOG_FORMAT=json`, cada línea del log de la aplicación y de `uvicorn` es un JSON válido con `ts`, `nivel`, `logger` y `mensaje`.
7. **Excepciones en `json`.** Un registro con excepción sigue siendo una sola línea JSON y trae `excepcion`.
8. **Tokens enmascarados en `json`.** Un pedido con `?token=<JWT>` o a `/identidad/invitaciones/<token>` deja `***` en la línea JSON, no el token.
9. **Valor inválido.** `LOG_FORMAT=xml` impide arrancar y el mensaje nombra la variable y los valores posibles.
10. **`cognion.sh estado`.** Muestra la respuesta de `/api/health` y la de `/api/health/ready`; si la segunda es `503`, el comando lo indica sin ocultar la primera.

## Fuera de alcance

Identificador de pedido (correlación entre líneas), métricas, trazas, alertas, rotación de logs; que el healthcheck de Docker o `desplegar.sh` pasen a usar `/health/ready` (queda para cuando se retome el despliegue en la nube); cambiar el nivel de log por módulo.

## Notas para `/implement-us`

- **Dónde va el formato:** `src/shared/frameworks/logging_config.py` ya tiene `configurar_logging(nivel)`, el filtro `FiltroTokens` y `_HandlerCognion`. Agregar un `FormateadorJson` y pasar `formato` desde `settings`; los handlers de `uvicorn` ya existen, así que en modo `json` se les cambia el formatter en vez de crear otros.
- **El filtro no alcanza para JSON:** `FiltroTokens` sanea `msg` y `args` de los loggers de `uvicorn`; el formateador debe volver a enmascarar el mensaje ya formateado y el traceback, que pueden traer un token.
- **Readiness:** usar `SessionLocal` de `src/shared/frameworks/db.py` y `asyncio.wait_for` para el tiempo máximo; no pasar por las dependencias de los BC. Probar el `503` apuntando la sesión a una base inexistente o con una excepción inyectada, sin tocar la base de desarrollo.
- **Pruebas con proceso real:** `ServidorReal` (`tests/integration/inc8/_servidor_real.py`) arranca `uvicorn` como subproceso y permite fijar variables de entorno; sirve para los escenarios de `uvicorn.access` en `json`. Esos tests exigen una base descartable inline.
- **`cognion.sh estado`** vive en `deploy/gcp/`; se puede probar su salida con un `curl` simulado o separando la función que arma el resumen.
- **Mantener la sincronía de los `Fake*`** si se toca algún puerto (aquí no se espera).
- Verificación al cierre de la iteración, en navegador o con `curl`: `/api/health` y `/api/health/ready` con la aplicación levantada en un servidor real.
