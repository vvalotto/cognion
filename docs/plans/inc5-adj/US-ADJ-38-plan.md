# Plan de Implementación: US-ADJ-38 - Solicitar recuperación de contraseña (endpoint público)

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-13

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion (BC `identidad`, con dependencia nueva hacia BC `notificaciones`)

## Métricas de Tiempo (tracker_cli.py)

| Fase | Tiempo real |
|------|-------------|
| 0 — Contexto | 41s |
| 1 — Escenarios BDD | 50s |
| 2 — Plan de implementación | 46s |
| 3 — Implementación (9 tareas) | 194s |
| 4 — Tests unitarios | 268s |
| 5 — Tests de integración | 245s |
| 6 — Validación BDD | 204s |
| 7 — Quality Gates | 887s |
| 8 — Documentación | (en curso) |

> Nota (`PRIN-001`, `docs/plans/.../implement-us`): los tiempos por tarea de Fase 3 son
> segundos porque el agente escribe el código directamente desde el plan ya aprobado — no
> son comparables a estimaciones de esfuerzo humano. La Fase 7 concentra la mayor parte del
> tiempo real por los ~200s de CodeGuard corriendo en modo `full` sobre 13 archivos.

## Lecciones Aprendidas

- ✅ Reutilizar el patrón de `Invitacion` (token + expiración + aggregate propio) para
  `TokenRecuperacionPassword` evitó decisiones de diseño nuevas — mismo generador
  (`secrets.token_urlsafe`), misma forma de repositorio (`guardar`/`obtener_por_token`/
  `actualizar`).
- ⚠️ Un directorio de tests con guion (`tests/unit/inc5-adj/`) no es un identificador Python
  válido — rompe los imports relativos/dotted entre archivos de test del mismo directorio
  (`ImportError: attempted relative import with no known parent package`). Los tests
  unitarios de esta US se movieron a `tests/unit/inc1/` (home ya establecido de BC Identidad,
  mismo criterio que `US-ADJ-23` a `30`) — los `.feature`/`step_defs` sí toleran el guion
  porque pytest-bdd no necesita importarlos por nombre de paquete.
- 💡 El manejo de "loguear y continuar" ante un fallo de envío de email debe vivir en el
  **Use Case**, no en el adapter — mismo contrato que `CanalEnvioPort` de Notificaciones
  (`NotificarAperturaUseCase`). El plan original lo había puesto en el adapter; se corrigió
  antes de escribir tests (Fase 4) para no duplicar la responsabilidad en dos lugares
  distintos del código.

Referencia de patrón ya existente en el proyecto para este tipo de aggregate con token +
expiración: `Invitacion` (`src/identidad/entities/invitacion.py`,
`GenerarInvitacionUseCase`, `SQLAlchemyInvitacionRepository`, `registro_router.py` como
ejemplo de endpoint público sin JWT). Referencia para el adapter cruzado hacia Notificaciones:
`src/actividad_evaluativa/frameworks/adapters/notificacion_port_in_process.py` +
`src/notificaciones/frameworks/adapters/smtp_canal_envio.py`.

## Componentes a Implementar

### 1. Entities (`src/identidad/entities/`)

- [x] `token_recuperacion_password.py`
  - `TokenRecuperacionPassword` (dataclass): `id`, `usuario_id`, `token`, `generado_en`,
    `expira_en`, `usado_en: datetime | None`
  - `staticmethod crear(usuario_id)`: token con `secrets.token_urlsafe(32)` (mismo generador
    que `Invitacion`), `expira_en = generado_en + timedelta(hours=1)` (INV-ID-13)
  - `invalidar(ahora)`: marca `usado_en = ahora` — reutilizado tanto para invalidar un token
    activo previo (INV-ID-12, esta US) como para marcarlo usado tras un canje exitoso
    (`US-ADJ-39`, mismo campo, mismo efecto: el token deja de poder canjearse)

### 2. Ports (`src/identidad/entities/ports/`)

- [x] `token_recuperacion_password_repository_port.py`
  - `TokenRecuperacionPasswordRepositoryPort(ABC)`: `guardar(token)`,
    `obtener_por_token(token) -> TokenRecuperacionPassword | None` (usado recién en
    `US-ADJ-39`, pero se define completo ahora junto con el aggregate/tabla),
    `invalidar_activos_de(usuario_id, ahora) -> None` (UPDATE directo — marca `usado_en=ahora`
    en cualquier token de ese usuario con `usado_en IS NULL`, sin necesidad de traerlos a
    memoria uno por uno), `actualizar(token)` (guarda cambios sobre un token existente, lo usa
    `US-ADJ-39` para persistir el canje)
- [x] `canal_recuperacion_port.py`
  - `CanalRecuperacionPort(ABC)`: `enviar_recuperacion(email_destinatario, token) -> None` —
    mismo criterio que `NotificadorPort.enviar_invitacion`, no propaga excepciones de envío
    hacia el use case (el propio adapter loguea y traga el error, igual que
    `NotificarAperturaUseCase` en Notificaciones)

### 3. Use Case (`src/identidad/use_cases/`)

- [x] `solicitar_recuperacion_password.py`
  - `SolicitarRecuperacionPasswordUseCase(usuario_repositorio, token_repositorio,
    canal_recuperacion)`
  - `execute(email: str) -> None`:
    1. Busca `Usuario` por email (`UsuarioRepositoryPort.obtener_por_email`, ya existente)
    2. Si no existe → retorna sin hacer nada (INV-ID-17, sin excepción — la ausencia de
       efecto es intencional, no un error)
    3. Si existe: `invalidar_activos_de(usuario.id, ahora)` (INV-ID-12), crea el token nuevo
       con `TokenRecuperacionPassword.crear(usuario.id)`, lo persiste, y llama
       `canal_recuperacion.enviar_recuperacion(usuario.email, token.token)`
  - Sin retorno de evento hacia el controller — la respuesta HTTP es siempre la misma
    genérica, no hay nada que el router deba diferenciar (INV-ID-17 se sostiene también en
    esta capa: el use case no informa al llamante si hizo algo o no)

### 4. Frameworks — persistencia (`src/identidad/`)

- [x] `frameworks/db/models.py`: agrega `TokenRecuperacionPasswordModel` (tabla
  `token_recuperacion_password`), mismas columnas que `InvitacionModel` salvo
  `usuario_id` (FK a `usuario.id`) en vez de `comision_id`/`docente_id`
- [x] `interface_adapters/gateways/token_recuperacion_password_repository.py`:
  `SQLAlchemyTokenRecuperacionPasswordRepository` — mismo patrón que
  `SQLAlchemyInvitacionRepository`; `invalidar_activos_de` usa un `UPDATE` de SQLAlchemy
  directo (`update(TokenRecuperacionPasswordModel).where(...)`), no round-trip por entidad
- [x] Migración Alembic nueva (`alembic revision --autogenerate` sobre la tabla nueva,
  revisar el archivo generado antes de aplicarlo — mismo criterio que
  `479b36fd0759_invitacion.py`)

### 5. Frameworks — adapter cruzado hacia Notificaciones (`src/identidad/frameworks/adapters/`)

- [x] `canal_recuperacion_port_in_process.py`
  - `CanalRecuperacionPortInProcess(CanalRecuperacionPort)` — único archivo de Identidad que
    importa `src.notificaciones` (`ADR-006`, mismo criterio de acoplamiento consciente que
    `notificacion_port_in_process.py`)
  - Compone `asunto`/`cuerpo` del email de recuperación (con el link `{FRONTEND_URL}
    /recuperar-password/{token}` — revisar en la implementación si ya existe una variable de
    entorno de URL de frontend en `settings.py`; si no existe, agregarla o resolverlo con un
    valor por defecto documentado, decisión a tomar en la tarea)
  - Invoca `SmtpCanalEnvio().enviar(...)` (`src/notificaciones/frameworks/adapters/
    smtp_canal_envio.py`) directo — no crea un Use Case nuevo dentro de Notificaciones,
    a diferencia de `notificar_apertura`/`notificar_cierre` (esos sí lo necesitan porque
    resuelven un roster vía `ComisionConsultaPort`; acá el destinatario ya lo tiene Identidad)
  - `try/except` alrededor de `canal_envio.enviar()` con `logger.warning(...)` — nunca propaga
    (mismo patrón que `NotificarAperturaUseCase`)

### 6. Interface Adapters — controller y router

- [x] `interface_adapters/controllers/recuperacion_password_controller.py`
  - `RecuperacionPasswordController(solicitar_recuperacion: SolicitarRecuperacionPasswordUseCase)`
  - `async def solicitar(email: str) -> None` — delega en el use case
- [x] `frameworks/api/schemas.py`: agrega `SolicitarRecuperacionPasswordRequest` (`email: str`)
- [x] `frameworks/api/recuperacion_password_router.py`
  - `router = APIRouter(prefix="/identidad", tags=["identidad"])`
  - `POST /identidad/recuperar-password/solicitar` — **sin** `Depends` de autenticación (mismo
    criterio que `registro_router.py`), `status_code=202`, responde siempre el mismo mensaje
    genérico sin importar el resultado interno del use case

### 7. Integración

- [x] `frameworks/dependencies.py`: agrega `get_canal_recuperacion()` (provee
  `CanalRecuperacionPortInProcess(session)`) y
  `get_recuperacion_password_controller(session)` (arma el controller con
  `SQLAlchemyUsuarioRepository`, `SQLAlchemyTokenRecuperacionPasswordRepository`,
  `get_canal_recuperacion()`)
- [x] `src/app.py`: importa y registra `recuperacion_password_router` con
  `app.include_router(...)`, mismo lugar que el resto de routers de Identidad

**Estado:** 9/9 tareas completadas

**Ajuste de diseño detectado en Fase 4** (antes de escribir tests): el plan original ponía el
`try/except` de fallo de envío dentro de `CanalRecuperacionPortInProcess` (adapter). Para
mantener consistencia con `CanalEnvioPort`/`NotificarAperturaUseCase` de Notificaciones (donde
el adapter no captura nada y el Use Case es quien decide "loguear y continuar"), se movió el
manejo de fallo a `SolicitarRecuperacionPasswordUseCase.execute()` — el adapter solo compone y
envía, sin capturar excepciones.

**Fase 4 (tests unitarios):** 12 tests nuevos en `tests/unit/inc1/` (entity, use case,
controller — no `tests/unit/inc5-adj/`: la BC Identidad ya usa `tests/unit/inc1/` como home de
sus unit tests independientemente del incremento que los agregue, mismo criterio que
`US-ADJ-23` a `30`; un directorio con guion no es un identificador Python válido, rompe los
imports relativos entre archivos de test). 100% cobertura en los 3 componentes, 466/466 tests
unitarios en verde.

**Fase 5 (tests de integración):** 10 tests nuevos en `tests/integration/inc1/` (repositorio
SQLAlchemy + endpoint API con SMTP fake, mismo patrón que
`test_invitaciones_api_integration.py`). `tests/integration/conftest.py` actualizado para
limpiar `token_recuperacion_password` en el fixture `limpiar_tablas_identidad`. 321/321 tests
de integración en verde.
