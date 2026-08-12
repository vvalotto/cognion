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

**Fase:** BL-002 (Incremento 1 — BC Identidad) cerrada el 2026-07-29 en desarrollo local
(`.cm/baselines/BL-002-bc-identidad.md`). Merge `develop → main` y tag `v0.3.0` diferidos —
mismo ítem abierto de infraestructura/Docker que el deploy de `BL-001`; se ejecutan cuando esa
decisión se resuelva. BC Identidad completo: RF-01 (registro por
invitación) y RF-02 (autenticación y RBAC por rol) implementados de punta a punta, backend
(Iteración 1: `US-1.1.0` a `US-1.1.5`) y frontend (Iteración 2: `US-1.1.6` a `US-1.1.9`)
integrados juntos, cumpliendo el criterio de cierre de baseline de `docs/plans/PLAN-CM.md` §7
(decisión 2026-07-24 — la Baseline no cierra backend-only). Decisiones previas al incremento:
invitación con expiración de 7 días, rechazo sin recuperación automática (`ADR-012`); JWT de
60 minutos sin refresh ni blacklist (`ADR-013`); hashing bcrypt (`ADR-014`).
**US-1.1.9 (Administrador da de alta un Docente desde la UI) cerrada 2026-07-29**, PR #35
mergeado a `develop`, `docs/reports/inc1/US-1.1.9-report.md`: pantallas `AltaDocente.tsx`/
`AltaDocenteExito.tsx` + guard de ruta `RequireRole` (ampliación de scope detectada en Fase 2:
el `.feature` asumía ruta protegida, pero no había guard client-side desde `US-1.1.6`).
**UAT manual de Víctor en navegador real** detectó y corrigió dos gaps preexistentes desde
`US-1.1.6`/`1.1.7`, invisibles a Vitest: falta de `CORSMiddleware` en el backend (bloqueaba
cualquier llamada real del frontend) y un bug de cascada CSS (regla heredada sin `@layer`
pisando las utilities de Tailwind) + paleta/tipografía no institucionales — corregidos dentro
de `US-1.1.9` a pedido de Víctor. 46/46 tests frontend, quality gates APROBADO
(`quality/reports/inc1/US-1.1.9-quality.json`). Esta US cierra la Iteración 2 y el Incremento 1.
**Quality gates de cierre ejecutados:** DesignReviewer del último PR — 0 CRITICAL, 27
advertencias; ArchitectAnalyst (`quality/reports/architectanalyst/BL-002-arquitectura.json`) —
3 críticos "Zone of Pain" a nivel de paquete raíz (`identidad`, `settings`, `shared`), leídos y
aceptados, `should_block: false` (nunca bloquea, solo informa tendencias — ver retrospectiva
de `BL-002` para el detalle y el ajuste propuesto para el próximo incremento).
Incremento 2 — Banco de Preguntas en curso, Iteración 1 (`docs/plans/inc2/inc2-candidatas.md`).
Iteración 0 — Modelado cerrada 2026-07-31 (US-2.0.1 event storming, Issue #38; US-2.0.2
wireframes, Issue #39). **US-2.1.1 (Docente da de alta una Materia; banco vacío en el mismo
flujo) cerrada 2026-07-31**, PR #56 mergeado a `develop`,
`docs/reports/inc2/US-2.1.1-report.md`. **US-2.1.2 (Comisión referencia Materia por puerto,
refactor técnico de BC Identidad) cerrada 2026-08-05**, PR #62 mergeado a `develop` (merge
`8294a82`), Issue #43 cerrado, `docs/reports/inc2/US-2.1.2-report.md`: `Comisión.materia_id`
resuelto contra `MateriaPort` sin imports directos entre BCs, migración con backfill
verificada por round-trip real. El pre-push gate (`DesignReviewer`, `CBOAnalyzer`) detectó un
CRITICAL (CBO=11/10 en `RegistrarEstudianteUseCase` al inyectar `MateriaPort`) recién en la
fase de PR — no cubierto por los Quality Gates de Fase 7, que miden pylint/CC/MI/coverage pero
no acoplamiento; se corrigió moviendo la resolución del nombre de materia a
`RegistroController` (detalle de presentación, no de la regla de negocio de registro). 158/158
tests, DesignReviewer 0 CRITICAL tras el fix. **US-2.1.3 (Docente carga una pregunta de
opción múltiple en un banco) cerrada 2026-08-06**, PR #65 mergeado a `develop` (merge
`80aca29`), Issue #44 cerrado, `docs/reports/inc2/US-2.1.3-report.md`: aggregate
`PreguntaPlantillaOpcionMultiple` autovalidante (INV-BP-02 exactamente una opción correcta,
INV-BP-03 mínimo 2 opciones), `CargarPreguntaOpcionMultipleUseCase`, endpoint
`POST /preguntas/opcion-multiple` (rol `docente`). Primer tipo de pregunta implementado —
establece el patrón que sigue `US-2.1.4` sin generalizar entre tipos. 180/180 tests, quality
gates APROBADO (pylint 9.37/10, CC máx 6, MI mín 56.4, coverage 99%), pre-push gate 0
CRITICAL.
**US-2.1.4 (Docente carga una pregunta de Verdadero/Falso en un banco) cerrada 2026-08-08**,
PR #68 mergeado a `develop` (merge `40849c4`), Issue #45 cerrado,
`docs/reports/inc2/US-2.1.4-report.md`: segundo aggregate de pregunta,
`PreguntaPlantillaVerdaderoFalso` (sin invariantes adicionales sobre `respuesta_correcta`),
`CargarPreguntaVerdaderoFalsoUseCase`, endpoint `POST /preguntas/verdadero-falso` (rol
`docente`), migración `respuesta_correcta` nullable en `pregunta_plantilla`. Repitió el patrón
de `US-2.1.3` sin generalizar entre tipos de pregunta, según lo previsto. 194/194 tests, quality
gates APROBADO (pylint 9.27/10, CC máx 6, MI mín 51.47, coverage 99%).
**US-2.1.5 (Docente edita una pregunta existente) cerrada 2026-08-12**, PR #71 mergeado a
`develop` (merge `39e2a12`), Issue #46 cerrado, `docs/reports/inc2/US-2.1.5-report.md`: método
`editar(...)` en `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso`
(reaplica INV-BP-02/03, tipo no editable), `EditarPreguntaUseCase`, endpoint
`PUT /preguntas/{pregunta_id}` (rol `docente`). Mismo patrón de CRITICAL de CBO que
`US-2.1.2` (`CBO=11/10` en `PreguntasController` al inyectar el tercer use case), corregido
tipando el evento de retorno como `object` en el controller. 219/219 tests, quality gates
APROBADO (pylint 9.27/10, CC máx 8, MI mín 49.62, coverage 99%).
**Próximo paso:** `US-2.1.6` — Docente elimina (baja lógica) una pregunta, ver
`docs/plans/inc2/inc2-candidatas.md` §Iteración 1 (2.1.7 al final). Sin spec ni Issue creados
todavía.
**Baseline abierta:** ninguna. BL-003 se abre al cierre del Incremento 2 (ver
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

**Perfil `implement-us` activo:** `clean-architecture-bc`
(`.claude/skills/implement-us/customizations/clean-architecture-bc.json`) — no
`hexagonal-ddd-bc` (perfil genérico de claude-dev-kit, no usado en este proyecto). Cualquier
doc de fase de `implement-us` que condicione comportamiento por nombre de perfil debe
referenciar `clean-architecture-bc`.

---

## Estructura del repositorio

```
cognion/
├── CLAUDE.md                        ← este archivo
├── CHANGELOG.md                     ← Keep a Changelog, actualizado en cada tag de baseline
├── .cm/baselines/                   ← BL-NNN.md + reportes de calidad
├── .githooks/pre-push               ← DesignReviewer — bloquea si CRITICAL
├── .pre-commit-config.yaml          ← black, isort, ruff, mypy (bloquea), CodeGuard (advierte)
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

**Regla de imports:** las capas internas nunca importan capas externas. Comunicación entre BCs: solo por puertos definidos en `entities/ports/` — nunca imports directos entre BCs. `shared/` es la única excepción transversal: puede tener las 4 capas (`entities/`, `use_cases/`, `interface_adapters/`, `frameworks/`) cuando el contenido es genuinamente transversal — sin lógica de negocio de un BC específico — no solo `entities/` (`ADR-017` para `shared/frameworks/db.py`, `ADR-019` para JWT/RBAC en `shared/entities/`+`frameworks/security/`+`interface_adapters/security/`). Cada BC sigue armando su propio composition root en `frameworks/dependencies.py`, importando de `shared` — nunca de otro BC.

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
| Commit backend | mypy (`src/` completo) | Pre-commit automático | Sí |
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
- El check de tipos integrado en CodeGuard (`software_limpio`) invoca mypy sin `--cache-dir`
  y con timeout de 10s — en corridas en frío puede superar ese tiempo y el check queda mudo
  (ni aprueba ni reporta error real), dejando pasar errores de tipo reales sin aviso. Bug
  reportado: `vvalotto/software_limpio#70`. Mientras se corrige ahí, el hook `mypy` dedicado
  (arriba, sobre `src/` completo, mismo comando que CI) es la fuente de verdad local para
  tipos — bloquea el commit si hay errores reales.

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
