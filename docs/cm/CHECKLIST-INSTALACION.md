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

- [ ] Crear `.claude/hooks/check-session-start.sh` — hook `SessionStart`, verifica si existe
      `session-needs-summary.flag` y obliga a resumir la sesión anterior antes de continuar
- [ ] Crear `.claude/hooks/save-session.sh` — hook `SessionEnd`, captura git status/branch y
      commits desde la última sesión, actualiza `session-current.md` y `session-metadata.json`
- [ ] Registrar ambos hooks en `.claude/settings.json`:
  ```json
  {
    "hooks": {
      "SessionStart": [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/check-session-start.sh"}]}],
      "SessionEnd": [{"hooks": [{"type": "command", "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/save-session.sh"}]}]
    }
  }
  ```
- [ ] Crear `.claude/commands/checkpoint.md` — slash command para checkpoints proactivos de sesión
- [ ] Crear `.claude/commands/resume.md` — slash command para restaurar contexto al iniciar sesión
- [ ] Crear carpeta de memoria de sesión (ruta análoga a la de AtaraxiaDive, ajustada al path de Cognion):
  ```
  ~/.claude/projects/-Users-victor-PycharmProjects-cognion/memory/
  ├── session-metadata.json
  ├── session-current.md
  └── session-history.md
  ```

---

## 7. GitHub — gestión administrativa

- [ ] Confirmar que el repo `cognion` tiene Issues habilitado
- [ ] Crear Milestone del primer Incremento (Incremento 0 — Walking Skeleton)
- [ ] Definir Labels: `us-iedd`, `incremento-0`, `incremento-1`, ..., `blocked`, `in-progress`, `done`
- [ ] Confirmar branch `develop` creado desde `main` para integración continua

---

## 8. CI/CD (ver `PLAN-CM.md` §11 — pipeline automático real, no deploy manual)

- [ ] Crear workflow de GitHub Actions para push/PR a `develop`: lint (ruff/mypy/eslint) +
      tests (pytest + tests frontend) + `designreviewer --config pyproject.toml`
- [ ] Crear workflow separado (o job condicional) para merge/tag a `main`: build de imagen
      Docker multi-stage + deploy automático + verificación de healthcheck post-deploy
- [ ] Crear `Dockerfile` multi-stage (frontend build → backend runtime) — convención en `PLAN-CM.md` §11
- [ ] Confirmar despliegue automático a la infraestructura elegida (Fly.io — ver ítem abierto
      de infraestructura definitiva en `docs/rf/ARQ_v1.md`)
- [ ] Configurar `alembic upgrade head` como paso del pipeline de deploy, no del build de la imagen

---

## 9. Frontend

- [ ] `npm install` en `frontend/` una vez creado el scaffold (React 19 + Vite + TypeScript + Tailwind + shadcn/ui)
- [ ] Configurar ESLint

---

## 10. Verificación final antes del Incremento 0

- [ ] `uv run pytest` corre sin errores (aunque no haya tests aún, el comando debe resolver)
- [ ] `codeguard src/` corre sin errores de configuración
- [ ] `designreviewer src/ --config pyproject.toml` corre sin errores de configuración
- [ ] Push de prueba a una branch de prueba confirma que el pre-push hook se activa
- [ ] `gh issue list` y `gh pr list` responden correctamente contra el repo `cognion`
