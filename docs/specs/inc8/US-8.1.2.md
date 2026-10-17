# US-8.1.2: URL base de API y WebSocket del frontend resuelta en build

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.1`
**Tipo**: `infra frontend` (técnica — sin cambio visible)
**Bounded Context**: transversal (`frontend/src/lib/`)
**Issue**: #515

---

## Descripcion (lenguaje de negocio)

Como **responsable de operar el sistema**,
quiero **que el frontend compilado hable con la API y el WebSocket del origen correcto, con HTTPS/WSS en producción**,
para **desplegar en Fly.io (`ADR-021`, `ADR-024`) sin editar código ni tener contenido mixto**.

---

## Contexto

`api-client.ts` y `canal-sesion-en-vivo.ts` repiten `import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"`.
Un build de producción sin la variable apuntaría a `localhost:8000`. La conversión `http→ws` / `https→wss`
(`replace(/^http/, "ws")`) ya funciona pero está duplicada y no resuelve bases relativas.

## Especificacion del comportamiento

- Módulo único `frontend/src/lib/config.ts`:
  - `resolverApiBaseUrl(envUrl, esProduccion, origen)`: si `envUrl` está definida y no vacía la usa
    (absoluta, o relativa como `/api`, resuelta contra `origen`); si no, en producción usa `origen`
    (mismo origen, `US-8.1.6`) y en desarrollo `http://localhost:8000`. Sin barra final.
  - `aUrlWebSocket(baseHttp)`: `http→ws`, `https→wss`.
  - Constantes `API_BASE_URL` y `WS_BASE_URL` evaluadas una vez.
- `api-client.ts` y `canal-sesion-en-vivo.ts` consumen esas constantes; se elimina la duplicación.
- `Dockerfile`: `ARG VITE_API_BASE_URL` opcional en la etapa del frontend (vacío = mismo origen).
- `frontend/.env.example` documenta el comportamiento.

## Escenarios (BDD)

1. Con `VITE_API_BASE_URL=https://api.x.fly.dev/` → base `https://api.x.fly.dev`, WebSocket `wss://api.x.fly.dev`.
2. Sin variable en producción en `https://app.fly.dev` → base `https://app.fly.dev`, WS `wss://app.fly.dev`.
3. Sin variable en desarrollo → `http://localhost:8000` / `ws://localhost:8000`.
4. `VITE_API_BASE_URL=/api` desde `http://10.0.0.5:5173` → `http://10.0.0.5:5173/api` / `ws://10.0.0.5:5173/api`.

## Fuera de alcance

Servir el frontend desde la imagen (`US-8.1.6`); CORS (`US-8.1.1`).

## Fuente de verdad UX

No aplica — sin cambios visuales ni de pantallas; refactor de configuración de red.
