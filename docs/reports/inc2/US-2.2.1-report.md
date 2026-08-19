# Reporte de Implementación: US-2.2.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.2.1 - Bloqueo automático de cuenta por 3 intentos fallidos consecutivos de login
- **Puntos estimados:** 3
- **Tiempo real:** ~23 min (fases 0-7, ver `docs/plans/US-2.2.1-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-19

---

## Componentes Implementados

### Entities
- ✅ **`Usuario`** (`src/identidad/entities/usuario.py`) — gana `bloqueada: bool`,
  `intentos_fallidos_login: int`, `intentos_fallidos_password: int` (defaults `False`/`0`/`0`)
- ✅ **`CuentaBloqueada`** (`src/identidad/entities/eventos.py`) — evento emitido al 3er fallo
  consecutivo
- ✅ **`CuentaBloqueadaError`** (`src/identidad/entities/errors.py`) — se lanza si se intenta
  loguear con una cuenta ya bloqueada, sin verificar la contraseña
- ✅ **`CredencialesInvalidas`** — gana el atributo `evento_cuenta_bloqueada` (ver nota de
  diseño abajo)

### Use Cases
- ✅ **`IniciarSesionUseCase`** (`src/identidad/use_cases/iniciar_sesion.py`) — verifica
  `bloqueada` antes de la contraseña, cuenta fallos/aciertos, bloquea al 3er fallo y persiste
  el estado en cada camino (éxito, fallo no-bloqueante, bloqueo)

### Puerto y Gateway
- ✅ **`UsuarioRepositoryPort.actualizar()`** (`src/identidad/entities/ports/usuario_repository_port.py`)
  — método nuevo, distinto de `guardar()` (alta); persiste cambios sobre un `Usuario`
  existente. Lo reutilizarán `US-2.2.4`/`US-2.2.5`.
- ✅ **`SQLAlchemyUsuarioRepository`** (`src/identidad/interface_adapters/gateways/usuario_repository.py`)
  — implementa `actualizar()`; `_armar_usuario()` hidrata también `bloqueada`/contadores

### Frameworks
- ✅ **`UsuarioModel`** (`src/identidad/frameworks/db/models.py`) — 3 columnas nuevas
- ✅ Migración Alembic `4c1b823c7d9f_usuario_bloqueo_intentos_fallidos.py` — `nullable=False`
  con `server_default` (backfill de filas existentes), aplicada localmente
- ✅ **`POST /identidad/login`** (`src/identidad/frameworks/api/auth_router.py`) — traduce
  `CuentaBloqueadaError` a `403` (antes de `CredencialesInvalidas`, que sigue en `401`)

---

## API Endpoints

| Método | Ruta | Descripción | Cambio |
|--------|------|-------------|--------|
| POST | `/identidad/login` | Autenticación (`US-1.1.4`) | Ahora responde `403` si la cuenta está bloqueada |

---

## Nota de diseño: evento en el camino de excepción

No hay event store en el proyecto — los eventos de dominio viajan devueltos junto al
resultado exitoso en el `tuple` de retorno de cada use case (patrón usado en toda la
Iteración 1/2). El camino de bloqueo de esta US termina en una excepción, no en un retorno,
así que no hay tupla donde devolver `CuentaBloqueada`. Se adjuntó como atributo
`evento_cuenta_bloqueada` de `CredencialesInvalidas`, seteado por el use case solo cuando el
fallo es el 3er intento consecutivo — la forma mínima de mantenerlo observable/testeable sin
introducir un mecanismo de publicación nuevo fuera de alcance.

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.51/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 6 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mín) | 53.50 | > 20 | ✅ |
| Cobertura de Tests | 99% | ≥ 95% | ✅ |

Fuente: `quality/reports/inc2/US-2.2.1-quality.json`. Pylint acotado a los 8 archivos de
`src/identidad` modificados/agregados por esta US. La única advertencia nueva (no
preexistente) es `R0902` (too-many-instance-attributes, 8/7) en `Usuario` — aceptada, son
atributos de estado del aggregate. La única línea sin cobertura es el guard defensivo
`if usuario_model is None: return` en `SQLAlchemyUsuarioRepository.actualizar()`, no
alcanzable en los flujos actuales.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (4 tests nuevos)
- `tests/unit/inc1/test_iniciar_sesion_use_case.py` — `TestBloqueoCuentaLogin` (4 tests: fallo
  bajo el límite, 3er fallo bloquea, acierto resetea el contador, intento sobre cuenta
  bloqueada). 100% coverage en `entities/` y `use_cases/` del BC.

### Tests de Integración (3 tests nuevos)
- `tests/integration/inc1/test_auth_api_integration.py` — `TestBloqueoCuentaLoginAPIIntegration`
  (3 tests contra la API real + DB real: 3er fallo bloquea con verificación en DB, intento
  sobre cuenta bloqueada responde 403, acierto antes del límite resetea el contador)

### Escenarios BDD (4 escenarios)
- `tests/features/inc2/US-2.2.1-bloqueo-cuenta-login.feature` +
  `tests/step_defs/inc2/test_us_2_2_1_steps.py` — los 4 criterios de aceptación de la spec,
  1:1

**Todos los tests pasando:** ✅ 281/281 (unit + integration + step_defs, suite completa)

---

## Archivos Creados/Modificados

### Código de producción
- `src/identidad/entities/usuario.py`
- `src/identidad/entities/eventos.py`
- `src/identidad/entities/errors.py`
- `src/identidad/entities/ports/usuario_repository_port.py`
- `src/identidad/interface_adapters/gateways/usuario_repository.py`
- `src/identidad/frameworks/db/models.py`
- `src/identidad/frameworks/api/auth_router.py`
- `src/identidad/use_cases/iniciar_sesion.py`
- `migrations/versions/4c1b823c7d9f_usuario_bloqueo_intentos_fallidos.py`

### Tests
- `tests/unit/inc1/_fakes.py` (agrega `actualizar()` a `FakeUsuarioRepository`)
- `tests/unit/inc1/test_iniciar_sesion_use_case.py`
- `tests/integration/inc1/test_auth_api_integration.py`
- `tests/features/inc2/US-2.2.1-bloqueo-cuenta-login.feature`
- `tests/step_defs/inc2/test_us_2_2_1_steps.py`

### Documentación
- `docs/plans/US-2.2.1-context.md`
- `docs/plans/US-2.2.1-plan.md`
- `docs/reports/inc2/US-2.2.1-report.md` (este archivo)
- `quality/reports/inc2/US-2.2.1-quality.json`

---

## Criterios de Aceptación

- [x] Fallo que no llega al límite: contador sube, cuenta sigue sin bloquear
- [x] Tercer fallo consecutivo bloquea la cuenta y emite `CuentaBloqueada`
- [x] Acierto resetea el contador a 0
- [x] Intento sobre cuenta ya bloqueada rechaza con `CuentaBloqueadaError` sin verificar password

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.2.2` — Administrador ve el listado de cuentas, filtra por rol/estado/búsqueda
- [ ] `US-2.2.5` — Usuario autenticado cambia su propia contraseña (reutiliza
  `intentos_fallidos_password` y `actualizar()` agregados en esta US)
- [ ] `US-2.2.9` — Login refleja el estado de cuenta bloqueada en el frontend (frontend
  pendiente, esta US es backend puro)

---

## Lecciones Aprendidas

- 💡 No hay event store en el proyecto — cuando un evento se emite en el mismo camino que
  termina en excepción, adjuntarlo como atributo de la excepción es la forma más simple de
  mantenerlo observable sin introducir infraestructura nueva.
- ✅ Agregar `actualizar()` al puerto (en vez de sobrecargar `guardar()`) deja el contrato de
  persistencia claro para que `US-2.2.4`/`US-2.2.5` lo reutilicen sin volver a tocar el puerto.
- ⚠️ Extender un puerto con un método abstracto nuevo rompe cualquier test double existente que
  lo implemente — hay que actualizar los fakes en la misma tarea, no como paso separado.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-19
