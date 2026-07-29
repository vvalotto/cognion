# Evidencia UAT — Incremento 1 "BC Identidad"

| Campo | Valor |
|-------|-------|
| Fecha | 2026-07-29 |
| Entorno | Propio (local, PostgreSQL vía Homebrew) |

---

## Capa 1 — Tests automatizados

### Backend

```
$ .venv/bin/python -m pytest tests/unit -q
71 passed

$ .venv/bin/python -m pytest tests/integration -q
38 passed

$ .venv/bin/python -m pytest tests/step_defs -q
23 passed
```

Total backend: **132/132 tests** (71 unitarios + 38 integración contra Postgres real + 23
BDD). `ruff check src/`: 0 violaciones. `mypy src/`: 0 errores (79 archivos). `codeguard
src/`: 0 errores, 1 advertencia (B101, patrón ya aceptado), 236 informativos.

### Frontend

```
$ npx vitest run --coverage
Test Files  13 passed (13)
     Tests  46 passed (46)

Statements   : 93.61% ( 132/141 )
Branches     : 88.05% ( 59/67 )
Functions    : 94.73% ( 36/38 )
Lines        : 93.52% ( 130/139 )
```

`oxlint`: 0 errores (1 warning preexistente, no introducido en este incremento).
`tsc --noEmit`: 0 errores.

---

## Capa 2 — HTTP (smoke test end-to-end)

```
$ .claude/skills/run-cognion/smoke.sh
== Postgres ==
OK
== Arrancando fake SMTP (puerto 2525) ==
OK
== Arrancando backend (puerto 8000) ==
== GET /health ==
OK (200)
== Bootstrap Administrador (scripts/seed_admin.py, ADR-016) ==
Administrador creado: 5a24859a-713c-4cb0-9f5d-0805d86e32fd (smoketest-8559-admin@fiuner.edu.ar)
OK
== POST /identidad/login (administrador) ==
OK (token obtenido)
== POST /usuarios (docente) ==
OK (id=e9314551-7526-40f7-8bb4-8ed01b6a650a)
== POST /comisiones ==
OK (id=9eab0336-f86c-4df1-b903-228417e44533)
== POST /comisiones/{id}/docentes ==
OK (200)
== POST /identidad/login (docente) ==
OK (token obtenido)
== POST /comisiones/{id}/invitaciones (docente) ==
OK (id=2e3b207f-2fee-46a5-8846-32c9b077174f)
== POST /identidad/registro con invitación vigente (US-1.1.8) ==
OK (materia=Smoke Test)
== POST /identidad/registro con token ya usado (esperado 422) ==
OK (422)
== POST /usuarios con email duplicado (esperado 409) ==
OK (409)

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

Cubre el flujo DoD completo: alta de Docente → creación de Comisión → asignación →
invitación → registro de Estudiante con token real → asignación automática a la
comisión, más los dos casos de error (409, 422).

---

## Capa 2 — UAT manual en navegador real (Víctor)

Flujo ejercitado: login como Administrador (`POST /identidad/login` real) → redirección a
`/docentes/nuevo` → formulario de alta de Docente (`POST /usuarios` real) →
`/docentes/nuevo/exito` con confirmación.

### Hallazgos (clasificados según `PROCEDIMIENTO-UAT.md` §8)

| Hallazgo | Severidad | Resolución |
|----------|-----------|------------|
| Backend sin `CORSMiddleware` — el navegador bloqueaba toda llamada real del frontend (preflight `OPTIONS` fallido, `Failed to fetch`) | 🔴 Bloqueante para el canal navegador (vía `curl`/Capa 2 automatizada no se manifestaba) | Resuelto en el mismo cierre — `src/app.py`, commit `3c94bad` |
| Estilo no respetaba el prototipo aprobado (`US-1.0.2`): regla CSS heredada sin `@layer` pisando las utilities de Tailwind + paleta/tipografía no institucionales | 🟡 Observación (el flujo funcional no se interrumpía, pero el criterio de aceptación de UX del incremento no se cumplía) | Resuelto dentro de `US-1.1.9` (commit `e18c651`) — ver adenda en `docs/reports/inc1/US-1.1.9-report.md` |

Ambos hallazgos fueron **resueltos antes del cierre de la baseline** — no quedan
Bloqueantes sin resolver (`PROCEDIMIENTO-UAT.md` §9).

Tras la corrección, se repitió el flujo completo en navegador real: login → alta de
Docente → confirmación, con la paleta institucional aplicada — capturas verificadas
manualmente en la sesión de cierre del incremento.

---

## Resultado

Sin hallazgos 🔴 Bloqueantes sin resolver. Criterio de aceptación de `design.md`
cumplido — flujo DoD completo, Capa 1 y Capa 2 aprobadas.

**UAT: ✅ Aprobado.**
