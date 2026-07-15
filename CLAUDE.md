# CLAUDE.md — Cognion

> Estado operativo actual del proyecto. Resume y enlaza evidencia — no duplica los documentos fuente.
> Actualizar al cierre de cada Incremento (SP-ADJ incluido).
> Jerarquía: Código y tests > Baselines > ADRs > Matriz de trazabilidad > **este archivo** > README.md
> Mapa documental y autoridad por tema, completo: `docs/inventario/DOCUMENTATION-MAP.md`.

---

## Contexto del proyecto

Plataforma web de evaluación universitaria con cuestionarios gamificados. Docente único (Víctor Valotto), materias de Ingeniería de Software y Gestión de Proyectos en FIUNER, 30–60 alumnos por comisión. Equipo de desarrollo: unipersonal.

Documentos de definición (no se modifican retroactivamente):
- `docs/rf/RF_v1.md` — 18 requerimientos funcionales
- `docs/rf/RNF_v1.md` — atributos de calidad y escenarios
- `docs/rf/ARQ_v1.md` — arquitectura de referencia, stack decidido, ADRs 001–006
- `docs/rf/PLAN_v1.md` — plan de implementación (7 incrementos, walking skeleton primero)

---

## Estado actual

**Fase:** Checklist de instalación resuelto (`docs/plans/CHECKLIST-INSTALACION.md`). Plan
reestructurado el 2026-07-15: Incremento 0 (Fundación Técnica) ahora es infraestructura pura,
sin BC Identidad — ver `docs/rf/PLAN_v1.md` (nota de revisión al inicio) y
`docs/plans/inc0/inc0-candidatas.md`. Deploy real a un entorno (Fly.io u otro) queda diferido
a un incremento posterior, pendiente de la decisión de infraestructura aún abierta.
**Próximo paso:** Completar la única iteración del Incremento 0 (PostgreSQL local vía Docker
Compose + Alembic inicializado en el repo). Luego arrancar el Incremento 1 (BC Identidad:
RF-01, RF-02, JWT, healthcheck) con su propia Iteración 0 — Modelado.
**Baseline abierta:** ninguna (BL-000 se abre al cerrar el Incremento 0).
**Branch activo:** `develop` (creado desde `main`).

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11 + FastAPI (async) |
| ORM | SQLAlchemy async + Alembic |
| Base de datos | PostgreSQL |
| Event store | Tabla append-only en PostgreSQL (JSONB) |
| Frontend | React 19 + TypeScript + Vite |
| Estilos / UI | Tailwind CSS + shadcn/ui |
| Containerización | Docker multi-stage |
| Hosting | Fly.io (testing/staging); producción pendiente |
| CI/CD | GitHub Actions |
| Auth | JWT — PyJWT + cryptography |
| Gestión de paquetes | uv (backend), npm (frontend) |

---

## Estructura del repositorio

```
cognion/
├── CLAUDE.md                        ← este archivo
├── CHANGELOG.md                     ← Keep a Changelog, actualizado en cada tag de baseline
├── .cm/baselines/                   ← BL-NNN.md + reportes de calidad
├── .githooks/pre-push               ← DesignReviewer — bloquea si CRITICAL
├── .pre-commit-config.yaml          ← black, isort, ruff, CodeGuard (advierte, no bloquea)
├── .github/workflows/               ← CI/CD: lint+test en develop, build+deploy en main
├── docs/
│   ├── rf/                          ← documentos de elicitación (RF, RNF, ARQ, PLAN) — históricos
│   ├── adr/                         ← ADR-NNN.md — decisiones arquitectónicas ratificadas
│   ├── architecture/                ← vista de arquitectura vigente (deriva de ARQ + ADRs)
│   ├── design/ux/                   ← wireframes-*.md + prototipos/*.html — gate obligatorio pre-frontend
│   ├── specs/incN/                  ← US-N.M.K.md — input de /implement-us
│   ├── plans/                       ← PLAN-CM.md, WORKFLOW-DESARROLLO.md, PROCEDIMIENTO-UAT.md,
│   │                                    CHECKLIST-INSTALACION.md + incN/incN-candidatas.md por incremento
│   ├── reports/                     ← reportes de cierre de /implement-us
│   ├── traceability/matrix.md       ← RF → BC → Incremento → US → estado
│   └── aprendizajes/                ← HITO-N.md — hallazgos del ensayo IEDD
├── src/<bc>/                        ← backend BC-first con Clean Architecture interna
├── frontend/                        ← React + TypeScript + Tailwind + shadcn/ui
├── quality/reports/                 ← evidencia de codeguard/, designreviewer/, architectanalyst/
└── tests/{unit,integration,features,uat}/incN/
```

---

## Arquitectura interna — reglas no negociables

Monolito modular con **Clean Architecture** interna. Bounded Contexts: Sesiones (Core), Banco de Preguntas, Identidad, Notificaciones, Analytics.

```
src/<bc>/
├── entities/           → reglas de negocio puras — sin dependencias externas
├── use_cases/          → orquestación — solo importa entities/
├── interface_adapters/ → controllers, presenters, gateways — solo importa use_cases/
└── frameworks/         → FastAPI, SQLAlchemy, WebSockets — implementa puertos
```

**Regla de imports:** las capas internas nunca importan capas externas. Comunicación entre BCs: solo por puertos definidos en `entities/ports/` — nunca imports directos entre BCs. `shared/entities/` es la única excepción transversal (tipos y utilidades sin lógica de negocio de un BC específico).

---

## Workflow de desarrollo — resumen operativo

Referencia completa: `docs/plans/WORKFLOW-DESARROLLO.md`. Referencia de política: `docs/plans/PLAN-CM.md`.

### Jerarquía de trabajo

```
Incremento (PLAN_v1.md, 0–6) → Baseline (BL-NNN) + tag git (v0.N.0) + Milestone GitHub
  └── Iteración
        └── US-IEDD (US-N.M.K) → GitHub Issue + docs/specs/incN/US-N.M.K.md + feature branch + /implement-us
```

### Branching

```
main          ← baselines (v0.N.0) — deploy automático al mergear
  └── develop ← integración continua — recibe PRs de cada US
        ├── feature/US-N.M.K-descripcion-corta
        ├── feature/inc-N-descripcion-corta    ← incrementos técnicos sin US
        └── fix/descripcion-corta
```

- `develop → main` solo al cerrar un Incremento (Baseline).
- PRs de features siempre apuntan a `develop`. `gh pr create` siempre con `--base develop`.

### Conventional Commits

```
feat(entities): agregar aggregate Sesion [US-2.1.1]
fix(interface_adapters): corregir endpoint ranking
test(entities): tests unitarios Sesion.cerrar_periodo
docs(adr): ADR-003 SQLite vs PostgreSQL
chore(cm): registrar BL-002 cierre Incremento 2
```

Scopes: `entities | use_cases | interface_adapters | frameworks | frontend | cm | tests | design`

### Ciclo por US-IEDD (orden no negociable)

```
1. git checkout -b feature/US-N.M.K-descripcion desde develop
2. Verificar branch activo con git branch
3. tracker init US-N.M.K → start_phase(0)  ← ANTES de cualquier artefacto
4. /implement-us US-N.M.K  (lee docs/specs/incN/US-N.M.K.md)
5. Commits atómicos con referencia [US-N.M.K]
6. /pr → merge a develop
```

**Política de tracking:** operaciones sobre `tracker_cli.py` estrictamente secuenciales, nunca en paralelo sobre el mismo JSON. Usar `.venv/bin/python .claude/tracking/tracker_cli.py`, no `uv run`.

---

## Quality gates

| Nivel | Herramienta | Modo | Bloquea |
|-------|-------------|------|---------|
| Commit backend | CodeGuard | Pre-commit automático | No — solo advierte |
| Push backend | DesignReviewer | Pre-push automático | Sí, si CRITICAL |
| Push/PR a develop | lint + tests + DesignReviewer | GitHub Actions CI | Sí |
| Merge/tag a main | build Docker + deploy + healthcheck | GitHub Actions CD | Sí |
| Cierre de Incremento | DesignReviewer manual + verificación UX | Manual | 0 CRITICAL requerido |
| UAT | Tests funcionales (Capa 1 + Capa 2) | Manual | Debe aprobar antes de merge a main |
| Cierre de Baseline | ArchitectAnalyst | **Siempre manual** | No bloquea — informa tendencias |

**Notas operativas críticas:**
- `designreviewer` **siempre** con `--config pyproject.toml` — sin el flag usa defaults genéricos que no reflejan el proyecto.
- El hook `.githooks/pre-push` **no se activa solo al clonar** — requiere `git config core.hooksPath .githooks` una vez por clon.
- Umbrales de `[tool.designreviewer]` se calibran **al inicio de cada Incremento completo**, no US por US.

---

## Gate de diseño UX (obligatorio antes de frontend)

Ninguna línea de `frontend/` sin artefacto aprobado en `docs/design/ux/`. Proceso:

```
1. Prototipo HTML navegable (docs/design/ux/prototipos/)
2. Validación humana (en el dispositivo real si el escenario lo exige)
3. Spec Markdown (docs/design/ux/wireframes-*.md)
4. Aprobación explícita de Víctor
5. Recién entonces escribir la spec de la US y el código
```

Toda spec de US que toca `frontend/` debe incluir el campo `## Fuente de verdad UX` con referencias a los artefactos consultados — sin ese campo la spec está incompleta.

**Por qué existe este gate:** en el proyecto de referencia (AtaraxiaDive), saltearlo produjo una US completa revertida al detectarse 14 gaps críticos en UAT. El código había sido especificado mirando el código existente en lugar del diseño aprobado (anti-patrón "spec-validatoria").

---

## Clasificación de hallazgos en UAT

Decidir el track **antes de codear**:
- Hallazgo **solo toca `frontend/`** → track informal, commit descriptivo, sin spec ni `/implement-us`.
- Hallazgo **toca cualquier archivo de `src/`** → track formal obligatorio: US-IEDD → spec → `/implement-us`.
- Si al resolver algo "de UX" la primera acción termina siendo abrir `src/`: pivotar al track formal.

---

## Convenciones de nomenclatura

| Artefacto | Patrón | Ejemplo |
|-----------|--------|---------|
| Baseline | `BL-NNN-slug.md` | `BL-001-incremento-0-walking-skeleton.md` |
| US-IEDD | `US-{inc}.{iter}.{seq}` | `US-2.3.1` |
| Branch de US | `feature/US-N.M.K-descripcion` | `feature/US-2.3.1-registrar-respuesta` |
| Branch técnico | `feature/inc-N-descripcion` | `feature/inc-0-fundacion-tecnica` |
| ADR | `ADR-NNN-slug.md` | `ADR-003-sqlite-vs-postgresql.md` |
| HITO | `HITO-N-SLUG.md` | `HITO-1-WALKING-SKELETON-FRICCION.md` |
| CI backend | `CI-C##` | `CI-C08` |
| CI frontend | `CI-F##` | `CI-F03` |
| Milestone GitHub | `Incremento N — <nombre>` | `Incremento 0 — Fundación Técnica` |
| Labels GitHub | `us-iedd`, `incremento-N`, `blocked`, `in-progress`, `done` | — |

---

## Ítems abiertos que requieren decisión

- **Algoritmo de puntaje en modo en vivo** (RF-10): combina tiempo, corrección, dificultad e importancia. Se cierra como spike en Incremento 6, Iteración 0.
- **Mecanismo de importación desde PDF** (RF-07): parseo automático vs. asistido. Se decide en Incremento 7.
- **Infraestructura definitiva** (ARQ_v1.md): Fly.io confirmado para testing; producción pendiente de decisión institucional (nube vs. servidor FIUNER).
- **Criterios de legibilidad en proyección** (RNF_v1.md): tamaño de fuente mínimo y contraste. Se define en etapa de diseño UX antes de Incremento 6.

---

## Al iniciar una sesión

1. Leer este archivo.
2. `git log --oneline -10` y `git status` para ver el estado real del repo.
3. Si hay una baseline abierta: leer `.cm/baselines/BL-NNN.md` en curso.
4. Si hay trackers activos: verificar con `.venv/bin/python .claude/tracking/tracker_cli.py status` antes de arrancar.
5. No preguntar por el stack ni por la arquitectura — están decididos en `docs/rf/ARQ_v1.md`.
