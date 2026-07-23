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

**Fase:** BL-001 (Incremento 0 — Fundación Técnica) cerrada el 2026-07-16 — tag `v0.2.0`
(`.cm/baselines/BL-001-fundacion-tecnica.md`). Pipeline técnico funcionando de punta a punta en
el entorno local: CI en verde (lint + tests + DesignReviewer), PostgreSQL local (Homebrew) con
migración de Alembic aplicada, `GET /health` → 200, build Docker en CI/CD. Deploy real a un
entorno queda diferido, pendiente de la decisión de infraestructura aún abierta.
**Decisiones resueltas el 2026-07-16 (previas al Incremento 1):** invitación con expiración de
7 días, rechazo sin recuperación automática ante link vencido/inválido, entrega por email vía
adaptador SMTP propio de BC Identidad (`ADR-012`); JWT con expiración de 60 minutos, sin
refresh ni blacklist (`ADR-013`); hashing de contraseñas con bcrypt (`ADR-014`).
**Incremento 1 (BC Identidad) en curso.** Iteración 0 — Modelado cerrada el 2026-07-18:
US-1.0.1 (event storming, Issue #2) y US-1.0.2 (wireframes de registro/login, Issue #4)
aprobados por Víctor (`docs/design/domain/BC-identidad-modelo.md`,
`docs/design/ux/wireframes-identidad.md`). Iteración 1 en curso: US-1.1.0 (alta de
usuarios/comisión/asignación de docentes, sin RF propio) implementada y mergeada a `develop`
el 2026-07-21 (PR #11, `docs/reports/inc1/US-1.1.0-report.md`, 37/37 tests). US-1.1.1 (Docente
genera link de invitación, Issue #6) mergeada a `develop` el 2026-07-22 (PR #14). US-1.1.2
(Estudiante se registra con link de invitación válido, Issue #7) mergeada a `develop` el
2026-07-23 (PR #15, `e776a42`, `docs/reports/inc1/US-1.1.2-report.md`, 77/77 tests) —
backend completo (`POST /identidad/registro`), frontend diferido a una US-IEDD separada
(sin infraestructura de routing/cliente API todavía). RF-01 permanece "Especificado" en
`docs/traceability/matrix.md` hasta cerrar también US-1.1.3. Issues #8–#10 abiertos para
US-1.1.3 a US-1.1.5 (`docs/plans/inc1/inc1-candidatas.md` §Iteración 1), ninguna con
branch/PR activo todavía.
**Próximo paso:** Arrancar US-1.1.3 (Estudiante intenta registrarse con link vencido o
inválido, Issue #8, refina `InvitacionNoValida` en excepciones específicas) —
`git checkout -b feature/US-1.1.3-...` desde `develop`, `tracker init`, luego
`/implement-us US-1.1.3`.
**Baseline abierta:** ninguna. BL-002 se abre al cierre del Incremento 1 (ver
`docs/plans/PLAN-CM.md` §7 para la numeración de baselines).
**Branch activo:** `develop`.

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

Monolito modular con **Clean Architecture** interna. Bounded Contexts: Actividad Evaluativa (Core, antes "Sesiones" — ver `ADR-015`), Banco de Preguntas, Identidad, Notificaciones, Analytics.

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
feat(entities): agregar aggregate ActividadEvaluativa [US-3.1.1]
fix(interface_adapters): corregir endpoint ranking
test(entities): tests unitarios ActividadEvaluativa.cerrar_periodo
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
6. /pr → push + gh pr create --base develop
7. Al mergear el PR (gh pr merge): sincronizar develop local (checkout + pull --ff-only,
   borrar branch feature local/remoto), y cerrar el Issue de la US asociado — comentario con
   los SHAs de los commits de la US + `gh issue close` — sin pedir confirmación previa, salvo
   que algo resulte ambiguo (no se encuentra el Issue, hay más de un candidato, etc.)
```

**Por qué el paso 7 es manual y no vía `Closes #N` en el commit/PR:** el repo mergea PRs a
`develop`, no a `main` (rama default) — GitHub solo autocierra Issues por `Closes #N` cuando
el merge es a la rama default.

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
- **Docker en el entorno de desarrollo local**: no instalado a la fecha (2026-07-16). Se
  usará más adelante en el proyecto — hasta entonces, PostgreSQL local corre vía Homebrew
  (ver `docs/rf/PLAN_v1.md` revisión 2026-07-16). El build de imagen Docker en CI/CD no se
  ve afectado — corre en GitHub Actions, no localmente.
- **Criterios de legibilidad en proyección** (RNF_v1.md): tamaño de fuente mínimo y contraste. Se define en etapa de diseño UX antes de Incremento 6.

---

## Al iniciar una sesión

1. Leer este archivo.
2. `git log --oneline -10` y `git status` para ver el estado real del repo.
3. Si hay una baseline abierta: leer `.cm/baselines/BL-NNN.md` en curso.
4. Si hay trackers activos: verificar con `.venv/bin/python .claude/tracking/tracker_cli.py status` antes de arrancar.
5. No preguntar por el stack ni por la arquitectura — están decididos en `docs/rf/ARQ_v1.md`.

## Al cerrar una sesión

1. Ejecutar `/checkpoint` — si hubo cambios en `docs/` durante la sesión, dispara
   `/docs-audit` automáticamente antes de guardar (ver `.claude/commands/checkpoint.md`).
