# US-8.1.6: Servir el frontend compilado desde la misma imagen y el mismo origen

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.1`
**Tipo**: `infra backend/frontend` (técnica — sin cambio visible)
**Bounded Context**: transversal (`src/servidor.py`, `Dockerfile`, `fly.toml`)
**Issue**: #519

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **que una sola imagen sirva el frontend y la API desde el mismo origen**,
para **desplegar una única aplicación en Fly.io (`ADR-021`, `ADR-024`) sin CORS, sin contenido mixto y con un solo certificado**.

---

## Contexto

- La imagen ya compila el frontend (`frontend/dist`) pero nada lo sirve: `src/app.py` solo expone la API.
- **Colisión de rutas:** la API no tiene prefijo y comparte rutas con el frontend (`/materias`, `/comisiones`,
  `/actividades`…). Servir ambos en la raíz haría que recargar o abrir un link a `/materias` devolviera JSON.
- El proxy de desarrollo de Vite ya usa `/api` (se reescribe quitando el prefijo): este es el mismo contrato.

## Especificacion del comportamiento

- Nuevo `src/servidor.py` con `crear_servidor(directorio_frontend)`:
  - monta la API existente (`src.app.app`, **sin cambios**) bajo `/api`;
  - sirve `frontend/dist` en `/`; para rutas del SPA sin archivo (sin extensión) devuelve `index.html`;
  - una ruta con extensión que no existe (`/assets/x.js`) responde 404, no `index.html`;
  - si `frontend/dist` no existe (desarrollo), solo monta la API.
  - El `lifespan` de la API (background task de vencimientos, `US-3.2.4`) debe seguir corriendo: Starlette no
    ejecuta el `lifespan` de una app montada, así que el servidor lo propaga.
- `Dockerfile`: `CMD` arranca `src.servidor:servidor` con `--proxy-headers --forwarded-allow-ips="*"` (detrás de Fly
  las redirecciones deben conservar `https`); `ARG VITE_API_BASE_URL` pasa a valer `/api` por defecto.
- `fly.toml`: el healthcheck pasa a `/api/health`.
- El WebSocket (`/api/sesiones-en-vivo/{id}/canal`) funciona bajo el montaje; `WS_BASE_URL` (`US-8.1.2`) ya lo resuelve.
- `src/app.py` y los tests existentes no cambian (siguen usando la API sin prefijo).

## Escenarios (BDD)

1. `GET /` y `GET /materias/123` (ruta del SPA) → `index.html`.
2. `GET /assets/app.js` existente → el archivo; inexistente → 404.
3. `GET /api/health` → `{"status": "ok"}`; `GET /api/materias` → respuesta de la API (401 sin token), no `index.html`.
4. Sin directorio de frontend → `/` responde 404 y `/api/health` sigue funcionando.
5. El `lifespan` de la API se ejecuta al arrancar el servidor.
6. Un WebSocket a `/api/...` se enruta a la API.

## Fuera de alcance

CD y staging (`US-8.2.x`); caché HTTP avanzada y compresión.

## Fuente de verdad UX

No aplica — sin cambios visuales ni de pantallas.
