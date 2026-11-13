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

> Historial detallado de cada incremento, US y UAT (incrementos 0 a 8): `docs/historial/ESTADO-HISTORICO.md`. Evidencia por baseline: `.cm/baselines/BL-NNN-*.md`; por US: `docs/reports/incN/`.

**Última baseline: `BL-017` (2026-11-13, sin tag)** — Incremento 10.1, documental: arquitectura y diseño detallado en `docs/architecture/` (vistas C4, datos, runtime, transversal, desarrollo, despliegue y trazabilidad de RNF), contrastadas con el código de la `1.0.0`; índice en `docs/architecture/README.md`. No cambia el producto: la versión publicada sigue siendo `v1.0.0` (`BL-016`). **Distancias con `RNF_v1.md`:** el despliegue automático y el backup mensual con retención de 12 meses no se cumplen como están escritos (`docs/architecture/70-trazabilidad-rnf-vistas.md`). **No verificado:** el camino del servidor con Docker real (Issue #624), celular real y las secuencias de runtime (no se ejecutaron). Antes: `BL-016` (Incremento 10, `v1.0.0`), `BL-015` (`v0.10.0`, sin UAT formal) y `BL-014` (`v0.9.1`).

**Alcance funcional:** Incrementos 0 a 6 y sus ajustes (3-ADJ a 7-ADJ) cerrados y mergeados a `main`. RF-01 a RF-06, RF-08 a RF-17 y RF-19 a RF-25 en **Validado** (matriz en `docs/traceability/matrix.md`). Quedan en alcance v1 sin implementar: **RF-07** (importación desde PDF, Incremento 7 Iteración 2 — falta decidir con Víctor el spike parseo automático vs. asistido) y **RF-18** (KPIs históricos, diferido sin incremento).

**Despliegue:** (Incremento 10, cerrado en `BL-016`) paquete de instalación por versión con `deploy/servidor/` para Linux con Docker y guía única `docs/INSTALACION.md`. Antes: primera versión instalable y operable local en la Mac de Víctor (`docs/plans/DESPLIEGUE-LOCAL.md`, `ENTORNO=local`). Despliegue de prueba en una VM `e2-micro` de GCP con la cuenta personal de Víctor (`ADR-025`, `docs/plans/DESPLIEGUE-GCP.md`, scripts en `deploy/gcp/`): verificado una vez y destruido el 2026-10-24 por costo; se retoma con `v0.9.1`. Las Iteraciones 2 y 3 del Incremento 8 (CD, staging, backup, observabilidad) siguen en standby a la espera del convenio institucional con Google; 17 Issues en el [Milestone diferido](https://github.com/vvalotto/cognion/milestone/17). Pendientes de operación: costo real de la IP pública, backup a Cloud Storage, runbook.

**Reglas operativas vigentes:**
- Los tests de integración y BDD vacían la base a la que apunte `DATABASE_URL`: usar siempre una base descartable inline (`DATABASE_URL=... pytest ...`), nunca la de desarrollo. `tests/unit/` no toca la base.
- Antes de cerrar una baseline: UAT (Capa 1 + Capa 2) y verificación en navegador real; Vitest con `fetch` mockeado no ve CORS, cascada CSS ni `AbortSignal`.
- Frontend: validar con `tsc -b` (no `--noEmit` solo) y `oxlint`; nunca `prettier --write`.
- El pre-push (`DesignReviewer`/`CBOAnalyzer`) es el único gate que mide acoplamiento; un controller o use case cerca de CBO=10 puede bloquear recién al pushear (separar por responsabilidad command/query).

**Higiene de repositorio** (relevamiento del 2026-09-30): cerrada; sin ramas ni PR abandonados conocidos.


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
| Hosting | Local sin Docker, servidor Linux con Docker (`deploy/servidor/`) y VM de prueba en GCP (`deploy/gcp/`); guía: `docs/INSTALACION.md`. Fly.io ya no se usa (`ADR-025`) |
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

Se deriva con `ls`; mapa documental en `docs/inventario/DOCUMENTATION-MAP.md`. Convenciones no obvias: backend en `src/<bc>/` con 4 capas, frontend en `frontend/`, tests por incremento en `tests/{unit,integration,features,uat}/incN/`, evidencia de calidad en `quality/reports/`, baselines en `.cm/baselines/`.

---

## Arquitectura interna — reglas no negociables

Monolito modular con **Clean Architecture** interna. Bounded Contexts: Actividad Evaluativa (Core, antes "Sesiones" — ver `ADR-015`), Banco de Preguntas, Identidad, Notificaciones, Analytics.

```
src/<bc>/
├── entities/           → reglas de negocio puras — sin dependencias externas
├── use_cases/          → orquestación — solo importa entities/
├── interface_adapters/ → controllers, presenters, gateways — solo importa use_cases/ (excepción: los gateways SQL importan los modelos ORM de `frameworks/db/models.py`)
└── frameworks/         → FastAPI, SQLAlchemy, WebSockets — implementa puertos
```

**Regla de imports:** las capas internas nunca importan capas externas. Comunicación entre BCs: solo por puertos definidos en `entities/ports/` — nunca imports directos entre BCs. `shared/` es la única excepción transversal: puede tener las 4 capas (`entities/`, `use_cases/`, `interface_adapters/`, `frameworks/`) cuando el contenido es genuinamente transversal — sin lógica de negocio de un BC específico — no solo `entities/` (`ADR-017` para `shared/frameworks/db.py`, `ADR-019` para JWT/RBAC en `shared/entities/`+`frameworks/security/`+`interface_adapters/security/`). Cada BC sigue armando su propio composition root en `frameworks/dependencies.py`, importando de `shared` — nunca de otro BC.

**Estas reglas las hace cumplir `import-linter` en el CI** (`uv run lint-imports`, contratos en `[tool.importlinter]` de `pyproject.toml`): capas dentro de cada BC, solo `frameworks/adapters/` importa de otro BC, `shared` no importa de ningún BC, y solo Analytics lee los modelos ORM de otro BC (`ADR-026`; las tres excepciones que quedaban, #600 a #602, se migraron en la Iteración 4 del Incremento 9 y ya no figuran en `ignore_imports`). La excepción de los gateways SQL está declarada ahí mismo (9 archivos de `identidad` y `banco_preguntas`).

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
| Push/PR a develop | lint + import-linter + tests + DesignReviewer | GitHub Actions CI | Sí |
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
- **"Zone of Pain" de `ArchitectAnalyst` — falso positivo aceptado permanentemente** (`US-ADJ-13`; causa raíz en `US-ADJ-19`, bug upstream [`vvalotto/software_limpio#77`](https://github.com/vvalotto/software_limpio/issues/77): `Ca=Ce=0` para todo el proyecto). No proponer "recalibrar" sin leer antes `docs/specs/ajustes/US-ADJ-13.md` y `US-ADJ-19.md`.
- **`architectanalyst` siempre con `--config pyproject.toml`** (detectado en `BL-012`): sin ese flag no lee
  `[tool.architectanalyst]` y busca `src/coverage.json` (el default) en vez de `../coverage.json` — el
  `CoverageAnalyzer` avisa "no se encontró coverage.json" aunque el archivo exista en la raíz. Con el flag
  reporta el % real. Mismo criterio que `designreviewer`.
- **Orden obligatorio al cerrar baseline: generar `coverage.json` antes de correr
  `architectanalyst`** (`US-ADJ-15`): `CoverageAnalyzer` busca el reporte relativo al `PATH`
  posicional del CLI (`src/` en este proyecto), no a la raíz del repo — con
  `coverage_report_path = "../coverage.json"` (ya configurado) resuelve correctamente contra
  `coverage.json` en la raíz, pero solo si ese archivo ya existe. Generarlo primero con
  `pytest --cov=src --cov-report=json` desde la raíz; si no, `CoverageAnalyzer` reporta warning
  de archivo no encontrado en vez del porcentaje real de cobertura.
- **`LayerViolationsAnalyzer` no es confiable** (mismo bug upstream #77, `US-ADJ-19`): nunca detecta violaciones. La regla de imports entre capas y entre BC la hace cumplir **`import-linter`** (`uv run lint-imports`, Issue #497), que falla en el CI y tiene probada una violación sembrada por contrato (`tests/unit/inc9/test_guarda_arquitectura.py`). Detalle de la herramienta anterior en `docs/specs/ajustes/US-ADJ-19.md`.

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

- ~~**Algoritmo de puntaje en modo en vivo** (RF-10)~~ — **resuelto 2026-09-17** con Víctor,
  antes del event storming del Incremento 6, Iteración 0
  (`docs/plans/inc6/inc6-candidatas.md` §Spike RF-10): `Puntaje = 1000 × FactorTiempo ×
  FactorDificultad × FactorImportancia` (0 si incorrecta), `FactorTiempo` lineal en `[0.5, 1.0]`
  según `tiempo_respuesta`/`tiempo_límite_sesión` (fijo por sesión, sin default),
  `FactorDificultad`/`FactorImportancia` en `{1.0, 1.5, 2.0}` por nivel BAJO/MEDIO/ALTO,
  ranking = suma simple sin bonus por racha.
- **Mecanismo de importación desde PDF** (RF-07): parseo automático vs. asistido. Se decide en Incremento 7.
- **Infraestructura definitiva** (ARQ_v1.md) — **en standby desde 2026-10-17**: depende de si se puede usar
  el convenio de la Universidad con Google (ver bloque del Incremento 8 y `ADR-021`, en revisión). Texto
  anterior: Fly.io confirmado para testing; producción
  pendiente de decisión institucional (nube vs. servidor FIUNER) y del mecanismo de backup
  asociado (`RNF_v1.md` Escenario 2 — mensual, retención 12 meses). Cambio de estrategia
  2026-08-24 (`docs/rf/PLAN_v1.md` revisión 2026-08-24): los Incrementos 3 a 7 corren con datos
  de prueba/locales, no datos reales de estudiantes — esta decisión se resuelve recién en la
  última iteración antes de la prueba funcional de validación previa al despliegue real, no
  antes del Incremento 3 como decía el plan original.
- **Docker en el entorno de desarrollo local**: no instalado a la fecha (2026-07-16). Se
  usará más adelante en el proyecto — hasta entonces, PostgreSQL local corre vía Homebrew
  (ver `docs/rf/PLAN_v1.md` revisión 2026-07-16). El build de imagen Docker en CI/CD no se
  ve afectado — corre en GitHub Actions, no localmente.
- **Criterios de legibilidad en proyección** (RNF_v1.md): tamaño de fuente mínimo y contraste. Se define en etapa de diseño UX antes de Incremento 6.
- **Cuenta de envío SMTP real para Notificaciones en producción** (RF-14, `US-5.1.1` a
  `US-5.1.3`): `SmtpCanalEnvio` ya es agnóstico del proveedor (`smtplib` contra
  `SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM` de `settings.py`) — hoy
  apunta a `localhost:25` sin autenticación, solo para el fake SMTP local de tests/UAT.
  Decisión pendiente sobre qué cuenta real usar como remitente, evaluada 2026-09-10 con
  Víctor: existen cuentas institucionales por materia (ej.
  `gestiondeproyectos@ingenieria.uner.edu.ar`) — usarlas es viable y preferible a que el
  email salga "de parte de" un Docente sin ser su cuenta real (spoofing, rechazado por
  SPF/DKIM del servidor institucional). Implementarlo requiere un salto de alcance respecto
  del diseño actual (una sola cuenta SMTP global para todo el sistema): agregar la
  responsabilidad de resolver qué cuenta usar según la materia de la actividad, con las
  credenciales reales resueltas por variable de entorno (una por materia) — nunca guardadas
  en el dominio (`Materia`) en texto plano, dada la escala real del proyecto (2-3 materias,
  no una tabla de credenciales). Encajaría como ajuste chico (`US-ADJ` o extensión de
  `US-5.1.1`) una vez resuelta la decisión mayor de infraestructura de producción de arriba
  — no tiene sentido implementarlo contra un entorno que todavía no despliega de verdad
  (`cd.yml` solo construye la imagen Docker, `flyctl deploy` sigue comentado).

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
