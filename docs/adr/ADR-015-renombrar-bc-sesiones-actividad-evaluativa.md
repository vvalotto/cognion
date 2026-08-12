# ADR-015 — Renombrar BC "Sesiones" a "Actividad Evaluativa"

**Estado:** Aceptado
**Fecha:** 2026-07-16

---

## Contexto

El BC Core Domain del sistema se llamaba "Sesiones", nombre heredado del vocabulario técnico
de "sesión" (session, en el sentido de infraestructura). Al revisar el catálogo de Bounded
Contexts (`docs/architecture/03-bounded-contexts.md`) antes de arrancar el Incremento 1, el
docente (dueño del lenguaje ubicuo) señaló que el nombre es ambiguo: no comunica que se trata
de una actividad pedagógica evaluativa — suena a "algo que hay que hacer" sin explicar qué. El
BC Sesiones todavía no se modeló (su Iteración 0 es en el Incremento 3) ni tiene código escrito,
por lo que este es el momento de menor costo para corregir el nombre.

## Opciones Consideradas

- **Mantener "Sesión"** — descartada: es el problema que se busca resolver.
- **"Evaluación"** — descartada: colisiona con el propósito general del sistema ("plataforma de
  evaluación universitaria"), se leería como el concepto abstracto de todo el sistema, no como
  la instancia concreta que rinde un estudiante.
- **"Instancia de Evaluación"** — descartada: correcta semánticamente pero más larga sin agregar
  claridad adicional sobre "Actividad Evaluativa".
- **"Actividad Evaluativa"** — elegida: nombra el concepto pedagógico (una actividad de clase de
  naturaleza evaluativa) sin sonar a examen formal únicamente, y cubre ambos modos (en vivo y
  período abierto) igual de bien que "Sesión".

## Decisión

El BC pasa a llamarse **Actividad Evaluativa**. El renombre se aplica tanto al BC como a su
agregado interno y a los eventos de dominio, para no dejar la ambigüedad exactamente donde más
importa (el nombre de la entidad que ejecuta un estudiante):

| Término anterior | Término nuevo |
|---|---|
| BC Sesiones | BC Actividad Evaluativa |
| Agregado `Sesion` | Agregado `ActividadEvaluativa` |
| `SesionEnVivo` | `ActividadEvaluativaEnVivo` |
| `SesionPeriodoAbierto` | `ActividadEvaluativaPeriodoAbierto` |
| `SesionCreada` (evento) | `ActividadEvaluativaCreada` |
| `SesionCerrada` (evento) | `ActividadEvaluativaCerrada` |
| `RespuestaRegistrada` | sin cambio — no lleva el nombre ambiguo |
| `PreguntaAsignada`, `Ranking` | sin cambio — no llevan el nombre ambiguo |

## Justificación

Renombrar antes de modelar (Incremento 3, Iteración 0) evita arrastrar el término ambiguo al
event storming, al código y a los tests. Renombrar solo el BC y dejar el agregado como "Sesión"
hubiera dejado la ambigüedad justo en el concepto central que el BC modela.

## Impacto en Configuración

- No aplica todavía a código — el BC Sesiones no tiene módulo en `src/` (se crea recién en el
  Incremento 3). El paquete se creará directamente como `src/actividad_evaluativa/`.
- Documentos vivos a actualizar ahora: `CLAUDE.md`, `docs/architecture/01-system-context.md`,
  `02-container-view.md`, `03-bounded-contexts.md`, `20-context-map-integrations.md`,
  `docs/traceability/matrix.md`, `docs/plans/PLAN-CM.md`, `docs/plans/WORKFLOW-DESARROLLO.md`.
- Documentos históricos (`docs/rf/RF_v1.md`, `RNF_v1.md`, `ARQ_v1.md`, `PLAN_v1.md`) no se
  reescriben — mantienen "Sesión/Sesiones" en su texto original, con una nota de revisión al
  inicio que remite a este ADR (mismo criterio ya usado para otros ajustes de `PLAN_v1.md`).
- ADRs ya aceptados que usan el término anterior (`ADR-002`, `ADR-003`, `ADR-004`, `ADR-005`,
  `ADR-006`, `ADR-009`, `ADR-010`, `ADR-011`) no se editan — son registro de decisión inmutable;
  su contenido sigue vigente, solo referido ahora al BC con su nuevo nombre.

## Consecuencias

- ✅ El lenguaje ubicuo del Core Domain queda alineado con el dominio pedagógico antes de que
  exista una sola línea de código o modelo de dominio para este BC.
- ⚠️ Los ADRs 002/003/004/005/006/009/010/011 y los documentos históricos siguen usando
  "Sesión/Sesiones" en su texto — quien los lea debe saber (por este ADR) que se refieren al BC
  hoy llamado Actividad Evaluativa. No hay una única fuente que unifique el término en todos
  los documentos del repositorio.
