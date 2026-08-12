# Plan de Implementación: US-1.1.1 - Docente genera link de invitación para una comisión

**Patrón:** Clean Architecture BC-First (entities → use_cases → interface_adapters → frameworks)
**Producto:** Cognion — BC Identidad
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-07-22

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (tiempos reales de ejecución del agente, no
comparables contra esfuerzo humano — ver nota PRIN-001 del skill `implement-us`).

| Fase | Tiempo real |
|---|---|
| 0 — Validación de Contexto | ~4 min |
| 1 — Escenarios BDD | ~2 min |
| 2 — Plan de Implementación | ~3 min |
| 3 — Implementación | ~9 min |
| 4 — Tests Unitarios | ~2 min |
| 5 — Tests de Integración | no registrado (gap de tracking, ver Lecciones Aprendidas) |
| 6 — Validación BDD | ~8 min |
| 7 — Quality Gates | ~7 min |
| **Total (hasta cierre de Fase 7)** | **~35 min + Fase 5 sin medir** |

## Lecciones Aprendidas

- ⚠️ **Gap de tracking:** no se ejecutó `tracker_cli.py start-phase 5` al iniciar la Fase 5 —
  el tiempo de esa fase no quedó registrado (`end-phase 5` reportó `?`). No bloquea nada
  (PRIN-001: el tracking es informativo), pero a futuro conviene verificar el `start-phase`
  como primer paso literal de cada fase, no darlo por hecho.
- ⚠️ **pytest-bdd no comparte steps entre archivos de step_defs** — cada `.feature` resuelve
  sus steps solo dentro del módulo que lo carga vía `scenarios(...)`. Un step con texto
  idéntico definido en otro archivo (ej. "el sistema rechaza la operación con {codigo}") no
  se reutiliza automáticamente; hay que redefinirlo (con su propio mapa de códigos) en cada
  archivo de steps o extraerlo a un `conftest.py` compartido si se repite mucho.
- ⚠️ Un stub SMTP async arrancado *dentro* de un step de pytest-bdd no sobrevive al step
  siguiente si cada step corre `asyncio.run()` (cierra el loop al terminar, ADR-018). Hay que
  correr el server en un thread daemon con su propio event loop persistente (`run_forever`),
  no dentro del mismo `asyncio.run()` que ejecuta la acción HTTP.
- 💡 Detectar por revisión manual (no por un test) que los dos `Port` nuevos tenían un `...`
  de más después del docstring — inconsistente con el resto del proyecto — antes de que
  pylint lo señalara en Fase 7, hubiera ahorrado una vuelta; para próximas US, revisar el
  estilo de los archivos hermanos (`comision_repository_port.py`) antes de escribir un `Port`
  nuevo, no solo el patrón general.
- 💡 Resolver por adelantado, antes del plan, las dos ambigüedades reales de la spec (falta de
  `email_destinatario` en el comando, dependencia de JWT no implementado todavía) evitó
  descubrirlas a mitad de la implementación — mismo criterio que "spec-validatoria" de
  AtaraxiaDive: mejor decidir el alcance explícitamente que inferirlo mirando el código.

## Decisiones de esta US (registradas para no repetir la discusión)

- **Sin guard de JWT/rol todavía:** el endpoint recibe `docente_id` explícito en el body
  (mismo patrón que `POST /comisiones/{id}/docentes` de US-1.1.0) en vez de derivarlo de un
  token — `US-1.1.4` (JWT) todavía no existe. INV-ID-08 se valida igual en el use case,
  independiente del mecanismo de autenticación. El guard se agrega después sin tocar esta
  lógica (ver `US-1.1.5`).
- **`email_destinatario` agregado al comando:** la spec original (`GenerarInvitacion(comision_id,
  docente_id)`) no incluye a quién mandar el email, pero la postcondición exige el envío
  (`ADR-012`). Se agrega `email_destinatario: str` como parámetro del comando y del request —
  no se persiste en el aggregate `Invitación` (no hace falta para validar el token después),
  solo se usa para el envío SMTP. Ajuste de alcance acordado con Víctor antes de este plan.
- **Adaptador SMTP propio de Identidad (`ADR-012`):** implementación real con `smtplib`
  (stdlib, sin dependencia nueva), leyendo host/puerto/credenciales de variables de entorno
  nuevas (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`). Se agregan a
  `.env.example` en esta US.
- **Token único:** `secrets.token_urlsafe(32)` (stdlib) — suficiente entropía, sin dependencia
  nueva, mismo criterio que bcrypt directo en US-1.1.0 (evitar deuda de librerías).
- **Lecciones de US-1.1.0 a aplicar de entrada:** usar `bcrypt`/stdlib en vez de librerías sin
  mantenimiento; probar contra Postgres real antes de cerrar Fase 3 (detectó bugs reales que
  los fakes no vieron); en Fase 6, los steps `pytest-bdd` async requieren `asyncio.run()`
  explícito (no soportan `async def` directo en 8.1.0).

---

## Componentes a Implementar

### 1. Entities (`src/identidad/entities/`)

- [x] `entities/invitacion.py`
  - `Invitacion` (dataclass): `id`, `comision_id`, `docente_id`, `token`, `generada_en`,
    `expira_en`, `usada_en: datetime | None = None`
  - `staticmethod crear(comision_id, docente_id) -> Invitacion`: genera `id` (uuid4), `token`
    (`secrets.token_urlsafe(32)`), `generada_en = ahora()`, `expira_en = generada_en + 7 días`
    (INV-ID-02, `ADR-012`)
- [x] `entities/eventos.py` (editar) — agregar `InvitacionGenerada` (frozen dataclass):
  `invitacion_id`, `comision_id`, `docente_id`, `token`, `ocurrido_en`
- [x] `entities/errors.py` (editar) — agregar `DocenteNoAsignadoAComision(Exception)`, mismo
  patrón que `UsuarioNoEsDocente` (guarda `docente_id` y `comision_id`, arma mensaje)
- [x] `entities/ports/invitacion_repository_port.py`
  - `InvitacionRepositoryPort(ABC)`: `async def guardar(invitacion) -> None`
- [x] `entities/ports/notificador_port.py`
  - `NotificadorPort(ABC)`: `async def enviar_invitacion(email_destinatario: str, token: str) -> None`
    (reutilizable desde `US-1.1.2`/`US-1.1.3` para el link de registro)

### 2. Use Cases (`src/identidad/use_cases/`)

- [x] `use_cases/generar_invitacion.py`
  - `GenerarInvitacionUseCase(comision_repositorio, invitacion_repositorio, notificador)`
  - `async def execute(comision_id, docente_id, email_destinatario) -> tuple[Invitacion, InvitacionGenerada]`
  - Orden: obtener comisión → validar `docente_id in comision.docentes_asignados` (si no,
    `DocenteNoAsignadoAComision`) → `Invitacion.crear(...)` → guardar → enviar email → emitir evento

### 3. Interface Adapters (`src/identidad/interface_adapters/`)

- [x] `interface_adapters/controllers/invitaciones_controller.py`
  - `InvitacionesController(generar_invitacion: GenerarInvitacionUseCase)`
  - `async def generar_invitacion(comision_id, docente_id, email_destinatario) -> tuple[Invitacion, InvitacionGenerada]`
- [x] `interface_adapters/gateways/invitacion_repository.py`
  - `SQLAlchemyInvitacionRepository(InvitacionRepositoryPort)` — `guardar()` sobre `InvitacionModel`

### 4. Frameworks (`src/identidad/frameworks/`)

- [x] `frameworks/db/models.py` (editar) — agregar `InvitacionModel` (`__tablename__ = "invitacion"`):
  `id`, `comision_id` (FK `comision.id`), `docente_id` (FK `docente.id`), `token` (String,
  unique), `generada_en`, `expira_en`, `usada_en` (nullable)
- [x] Migración Alembic nueva (`alembic revision --autogenerate`) — tabla `invitacion`
- [x] `frameworks/smtp/notificador_smtp.py`
  - `SmtpNotificador(NotificadorPort)` — implementa `enviar_invitacion` con `smtplib` +
    variables de entorno (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`)
  - Envío en `asyncio.to_thread` para no bloquear el event loop (`smtplib` es sync)
- [x] `frameworks/api/schemas.py` (editar) — agregar `GenerarInvitacionRequest`
  (`docente_id: UUID`, `email_destinatario: str`) y `InvitacionResponse` (`id`, `comision_id`,
  `docente_id`, `expira_en`)
- [x] `frameworks/api/invitaciones_router.py`
  - `POST /comisiones/{comision_id}/invitaciones` → 201 `InvitacionResponse`, 422 si
    `DocenteNoAsignadoAComision`, 404 si `ComisionNoExiste`
- [x] `frameworks/dependencies.py` (editar) — `get_invitaciones_controller(session)`
- [x] `.env.example` (editar) — agregar variables `SMTP_*`, más defaults en `src/settings.py`

### 5. Integración

- [x] Registrar `invitaciones_router` en `src/app.py` (`app.include_router(...)`)
- [x] Verificar migración aplicada localmente (`alembic upgrade head`) antes de Fase 4

**Estado:** 14/14 tareas completadas

## Verificación manual end-to-end (antes de Fase 4)

Contra Postgres local real, vía `httpx.ASGITransport` (sin levantar un proceso servidor
aparte) y un stub SMTP asyncio local en `127.0.0.1:2525` (no hay servidor SMTP real en este
entorno de desarrollo):

- `POST /comisiones/{id}/invitaciones` con docente asignado → 201, `Invitacion` persistida,
  `expira_en` = +7 días, email "enviado" (aceptado por el stub) sin excepciones.
- Mismo endpoint con un docente **no** asignado a la comisión → 422
  `DocenteNoAsignadoAComision`, sin invitación creada.
- Datos de prueba limpiados de Postgres al finalizar (prefijo `us111%`).

No se detectó código obsoleto tras la implementación — no hay clases/funciones reemplazadas.

## Fase 4 — Tests Unitarios

9 tests nuevos (100% cobertura en entities/use_cases/interface_adapters nuevos; `frameworks/`
queda fuera del gate de cobertura por `pyproject.toml` — `omit = ["src/*/frameworks/*"]`):

- `tests/unit/inc1/test_invitacion.py` — 3 tests, `Invitacion.crear` (token único, expiración a 7 días)
- `tests/unit/inc1/test_generar_invitacion_use_case.py` — 4 tests, `GenerarInvitacionUseCase`
- `tests/unit/inc1/test_invitaciones_controller.py` — 1 test, `InvitacionesController`
- `tests/unit/inc1/test_notificador_smtp.py` — 2 tests, `SmtpNotificador` (mock de `smtplib.SMTP`)
- `tests/unit/inc1/_fakes.py` (editado) — agregado `FakeInvitacionRepository`, `FakeNotificador`

Suite completa: 30/30 tests pasan (21 preexistentes + 9 nuevos), sin regresiones.

## Fase 5 — Tests de Integración (contra Postgres local real)

- `tests/integration/conftest.py` (editado) — agregado `DELETE FROM invitacion` a la limpieza
  `autouse` (antes de `comision_docentes`/`comision`/`docente`, por la FK nueva)
- `tests/integration/inc1/test_invitacion_repository_integration.py` — 1 test,
  `SQLAlchemyInvitacionRepository.guardar` persiste correctamente
- `tests/integration/inc1/test_invitaciones_api_integration.py` — 3 tests, flujo completo
  `POST /comisiones/{id}/invitaciones` (201, 422 por `DocenteNoAsignadoAComision`, 404 por
  `ComisionNoExiste`) — con un stub SMTP asyncio local (fixture `fake_smtp_server`, puerto
  efímero vía `monkeypatch` de `settings`) para no depender de un servidor SMTP real

Suite completa: 16/16 tests de integración pasan. Datos de prueba limpiados correctamente
(verificado con `SELECT count(*)` sobre `usuario`/`comision`/`invitacion` tras la corrida).

## Fase 6 — Validación BDD

- `tests/step_defs/inc1/test_us_1_1_1_steps.py` — steps de los 2 escenarios de
  `US-1.1.1-generar-invitacion.feature`, mismo patrón que US-1.1.0 (`asyncio.run()` explícito
  por step, ADR-018)
- **Steps NO se comparten entre archivos** — confirmado empíricamente: pytest-bdd resuelve
  steps solo dentro del módulo que carga el `.feature` vía `scenarios(...)`, no globalmente.
  El step `el sistema rechaza la operación con {codigo_error}` se define de forma independiente
  en este archivo (con su propio mapa de códigos), no reutilizando el de US-1.1.0.
- **Stub SMTP en thread con loop propio:** como cada step corre `asyncio.run()` (loop nuevo y
  descartado al terminar), un server async arrancado dentro de un step no sobrevive al step
  siguiente. Se resolvió con un thread daemon dedicado que corre su propio event loop
  (`run_forever` vía `serve_forever()`), fixture `autouse` que lo arranca/cierra por escenario.
- `pyproject.toml` (editado) — agregados markers `US-1.1.1` y `generar-invitacion` (evita
  `PytestUnknownMarkWarning`)

Suite BDD completa: 7/7 escenarios pasan (5 preexistentes de US-1.1.0 + 2 nuevos). Suite total
del proyecto (unit + integration + BDD): **53/53 tests pasan**. Postgres verificado limpio.

## Fase 7 — Quality Gates

| Métrica | Resultado | Umbral | Estado |
|---|---|---|---|
| Pylint | 9.58/10 | ≥ 8.0 | ✅ |
| CC máx/función | 3 | ≤ 10 | ✅ |
| MI mínimo | 55.58 | > 20 | ✅ |
| Coverage | 100% (116/116 statements) | ≥ 95% | ✅ |

**Estado: APROBADO** — `quality/reports/inc1/US-1.1.1-quality.json`

Hallazgo real corregido durante esta fase: los 2 Ports nuevos (`InvitacionRepositoryPort`,
`NotificadorPort`) tenían un `...` de más después del docstring del método abstracto —
inconsistente con el resto del proyecto, donde el docstring solo ya es el cuerpo del método.
Pylint lo señaló como `W2301 unnecessary-ellipsis`; corregido antes de este reporte.

Hallazgos R0903 (too-few-public-methods) en Use Cases/Ports/Gateway/modelos ORM: falsos
positivos esperados para Clean Architecture, mismo criterio ya documentado en el reporte de
calidad de US-1.1.0 — no requieren acción.
