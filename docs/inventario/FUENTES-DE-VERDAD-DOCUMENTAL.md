# Fuentes de verdad documental — Cognión

> Estado documental: vigente
> Fuente de verdad para: jerarquía documental y autoridad por tema
> Última actualización: 2026-07-14

## 1. Propósito

Define qué documento es autoridad para cada tipo de información del proyecto, y evita que el
mismo hecho se duplique en detalle en varios lugares. Ante contradicción entre documentos, este
archivo decide.

---

## 2. Principio rector

Cada tema tiene una fuente principal. Otros documentos pueden resumirla o enlazarla, pero no
duplicarla en detalle. Orden general de precedencia (ya declarado en `CLAUDE.md`):

1. Código y tests — estado implementado y validado.
2. Baselines (`.cm/baselines/`) — cierres formales de incremento.
3. ADRs (`docs/adr/`) — decisiones arquitectónicas y sus trade-offs.
4. Matriz de trazabilidad (`docs/traceability/matrix.md`) — cobertura RF → BC → Incremento → US → estado.
5. `CLAUDE.md` — estado operativo de trabajo.
6. `README.md` — solo síntesis de entrada.

---

## 3. Fuentes de verdad por tema

| Tema | Fuente de verdad | Documentos secundarios | Regla de uso |
|---|---|---|---|
| Presentación breve del proyecto | `README.md` | `docs/requirements/vision.md` | El README resume; no contiene detalle extenso. |
| Propósito del producto | `docs/requirements/vision.md` | `README.md`, `CLAUDE.md` | El README solo incluye una versión breve. |
| Propósito del ensayo IEDD | `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md` | `CLAUDE.md`, `docs/aprendizajes/HITO-*.md` | La explicación completa vive en `iedd/`, no en el README. |
| Estado operativo actual | `CLAUDE.md` | `README.md`, `docs/traceability/matrix.md`, `.cm/baselines/` | `CLAUDE.md` resume y enlaza evidencia — no la reproduce. |
| Estado validado por baseline | `.cm/baselines/` | `CLAUDE.md`, `README.md` | Las baselines mandan sobre cierres formales de incremento. |
| Workflow vigente de desarrollo | `docs/cm/WORKFLOW-DESARROLLO.md` | `CLAUDE.md`, `docs/cm/PLAN-CM.md` | Si hay diferencia entre `CLAUDE.md` y el workflow, manda el workflow. |
| Política de gestión de configuración | `docs/cm/PLAN-CM.md` | `docs/cm/WORKFLOW-DESARROLLO.md` | El workflow ejecuta la política; no la redefine. |
| Plan de incrementos | `docs/rf/PLAN_v1.md` | `docs/traceability/matrix.md` | Documento histórico de elicitación — no se reescribe retroactivamente; los ajustes de proceso viven en `WORKFLOW-DESARROLLO.md`. |
| Requerimientos funcionales | `docs/rf/RF_v1.md` | `docs/traceability/matrix.md` | Catálogo base — histórico, no se modifica retroactivamente. |
| Atributos de calidad / RNF | `docs/rf/RNF_v1.md` | `docs/rf/ARQ_v1.md`, quality reports | Fuente de escenarios de calidad y medidas acordadas. |
| Arquitectura de referencia (decisión inicial) | `docs/rf/ARQ_v1.md` | `docs/architecture/`, `docs/adr/` | Histórico — arquitectura *vigente* vive en `docs/architecture/` una vez creada; hasta entonces, ARQ_v1 manda. |
| Arquitectura vigente | `docs/architecture/` | `docs/adr/`, `docs/rf/ARQ_v1.md` (histórico una vez que `architecture/` tenga contenido) | Vista técnica principal, se actualiza por incremento. |
| Decisiones arquitectónicas | `docs/adr/` | `docs/architecture/`, `docs/rf/ARQ_v1.md` | Los ADRs registran decisión y trade-offs; no se reescriben, se supersedan con un nuevo ADR. |
| Modelo de dominio por BC | `docs/design/domain/BC-<bc>-modelo.md` | `docs/rf/RF_v1.md`, specs US-IEDD | Producto de la Iteración 0 — Modelado (`PLAN_v1.md`). Se actualiza con refactorings reales del agregado. |
| Diseño UX aprobado | `docs/design/ux/wireframes-*.md` + `docs/design/ux/prototipos/` | specs de US que tocan `frontend/` | Gate obligatorio antes de codear frontend — ver `CLAUDE.md`. |
| Trazabilidad | `docs/traceability/matrix.md` | specs US-IEDD, baselines | Debe distinguir estados de madurez (backlog / en curso / cerrado). |
| Especificaciones US-IEDD | `docs/specs/incN/` | `docs/traceability/matrix.md` | Fuente de especificación detallada; input de `/implement-us`. |
| US candidatas / planes de incremento | `docs/plans/incN/` | `CLAUDE.md`, specs US-IEDD | Documento de trabajo — se marca cerrado una vez aprobadas las US. |
| Aprendizajes metodológicos | `docs/aprendizajes/HITO-*.md` | baselines, `docs/iedd/` | Evidencia del ensayo IEDD; no se reescriben salvo corrección editorial. |
| Reportes de cierre de US | `docs/reports/` | `docs/traceability/matrix.md` | Evidencia de cierre de `/implement-us`. |
| Reportes de calidad (CodeGuard, DesignReviewer, ArchitectAnalyst) | `quality/reports/` | `CLAUDE.md`, `.cm/baselines/` | Evidencia técnica; no se edita a mano. |
| Gestión de configuración (baselines, tags) | `.cm/baselines/` | `docs/cm/PLAN-CM.md` | Fuente de registros de cierre de incremento. |
| Marco metodológico IEDD | `docs/iedd/` | `CLAUDE.md` | Vigente y estable — no cambia por incremento. |

---

## 4. Convención de estado documental

| Estado documental | Uso |
|---|---|
| Vigente | Documento activo que debe reflejar el estado actual de su tema. |
| Histórico | Conservado como memoria previa (ej. `RF_v1.md`, `PLAN_v1.md` una vez cerrado un incremento sobre ellos). No manda sobre el estado actual. |
| Evidencia | Registra cierre, hito, reporte o baseline. |
| Operativo | Guía el trabajo diario (`CLAUDE.md`, workflows). |
| Derivado | Resume información de otras fuentes (este documento, el mapa documental). |

### Encabezados recomendados

```md
> Estado documental: vigente
> Fuente de verdad para: <tema>
> Última actualización: AAAA-MM-DD
```

```md
> Estado documental: histórico
> Conservado como evidencia de elicitación o decisión previa.
> No usar como fuente de verdad para el estado actual.
> Fuente vigente relacionada: <archivo>
```

---

## 5. Reglas de actualización

1. El estado resumido puede aparecer en `README.md`, pero el detalle vive en `CLAUDE.md`,
   la matriz o la baseline correspondiente.
2. Las decisiones arquitectónicas nuevas se registran como ADR antes de reflejarse en
   `docs/architecture/`.
3. Los documentos de elicitación (`RF_v1.md`, `RNF_v1.md`, `ARQ_v1.md`, `PLAN_v1.md`) **no se
   modifican retroactivamente** — ver `CLAUDE.md`. Correcciones de proceso van al workflow.
4. La matriz de trazabilidad evita el uso ambiguo de "definido" — debe distinguir madurez.
5. Los documentos de evidencia (HITOs, reportes, baselines) no se reescriben salvo corrección
   editorial menor.
6. Todo documento derivado enlaza a su fuente principal.

---

## 6. Próximo paso

Este documento se referencia desde `docs/inventario/DOCUMENTATION-MAP.md`, que ofrece la
navegación mínima basada en esta jerarquía.
