# BL-002 — BC Identidad (Incremento 1)

| Campo | Valor |
|-------|-------|
| Tipo | Incremento |
| Fecha apertura | 2026-07-16 |
| Fecha cierre | 2026-07-29 |
| Git tag inicial | `v0.2.0` |
| Git tag cierre | `v0.3.0` |
| Estado | ✅ Completado |
| DoD | Un estudiante se registra vía link de invitación y queda asignado automáticamente a su comisión; un docente y un administrador se autentican y reciben un JWT con su rol correcto. Corre en el entorno local sobre la fundación técnica del Incremento 0 (`docs/plans/inc1/inc1-candidatas.md` §DoD del Incremento). Backend y frontend implementados e integrados juntos — criterio de cierre de baseline de `docs/plans/PLAN-CM.md` §7 (decisión 2026-07-24). |

---

## Descripción

Cierra el Incremento 1 de `PLAN_v1.md`: BC Identidad completo, RF-01 (registro por
invitación) y RF-02 (autenticación y RBAC por rol) implementados de punta a punta —
backend (Iteración 1, `US-1.1.0` a `US-1.1.5`) y frontend (Iteración 2, `US-1.1.6` a
`US-1.1.9`). Incluye la corrección de dos hallazgos de UAT manual en navegador real
detectados al cierre de la última US (`US-1.1.9`): falta de CORS en el backend y un bug de
cascada CSS + paleta no institucional en el frontend, ambos presentes desde `US-1.1.6`/`1.1.7`
sin detectarse antes por depender de una verificación visual real, no solo de tests con
`fetch` mockeado.

---

## Inventario de Configuration Items

| CI | Artefacto | Tipo | Descripción |
|----|-----------|------|-------------|
| CI-D15 | `ADR-012`, `ADR-013`, `ADR-014` | Documento | Invitación (expiración 7 días, sin recuperación), JWT (60 min, sin refresh/blacklist), hashing bcrypt — decisiones resueltas 2026-07-16, previas al incremento |
| CI-D16 | `ADR-016-bootstrap-primer-administrador.md` | Documento | Bootstrap del primer Administrador vía `scripts/seed_admin.py` (bypassa la API, problema de huevo-y-gallina) |
| CI-D17 | `ADR-017`, `ADR-018` | Documento | Engine/sesión SQLAlchemy compartidos (`shared/frameworks/db.py`), `NullPool` |
| CI-D18 | `ADR-011-estandares-interfaz-shadcn-wcag.md` | Documento | Estándares de interfaz frontend (shadcn/ui, WCAG) |
| CI-D19 | `docs/design/domain/BC-identidad-modelo.md` | Documento | Event storming del BC Identidad (`US-1.0.1`) |
| CI-D20 | `docs/design/ux/wireframes-identidad.md` + prototipo | Documento | Wireframes y prototipo navegable de Identidad (`US-1.0.2`), gate UX de todo el frontend de este incremento |
| CI-D21 | `docs/plans/PLAN-CM.md` §7 (revisión 2026-07-24) | Documento | Decisión: la baseline no cierra backend-only, exige frontend implementado e integrado |
| CI-C04 | `src/identidad/` (BC completo) | Código de backend | Entities/use_cases/interface_adapters/frameworks — `Usuario`, `Comisión`, `Invitación`, RBAC (`US-1.1.0` a `US-1.1.5`) |
| CI-C05 | `src/shared/frameworks/db.py` | Código de backend | Engine y sesión async de SQLAlchemy compartidos entre BCs (`ADR-017`/`018`) |
| CI-C06 | `scripts/seed_admin.py` | Código de backend | Bootstrap del primer Administrador (`ADR-016`) |
| CI-C07 | `src/app.py` — `CORSMiddleware` | Código de backend | Corrección de UAT (`US-1.1.9`) — gap preexistente desde `US-1.1.7`, invisible en Vitest |
| CI-F01 | `frontend/src/router.tsx`, `lib/api-client.ts`, `lib/session.ts` | Código de frontend | Infraestructura de frontend: routing, cliente API con manejo de JWT/401/403, sesión (`US-1.1.6`) — primer CI-F del proyecto |
| CI-F02 | `frontend/src/pages/Login.tsx`, `LoginError.tsx` | Código de frontend | Login por rol (`US-1.1.7`) |
| CI-F03 | `frontend/src/pages/Registro*.tsx` | Código de frontend | Registro por invitación (`US-1.1.8`), incluye ampliación de `RegistroResponse.materia` |
| CI-F04 | `frontend/src/pages/AltaDocente*.tsx`, `components/RequireRole.tsx` | Código de frontend | Alta de Docente por Administrador (`US-1.1.9`), guard de ruta por rol |
| CI-F05 | `frontend/src/index.css`, `components/Logo.tsx`/`TopStrip.tsx`, `layouts/*` | Código de frontend | Corrección de UAT — paleta/tipografía institucional del prototipo, bug de cascada CSS sin `@layer` |
| CI-T05 | `.claude/skills/run-cognion/smoke.sh` + `fake_smtp.py` | Herramienta | Driver de smoke test end-to-end del backend (alta usuario/comisión/asignación/invitación/registro + casos de error) |

---

## Métricas al cerrar

**Backend:**
- `pytest tests/`: 132 passed (71 unitarios + 38 integración + 23 BDD/step_defs)
- `ruff check src/`: 0 violaciones
- `mypy src/`: 0 errores (79 archivos)
- `codeguard src/`: 0 errores, 1 advertencia (B101, patrón ya aceptado), 236 informativos
- `smoke.sh` (end-to-end real contra Postgres): `SMOKE TEST OK` — UAT Capa 2 (`PROCEDIMIENTO-UAT.md`)

**Frontend:**
- `vitest run`: 46/46 tests, 13 archivos
- Cobertura: 93.61% statements / 88.05% branches (umbral `vitest.config` 80%)
- `oxlint`: 0 errores, 1 warning preexistente (no introducido en este incremento)
- `tsc --noEmit`: 0 errores

**Diseño:**
- `designreviewer src/ --config pyproject.toml` (CI del último PR, #35): 0 CRITICAL, 27 advertencias
- `architectanalyst src/ --sprint-id BL-002`: 3 críticos (Zone of Pain: `identidad`, `settings`, `shared` — leídos y aceptados, ver Decisiones), 3 warnings, `should_block: false` (`quality/reports/architectanalyst/BL-002-arquitectura.json`)

---

## Decisiones técnicas relevantes

| Decisión | Contexto |
|----------|----------|
| Criterio de cierre de baseline: backend + frontend juntos | `PLAN_v1.md` no separa frontend como iteración propia — el Hito se redacta en comportamiento observable ("un estudiante se registra"), no solo verificable por `pytest`/`curl`. Decisión registrada 2026-07-24 al cierre de la Iteración 1 (`docs/plans/PLAN-CM.md` §7). |
| Ampliación de `RegistroResponse.materia` (`US-1.1.8`) | El wireframe pedía mostrar el nombre de la comisión, pero solo se exponía `comision_id` (UUID). Gap detectado en Fase 2 de planificación, antes de escribir código — se amplió el backend reutilizando un puerto ya existente (`ComisionRepositoryPort.obtener_por_id`), sin decisión arquitectónica nueva. |
| Guard de ruta `RequireRole` (`US-1.1.9`) | El `.feature` de la spec asumía ruta protegida por rol, pero `router.tsx`/`AppLayout.tsx` (`US-1.1.6`) no tenían ningún guard client-side — el 401/403 de `US-1.1.6` es reactivo, no un guard de navegación. Gap detectado en Fase 2. Se agregó un componente reutilizable, pensando en próximas rutas protegidas por rol. |
| Corrección de UAT — CORS y estilo institucional (`US-1.1.9`) | Un smoke test manual de Víctor en navegador real detectó dos gaps invisibles a Vitest: (1) falta de `CORSMiddleware` en el backend, bloqueaba cualquier llamada real del frontend; (2) una regla CSS heredada sin `@layer` en `index.css` (boilerplate de un starter genérico) pisaba las utilities de Tailwind, y la paleta/tipografía no eran las institucionales del prototipo aprobado (`US-1.0.2`). Ambos gaps existían desde `US-1.1.6`/`1.1.7` — se corrigieron dentro de `US-1.1.9` a pedido explícito de Víctor, aunque afectan a toda la app. |
| Bug de CodeGuard/mypy en frío (`software_limpio#70`) | El check de tipos integrado en CodeGuard invoca mypy sin `--cache-dir` y con timeout de 10s — en corridas en frío puede superar ese tiempo y quedar mudo. Parche local: hook `mypy` dedicado sobre `src/` completo (mismo comando que CI), bloqueante, como fuente de verdad local para tipos. |
| ArchitectAnalyst — 3 críticos "Zone of Pain" aceptados | `identidad`, `settings` y `shared` miden D≈1.0 (estables pero concretos) a nivel de paquete raíz — `settings` ya estaba así en `BL-001` (mismo falso positivo de granularidad: el módulo queda fuera de las 4 capas que la herramienta conoce). `identidad`/`shared` son nuevos en este incremento, sin dato de tendencia previo. No amerita agregar abstracciones artificiales — ver "Qué ajustar" en la retrospectiva. |

---

## Retrospectiva

### ¿Qué funcionó?

- Detectar gaps spec-vs-código en Fase 2 de planificación (antes de escribir código) evitó
  rework en dos US seguidas: `materia` en `US-1.1.8` y `RequireRole` en `US-1.1.9` — mismo
  patrón, ya consolidado como hábito del equipo.
- El smoke test de backend (`smoke.sh`) como verificación end-to-end reutilizable detectó
  con confianza que el flujo real (alta → invitación → registro, casos de error) seguía
  funcionando después de cada cambio, sin depender solo de tests unitarios mockeados.
- Pedir un UAT manual en navegador real al cierre de la última US de la iteración — aunque
  tardío — sí encontró los dos gaps reales (CORS, estilo) que ninguna otra capa de
  verificación (Vitest, CI, DesignReviewer) podía detectar por diseño.

### ¿Qué fue más difícil de lo esperado?

- El estilo institucional aprobado en el prototipo (`US-1.0.2`) nunca se verificó
  visualmente en un navegador real durante las primeras tres US de frontend (`US-1.1.6` a
  `1.1.8`) — la regla del proyecto de "iniciar el servidor y probar en un navegador antes de
  reportar como completo" no se aplicó de forma consistente hasta el cierre de la última US
  de la iteración, permitiendo que un bug de cascada CSS y una paleta incorrecta
  persistieran sin detectarse durante 3 historias completas.
- La decisión de exigir backend y frontend juntos para cerrar la baseline (`PLAN-CM.md` §7)
  surgió a mitad del incremento (2026-07-24, tras cerrar la Iteración 1 de solo backend) en
  vez de estar prevista desde la planificación inicial — funcionó, pero fue una corrección
  de rumbo reactiva, no proactiva.

### ¿Qué ajustar en el próximo incremento?

- Agregar un paso explícito de "smoke test visual en navegador real" al cierre de **cada**
  US de frontend (no solo al final de la iteración) — evita acumular deuda de UX invisible
  a Vitest durante varias historias seguidas.
- Recalibrar los umbrales de `[tool.architectanalyst]` ahora que `identidad` es el primer BC
  real dentro de las 4 capas de Clean Architecture — decidir si el "Zone of Pain" a nivel de
  paquete raíz amerita exponer abstracciones a ese nivel, o si sigue siendo un falso positivo
  de granularidad de la herramienta (mismo caso que `settings.py` en `BL-001`).

---

*Creado: 2026-07-29*
