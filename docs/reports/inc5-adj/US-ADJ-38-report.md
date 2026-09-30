# Reporte de Implementación: US-ADJ-38 - Solicitar recuperación de contraseña (endpoint público)

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-38 |
| **Título** | Solicitar recuperación de contraseña (endpoint público) |
| **Producto** | cognion |
| **Prioridad** | Alta — primera de la Iteración 2 del Incremento 5-ADJ, `US-ADJ-39` depende de esta |
| **Puntos estimados** | 3 |
| **Fecha inicio** | 2026-09-13 |
| **Fecha fin** | 2026-09-13 |
| **Tiempo real** | ~35 min de tracking (Fases 0 a 9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Primera US de la Iteración 2 del Incremento 5-ADJ (recuperación de contraseña por
autoservicio): agrega el aggregate `TokenRecuperacionPassword` (token único, expiración a
1 hora, INV-ID-13) y el comando `SolicitarRecuperacionPasswordUseCase`, que busca el
`Usuario` por email, invalida cualquier token activo previo del mismo usuario (INV-ID-12) y
dispara el envío del email — endpoint público `POST /identidad/recuperar-password/solicitar`,
que responde siempre `202 Accepted` con el mismo mensaje genérico exista o no la cuenta
(INV-ID-17, no filtrar existencia de cuentas).

Hito arquitectónico de la US: **primera vez que BC Identidad depende de un puerto de BC
Notificaciones** — `CanalRecuperacionPort`/`CanalRecuperacionPortInProcess` invocan
`SmtpCanalEnvio` de Notificaciones directo (`ADR-006`), en vez del adaptador SMTP propio que
usa `GenerarInvitacion` (`ADR-012`). El manejo de un fallo de envío ("loguear y continuar")
vive en el Use Case, no en el adapter — mismo contrato que `CanalEnvioPort` de Notificaciones.

---

## Componentes Implementados

### Código Fuente (Backend)

- ✅ `src/identidad/entities/token_recuperacion_password.py` — aggregate `TokenRecuperacionPassword` (nuevo)
- ✅ `src/identidad/entities/ports/token_recuperacion_password_repository_port.py` — puerto de persistencia (nuevo)
- ✅ `src/identidad/entities/ports/canal_recuperacion_port.py` — puerto Identidad → Notificaciones (nuevo)
- ✅ `src/identidad/use_cases/solicitar_recuperacion_password.py` — `SolicitarRecuperacionPasswordUseCase` (nuevo)
- ✅ `src/identidad/frameworks/db/models.py` — `TokenRecuperacionPasswordModel` agregado
- ✅ `src/identidad/interface_adapters/gateways/token_recuperacion_password_repository.py` — gateway SQLAlchemy (nuevo)
- ✅ `src/identidad/frameworks/adapters/canal_recuperacion_port_in_process.py` — adapter cruzado hacia Notificaciones (nuevo)
- ✅ `src/identidad/interface_adapters/controllers/recuperacion_password_controller.py` — controller (nuevo)
- ✅ `src/identidad/frameworks/api/recuperacion_password_router.py` — endpoint `POST /identidad/recuperar-password/solicitar` (nuevo)
- ✅ `src/identidad/frameworks/api/schemas.py` — `SolicitarRecuperacionPasswordRequest`/`Response` agregados
- ✅ `src/identidad/frameworks/dependencies.py` — composition root: `get_canal_recuperacion()`, `get_recuperacion_password_controller()`
- ✅ `src/app.py` — registra el router nuevo
- ✅ `src/settings.py` — `frontend_url` agregado (link del email de recuperación)
- ✅ `migrations/versions/e31e7dfcab3a_token_recuperacion_password.py` — tabla `token_recuperacion_password`

**Total archivos de producción:** 14 (13 nuevos, 1 migración; 4 modificados: `models.py`, `dependencies.py`, `app.py`, `settings.py`)

---

### Tests

#### Tests Unitarios (12 tests)
- ✅ `tests/unit/inc1/test_token_recuperacion_password.py` — 5 tests (entity: `crear`, `invalidar`)
- ✅ `tests/unit/inc1/test_solicitar_recuperacion_password_use_case.py` — 5 tests (use case: happy path, INV-ID-17, INV-ID-12, resiliencia ante fallo de envío)
- ✅ `tests/unit/inc1/test_recuperacion_password_controller.py` — 2 tests (controller delega al use case)
- ✅ `tests/unit/inc1/_fakes.py` ampliado — `FakeTokenRecuperacionPasswordRepository`, `FakeCanalRecuperacion`

**Estado:** 12/12 pasando · **100% cobertura** en entity/use case/controller

#### Tests de Integración (10 tests)
- ✅ `tests/integration/inc1/test_token_recuperacion_password_repository_integration.py` — 6 tests (gateway SQLAlchemy contra Postgres real)
- ✅ `tests/integration/inc1/test_recuperacion_password_api_integration.py` — 4 tests (endpoint end-to-end con SMTP fake)
- ✅ `tests/integration/conftest.py` — `limpiar_tablas_identidad` ampliado con `token_recuperacion_password`

**Estado:** 10/10 pasando

#### Escenarios BDD (4 escenarios)
- ✅ `tests/features/inc5-adj/US-ADJ-38-solicitar-recuperacion-password.feature`
- ✅ `tests/step_defs/inc5-adj/test_us_adj_38_steps.py` (nuevo) — incluye stub SMTP propio (mismo patrón que `US-ADJ-26`/`US-ADJ-36`)

**Estado:** 4/4 pasando

**Total tests nuevos:** 26 (12 unit + 10 integration + 4 BDD) · **Estado global:** 1011/1012
tests del proyecto completo (unit + integration + BDD) en verde — el único fallo es
`test_rechazo_fuera_del_período_vigente` (`tests/step_defs/inc3/test_us_3_2_1_steps.py`),
flake preexistente ya documentado (ventana de tiempo ajustada, confirmado ajeno a esta US).

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (13 archivos modificados/agregados) | 9.75/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx) | 3 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** (mín) | 49.97 | > 20 | ✅ |
| **Coverage** (entity + use case + controller + gateway) | 99% | ≥ 95% | ✅ |
| **mypy** (13 archivos) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (13 archivos modificados/agregados) | 33 errors, 6 warnings | 0 CRITICAL | ✅ |

### Detalle de Pylint

```
Your code has been rated at 9.75/10

Hallazgos restantes (no bloqueantes):
- R0903 (too-few-public-methods) en 4 clases de una sola responsabilidad
  (CanalRecuperacionPort, CanalRecuperacionPortInProcess, RecuperacionPasswordController,
  SolicitarRecuperacionPasswordUseCase) — patrón ya aceptado en el proyecto para puertos ABC
  de un método, adapters, controllers y use cases.
- R0903 x7 en modelos SQLAlchemy preexistentes de models.py (sin cambios de esta US).
```

### Detalle de Coverage

```
Name                                                                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------------------------------------------------
src/identidad/entities/ports/canal_recuperacion_port.py                                   5      0   100%
src/identidad/entities/ports/token_recuperacion_password_repository_port.py              14      0   100%
src/identidad/entities/token_recuperacion_password.py                                     20      0   100%
src/identidad/interface_adapters/controllers/recuperacion_password_controller.py           7      0   100%
src/identidad/interface_adapters/gateways/token_recuperacion_password_repository.py       33      1    97%   60
src/identidad/use_cases/solicitar_recuperacion_password.py                                25      0   100%
-------------------------------------------------------------------------------------------------------------------
TOTAL                                                                                    104      1    99%
```

Línea 60 sin cubrir: `ValueError` defensivo de `actualizar()` sobre un token inexistente —
mismo patrón sin testear en `SQLAlchemyInvitacionRepository.actualizar()` (error del llamador,
no un caso de negocio a ejercitar).

### Detalle de CodeGuard

> Requiere que el reporte se haya generado con `--analysis-type full` (ver Fase 7) — en
> modo `pre-commit` (default de la CLI) solo corren 3 de los 9 checks, sin ninguna señal
> de que los otros 6 fueron omitidos (`vvalotto/software_limpio#71`).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 13 |
| PEP8 | 0 | 2 | 11 |
| Complexity | 0 | 0 | 13 |
| DeadCode | 13 | 0 | 0 |
| Maintainability | 0 | 0 | 13 |
| Pylint | 4 | 4 | 5 |
| Spelling | 13 | 0 | 0 |
| Types | 2 | 0 | 10 |
| UnusedImports | 1 | 0 | 12 |

Fuente: `quality/reports/inc5-adj/US-ADJ-38-codeguard.json` →
`quality.codeguard.checks` en `quality/reports/inc5-adj/US-ADJ-38-quality.json`.

Los 13 errores de `DeadCode` y los 13 de `Spelling` son `vulture not installed`/`codespell not
installed` — herramientas no instaladas en este entorno, mismo gap preexistente ya visto en
`US-ADJ-36` (no introducido por esta US). Los 4 errores + 4 warnings de `Pylint` y los 2 de
`Types` son timeouts de pylint/mypy por archivo (>10s en frío, bug conocido documentado en
`CLAUDE.md`/`vvalotto/software_limpio#70`) — la fuente de verdad real es el pylint (9.75/10) y
mypy (0 issues) corridos directo sobre el mismo set de 13 archivos, ver tabla de arriba. Los 2
warnings de `PEP8` (line-too-long) ya fueron corregidos antes de cerrar Fase 7; el JSON crudo
de CodeGuard quedó generado antes del fix (no se regeneró, costo ~200s, pylint directo ya
confirma 0 `line-too-long`).

---

## Criterios de Aceptación

- [x] `POST /identidad/recuperar-password/solicitar` con un email de cuenta existente crea un
  `TokenRecuperacionPassword` válido por 1 hora
- [x] El mismo endpoint con un email inexistente responde igual (202, mismo mensaje), sin
  crear nada — INV-ID-17
- [x] Solicitar dos veces invalida el token anterior sin usar — INV-ID-12
- [x] Un fallo de envío de email no bloquea la respuesta — el token queda creado igual
- [x] Primera vez que Identidad depende de un puerto de Notificaciones, resuelto con el mismo
  mecanismo ya ratificado (`ADR-006`)

**Estado:** 5/5 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Mismo patrón que `Invitacion`/`GenerarInvitacionUseCase` (token + expiración + aggregate
propio, `ADR-012`), con una diferencia arquitectónica deliberada: el canal de envío no es un
adaptador SMTP propio de Identidad, sino un puerto nuevo (`CanalRecuperacionPort`) hacia BC
Notificaciones, resuelto con el mismo mecanismo de acoplamiento consciente ya ratificado en
`ADR-006` (puerto propio del BC consumidor + adapter in-process en `frameworks/`).

### Flujo de Datos

```
POST /identidad/recuperar-password/solicitar {email}
  → RecuperacionPasswordController.solicitar(email)
    → SolicitarRecuperacionPasswordUseCase.execute(email)
      1. UsuarioRepositoryPort.obtener_por_email(email)
      2. Si no existe → return (sin excepción, sin efecto — INV-ID-17)
      3. Si existe:
         a. TokenRecuperacionPasswordRepositoryPort.invalidar_activos_de(usuario.id, ahora)  ← INV-ID-12
         b. TokenRecuperacionPassword.crear(usuario.id)  ← INV-ID-13, expira_en = +1h
         c. TokenRecuperacionPasswordRepositoryPort.guardar(token)
         d. try: CanalRecuperacionPort.enviar_recuperacion(usuario.email, token.token)
            except: logger.warning(...)  ← no propaga, mismo criterio que NotificarAperturaUseCase
  ← siempre 202 Accepted, mensaje genérico
```

---

## Cambios no Previstos

- **Ajuste de diseño en Fase 4** (antes de escribir tests): el plan original ponía el
  `try/except` de fallo de envío dentro de `CanalRecuperacionPortInProcess` (adapter). Se
  movió a `SolicitarRecuperacionPasswordUseCase.execute()` para mantener consistencia con
  `CanalEnvioPort`/`NotificarAperturaUseCase` de Notificaciones (el adapter no captura nada,
  el Use Case decide "loguear y continuar").
- **Ubicación de los tests unitarios** (Fase 4): el plan asumía `tests/unit/inc5-adj/` (mismo
  nombre que la carpeta de features/step_defs), pero un directorio con guion no es un
  identificador Python válido — rompe los imports relativos entre archivos de test del mismo
  directorio. Los 12 tests unitarios se ubicaron en `tests/unit/inc1/` en su lugar, home ya
  establecido de BC Identidad para sus unit tests independientemente del incremento que los
  agrega (mismo criterio que `US-ADJ-23` a `30`).

---

## Testing Manual Realizado

No aplica — endpoint backend puro sin pantalla propia (la pantalla llega en `US-ADJ-40`).
Verificado end-to-end con la suite automatizada (unit + integración + BDD, incluido el envío
real de SMTP contra un stub local).

---

## Deuda Técnica

Ninguna introducida por esta US. Persiste la deuda ya documentada de CodeGuard (vulture/
codespell no instalados, timeout de pylint/mypy en frío) — ajena a esta US, ya reportada
upstream (`vvalotto/software_limpio#70`, `#71`).

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-39` — Confirmar nueva contraseña con token de recuperación (endpoint público) —
  depende de esta US (el token ya debe poder generarse).
- [ ] `US-ADJ-40` — Pantallas de recuperación de contraseña — depende de `US-ADJ-38`/`39`.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 41s |
| BDD (escenarios) | 50s |
| Plan | 46s |
| Implementación (9 tareas) | 194s |
| Tests Unitarios | 268s |
| Tests de Integración | 245s |
| Validación BDD | 204s |
| Quality Gates | 887s |
| Documentación | 83s |
| **TOTAL** | **~2018s (~34 min)** |

La mayor parte del tiempo (Quality Gates) corresponde a CodeGuard corriendo en modo `full`
sobre 13 archivos (~200s) más la corrida completa de pylint/radon/mypy — no a esfuerzo de
diagnóstico o corrección, a diferencia de `US-ADJ-36`.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar el patrón ya existente de `Invitacion` (token + expiración + aggregate propio,
   repositorio con la misma forma) evitó decisiones de diseño nuevas para la parte de
   persistencia — la única decisión real fue el puerto cruzado hacia Notificaciones.
2. Revisar `NotificarAperturaUseCase`/`CanalEnvioPort` antes de implementar el adapter
   detectó la inconsistencia de diseño (dónde vive el `try/except`) antes de escribir tests,
   evitando tener que rehacer tests ya escritos.

### Recomendaciones para Próximas Historias

1. Nunca nombrar un directorio de tests nuevo con el mismo slug con guion que su carpeta de
   `features`/`plans` (`inc5-adj`) — usar el directorio de tests unitarios ya establecido del
   BC (`tests/unit/inc1/` para Identidad) en vez de crear uno nuevo por incremento.
2. Al agregar un puerto cruzado hacia otro BC, revisar primero cómo maneja excepciones el
   puerto análogo ya existente en el BC destino (`CanalEnvioPort`) antes de decidir dónde va
   el manejo de errores — evita tener que mover código entre Fase 3 y Fase 4.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-13.
