# Architecture Documentation — Cognión

## Propósito

Esta carpeta concentra la **descripción arquitectónica vigente** de Cognión: cómo está
estructurada la solución, cuáles son sus componentes principales, cómo colaboran entre sí y qué
restricciones de diseño deben preservarse a medida que el sistema evoluciona.

No reemplaza a `docs/rf/ARQ_v1.md` (arquitectura de referencia inicial, histórica) ni a
`docs/adr/` (el *por qué* de cada decisión) — los organiza desde una perspectiva arquitectónica
descriptiva y se mantiene actualizada por incremento, mientras que ARQ_v1 no se modifica
retroactivamente.

## Alcance

Describe:

- la visión estructural del sistema (contexto, contenedores);
- la descomposición en Bounded Contexts (a medida que cada uno se modela — ver Iteración 0 en
  `docs/rf/PLAN_v1.md`);
- las interacciones relevantes entre BCs;
- las preocupaciones transversales de arquitectura;
- la vista de despliegue.

No documenta el razonamiento histórico de cada decisión (eso vive en `docs/adr/`) ni el
modelado de dominio detallado por BC (eso vive en `docs/design/domain/`).

## Relación con otras carpetas

- `docs/adr/` — registra **por qué** se tomó una decisión arquitectónica.
- `docs/design/domain/` — modelo de dominio por BC (event storming, agregados, eventos).
- `docs/architecture/` — describe **cómo queda la solución** a partir de esas decisiones y
  modelos.

Regla práctica: si el documento justifica una decisión, va en `adr/`; si modela dominio de un
BC, va en `design/domain/`; si describe la arquitectura actual del sistema, va aquí.

## Cómo crece esta carpeta

A diferencia de `docs/adr/` (que se extrajo completo desde el arranque), las vistas de esta
carpeta se completan **incrementalmente**:

- Las vistas globales (`01-system-context.md`, `02-container-view.md`) se escriben una vez,
  antes del Incremento 0, porque no dependen de ningún BC en particular.
- Las vistas por BC (`1X-bc-<nombre>.md`) se escriben en la Iteración 0 — Modelado del
  incremento que introduce o extiende ese BC (ver `docs/rf/PLAN_v1.md`), junto al event storming
  correspondiente — no todas de una vez.

## Estructura actual de esta carpeta

```text
docs/architecture/
  README.md                          ← este documento
  _plantilla-vista.md                ← plantilla de cada vista (Incremento 10.1)
  01-system-context.md               ← C4-1 (corregido, Fase 1)
  02-container-view.md               ← C4-2 (corregido, Fase 1)
  03-bounded-contexts.md             ← catálogo de BC (corregido, Fase 2)
  10-componentes-identidad.md        ← C4-3, pendiente (Fase 2, PR 2b)
  11-componentes-banco-preguntas.md  ← C4-3, creado
  12-componentes-actividad-evaluativa.md ← C4-3, pendiente (Fase 2, PR 2b)
  13-componentes-analytics.md        ← C4-3, creado
  14-componentes-notificaciones.md   ← C4-3, creado
  20-context-map-integrations.md     ← corregido (Fase 2)
  24-modelo-datos-postgresql.md      ← a completar (Fase 3)
  24a-modelo-datos-identidad.md            ← a corregir (Fase 3)
  24b-modelo-datos-banco-preguntas.md      ← creado
  24c-modelo-datos-actividad-evaluativa.md ← creado
  30-runtime-interactions.md         ← pendiente (Fase 3)
  40-cross-cutting-concerns.md       ← pendiente (Fase 4)
  50-development-view.md             ← pendiente (Fase 4)
  60-deployment-view.md              ← pendiente (Fase 4)
```

El plan por fases, el relevamiento de brechas y el método de verificación contra el código están en
`docs/plans/inc10-1/inc10-1-relevamiento-y-plan.md` (Incremento 10.1, documental, sin US).

## Principios de documentación

- Descriptivos, no aspiracionales, salvo que se indique explícitamente arquitectura objetivo.
- No duplicar texto completo ya existente en `adr/` o `design/domain/` — enlazar la fuente.
- Separar vista estática, vista dinámica y preocupaciones transversales.
- Acompañar cada vista con el diagrama mínimo necesario (Mermaid, C4).

## Mantenimiento

Cuando cambie la estructura de esta carpeta, actualizar en conjunto: este índice y los enlaces
cruzados desde `docs/inventario/DOCUMENTATION-MAP.md` y `CLAUDE.md` si corresponde.
