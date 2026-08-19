# Plan de Implementación: US-2.2.1 - Bloqueo automático de cuenta por 3 intentos fallidos consecutivos de login

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — BC Identidad
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-19

## Métricas de Tiempo (tracking automático, tiempos de agente — ver PRIN-001 en `implement-us`)

| Fase | Tiempo real |
|------|-------------|
| Fase 0 — Contexto | 79s |
| Fase 1 — BDD | 49s |
| Fase 2 — Plan | 167s |
| Fase 3 — Implementación | 408s |
| Fase 4 — Tests unitarios | 96s |
| Fase 5 — Tests de integración | 80s |
| Fase 6 — Validación BDD | 183s |
| Fase 7 — Quality gates | 258s |
| **Total (hasta Fase 7)** | **~23 min** |

## Lecciones Aprendidas

- 💡 No hay event store en el proyecto — cuando un evento de dominio se emite en el mismo
  camino que termina en excepción (no en un retorno exitoso), adjuntarlo como atributo de la
  excepción es la forma más simple de mantenerlo observable sin introducir infraestructura
  nueva fuera de alcance.
- ✅ Agregar `actualizar()` al puerto `UsuarioRepositoryPort` (en vez de sobrecargar `guardar()`)
  deja el contrato de persistencia claro y listo para que `US-2.2.4`/`US-2.2.5` lo reutilicen
  sin volver a tocar el puerto.
- ⚠️ `FakeUsuarioRepository` en `tests/unit/inc1/_fakes.py` dejó de ser instanciable en cuanto
  se agregó el método abstracto nuevo al puerto — hay que recordar actualizar los test doubles
  del puerto en la misma tarea que se lo extiende, no como paso separado.

## Componentes a Implementar

### 1. Entities
- [x] `src/identidad/entities/usuario.py`
  - Agregar campos `bloqueada: bool = False`, `intentos_fallidos_login: int = 0`,
    `intentos_fallidos_password: int = 0` al dataclass `Usuario`
  - No rompe `Usuario.crear()`/`crear_estudiante()` (dataclass no frozen, campos con default)
- [x] `src/identidad/entities/eventos.py`
  - Agregar `CuentaBloqueada(usuario_id: UUID, ocurrido_en: datetime)`
- [x] `src/identidad/entities/errors.py`
  - Agregar `CuentaBloqueadaError(usuario_id: UUID)` — mensaje explícito de cuenta bloqueada
    (no reutiliza el mensaje genérico de `CredencialesInvalidas`, es un error distinto en el
    dominio aunque HTTP-wise ambos casos de fallo devuelvan un status de rechazo)

### 2. Use Cases
- [x] `src/identidad/use_cases/iniciar_sesion.py`
  - Antes de verificar contraseña: si `usuario.bloqueada`, lanzar `CuentaBloqueadaError` sin
    tocar contadores ni verificar password
  - Si falla la verificación de password: incrementar `intentos_fallidos_login`; si llega a 3,
    `bloqueada = True` y se arma el evento `CuentaBloqueada` (se retorna/emite junto con
    `CredencialesInvalidas` — la excepción se sigue lanzando en todos los casos de fallo,
    el evento se persiste vía el repositorio antes de lanzar)
  - Si la verificación de password es exitosa: `intentos_fallidos_login = 0`
  - En ambos casos (éxito y fallo no-bloqueante) se persiste el `Usuario` con el contador
    actualizado a través de `usuario_repositorio.actualizar(usuario)` — nuevo método de
    persistencia (ver punto 3)
  - Caso "email no existe" (usuario is None) no cambia: sigue lanzando `CredencialesInvalidas`
    sin nada que persistir

### 3. Puerto y Gateway de persistencia
- [x] `src/identidad/entities/ports/usuario_repository_port.py`
  - Agregar método abstracto `actualizar(usuario: Usuario) -> None` — persiste cambios sobre
    un `Usuario` existente (distinto de `guardar`, que es alta). Lo reutilizarán
    `US-2.2.4`/`US-2.2.5` para persistir `password_hash` y los contadores.
- [x] `src/identidad/interface_adapters/gateways/usuario_repository.py`
  - Implementar `actualizar()`: `UPDATE` de `bloqueada`, `intentos_fallidos_login`,
    `intentos_fallidos_password`, `password_hash` sobre `UsuarioModel` por `usuario.id`
  - `_armar_usuario` ahora también hidrata `bloqueada`/contadores desde el modelo

### 4. Frameworks — persistencia
- [x] `src/identidad/frameworks/db/models.py`
  - `UsuarioModel`: agregar columnas `bloqueada: Mapped[bool]` (default `False`),
    `intentos_fallidos_login: Mapped[int]` (default `0`),
    `intentos_fallidos_password: Mapped[int]` (default `0`)
- [x] Migración Alembic nueva (`migrations/versions/4c1b823c7d9f_usuario_bloqueo_intentos_fallidos.py`)
  - `down_revision = "6f523d16bf1c"` (head actual)
  - `add_column` de las 3 columnas nuevas en `usuario`, `nullable=False` con
    `server_default` (`false`, `0`, `0`) para el backfill de filas existentes
  - Aplicada localmente (`alembic upgrade head`)

### 5. Interface Adapters / Frameworks — traducción HTTP
- [x] `src/identidad/frameworks/api/auth_router.py`
  - Capturar `CuentaBloqueadaError` y traducir a `403 Forbidden` (antes que
    `CredencialesInvalidas`, que sigue mapeando a `401`) — mismo patrón ya usado para
    `CredencialesInvalidas` en este archivo; la spec ubica la traducción en
    `interface_adapters/controllers/auth_controller.py`, pero el código existente ya resuelve
    esta traducción en el router de frameworks (`AuthController.iniciar_sesion` es un simple
    delegado sin manejo de excepciones) — se sigue el patrón real del repo, no el de la spec

## Integración
- [x] Ninguna dependencia nueva que registrar en `dependencies.py` — `IniciarSesionUseCase`
  sigue recibiendo el mismo repositorio, solo gana un método más en su interfaz
- [x] `tests/unit/inc1/_fakes.py` — `FakeUsuarioRepository` implementa `actualizar()` (nueva
  obligación del puerto), sin la cual dejaría de ser instanciable

## Nota de diseño (no prevista en el plan original)
`CredencialesInvalidas` gana un atributo `evento_cuenta_bloqueada: CuentaBloqueada | None`,
seteado por `IniciarSesionUseCase` cuando el fallo es el 3er intento consecutivo. No hay event
store en el proyecto — los eventos de dominio se devuelven junto al resultado exitoso en el
`tuple` de retorno de cada use case (patrón ya usado en toda la Iteración 1/2). Como el camino
de bloqueo termina en una excepción (no en un retorno), no hay tupla donde devolver el evento;
adjuntarlo a la excepción es la forma mínima de que sea observable/testeable sin introducir un
mecanismo de publicación nuevo fuera de alcance de esta US.

**Estado:** 8/8 tareas completadas
