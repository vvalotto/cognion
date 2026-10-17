# ADR-021 — Destino de despliegue de producción: Fly.io

**Estado:** En revisión (2026-10-17) — standby hasta saber si se puede usar el convenio de la Universidad con Google
**Fecha:** 2026-10-16
**Origen:** `US-8.0.1` (Issue #510), Incremento 8 — Despliegue y operación.

---

## Contexto

`ARQ_v1.md` dejó abierta la infraestructura de producción (nube vs. servidor institucional
FIUNER). Fly.io ya es el destino de testing/staging. El uso real previsto en el corto plazo es
una **comisión piloto**: datos reales de estudiantes, escala chica, tolerancia a una ventana de
mantenimiento. Equipo unipersonal (driver 4 de `ARQ_v1.md`).

## Opciones Consideradas

- **Servidor FIUNER** — descartada por ahora: obliga a operar VM, TLS, red, backups y acceso sin
  equipo de soporte, y puede depender de trámites institucionales fuera del control del proyecto.
- **Fly.io ahora, FIUNER después** — absorbida por la opción elegida: el diseño se mantiene
  portable, así la migración queda abierta sin comprometerla.
- **Fly.io como producción** — elegida.

## Decisión

Producción se despliega en **Fly.io**, mismo proveedor que staging. Postgres administrado,
secrets nativos y TLS/WSS incluidos. Se mantiene la portabilidad: el artefacto es una imagen
Docker configurada solo por variables de entorno, sin dependencias específicas de Fly.io en el
código de la aplicación.

## Consecuencias

- ✅ Staging y producción espejo; WSS real sin infraestructura propia.
- ✅ Desbloquea `US-8.0.2` (backup sobre Postgres de Fly.io), `US-8.0.3` y `US-8.0.4`.
- ⚠️ La residencia del dato queda fuera de la institución; **revisar** si FIUNER lo exige al
  pasar de piloto a cursada completa.
- ⚠️ Costo recurrente de Fly.io (app + Postgres) a presupuestar.

## Revisión 2026-10-17

- **Standby:** se pospone la elección de nube hasta saber si la Universidad ofrece un convenio con Google Cloud
  (créditos o exigencias de residencia de datos). Hasta entonces el sistema se usa en red local (`US-8.5.x`).
- **Supuesto incorrecto:** este ADR y `ARQ_v1.md` hablan de "Postgres administrado sin overhead" en Fly.io. Hoy el
  `fly postgres` está deprecado (sin mantenimiento ni soporte) y lo administrado es *Managed Postgres*, desde
  unos 38 USD/mes más disco. Con esto la ventaja de costo de Fly.io para el piloto desaparece.
- **Alternativas relevadas** (precios y límites de las páginas oficiales al 2026-10-17): Neon (plan gratis con 1 GB
  y 100 horas de cómputo; Launch por uso; región São Paulo), Supabase (descartada: el plan gratis se pausa y no
  tiene backups), Cloud SQL (sin capa gratuita; las instancias compartidas más chicas quedan fuera del SLA),
  Cloud Run (el canal WebSocket en memoria y el verificador de vencimientos obligan a una sola instancia y CPU
  siempre asignada) y una VM e2-micro gratuita (solo regiones de EE.UU., 1 GB de RAM).
- Se mantiene Postgres como motor (`ADR-004`): el código usa JSONB, UUID nativo y `ON CONFLICT`.

