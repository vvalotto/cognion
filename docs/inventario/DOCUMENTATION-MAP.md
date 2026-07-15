# Mapa documental — Cognión

> Estado documental: vigente
> Fuente de verdad para: navegación documental y jerarquía de lectura
> Última actualización: 2026-07-14

## 1. Propósito

Guía mínima para saber qué documento consultar según la necesidad de lectura o trabajo. No
redefine autoridad — para eso ver
[`FUENTES-DE-VERDAD-DOCUMENTAL.md`](./FUENTES-DE-VERDAD-DOCUMENTAL.md).

---

## 2. Lectura rápida recomendada (orden pedagógico)

| Orden | Documento | Para qué leerlo |
|---|---|---|
| 1 | `README.md` | Qué es Cognión, stack y estado resumido. |
| 2 | `CLAUDE.md` | Estado operativo actual y reglas de trabajo con IA. |
| 3 | `docs/requirements/vision.md` | Problema, usuarios, alcance v1 y criterios de éxito. |
| 4 | `docs/rf/ARQ_v1.md` + `docs/adr/` | Arquitectura de referencia decidida y sus ADRs. |
| 5 | `docs/rf/PLAN_v1.md` | Los 7 incrementos, orden por riesgo, Iteración 0 — Modelado. |
| 6 | `docs/traceability/matrix.md` | Trazabilidad RF → BC → Incremento → US → estado. |

> Este es un orden *pedagógico* para un primer acercamiento — no es orden de autoridad. Ver
> `FUENTES-DE-VERDAD-DOCUMENTAL.md §2` para precedencia ante conflicto.

---

## 3. Precedencia en caso de conflicto

Código y tests › baselines (`.cm/baselines/`) › ADRs (`docs/adr/`) › matriz de trazabilidad ›
`CLAUDE.md` › `README.md`. Detalle completo en
[`FUENTES-DE-VERDAD-DOCUMENTAL.md §2`](./FUENTES-DE-VERDAD-DOCUMENTAL.md#2-principio-rector).

---

## 4. Fuentes de verdad por tema (entradas frecuentes)

> La tabla completa vive en
> [`FUENTES-DE-VERDAD-DOCUMENTAL.md §3`](./FUENTES-DE-VERDAD-DOCUMENTAL.md#3-fuentes-de-verdad-por-tema).
> Esto es solo un atajo para los temas más consultados.

| Tema | Fuente principal | Uso |
|---|---|---|
| Presentación breve | `README.md` | Entrada rápida, sin detalle completo. |
| Estado operativo actual | `CLAUDE.md` | Memoria operativa para desarrollo asistido por IA. |
| Visión del producto | `docs/requirements/vision.md` | Problema, usuarios, alcance, criterios de éxito. |
| Workflow de desarrollo | `docs/plans/WORKFLOW-DESARROLLO.md` | Procedimiento vigente para US, incrementos, Iteración 0 — Modelado. |
| Plan de incrementos | `docs/rf/PLAN_v1.md` | Los 7 incrementos y su orden por riesgo. |
| Modelo de dominio por BC | `docs/design/domain/BC-<bc>-modelo.md` | Event storming aprobado — se crea en la Iteración 0 de cada incremento que introduce/extiende un BC. |
| Diseño UX aprobado | `docs/design/ux/` | Gate obligatorio antes de código en `frontend/`. |
| Trazabilidad | `docs/traceability/matrix.md` | Relación RF → BC → incremento → US → estado. |

---

## 5. Documentos de inventario y adecuación documental

| Documento | Rol |
|---|---|
| `docs/inventario/FUENTES-DE-VERDAD-DOCUMENTAL.md` | Jerarquía documental y autoridad por tema. |
| `docs/inventario/DOCUMENTATION-MAP.md` | Mapa mínimo de navegación (este documento). |

---

## 6. Documentos históricos (no se modifican retroactivamente)

| Documento | Observación |
|---|---|
| `docs/rf/RF_v1.md` | Elicitación funcional inicial. Fuente base para la matriz de trazabilidad. |
| `docs/rf/RNF_v1.md` | Atributos de calidad y escenarios validados. |
| `docs/rf/ARQ_v1.md` | Arquitectura de referencia inicial y ADRs 001–006 — hasta que `docs/architecture/` tenga contenido propio, esta es la fuente vigente. |
| `docs/rf/PLAN_v1.md` | Plan de 7 incrementos. Ajustes de *proceso* (ej. Iteración 0 — Modelado) se documentan en `WORKFLOW-DESARROLLO.md`; el plan mismo no se reescribe salvo agregar la estructura de iteraciones. |

---

## 7. Documentos de evidencia

| Documento / carpeta | Tipo de evidencia |
|---|---|
| `.cm/baselines/` | Cierre formal de baselines (aún no existe — se abre con BL-000 al iniciar el Incremento 0). |
| `docs/aprendizajes/HITO-*.md` | Aprendizajes y decisiones emergentes del ensayo IEDD. |
| `quality/reports/` | Reportes de CodeGuard, DesignReviewer y ArchitectAnalyst. |
| `docs/reports/` | Reportes de cierre de `/implement-us` por US (aún no existe — se crea con la primera US). |
| `tests/` | Evidencia ejecutable de validación técnica. |

---

## 8. Regla editorial básica

No duplicar el estado detallado del proyecto en varios documentos.

- El README resume.
- `CLAUDE.md` orienta el trabajo operativo.
- La matriz documenta trazabilidad.
- Las baselines evidencian cierres.
- Los ADRs registran decisiones.
- Los HITOs preservan aprendizajes.

Ante contradicción, consultar `docs/inventario/FUENTES-DE-VERDAD-DOCUMENTAL.md`.
