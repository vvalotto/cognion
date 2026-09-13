# Reporte de Implementación: US-ADJ-39 - Confirmar nueva contraseña con token de recuperación (endpoint público)

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-39 |
| **Título** | Confirmar nueva contraseña con token de recuperación (endpoint público) |
| **Producto** | cognion |
| **Prioridad** | Alta — segunda de la Iteración 2 del Incremento 5-ADJ, depende de `US-ADJ-38` (ya cerrada) |
| **Puntos estimados** | 3 |
| **Fecha inicio** | 2026-09-13 |
| **Fecha fin** | 2026-09-13 |
| **Tiempo real** | ~28 min de tracking (Fases 0 a 9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Segunda US de la Iteración 2 del Incremento 5-ADJ (recuperación de contraseña por
autoservicio): cierra el flujo que `US-ADJ-38` dejó abierto — agrega
`ConfirmarNuevaPasswordUseCase`, que canjea un `TokenRecuperacionPassword` vigente por una
contraseña nueva, endpoint público `POST /identidad/recuperar-password/confirmar`.

Reutiliza sin cambios el aggregate y el puerto de persistencia ya creados en `US-ADJ-38` —
sin puertos ni gateways nuevos. Único componente de dominio genuinamente nuevo:
`Usuario.recuperar_password()`, un método de mutación que actualiza `password_hash` sin
tocar `bloqueada` ni los contadores de intentos fallidos (a diferencia de
`resetear_password()`, que desbloquea, y `cambiar_password()`, que resetea un contador) —
necesario para cumplir la postcondición explícita del modelo (`BC-identidad-modelo.md`
§13.4): una cuenta bloqueada sigue bloqueada después de recuperar su contraseña.

---

## Componentes Implementados

### Código Fuente (Backend)

- ✅ `src/identidad/entities/errors.py` — `TokenRecuperacionInvalido`, `TokenRecuperacionVencido`, `TokenRecuperacionYaUsado` (nuevas)
- ✅ `src/identidad/entities/token_recuperacion_password.py` — `verificar_vigente()` (nuevo método)
- ✅ `src/identidad/entities/usuario.py` — `recuperar_password()` (nuevo método)
- ✅ `src/identidad/entities/eventos.py` — `PasswordRecuperada` (nuevo)
- ✅ `src/identidad/use_cases/confirmar_nueva_password.py` — `ConfirmarNuevaPasswordUseCase` (nuevo)
- ✅ `src/identidad/interface_adapters/controllers/recuperacion_password_controller.py` — método `confirmar()` agregado
- ✅ `src/identidad/frameworks/api/schemas.py` — `ConfirmarRecuperacionPasswordRequest`/`Response` agregados
- ✅ `src/identidad/frameworks/api/recuperacion_password_router.py` — endpoint `POST /identidad/recuperar-password/confirmar` (nuevo)
- ✅ `src/identidad/frameworks/dependencies.py` — `get_recuperacion_password_controller()` extendido con `ConfirmarNuevaPasswordUseCase`

**Total archivos de producción:** 9 (2 nuevos: `confirmar_nueva_password.py`; el resto
modificados). Sin puertos, gateways ni migraciones nuevas — todo lo de persistencia ya
existía desde `US-ADJ-38`.

---

### Tests

#### Tests Unitarios (13 tests nuevos)
- ✅ `tests/unit/inc1/test_token_recuperacion_password.py` ampliado — 5 tests (`verificar_vigente`)
- ✅ `tests/unit/inc1/test_usuario.py` ampliado — 3 tests (`recuperar_password`)
- ✅ `tests/unit/inc1/test_confirmar_nueva_password_use_case.py` (nuevo) — 8 tests (happy path, token ya usado/vencido/inexistente, password inválida, usuario huérfano, cuenta bloqueada)
- ✅ `tests/unit/inc1/test_recuperacion_password_controller.py` actualizado a la firma de 2 use cases + 1 test nuevo de `confirmar()`

**Estado:** 483/483 tests unitarios del proyecto en verde · **100% cobertura** en los 6
componentes de negocio tocados (excepto `usuario.py`, 95% — 4 líneas pre-existentes sin
relación con esta US).

#### Tests de Integración (6 tests nuevos)
- ✅ `tests/integration/inc1/test_confirmar_recuperacion_password_api_integration.py` (nuevo) — happy path con login real post-canje, token ya usado, vencido, inexistente, password débil, cuenta bloqueada que sigue bloqueada

**Estado:** 86/86 tests de integración de `inc1` en verde

#### Escenarios BDD (6 escenarios nuevos)
- ✅ `tests/features/inc5-adj/US-ADJ-39-confirmar-recuperacion-password.feature`
- ✅ `tests/step_defs/inc5-adj/test_us_adj_39_steps.py` (nuevo)

**Estado:** 6/6 pasando

**Total tests nuevos:** 25 (13 unit + 6 integration + 6 BDD) · **Estado global:** 230/231
tests de `tests/step_defs/` en verde — el único fallo es
`test_rechazo_fuera_del_período_vigente` (`tests/step_defs/inc3/test_us_3_2_1_steps.py`),
flake preexistente ya documentado en `CLAUDE.md`, ajeno a esta US.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (9 archivos modificados/agregados) | 9.96/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx) | 8 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** (mín) | 57.53 | > 20 | ✅ |
| **Coverage** (entities + use case + controller) | 100% | ≥ 95% | ✅ |
| **mypy** (9 archivos) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (9 archivos modificados/agregados) | 18 errors, 2 warnings | 0 CRITICAL | ✅ |

### Detalle de Pylint

```
Your code has been rated at 9.96/10

Hallazgos restantes (no bloqueantes):
- R0902 (too-many-instance-attributes, 10/7) en Usuario — pre-existente, confirmado contra
  develop antes de esta US, no introducido por ella.
- R0903 (too-few-public-methods) en ConfirmarNuevaPasswordUseCase — mismo patrón ya
  aceptado en el proyecto para Use Cases de un solo comando.
```

### Detalle de Coverage

```
Name                                                                               Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------------------------------------------
src/identidad/entities/errors.py                                                      71      0   100%
src/identidad/entities/eventos.py                                                     68      0   100%
src/identidad/entities/token_recuperacion_password.py                                 26      0   100%
src/identidad/entities/usuario.py                                                      87      4    95%   117-118, 127, 135
src/identidad/interface_adapters/controllers/recuperacion_password_controller.py      13      0   100%
src/identidad/use_cases/confirmar_nueva_password.py                                   34      0   100%
----------------------------------------------------------------------------------------------------------------
TOTAL                                                                                 299      4    99%
```

Las 4 líneas sin cubrir de `usuario.py` (117-118, 127, 135) son `editar_datos()`/
`deshabilitar()`/`activar()` — pre-existentes, sin relación con esta US.

### Detalle de CodeGuard

> Requiere que el reporte se haya generado con `--analysis-type full` (ver Fase 7) — en
> modo `pre-commit` (default de la CLI) solo corren 3 de los 9 checks, sin ninguna señal
> de que los otros 6 fueron omitidos (`vvalotto/software_limpio#71`).

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 9 |
| PEP8 | 0 | 0 | 9 |
| Complexity | 0 | 0 | 9 |
| DeadCode | 9 | 0 | 0 |
| Maintainability | 0 | 0 | 9 |
| Pylint | 0 | 2 | 7 |
| Spelling | 9 | 0 | 0 |
| Types | 0 | 0 | 9 |
| UnusedImports | 0 | 0 | 9 |

Fuente: `quality/reports/inc5-adj/US-ADJ-39-codeguard.json` →
`quality.codeguard.checks` en `quality/reports/inc5-adj/US-ADJ-39-quality.json`.

Los 9 errores de `DeadCode` y los 9 de `Spelling` son `vulture not installed`/`codespell not
installed` — herramientas no instaladas en este entorno, mismo gap preexistente ya visto en
`US-ADJ-38` (no introducido por esta US). Los 2 warnings de `Pylint` son
`recuperacion_password_router.py` (6.88/10) y `schemas.py` (7.14/10) evaluados aisladamente
por CodeGuard (un archivo a la vez) — el mismo pylint corrido junto con el resto de los
archivos tocados da 10.00/10 sobre ambos (ver tabla de arriba). La fuente de verdad real es
el pylint (9.96/10) y mypy (0 issues) corridos directo sobre el mismo set de 9 archivos.

---

## Criterios de Aceptación

- [x] Confirmar con un token vigente y contraseña válida responde 200, actualiza
  `Usuario.password_hash` y marca el token como usado
- [x] Confirmar con un token ya usado responde `TokenRecuperacionYaUsado`, sin cambiar el hash
- [x] Confirmar con un token vencido responde `TokenRecuperacionVencido` (INV-ID-13)
- [x] Confirmar con un token inexistente responde `TokenRecuperacionInvalido`
- [x] Confirmar con una contraseña que no cumple INV-ID-11 ampliada responde
  `PasswordDemasiadoCorta`/`PasswordSinComplejidadSuficiente`, sin marcar el token
- [x] Confirmar sobre una cuenta bloqueada actualiza el hash pero no desbloquea la cuenta

**Estado:** 6/6 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Mismo patrón que `RegistrarEstudianteUseCase`/`Invitacion.verificar_vigente()` (`US-1.1.6`):
un método de entidad `verificar_vigente(ahora)` que centraliza la distinción entre
"ya usado" y "vencido", consultado por el Use Case antes de mutar cualquier estado. Sin
decisión arquitectónica nueva — reutiliza el aggregate, el puerto y el mapeo de errores ya
existentes.

### Flujo de Datos

```
POST /identidad/recuperar-password/confirmar {token, password_nueva}
  → RecuperacionPasswordController.confirmar(token, password_nueva)
    → ConfirmarNuevaPasswordUseCase.execute(token, password_nueva)
      1. TokenRecuperacionPasswordRepositoryPort.obtener_por_token(token)
      2. Si no existe → TokenRecuperacionInvalido
      3. token.verificar_vigente(ahora) → TokenRecuperacionYaUsado / TokenRecuperacionVencido
      4. UsuarioRepositoryPort.obtener_por_id(token.usuario_id)
      5. Usuario.validar_password_nueva(password_nueva) → PasswordDemasiadoCorta / PasswordSinComplejidadSuficiente
      6. usuario.recuperar_password(hasher.hash(password_nueva))  ← no toca bloqueada/contadores
      7. UsuarioRepositoryPort.actualizar(usuario)
      8. token.invalidar(ahora)
      9. TokenRecuperacionPasswordRepositoryPort.actualizar(token)
  ← 200 OK / 422 según la excepción
```

---

## Cambios no Previstos

Ninguno respecto del plan aprobado en Fase 2 — el único punto marcado explícitamente como
decisión de diseño (el método nuevo `Usuario.recuperar_password()`, en vez de reutilizar
`resetear_password()`/`cambiar_password()`) ya estaba señalado en el plan antes de
implementar, no surgió como ajuste posterior.

---

## Testing Manual Realizado

No aplica — endpoint backend puro sin pantalla propia (la pantalla llega en `US-ADJ-40`).
Verificado end-to-end con la suite automatizada (unit + integración + BDD), incluido el
login real con la contraseña nueva tras el canje.

---

## Deuda Técnica

Ninguna introducida por esta US. Persiste la deuda ya documentada de CodeGuard (vulture/
codespell no instalados, pylint por archivo aislado da falsos negativos) — ajena a esta US,
ya reportada upstream (`vvalotto/software_limpio#71`).

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-40` — Pantallas de recuperación de contraseña — depende de `US-ADJ-38`/`39`,
  cierra completa la Iteración 2 del Incremento 5-ADJ.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 36s |
| BDD (escenarios) | 26s |
| Plan | 134s |
| Implementación (9 tareas) | 164s |
| Tests Unitarios | 155s |
| Tests de Integración | 156s |
| Validación BDD | 434s |
| Quality Gates | 459s |
| Documentación | 51s |
| **TOTAL** | **~1615s (~27 min)** |

La mayor parte del tiempo (Validación BDD y Quality Gates) corresponde a la corrida de la
suite completa de `tests/step_defs/` (231 escenarios, ~5 min) y de CodeGuard en modo `full`
sobre 9 archivos — no a esfuerzo de diagnóstico o corrección.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. El modelo de dominio (`BC-identidad-modelo.md` §13.4, escrito en `US-ADJ-32`) ya
   especificaba el comando, el evento y las tres excepciones exactos — cero decisiones de
   diseño de dominio nuevas durante la implementación.
2. Reutilizar `TokenRecuperacionPassword.invalidar()` (ya pensado en `US-ADJ-38` para este
   caso, según su propio docstring) evitó un método nuevo redundante en la entidad.

### Recomendaciones para Próximas Historias

1. Cuando la spec de una US dice "mismo método que X" pero el criterio de aceptación en
   Gherkin exige un comportamiento distinto al de X (acá: `resetear_password()` desbloquea,
   pero el escenario exige que la cuenta siga bloqueada), el Gherkin es la fuente de verdad
   — vale la pena señalar la contradicción al usuario en la Fase 2 antes de codear, no
   asumir en silencio cuál de las dos lecturas es la correcta.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-13.
