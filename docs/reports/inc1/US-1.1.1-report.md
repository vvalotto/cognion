# Reporte de Implementación: US-1.1.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.1 - Docente genera link de invitación para una comisión
- **Puntos estimados:** 3
- **Tiempo real:** ~35 min hasta cierre de Fase 7 + Fase 5 sin medir (gap de tracking, ver
  Lecciones Aprendidas) — tracking de ejecución del agente, no comparable contra esfuerzo
  humano (nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-07-22

Segunda US de la Iteración 1 (BC Identidad). Con `US-1.1.0` resuelta (Usuario/Comisión/
asignación de Docente), esta US habilita el paso siguiente de RF-01: un Docente asignado a
una Comisión puede generar una invitación con token único y expiración a 7 días (`ADR-012`),
que envía por email — precondición de `US-1.1.2` (registro de Estudiante por invitación).

---

## Componentes Implementados

### Entities (`src/identidad/entities/`)
- ✅ `invitacion.py` — aggregate `Invitacion`, `crear()` genera token único
  (`secrets.token_urlsafe(32)`) y `expira_en = generada_en + 7 días` (INV-ID-02, `ADR-012`)
- ✅ `eventos.py` (editado) — `InvitacionGenerada`
- ✅ `errors.py` (editado) — `DocenteNoAsignadoAComision` (INV-ID-08)
- ✅ `ports/invitacion_repository_port.py`, `ports/notificador_port.py`

### Use Cases (`src/identidad/use_cases/`)
- ✅ `GenerarInvitacionUseCase` — valida INV-ID-08 (`docente_id` ∈ `docentes_asignados`),
  genera y persiste la invitación, envía el email, emite `InvitacionGenerada`

### Interface Adapters (`src/identidad/interface_adapters/`)
- ✅ `controllers/invitaciones_controller.py`
- ✅ `gateways/invitacion_repository.py` — `SQLAlchemyInvitacionRepository`

### Frameworks (`src/identidad/frameworks/`)
- ✅ `smtp/notificador_smtp.py` — `SmtpNotificador`, `smtplib` en `asyncio.to_thread`
  (no bloquea el event loop)
- ✅ `db/models.py` (editado) — `InvitacionModel`
- ✅ `api/schemas.py` (editado) — `GenerarInvitacionRequest`, `InvitacionResponse`
- ✅ `api/invitaciones_router.py` — `POST /comisiones/{comision_id}/invitaciones`
- ✅ `dependencies.py` (editado) — `get_notificador()`, `get_invitaciones_controller()`

### Configuración
- ✅ `src/settings.py` (editado) — `smtp_host/port/user/password/from` con defaults
- ✅ `.env.example` (editado) — variables `SMTP_*`

### Migraciones
- ✅ `migrations/versions/479b36fd0759_invitacion.py` — tabla `invitacion`, aplicada contra
  Postgres local

### Integración
- ✅ `src/app.py` (editado) — `invitaciones_router` registrado

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| POST | `/comisiones/{comision_id}/invitaciones` | Generar invitación para la Comisión | ⚠️ Pendiente — sin guard todavía, se agrega en `US-1.1.5` |

**OpenAPI Docs:** `/docs`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.58/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 3 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 55.58 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% | ≥ 95.0% | ✅ |

Fuente: `quality/reports/inc1/US-1.1.1-quality.json`. Coverage medido sobre
`entities`/`use_cases`/`interface_adapters` de esta US (116/116 statements) —
`frameworks/` excluido del gate por convención del proyecto (`pyproject.toml`).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (9 tests) — `tests/unit/inc1/`
- `test_invitacion.py` — aggregate `Invitacion` (3 tests)
- `test_generar_invitacion_use_case.py` — use case con fakes de los ports (4 tests)
- `test_invitaciones_controller.py` (1 test)
- `test_notificador_smtp.py` — `SmtpNotificador` mockeando `smtplib.SMTP` (2 tests)

### Tests de Integración (4 tests) — `tests/integration/inc1/`
- `test_invitacion_repository_integration.py` (1 test) — gateway SQLAlchemy contra Postgres
  local real
- `test_invitaciones_api_integration.py` (3 tests) — endpoint FastAPI vía `httpx.AsyncClient`,
  con un stub SMTP local (fixture `fake_smtp_server`) para no depender de un servidor SMTP real

### Escenarios BDD (2 escenarios) — `tests/features/inc1/US-1.1.1-*.feature` + `tests/step_defs/inc1/`
- Docente asignado genera invitación
- Rechazo por Docente no asignado a la comisión

**Todos los tests pasando:** ✅ 53/53 (suite completa del proyecto)

---

## Migraciones de Base de Datos

- ✅ `migrations/versions/479b36fd0759_invitacion.py`
  - Tabla `invitacion` (FK a `comision.id` y `docente.id`, `token` único)
  - Aplicada contra PostgreSQL local (`alembic upgrade head`)

---

## Ajustes de Alcance Resueltos con Víctor (antes del plan)

1. **Sin JWT/guard todavía:** el endpoint recibe `docente_id` explícito en el body (mismo
   patrón que `POST /comisiones/{id}/docentes` de US-1.1.0) — `US-1.1.4` (login/JWT) todavía
   no existe. INV-ID-08 se valida igual en el use case, independiente del mecanismo de
   autenticación.
2. **`email_destinatario` agregado al comando:** la spec original (`GenerarInvitacion(comision_id,
   docente_id)`) no incluía a quién mandar el email, pero la postcondición exige el envío
   (`ADR-012`). Se agregó como parámetro del comando y del request, sin persistirlo en el
   aggregate `Invitación`.

---

## Archivos Creados/Modificados

**Producción:** `src/identidad/entities/invitacion.py`, `entities/eventos.py` (editado),
`entities/errors.py` (editado), `entities/ports/invitacion_repository_port.py`,
`entities/ports/notificador_port.py`, `use_cases/generar_invitacion.py`,
`interface_adapters/controllers/invitaciones_controller.py`,
`interface_adapters/gateways/invitacion_repository.py`, `frameworks/smtp/notificador_smtp.py`,
`frameworks/db/models.py` (editado), `frameworks/api/schemas.py` (editado),
`frameworks/api/invitaciones_router.py`, `frameworks/dependencies.py` (editado),
`src/settings.py` (editado), `src/app.py` (editado),
`migrations/versions/479b36fd0759_invitacion.py` — ~250 líneas.

**Tests:** `tests/unit/inc1/test_invitacion.py`, `test_generar_invitacion_use_case.py`,
`test_invitaciones_controller.py`, `test_notificador_smtp.py`, `_fakes.py` (editado),
`tests/integration/inc1/test_invitacion_repository_integration.py`,
`test_invitaciones_api_integration.py`, `tests/integration/conftest.py` (editado),
`tests/step_defs/inc1/test_us_1_1_1_steps.py`,
`tests/features/inc1/US-1.1.1-generar-invitacion.feature` — ~470 líneas.

**Configuración:** `.env.example` (editado), `pyproject.toml` (editado — markers
`US-1.1.1`/`generar-invitacion`).

**Documentación:** `docs/plans/inc1/US-1.1.1-{context,plan}.md`,
`docs/reports/inc1/US-1.1.1-report.md` (este archivo),
`quality/reports/inc1/US-1.1.1-{quality,pylint,cc,coverage}.json`,
`docs/traceability/matrix.md` (editado), `CHANGELOG.md` (editado).

---

## Criterios de Aceptación

- [x] Docente asignado genera invitación — `Invitacion` persistida con token único,
  `expira_en` a 7 días, email enviado, evento `InvitacionGenerada`
- [x] Rechazo por Docente no asignado a la comisión — `DocenteNoAsignadoAComision`, ninguna
  invitación se crea

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-1.1.2` — Estudiante se registra con un link de invitación válido (siguiente US de
  la Iteración 1)
- [ ] `US-1.1.5` — agregar el guard de rol `docente` al endpoint de esta US, hoy sin
  protección
- [ ] RF-01 permanece "Especificado" en `docs/traceability/matrix.md` hasta que también estén
  implementadas `US-1.1.2` y `US-1.1.3`

---

## Lecciones Aprendidas

- ⚠️ No se ejecutó `tracker_cli.py start-phase 5` al iniciar la Fase 5 — el tiempo de esa
  fase no quedó registrado. No bloquea nada (PRIN-001), pero conviene verificar el
  `start-phase` como primer paso literal de cada fase.
- ⚠️ `pytest-bdd` no comparte step definitions entre archivos de `step_defs` — cada
  `.feature` resuelve sus steps solo dentro del módulo que lo carga vía `scenarios(...)`. Un
  step con texto idéntico en otro archivo no se reutiliza automáticamente.
- ⚠️ Un stub SMTP async arrancado *dentro* de un step de pytest-bdd no sobrevive al step
  siguiente, porque cada step corre `asyncio.run()` (cierra su loop al terminar, `ADR-018`).
  Se resolvió con un thread daemon con su propio event loop persistente (`serve_forever`).
- 💡 Resolver por adelantado, antes del plan, las dos ambigüedades reales de la spec (falta
  de `email_destinatario` en el comando, dependencia de JWT no implementado todavía) evitó
  descubrirlas a mitad de la implementación.
- 💡 Revisar el estilo de los archivos hermanos (`comision_repository_port.py`) antes de
  escribir un `Port` nuevo hubiera evitado el hallazgo `unnecessary-ellipsis` de Fase 7.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-22
