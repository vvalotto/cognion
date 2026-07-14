# Checklist de Instalación — Cognion

> Estado documental: operativo
> Uso principal: guía de arranque del entorno de desarrollo antes de iniciar el Incremento 0
> Fuente normativa relacionada: `docs/cm/PLAN-CM.md`
> Última actualización: 2026-07-13

---

## 1. Propósito

Checklist de herramientas y artefactos que deben instalarse/configurarse en Cognion antes
de arrancar el Incremento 0 (Walking Skeleton) de `docs/rf/PLAN_v1.md`. Es la lista de
arranque — el "por qué" de cada herramienta y su rol en el ciclo de desarrollo está en
`docs/cm/PLAN-CM.md` y en `docs/cm/WORKFLOW-DESARROLLO.md` (a crear).

Marcar cada ítem al completarlo. No se avanza al Incremento 0 con ítems obligatorios sin marcar.

---

## 2. Runtime y gestores

- [x] **Python 3.11+** — 3.12.0
- [x] **uv** (gestor de paquetes/venv) — 0.9.18
- [x] **Node.js + npm** (frontend React + Vite) — Node 22.17.0 / npm 10.9.2
- [x] **gh CLI** — 2.96.0
- [x] **jq** — 1.7.1

---

## 3. Quality agents (`software_limpio`)

- [x] Agregar a `pyproject.toml` — `[tool.uv.sources]` con git source
- [x] Instalar como dependencia de desarrollo — `uv sync --all-groups`
- [x] Configurar `[tool.codeguard]` — min_pylint_score=8.0, max_cyclomatic_complexity=10
- [x] Configurar `[tool.designreviewer]` — calibrado para Clean Architecture (max_cbo=10, max_wmc=25)
- [x] Configurar `[tool.architectanalyst]` — layers: entities/use_cases/interface_adapters/frameworks
- [x] Crear `.githooks/pre-push` con: `designreviewer src/ --config pyproject.toml`
- [x] Crear `.pre-commit-config.yaml` con hooks: black, isort, ruff, codeguard
- [x] `git config core.hooksPath .githooks` — ejecutado manualmente

---

## 4. Herramientas estándar de calidad Python (PyPI)

- [x] black, isort, ruff, mypy, pylint, pre-commit — incluidos en `[dependency-groups] dev`
- [x] pytest, pytest-asyncio, pytest-bdd, pytest-cov — incluidos en `[dependency-groups] dev`
- [x] Configurar secciones `[tool.black]`, `[tool.isort]`, `[tool.ruff]`, `[tool.mypy]`,
      `[tool.pytest.ini_options]`, `[tool.coverage.run]` en `pyproject.toml`

---

## 5. Claude Dev Kit

- [x] Instalar desde `~/PycharmProjects/claude-dev-kitc/install/installer.py --profile fastapi-rest --yes --force`
- [x] Verificar que quedaron instalados:
  - `.claude/skills/implement-us/` (skill.md, config.json, phases/, customizations/)
  - `.claude/tracking/tracker_cli.py` + `time_tracker.py`
- [x] Perfil propio creado: `.claude/skills/implement-us/customizations/clean-architecture-bc.json`
      (capas: entities/use_cases/interface_adapters/frameworks — no el layered genérico de fastapi-rest)
- [x] `config.json` actualizado con `architecture_pattern: clean-architecture` y componentes de CA

---

## 6. Gestión de sesión (hooks + commands propios, no son de terceros)

- [x] Crear `.claude/hooks/check-session-start.sh` — avisa si hay sesión sin resumir
- [x] Crear `.claude/hooks/save-session.sh` — captura git state y activa flag al cerrar
- [x] Registrar ambos hooks en `.claude/settings.json` (SessionStart / SessionEnd)
- [x] Crear `.claude/commands/checkpoint.md` — slash command /checkpoint
- [x] Crear `.claude/commands/resume.md` — slash command /resume
- [x] Crear archivos de memoria de sesión en:
      `~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/`
      (session-metadata.json, session-current.md, session-history.md)

---

## 7. GitHub — gestión administrativa

- [x] Issues habilitado en el repo
- [x] Milestone creado: "Incremento 0 — Walking Skeleton" (#1)
- [x] Labels creados: us-iedd, incremento-0..6, blocked, in-progress, done
- [x] Branch `develop` creado y pusheado desde `main`

---

## 8. CI/CD (ver `PLAN-CM.md` §11 — pipeline automático real, no deploy manual)

- [x] `.github/workflows/ci.yml`: lint (ruff, mypy, eslint) + pytest + DesignReviewer en push/PR a develop
- [x] `.github/workflows/cd.yml`: build Docker en push/tag a main — deploy y healthcheck comentados hasta definir infraestructura
- [x] `Dockerfile` multi-stage (node:22 frontend build → python:3.12-slim runtime)
- [x] `.dockerignore` creado
- [ ] Deploy automático a Fly.io — pendiente de decisión de infraestructura (ítem abierto ARQ_v1.md)
- [x] `alembic upgrade head` documentado como paso del pipeline de deploy (comentado en cd.yml hasta tener DB)

---

## 9. Frontend

- [x] `npm install` en `frontend/` — React 19 + Vite + TypeScript
- [x] Tailwind CSS v4 instalado con plugin `@tailwindcss/vite`
- [x] shadcn/ui inicializado (preset nova, Base library)
- [x] Path aliases configurados (`@/*` → `./src/*`) en tsconfig.app.json y vite.config.ts
- [x] Linter: oxlint (reemplaza ESLint en el template de Vite — más rápido, mismo objetivo)
- [x] Build verificado: `npm run build` exitoso

---

## 10. Verificación final antes del Incremento 0

- [x] `uv run pytest` corre sin errores (0 tests collected — correcto en esta etapa)
- [x] `codeguard src/` — 0 errores, 0 advertencias, 87 informativos
- [x] `designreviewer src/ --config pyproject.toml` — 0 violaciones detectadas
- [x] Push a `develop` confirma que el pre-push hook se activa (DesignReviewer corrió antes del push)
- [x] `gh issue list` y `gh pr list` responden correctamente contra el repo `cognion`
