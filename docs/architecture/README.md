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
  01-system-context.md               ← creado
  02-container-view.md               ← creado
  03-bounded-contexts.md             ← pendiente (Iteración 0, Incremento 1)
  1X-bc-<nombre>.md                  ← pendiente, uno por BC modelado
  20-context-map-integrations.md     ← pendiente
  30-runtime-interactions.md         ← pendiente
  40-cross-cutting-concerns.md       ← pendiente
  60-deployment-view.md              ← pendiente
```

## Principios de documentación

- Descriptivos, no aspiracionales, salvo que se indique explícitamente arquitectura objetivo.
- No duplicar texto completo ya existente en `adr/` o `design/domain/` — enlazar la fuente.
- Separar vista estática, vista dinámica y preocupaciones transversales.
- Acompañar cada vista con el diagrama mínimo necesario (Mermaid, C4).

## Mantenimiento

Cuando cambie la estructura de esta carpeta, actualizar en conjunto: este índice y los enlaces
cruzados desde `docs/inventario/DOCUMENTATION-MAP.md` y `CLAUDE.md` si corresponde.
