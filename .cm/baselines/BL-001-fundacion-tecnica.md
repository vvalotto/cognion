# BL-001 — Fundación Técnica (Incremento 0)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento |
| Fecha apertura | 2026-07-16 |
| Fecha cierre | 2026-07-16 |
| Git tag inicial | `v0.1.0` |
| Git tag cierre | `v0.2.0` |
| Estado | ✅ Completado |
| DoD | Pipeline técnico funcionando de punta a punta en el entorno local: push a `develop` dispara CI en verde (lint + tests + DesignReviewer); PostgreSQL local recibe una migración de Alembic aplicada con éxito; la app expone `GET /health` → 200; push/merge a `main` construye la imagen Docker sin errores. Deploy a un entorno real y su healthcheck quedan explícitamente fuera de alcance — pendientes de la decisión de infraestructura (`ARQ_v1.md`, ítem abierto). |

---

## Descripción

Cierra el Incremento 0 de `PLAN_v1.md`: fundación técnica sin lógica de negocio — esqueleto
de Clean Architecture, PostgreSQL local, Alembic inicializado, y evidencia real de un
pipeline CI/CD integrado. Docker para infraestructura local (Docker Compose) queda diferido
a un incremento posterior — no estaba disponible en el entorno de desarrollo; PostgreSQL
corrió vía Homebrew en su lugar (ver `docs/rf/PLAN_v1.md`, revisión 2026-07-16). El build de
imagen Docker en CI/CD no se ve afectado por esa ausencia, porque corre en GitHub Actions.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D12 | `docs/rf/PLAN_v1.md` (revisión 2026-07-16) | Documento | Docker local diferido; PostgreSQL vía Homebrew documentado |
| CI-D13 | `docs/aprendizajes/HITO-3-*.md` | Documento | Inconsistencia entre `CLAUDE.md` y `WORKFLOW-DESARROLLO.md` sobre `incN-candidatas.md` |
| CI-D14 | `quality/reports/uat/inc0/design.md` + `evidencia.md` | Documento | UAT Capa 2 — diseño y evidencia |
| CI-C01 | `src/settings.py` | Código de backend | Configuración desde `.env` (pydantic-settings) |
| CI-C02 | `migrations/` + `alembic.ini` | Código de backend | Alembic async inicializado, primera migración (`696c5efea732`) |
| CI-C03 | `tests/unit/inc0/test_health.py` | Código de backend | Primer test real del proyecto — retira la tolerancia de "0 tests" en CI |
| CI-T04 | `pyproject.toml` — `[tool.mypy] plugins` | Herramienta | Plugin `pydantic.mypy` — evita falsos positivos de mypy --strict en `BaseSettings` |

---

## Métricas al cerrar

- `uv run pytest`: 1 passed (antes: 0 tests tolerados)
- `uv run ruff check src/ migrations/`: 0 violaciones
- `uv run mypy src/`: 0 errores (30 archivos)
- `designreviewer src/ --config pyproject.toml`: 0 violaciones
- `codeguard src/`: 0 errores, 0 advertencias, 90 informativos
- `architectanalyst src/ --sprint-id BL-001`: 1 crítico, 1 warning — ambos leídos y
  aceptados (ver Decisiones técnicas relevantes), `should_block: false`

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| PostgreSQL local vía Homebrew en vez de Docker Compose | Docker no estaba disponible en el entorno de desarrollo. Se decide usarlo más adelante en el proyecto — queda como ítem abierto en `CLAUDE.md`. Alembic corre igual, sin cambios, contra la instancia de Homebrew. |
| `settings.py` aceptado como "Zone of Pain" (D=1.00) en ArchitectAnalyst | Falso positivo de calibración: el módulo está fuera de las 4 capas de Clean Architecture que la herramienta conoce (`entities/use_cases/interface_adapters/frameworks`), por lo que Ca=Ce=0 no es representativo. Agregar abstracciones artificiales sería sobre-ingeniería. |
| UAT Capa 1 (dominio) y checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4) no ejecutados | El Incremento 0 no tiene dominio (Capa 1 no aplica) y no hay entorno de staging desplegado todavía (mismo ítem abierto de infraestructura). Documentado en `quality/reports/uat/inc0/design.md`, no es un gap nuevo. |
| Próximo paso de `CLAUDE.md` corregido antes de ejecutar el incremento | Pedía `docs/plans/inc0/inc0-candidatas.md`, artefacto que `WORKFLOW-DESARROLLO.md` §3 reserva para incrementos con US-IEDD — el Incremento 0 usa el ciclo §6 (técnico sin US). Ver `HITO-3`. |
| Skill `/docs-audit` creado antes de ejecutar el incremento | Deriva de la experiencia de AtaraxiaDive (deriva documental). Cierra 4 huérfanos detectados en `docs/inventario/`. Ver `HITO-2`. |

---

## Retrospectiva

### ¿Qué funcionó?

- Verificar la disponibilidad real de herramientas (Docker) antes de ejecutar el plan
  evitó quedar bloqueados a mitad de tarea — se detectó y resolvió el reemplazo (Homebrew)
  como decisión explícita, documentada, antes de escribir una sola línea de configuración.
- El criterio de "leer completo antes de asumir" (aplicado en `HITO-1` y `HITO-3`) se
  repitió acá: antes de ejecutar el checklist de cierre de baseline (§7), se auditó cuáles
  de sus 8 pasos aplicaban realmente a un incremento sin dominio y sin entorno de staging,
  en vez de correrlos mecánicamente.
- El hallazgo crítico de ArchitectAnalyst se leyó e interpretó (no se ignoró ni se
  "arregló" artificialmente) — consistente con la regla de que ArchitectAnalyst es
  siempre manual.

### ¿Qué fue más difícil de lo esperado?

- El propio `PLAN-CM.md` §11 da un DoD de ejemplo para el Incremento 0 que incluye
  "healthcheck del entorno destino responde 200" — inconsistente con el propio Hito de
  `PLAN_v1.md`, que excluye explícitamente el deploy real de este incremento. No se
  corrigió `PLAN-CM.md` en esta sesión (queda para una revisión posterior si genera
  confusión real) — se documentó la precedencia (el Hito de `PLAN_v1.md` manda sobre el
  ejemplo ilustrativo de `PLAN-CM.md`).

### ¿Qué ajustar en el próximo incremento?

- Cuando se adopte Docker (fecha no definida), migrar PostgreSQL local de Homebrew a
  Docker Compose sin tocar Alembic ni el dominio — la revisión de `PLAN_v1.md` del
  2026-07-16 ya deja este paso previsto.
- Recalibrar los umbrales de `[tool.architectanalyst]` cuando el Incremento 1 (BC
  Identidad) agregue el primer módulo real dentro de las 4 capas — el falso positivo de
  `settings.py` no debería repetirse para código de dominio real.

---

*Creado: 2026-07-16*
