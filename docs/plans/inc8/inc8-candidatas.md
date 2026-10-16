# Incremento 8 — Despliegue y operación

**Estado:** en curso desde 2026-10-16. Iteración 0 (spikes) resuelta: `ADR-021` (Fly.io), `ADR-022` (backup pg_dump → Drive), `ADR-023` (SMTP por materia), `ADR-024` (dominio fly.dev).
**Milestone:** [Incremento 8 — Despliegue y operación](https://github.com/vvalotto/cognion/milestone/16)
**Política:** sin BC nuevo ni RF funcional nuevo — no abre con Iteración 0 de Modelado. Abre
con una iteración de **spikes de decisión** (infraestructura, backup, SMTP, dominio), porque
sin ellas el resto no se puede especificar.

## Origen

Los Incrementos 0 a 7 (+ ADJ) construyeron y validaron el producto, pero ninguno definió cómo se
**empaqueta, instala, configura y opera** en un entorno de uso final. Hoy:

- `cd.yml` solo construye la imagen Docker; migraciones, `flyctl deploy` y healthcheck
  post-deploy están comentados.
- `src/app.py` tiene CORS fijo a `http://localhost:5173`; el frontend usa
  `VITE_API_BASE_URL ?? "http://localhost:8000"` (HTTP y WebSocket).
- No hay procedimiento de bootstrap del primer Administrador, ni de backup/restore, ni runbook.
- `docs/plans/CHECKLIST-INSTALACION.md` cubre solo el entorno de **desarrollo**.
- El RNF de Administrabilidad (`RNF_v1.md` Escenario 2: backup mensual, retención 12 meses) y el
  checkpoint de staging del RNF de rendimiento con WSS real (`PROCEDIMIENTO-UAT.md` §4) siguen
  sin cubrir. La decisión de infraestructura de producción (`ARQ_v1.md`) sigue abierta.

Decisión de secuencia a confirmar por Víctor: este incremento va **antes o después de RF-07**
(importación PDF, Incremento 7 Iteración 2). Recomendación: antes de cualquier uso con datos
reales de estudiantes, RF-07 puede ir en paralelo o después.

## Alcance

| # | Iteración | Qué | Track |
|---|---|---|---|
| 0 | Decisiones (spikes) | Infraestructura destino, backup, SMTP real, dominio/TLS | Spike (`tipo:spike`), con Víctor presente |
| 1 | Artefacto desplegable | Configuración por entorno, fail-fast, migraciones, bootstrap de Administrador | Formal (`/implement-us`) |
| 2 | Despliegue automático | CD completo, staging, rollback, checkpoint RNF con WSS real | Formal / infraestructura |
| 3 | Operación | Backup y restore, observabilidad, `downgrade` de migraciones | Formal / infraestructura |
| 4 | Entrega e instalación | Guía de instalación, runbook, ensayo de instalación limpia, cierre | Documentación + UAT |

## Iteración 0 — Decisiones

| US | Título | Resuelve |
|---|---|---|
| US-8.0.1 | Spike: destino de despliegue de producción (Fly.io vs servidor FIUNER) | Ítem abierto "Infraestructura definitiva" |
| US-8.0.2 | Spike: estrategia de backup y restauración | RNF Escenario 2 (mensual, 12 meses) |
| US-8.0.3 | Spike: cuenta SMTP real por materia | Ítem abierto "Cuenta de envío SMTP" (RF-14) |
| US-8.0.4 | Spike: dominio, TLS y política de acceso | WSS real, CORS, URL del frontend |

Gate: las cuatro decisiones registradas (ADR donde corresponda) antes de especificar la
Iteración 1 en detalle.

## Iteración 1 — Artefacto desplegable

| US | Título |
|---|---|
| US-8.1.1 | CORS configurable por entorno (`allow_origins` desde settings) |
| US-8.1.2 | URL base de API y WebSocket del frontend resuelta en build (HTTP/HTTPS, WS/WSS) |
| US-8.1.3 | Validación fail-fast de settings de producción (`secret_key`, `database_url`, SMTP) |
| US-8.1.4 | Migraciones Alembic como paso explícito de release (no al arrancar la app) |
| US-8.1.5 | Bootstrap del primer Administrador (comando idempotente, sin contraseña en el repo) |
| US-8.1.6 | Servir el frontend compilado desde el mismo origen (o proxy) y verificarlo en la imagen |
| US-8.1.7 | Cuenta SMTP resuelta por materia con fallback global (`ADR-023`) |

## Iteración 2 — Despliegue automático

| US | Título |
|---|---|
| US-8.2.1 | CD: migraciones + deploy + healthcheck post-deploy habilitados en `main`/tags |
| US-8.2.2 | Entorno de staging espejo del de producción |
| US-8.2.3 | Rollback: volver a la imagen/versión anterior y a su esquema |
| US-8.2.4 | Checkpoint de staging del RNF de rendimiento (≤100 ms, WSS real) — `PROCEDIMIENTO-UAT.md` §4 |

## Iteración 3 — Operación

| US | Título |
|---|---|
| US-8.3.1 | Backup automático mensual con retención de 12 meses |
| US-8.3.2 | Restauración probada desde un backup real (ensayo documentado) |
| US-8.3.3 | Observabilidad mínima: logs estructurados y healthcheck de readiness (base de datos) |
| US-8.3.4 | `alembic downgrade base` funcional (FK sin nombre en `estudiante`) |

## Iteración 4 — Entrega e instalación

| US | Título |
|---|---|
| US-8.4.1 | Guía de instalación en el entorno final (reemplaza el alcance "solo desarrollo" del checklist) |
| US-8.4.2 | Runbook operativo: arranque, parada, rotación de secretos, restauración, incidentes |
| US-8.4.3 | Ensayo de instalación limpia desde cero + UAT de despliegue; cierre como `BL-013` |

## Definition of Done del incremento

1. Una instalación limpia en el entorno de producción elegido, siguiendo solo la guía, queda
   operativa (primer Administrador incluido) sin tocar código.
2. El deploy desde `main`/tag es automático, con healthcheck y rollback ensayado.
3. Backup mensual en ejecución y una restauración probada de punta a punta.
4. Checkpoint de staging del RNF de rendimiento con WSS real, medido.
5. Quality gates del cierre de baseline y UAT de despliegue sin hallazgos 🔴.

## Fuera de alcance

RF-07 (Iteración 2 del Incremento 7), RF-18 (KPIs históricos), multi-inscripción de
estudiantes, issues de deuda técnica #496–#498 y #500–#502 (se priorizan aparte).
