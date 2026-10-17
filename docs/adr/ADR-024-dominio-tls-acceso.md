# ADR-024 — Dominio, TLS y política de acceso: subdominio de fly.dev

**Estado:** En revisión (2026-10-17) — depende de `ADR-021`
**Fecha:** 2026-10-16
**Origen:** `US-8.0.4` (Issue #513), Incremento 8. Depende de `ADR-021`.

---

## Contexto

Hace falta una URL estable para el frontend y la API, con TLS (HTTPS/WSS) y un origen conocido
para CORS. El piloto no justifica trámites institucionales ni costo de dominio.

## Opciones Consideradas

- **Subdominio institucional UNER** — descartada por ahora: requiere gestión con sistemas.
- **Dominio propio** — descartada: costo y trabajo de DNS sin necesidad en el piloto.
- **Subdominio de `fly.dev`** — elegida.

## Decisión

Producción y staging se publican bajo subdominios de `fly.dev` con TLS automático de Fly.io. El
frontend se sirve desde el mismo origen que la API (`US-8.1.6`), lo que simplifica CORS y evita
contenido mixto: HTTP→HTTPS y WS→WSS. `allow_origins` se configura por entorno (`US-8.1.1`).

## Consecuencias

- ✅ Cero trámites, TLS y WSS incluidos.
- ⚠️ La URL no es institucional; migrar a dominio UNER/propio es un cambio de configuración, no
  de código.
- ⚠️ La entregabilidad de email no depende del dominio de la app (ver `ADR-023`).

## Revisión 2026-10-17

Queda en revisión junto con `ADR-021`: el subdominio de `fly.dev` solo aplica si finalmente se usa Fly.io. En el
despliegue local (`US-8.5.x`) el acceso es por IP o nombre `.local` de la red del aula, sin TLS, con el frontend y
la API servidos desde el mismo origen (`US-8.1.6`).

