# Reporte de Implementación: US-ADJ-42 - Autoregistro de Estudiante (endpoint público)

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-42 |
| **Título** | Autoregistro de Estudiante (endpoint público) |
| **Producto** | identidad |
| **Prioridad** | Segunda de la Iteración 3 del Incremento 5-ADJ — `US-ADJ-43` depende de esta |
| **Puntos estimados** | 3 |
| **Fecha inicio** | 2026-09-13 |
| **Fecha fin** | 2026-09-13 |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Segunda US de la Iteración 3 del Incremento 5-ADJ (autoregistro con selección de perfil):
agrega el comando `AutoregistrarEstudianteUseCase`, hermano de `AutoregistrarDocenteUseCase`
(`US-ADJ-41`), endpoint público `POST /identidad/autoregistro/estudiante` que crea una cuenta
`Estudiante` asignada a una `Comisión` existente y activa de inmediato (INV-ID-16), sin
invitación ni Docente. Reutiliza en su totalidad `Usuario.crear_estudiante()`/
`UsuarioRepositoryPort`/`PasswordHasherPort`/`ComisionRepositoryPort` ya existentes y el evento
`UsuarioAutoregistrado` de `US-ADJ-41` sin cambios de shape. Mismo criterio de "dos comandos
separados" ya documentado en `BC-identidad-modelo.md` §13.2 — no se generalizó con un parámetro
`perfil`, porque `Estudiante` exige `comision_id` (INV-ID-14) y `Docente` no admite ninguno.

Sin decisiones arquitectónicas nuevas — mismo patrón ya usado en `AutoregistrarDocente`/
`RegistrarEstudiante`.

---

## Componentes Implementados

### Código Fuente (Backend)

- ✅ `src/identidad/use_cases/autoregistrar_estudiante.py` — `AutoregistrarEstudianteUseCase` (nuevo)
- ✅ `src/identidad/interface_adapters/controllers/autoregistro_controller.py` — método `autoregistrar_estudiante` agregado
- ✅ `src/identidad/frameworks/api/autoregistro_router.py` — endpoint `POST /identidad/autoregistro/estudiante` (nuevo)
- ✅ `src/identidad/frameworks/api/schemas.py` — `AutoregistrarEstudianteRequest` agregado (reutiliza `AutoregistroResponse`)
- ✅ `src/identidad/frameworks/dependencies.py` — `get_autoregistro_controller()` cablea el nuevo use case

**Total archivos de producción:** 5 (1 nuevo; 4 modificados)

---

### Tests

#### Tests Unitarios (6 tests)
- ✅ `tests/unit/inc1/test_autoregistrar_estudiante_use_case.py` — 4 tests (use case: happy path, email duplicado, comisión inexistente, password débil)
- ✅ `tests/unit/inc1/test_autoregistro_controller.py` — 2 tests (controller delega ambos use cases; test de Docente preexistente actualizado a la nueva firma de 2 argumentos)

**Estado:** 6/6 pasando · **100% cobertura** en use case/controller

#### Tests de Integración (5 tests)
- ✅ `tests/integration/inc5-adj/test_autoregistro_estudiante_api_integration.py` — 5 tests (endpoint end-to-end contra Postgres real, incluido login inmediato post-alta)

**Estado:** 5/5 pasando

#### Escenarios BDD (5 escenarios)
- ✅ `tests/features/inc5-adj/US-ADJ-42-autoregistro-estudiante.feature`
- ✅ `tests/step_defs/inc5-adj/test_us_adj_42_steps.py` (nuevo)

**Estado:** 5/5 pasando

**Total tests nuevos:** 16 (6 unit + 5 integration + 5 BDD) · **Estado global:** unit 492/492,
integration 336/336, BDD 240/240 tests del proyecto completo en verde, sin regresiones.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (5 archivos modificados/agregados) | 9.58/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx) | 3 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** | A (>20) | > 20 | ✅ |
| **Coverage** (use case + controller) | 100% | ≥ 95% | ✅ |
| **CodeGuard** (`--analysis-type full`, 5 archivos) | 0 errors, 135 warnings, 39 infos | 0 CRITICAL | ✅ |

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 5 |
| PEP8 | 0 | 0 | 5 |
| Complexity | 0 | 0 | 5 |
| DeadCode | 0 | 131 | 1 |
| Maintainability | 0 | 0 | 5 |
| Pylint | 0 | 0 | 5 |
| Spelling | 0 | 4 | 3 |
| Types | 0 | 0 | 5 |
| UnusedImports | 0 | 0 | 5 |

Fuente: `quality/reports/inc5-adj/US-ADJ-42-codeguard.json`.

Los 131 warnings de `DeadCode` (vulture) son el mismo tipo de falso positivo ya aceptado en
`US-ADJ-41` (57 warnings sobre 4 archivos) — acá crecen porque `dependencies.py` (composition
root completo del BC, no solo el código nuevo de esta US) entra en el set analizado y vulture
no ve los imports desde fuera de ese conjunto aislado de 5 archivos. Pylint directo (9.58/10)
sobre los archivos modificados es la fuente de verdad real.

---

## Criterios de Aceptación

- [x] `POST /identidad/autoregistro/estudiante` con un email no usado y un `comision_id`
  existente crea un `Usuario` con perfil `Estudiante` asignado a esa comisión, activo de
  inmediato, responde `201 Created`
- [x] El mismo endpoint con un email ya registrado responde `409 Conflict`, sin crear nada
- [x] El mismo endpoint con un `comision_id` inexistente responde `422`, sin crear nada
- [x] El mismo endpoint con una contraseña que no cumple INV-ID-11 responde `422`, sin crear
  nada
- [x] La cuenta creada puede loguearse inmediatamente con `POST /identidad/login`

**Estado:** 5/5 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Mismo patrón que `AutoregistrarDocenteUseCase`/`RegistrarEstudianteUseCase`: valida email
único, valida `comision_id` contra `ComisionRepositoryPort.obtener_por_id()` (INV-ID-14), valida
`password` contra `Usuario.validar_password_nueva()` (INV-ID-11 ampliada), crea el `Usuario` vía
el factory ya existente (`Usuario.crear_estudiante(...)`), persiste. Sin puertos nuevos, sin
dependencias nuevas entre BCs.

### Flujo de Datos

```
POST /identidad/autoregistro/estudiante {nombre, email, password, comision_id}
  → AutoregistroController.autoregistrar_estudiante(nombre, email, password, comision_id)
    → AutoregistrarEstudianteUseCase.execute(nombre, email, password, comision_id)
      1. UsuarioRepositoryPort.existe_email(email) → si existe, EmailYaRegistrado (409)
      2. ComisionRepositoryPort.obtener_por_id(comision_id) → si None, ComisionNoExiste (422)
      3. Usuario.validar_password_nueva(password) → si no cumple, 422
      4. Usuario.crear_estudiante(nombre, email, hash, comision_id) — bloqueada=False (INV-ID-16)
      5. UsuarioRepositoryPort.guardar(usuario)
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

- [ ] `US-ADJ-43` — Pantalla de autoregistro con selección de perfil (Docente/Estudiante),
  formulario dinámico con selector Materia→Comisión para Estudiante — depende de
  `US-ADJ-41`/`42`.

---

## Aprobación

Pendiente de revisión por Víctor.
