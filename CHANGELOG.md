# Changelog

Todos los cambios notables de Cognion se documentan en este archivo.

Formato: [Keep a Changelog](https://keepachangelog.com/es/1.0.0/)
Versionado: [Semantic Versioning](https://semver.org/lang/es/)

---

## [Unreleased]

### Added
- [US-1.1.5] El sistema restringe el acceso a funcionalidades según el rol del usuario autenticado — BC Identidad
  - `JWTPayload` (VO) — `usuario_id` + `rol` resueltos al decodificar un JWT válido, sin
    volver a consultar la base (ADR-013, sin refresh/blacklist)
  - `JWTIssuerPort.verificar(token)` — nuevo método sobre el puerto existente (`US-1.1.4`);
    `PyJWTIssuer.verificar()` decodifica con PyJWT, `JWTExpirado`/`JWTInvalido` según el caso
  - `get_current_user` (`interface_adapters/security/get_current_user.py`) — dependency FastAPI
    que extrae y valida el JWT del header `Authorization: Bearer`; 401 si falta o no es válido
  - `require_rol(roles_permitidos, get_current_user)` (`interface_adapters/security/require_rol.py`)
    — dependency que compone sobre `get_current_user` y exige el rol; 403 si no está permitido.
    Ambos builders reciben la abstracción como parámetro (no importan `frameworks/`) — el wiring
    con `PyJWTIssuer` ocurre en el composition root (`frameworks/dependencies.py`)
  - Endpoints protegidos: `POST /usuarios` y `POST /comisiones`, `POST /comisiones/{id}/docentes`
    con `require_administrador` (`US-1.1.0`); `POST /comisiones/{id}/invitaciones` con
    `require_docente` (`US-1.1.1`). `POST /identidad/login` y `POST /identidad/registro`
    permanecen públicos (precondición de tener un JWT)
  - RF-02 pasa a Implementado — las dos US-IEDD que requería (`US-1.1.4`, `US-1.1.5`) están
    cerradas en backend
  - 12 tests unitarios nuevos + 6 de integración + 6 escenarios BDD; se actualizaron los
    `step_defs` y tests de integración de `US-1.1.0` a `US-1.1.4` para autenticarse contra los
    endpoints ahora protegidos (helper compartido `tests/step_defs/inc1/_auth_headers.py` y
    fixtures `admin_headers`/`docente_headers` en `tests/integration/conftest.py`) — el primer
    Administrador se emite directo con `PyJWTIssuer`, sin pasar por la API (huevo-y-gallina,
    igual que en un despliegue real)
  - Suite total del proyecto: 132/132 tests, cobertura 100% en los componentes nuevos
    (`entities/`, `interface_adapters/security/`)
- [US-1.1.4] Docente, administrador y estudiante se autentican y reciben un JWT con su rol — BC Identidad
  - `IniciarSesionUseCase` — verifica email/password contra el hash bcrypt guardado; emite un
    JWT vía `JWTIssuerPort` con claim `rol` derivado de `Usuario.tipo_perfil` (`TipoPerfil`,
    ya existente — no se creó un VO `Rol` adicional por ser una envoltura redundante sobre
    `TipoPerfil`, decisión aprobada antes de implementar, ver `docs/plans/inc1/US-1.1.4-plan.md`)
  - VO `JWT` (`token`, `rol`, `expira_en`) y puerto `JWTIssuerPort`; `PyJWTIssuer` — adaptador
    PyJWT (`ADR-007`), firma con `settings.secret_key`/`algorithm`, `exp` a 60 minutos desde
    la emisión (`ADR-013`)
  - `CredencialesInvalidas` — mismo error genérico tanto si el email no existe como si la
    contraseña no verifica, para no filtrar existencia de cuentas; evento `SesionIniciada`
  - `UsuarioRepositoryPort.obtener_por_email` nuevo (puerto y gateway SQLAlchemy)
  - Endpoint público `POST /identidad/login` — 200 con `access_token`/`rol`/`expira_en`, 401
    genérico ante credenciales inválidas
  - Corrección de configuración: `ACCESS_TOKEN_EXPIRE_MINUTES` estaba en 30 desde el walking
    skeleton, desalineado con `ADR-013` (60 min) — alineado en `settings.py`, `.env` y
    `.env.example`
  - Alcance: solo backend — `Login.tsx`/`LoginError.tsx`/`frontend/src/lib/auth.ts` quedan
    diferidos a la misma US-IEDD de frontend que ya diferían las US anteriores de Identidad
    (`frontend/src` sigue sin routing ni cliente API), ver `docs/plans/inc1/US-1.1.4-context.md`
  - 10 tests unitarios nuevos + 7 de integración + 5 escenarios BDD; suite total del proyecto
    107/107, coverage 100% en entities/use_cases/interface_adapters, 99% total del proyecto
- [US-1.1.3] Estudiante intenta registrarse con link vencido o inválido — BC Identidad
  - `InvitacionNoValida` (guard genérico de `US-1.1.2`) refinada en tres excepciones
    específicas: `InvitacionInvalida` (token inexistente), `InvitacionVencida`
    (`expira_en` pasado), `InvitacionYaUsada` (`usada_en` no null)
  - `Invitacion.verificar_vigente(ahora)` — nuevo método que distingue el motivo del
    rechazo (INV-ID-01, INV-ID-03); `Invitacion.aceptar()` lo reutiliza
  - `RegistrarEstudianteUseCase._buscar_invitacion_vigente` distingue token inexistente de
    invitación vencida/ya usada
  - `POST /identidad/registro` sigue devolviendo 422 para los tres casos (mismo mensaje al
    Estudiante; el backend distingue internamente solo para logging/debug, según wireframe)
  - Alcance: solo backend — la pantalla `RegistroError.tsx` (`#registro-error`) queda
    diferida a la misma US-IEDD de frontend que ya difería `Registro.tsx`/`RegistroExito.tsx`
    desde `US-1.1.2` (ver `docs/plans/inc1/US-1.1.3-context.md`)
  - 3 tests unitarios nuevos + 1 de integración + 3 escenarios BDD backend; suite total del
    proyecto 85/85 (excluyendo el escenario de UI diferido), coverage 100% en los archivos
    modificados
- [US-1.1.2] Estudiante se registra con un link de invitación válido — BC Identidad
  - `Estudiante` gana `comision_id` (INV-ID-05: nunca existe sin comisión); nueva factory
    `Usuario.crear_estudiante` — único camino de construcción de un `Estudiante`.
    `Usuario.crear()` genérico ya no admite `TipoPerfil.ESTUDIANTE`
  - `Invitacion.es_vigente`/`Invitacion.aceptar` (INV-ID-01, INV-ID-03); error
    `InvitacionNoValida` (guard genérico de esta US — `US-1.1.3` lo refina en las tres
    excepciones específicas de su propio alcance); eventos `InvitacionAceptada`,
    `UsuarioRegistrado`
  - `RegistrarEstudianteUseCase` — valida invitación vigente, valida email libre, crea
    Usuario+Estudiante y consume la invitación en la misma operación
  - Endpoint público `POST /identidad/registro` (sin guard JWT, mismo criterio que
    `US-1.1.1` — el Estudiante todavía no tiene sesión al registrarse)
  - Migración Alembic: columna `comision_id` en `estudiante`
  - Alcance: solo backend — el frontend de registro (`Registro.tsx`, `RegistroExito.tsx`)
    queda diferido a una US-IEDD separada, dado que `frontend/src` no tenía routing ni
    cliente API todavía (ver `docs/plans/inc1/US-1.1.2-context.md`)
  - 15 tests nuevos (10 unitarios + 3 integración + 2 BDD), coverage 100% en
    entities/use_cases/interface_adapters; suite total del proyecto 77/77
- [US-1.1.1] Docente genera link de invitación para una comisión — BC Identidad
  - `Invitación` (aggregate) con token único (`secrets.token_urlsafe`) y expiración a 7 días
    (`ADR-012`), evento `InvitacionGenerada`
  - `GenerarInvitacionUseCase` — valida INV-ID-08 (docente asignado a la comisión), genera
    token, persiste, envía email, emite evento
  - Endpoint `POST /comisiones/{id}/invitaciones` (sin guard de rol todavía, mismo criterio
    que US-1.1.0 — se agrega en `US-1.1.5`); `docente_id` y `email_destinatario` explícitos
    en el body (ajuste de alcance sobre la spec original, ver `docs/plans/inc1/US-1.1.1-plan.md`)
  - `SmtpNotificador` — adaptador SMTP propio de Identidad (`ADR-012`), `smtplib` en
    `asyncio.to_thread`; variables `SMTP_*` nuevas en `.env.example`
  - Migración Alembic: tabla `invitacion`
  - 16 tests nuevos (9 unitarios + 4 integración + 2 BDD via `step_defs` + 1 gateway),
    coverage 100% en entities/use_cases/interface_adapters; suite total del proyecto 53/53
- [US-1.1.0] Administrador da de alta cuentas de usuario, crea una comisión y asigna docentes
  — BC Identidad, precondición del resto de la Iteración 1
  - `Usuario` (aggregate) + entities subordinadas `Docente`/`Administrador`/`Estudiante`,
    `Comisión` (aggregate), eventos `UsuarioCreado`/`ComisionCreada`/`DocenteAsignado`
  - `CrearUsuarioUseCase`, `CrearComisionUseCase`, `AsignarDocenteAComisionUseCase`
  - Endpoints `POST /usuarios`, `POST /comisiones`, `POST /comisiones/{id}/docentes` (sin
    guard de rol todavía — se agrega en `US-1.1.5`)
  - `scripts/seed_admin.py` — bootstrap del primer Administrador (`ADR-016`)
  - Migración Alembic: tablas `usuario`, `docente`, `administrador`, `estudiante`, `comision`,
    `comision_docentes`
  - 37 tests (20 unitarios + 9 integración + 5 BDD via `step_defs`), coverage 100% en
    entities/use_cases/interface_adapters
  - `ADR-016` (bootstrap admin), `ADR-017` (DB session compartida `shared/frameworks/db.py`),
    `ADR-018` (`NullPool` en el engine SQLAlchemy)

### Fixed
- `passlib` incompatible con `bcrypt>=4.1` — reemplazado por `bcrypt` directo
- Orden de inserción `Usuario`/perfil sin `relationship()` ORM causaba violación de FK —
  corregido con flush intermedio en `SQLAlchemyUsuarioRepository`
- `pytest-asyncio` sin `loop_scope` explícito rompía el engine compartido entre tests con
  distintos event loops — fijado a `session` scope

## [0.2.0] - 2026-07-16

### Added
- PostgreSQL local (vía Homebrew) y Alembic inicializado (`alembic.ini`, `migrations/`)
- `src/settings.py` — configuración desde `.env` con pydantic-settings
- Primer test real del proyecto (`tests/unit/inc0/test_health.py`)
- `.claude/commands/docs-audit.md` — skill de auditoría de trazabilidad documental
- HITO-2 y HITO-3 (`docs/aprendizajes/`)
- BL-001 — cierre del Incremento 0 (`.cm/baselines/BL-001-fundacion-tecnica.md`)

### Changed
- CI ya no tolera "0 tests" — retirado tras agregar el primer test real
- `docs/rf/PLAN_v1.md`: Docker local diferido a un incremento posterior; PostgreSQL local
  corre vía Homebrew mientras tanto
- `CLAUDE.md`: corregido el "próximo paso" — el Incremento 0 no usa `incN-candidatas.md`

## [0.1.0] - 2026-07-15

### Added
- Fundación documental: RF_v1, RNF_v1, ARQ_v1, PLAN_v1
- Plan de Gestión de Configuración (`docs/plans/PLAN-CM.md`), checklist de instalación y
  workflow de desarrollo
- ADRs 001-011 ratificados y matriz de trazabilidad inicial
- Primer HITO de aprendizaje (`docs/aprendizajes/HITO-1-*.md`)
- BL-000 — cierre de la fundación documental (`.cm/baselines/BL-000-fundacion-documental.md`)

### Changed
- Plan de incrementos (`PLAN_v1.md`) reestructurado: Incremento 0 pasa a ser fundación técnica
  pura, BC Identidad se mueve a un nuevo Incremento 1, resto renumerado (2-7)
- `docs/cm/` renombrado a `docs/plans/`
