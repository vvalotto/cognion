# BL-000 — Fundación Documental

| Campo | Valor |
|-------|-------|
| Tipo | Fundacional |
| Fecha apertura | 2026-06-24 |
| Fecha cierre | 2026-07-15 |
| Git tag inicial | — (repo sin tags previos) |
| Git tag cierre | `v0.1.0` |
| Estado | ✅ Completado |
| DoD | Elicitación completa (RF, RNF, ARQ, PLAN) verificada por Víctor; plan de gestión de configuración, workflow de desarrollo y procedimiento de UAT definidos; checklist de instalación resuelto; matriz de trazabilidad inicial poblada; plan de incrementos internamente consistente (sin contradicciones entre sus propias reglas y su contenido). |

## Descripción

Cierra la etapa de definición del proyecto: documentos de elicitación (RF_v1, RNF_v1, ARQ_v1,
PLAN_v1), plan de Gestión de Configuración y procedimientos operativos (CM, workflow, UAT),
entorno de desarrollo instalado, y el plan de incrementos revisado y corregido antes de
ejecutar cualquier código. No incluye implementación — `src/` son capas vacías (esqueleto),
sin lógica de negocio todavía.

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D01 | `docs/rf/RF_v1.md` | Documento | 18 requerimientos funcionales |
| CI-D02 | `docs/rf/RNF_v1.md` | Documento | Atributos de calidad y escenarios |
| CI-D03 | `docs/rf/ARQ_v1.md` | Documento | Arquitectura de referencia, stack, ADRs 001-006 |
| CI-D04 | `docs/rf/PLAN_v1.md` | Documento | Plan de implementación — 8 incrementos, revisado 2026-07-15 |
| CI-D05 | `docs/adr/ADR-001..011` | Documento | ADRs ratificados (monolito modular, event sourcing, PostgreSQL, WebSockets, JWT/RBAC, CI/CD, Unit of Work, healthcheck, shadcn/WCAG) |
| CI-D06 | `docs/plans/PLAN-CM.md` | Documento | Plan de Gestión de Configuración |
| CI-D07 | `docs/plans/WORKFLOW-DESARROLLO.md` | Documento | Procedimiento operativo de branching, PRs, ciclo US/Incremento |
| CI-D08 | `docs/plans/CHECKLIST-INSTALACION.md` | Documento | Checklist de entorno — resuelto |
| CI-D09 | `docs/plans/PROCEDIMIENTO-UAT.md` | Documento | Procedimiento de UAT por incremento |
| CI-D10 | `docs/traceability/matrix.md` | Documento | Matriz RF/RNF → BC → Incremento → US-IEDD → estado |
| CI-D11 | `docs/aprendizajes/HITO-1-*.md` | Documento | Primer hallazgo de aprendizaje del ensayo IEDD |
| CI-T01 | `.pre-commit-config.yaml`, `.githooks/pre-push` | Herramienta | CodeGuard (advierte) + DesignReviewer (bloquea CRITICAL) |
| CI-T02 | `.github/workflows/ci.yml`, `cd.yml` | Herramienta | CI (lint+test+DesignReviewer) y CD (build Docker, deploy comentado) |
| CI-T03 | `.claude/skills/implement-us/`, `.claude/tracking/` | Herramienta | Claude Dev Kit con perfil Clean Architecture BC-first |

## Métricas al cerrar

No aplica métricas de código (sin implementación todavía — `src/` es esqueleto vacío).
`uv run pytest`: 0 tests recolectados (tolerado por CI hasta que el Incremento 0 agregue tests
reales). `designreviewer src/ --config pyproject.toml`: 0 violaciones (nada que analizar).

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Separar fundación técnica (Incremento 0) del primer BC de dominio (Identidad, Incremento 1) | El plan original mezclaba ambas bajo "Walking Skeleton", contradiciendo la regla de modelado de dominio del propio plan — ver `HITO-1` |
| Postgres local vía Docker Compose para desarrollo; Fly.io Postgres diferido a cuando se resuelva la decisión de infraestructura | ADR-004 ya preveía Docker Compose para desarrollo local; Fly.io es para el entorno desplegado, no para el día a día |
| `docs/cm/` renombrado a `docs/plans/` | Alineación con la estructura del proyecto de referencia AtaraxiaDive |
| Hito del Incremento 0 reformulado: verificación con evidencia, no instalación declarada | Ver `HITO-1` — instalar y verificar son actos distintos |

## Retrospectiva

### ¿Qué funcionó?

- El uso del MCP de AtaraxiaDive como fuente de precedente concreto (formato de candidatas,
  separación fundación técnica / primer BC) aceleró la corrección del plan una vez consultado.
- Las preguntas directas de Víctor sobre decisiones puntuales (Fly.io, dominio de Identidad)
  expusieron inconsistencias que ninguna revisión automática podía detectar.

### ¿Qué fue más difícil de lo esperado?

- El plan de incrementos (`PLAN_v1.md`) se redactó sin verificar su propia consistencia interna
  contra las reglas que el mismo documento declaraba — la contradicción pasó dos revisiones
  (elicitación + primera sesión de planificación operativa) sin detectarse.
- Se citó el precedente de AtaraxiaDive una primera vez sin replicar su distinción real
  (fundación técnica vs. primer BC), solo su vocabulario ("Walking Skeleton").

### ¿Qué ajustar en el próximo incremento?

- Antes de bajar cualquier incremento a candidatas operativas, auditar el documento de origen
  (`PLAN_v1.md`) contra sus propias reglas declaradas — no asumir que un documento "verificado"
  en elicitación está libre de inconsistencias en su aplicación.
- Verificar la definición de "Baseline" en `PLAN-CM.md` §7 antes de asumir a qué momento
  corresponde cada BL — la propia sesión asumió inicialmente que BL-000 cerraba el Incremento 0
  del plan, cuando el documento normativo ya la define como cierre de la fundación documental.

---

*Creado: 2026-07-15*
