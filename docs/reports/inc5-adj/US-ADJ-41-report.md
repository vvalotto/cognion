# Reporte de Implementación: US-ADJ-41 - Autoregistro de Docente (endpoint público)

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-41 |
| **Título** | Autoregistro de Docente (endpoint público) |
| **Producto** | cognion |
| **Prioridad** | Alta — primera de la Iteración 3 del Incremento 5-ADJ, `US-ADJ-42`/`43` dependen de esta |
| **Puntos estimados** | 3 |
| **Fecha inicio** | 2026-09-13 |
| **Fecha fin** | 2026-09-13 |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Primera US de la Iteración 3 del Incremento 5-ADJ (autoregistro con selección de perfil):
agrega el comando `AutoregistrarDocenteUseCase` y el evento `UsuarioAutoregistrado`, endpoint
público `POST /identidad/autoregistro/docente` que crea una cuenta `Docente` activa de
inmediato (INV-ID-16), sin invitación ni Administrador. Reutiliza en su totalidad
`Usuario.crear()`/`UsuarioRepositoryPort`/`PasswordHasherPort` ya existentes — la única
diferencia real con `CrearUsuarioUseCase` es el actor (sin autenticar) y el evento emitido
(`UsuarioAutoregistrado` en vez de `UsuarioCreado`, mismo shape, distinto tipo — modelado así
en `BC-identidad-modelo.md` §13.2 para distinguir alta administrativa de autoservicio).

Sin decisiones arquitectónicas nuevas — mismo patrón ya usado en `RegistrarEstudiante`/
`CrearUsuario`.

---

## Componentes Implementados

### Código Fuente (Backend)

- ✅ `src/identidad/entities/eventos.py` — evento `UsuarioAutoregistrado` agregado
- ✅ `src/identidad/use_cases/autoregistrar_docente.py` — `AutoregistrarDocenteUseCase` (nuevo)
- ✅ `src/identidad/interface_adapters/controllers/autoregistro_controller.py` — controller (nuevo)
- ✅ `src/identidad/frameworks/api/autoregistro_router.py` — endpoint `POST /identidad/autoregistro/docente` (nuevo)
- ✅ `src/identidad/frameworks/api/schemas.py` — `AutoregistrarDocenteRequest`/`AutoregistroResponse` agregados
- ✅ `src/identidad/frameworks/dependencies.py` — composition root: `get_autoregistro_controller()`
- ✅ `src/app.py` — registra el router nuevo

**Total archivos de producción:** 7 (3 nuevos; 4 modificados)

---

### Tests

#### Tests Unitarios (4 tests)
- ✅ `tests/unit/inc1/test_autoregistrar_docente_use_case.py` — 3 tests (use case: happy path, email duplicado, password débil)
- ✅ `tests/unit/inc1/test_autoregistro_controller.py` — 1 test (controller delega al use case)

**Estado:** 4/4 pasando · **100% cobertura** en use case/controller

#### Tests de Integración (4 tests)
- ✅ `tests/integration/inc5-adj/test_autoregistro_docente_api_integration.py` — 4 tests (endpoint end-to-end contra Postgres real, incluido login inmediato post-alta)

**Estado:** 4/4 pasando

#### Escenarios BDD (4 escenarios)
- ✅ `tests/features/inc5-adj/US-ADJ-41-autoregistro-docente.feature`
- ✅ `tests/step_defs/inc5-adj/test_us_adj_41_steps.py` (nuevo)

**Estado:** 4/4 pasando

**Total tests nuevos:** 12 (4 unit + 4 integration + 4 BDD) · **Estado global:** 1053/1053
tests del proyecto completo (unit + integration + BDD) en verde, sin regresiones.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (7 archivos modificados/agregados) | 9.93/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx) | 3 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** | A (>20) | > 20 | ✅ |
| **Coverage** (use case + controller) | 100% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (`--analysis-type full`, 4 archivos) | 0 errors, 60 warnings, 31 infos | 0 CRITICAL | ✅ |

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 4 |
| PEP8 | 0 | 0 | 4 |
| Complexity | 0 | 0 | 4 |
| DeadCode | 0 | 57 | 1 |
| Maintainability | 0 | 0 | 4 |
| Pylint | 0 | 0 | 4 |
| Spelling | 0 | 3 | 2 |
| Types | 0 | 0 | 4 |
| UnusedImports | 0 | 0 | 4 |

Fuente: `quality/reports/inc5-adj/US-ADJ-41-codeguard.json`.

Los 57 warnings de `DeadCode` (vulture) son falso positivo esperado al analizar 4 archivos
aislados del resto del proyecto: `eventos.py` completo (10 eventos preexistentes, no solo el
nuevo) aparece como "clase nunca usada" porque vulture no ve los imports desde otros módulos
fuera del set analizado — mismo patrón de ruido ya aceptado en corridas de `CodeGuard` sobre
subconjuntos de archivos en USs previas. Pylint directo (9.93/10) y mypy (0 errores) sobre
`src/` completo son la fuente de verdad real.

---

## Criterios de Aceptación

- [x] `POST /identidad/autoregistro/docente` con un email no usado crea un `Usuario` con
  perfil `Docente`, activo de inmediato, responde `201 Created`
- [x] El mismo endpoint con un email ya registrado responde `409 Conflict`, sin crear nada
- [x] El mismo endpoint con una contraseña que no cumple INV-ID-11 responde `422`, sin crear
  nada
- [x] La cuenta creada puede loguearse inmediatamente con `POST /identidad/login`

**Estado:** 4/4 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Mismo patrón que `CrearUsuarioUseCase`/`RegistrarEstudianteUseCase`: valida email único,
valida `password` contra `Usuario.validar_password_nueva()` (INV-ID-11 ampliada), crea el
`Usuario` vía el factory ya existente (`Usuario.crear(..., TipoPerfil.DOCENTE)`), persiste.
Sin puertos nuevos, sin dependencias nuevas entre BCs.

### Flujo de Datos

```
POST /identidad/autoregistro/docente {nombre, email, password}
  → AutoregistroController.autoregistrar_docente(nombre, email, password)
    → AutoregistrarDocenteUseCase.execute(nombre, email, password)
      1. UsuarioRepositoryPort.existe_email(email) → si existe, EmailYaRegistrado (409)
      2. Usuario.validar_password_nueva(password) → si no cumple, 422
      3. Usuario.crear(nombre, email, hash, TipoPerfil.DOCENTE) — bloqueada=False (INV-ID-16)
      4. UsuarioRepositoryPort.guardar(usuario)
  ← 201 Created con los datos del Usuario
```

---

## Cambios no Previstos

Ninguno — la spec se implementó tal como estaba escrita, sin gaps detectados en el camino.

---

## Testing Manual Realizado

No aplica — endpoint backend puro sin pantalla propia (la pantalla llega en `US-ADJ-43`).
Verificado end-to-end con la suite automatizada (unit + integración + BDD).

---

## Deuda Técnica

Ninguna introducida por esta US.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-42` — Autoregistro de Estudiante (endpoint público) — sigue a esta.
- [ ] `US-ADJ-43` — Pantallas de autoregistro con selección de perfil — depende de
  `US-ADJ-41`/`42`.

---

## Aprobación

Pendiente de revisión por Víctor.
