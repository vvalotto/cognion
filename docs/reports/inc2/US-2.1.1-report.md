# Reporte de Implementación: US-2.1.1

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.1 - Docente da de alta una materia y su banco de preguntas
- **Puntos estimados:** 3
- **Tiempo real:** ~43 min (tracking de ejecución del agente, no comparable contra esfuerzo
  humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-02

Primera US de la Iteración 1 del Incremento 2 (BC Banco de Preguntas). Es la precondición de
toda la iteración: sin `Materia`/`Banco` no hay contra qué cargar una `PreguntaPlantilla`
(`US-2.1.3` a `US-2.1.7`). Incluyó un refactor previo no anticipado en la spec: extraer
JWT/RBAC de `src/identidad` a `src/shared` (`ADR-019`), necesario porque esta es la primera US
fuera de Identidad que exige un rol (`docente`) en su endpoint.

---

## Componentes Implementados

### Refactor previo (`ADR-019`) — JWT/RBAC de `identidad` a `shared`
- ✅ `src/shared/entities/tipo_perfil.py`, `jwt.py`, `errors.py` — `TipoPerfil`, `JWT`,
  `JWTPayload`, `JWTInvalido`, `JWTExpirado`
- ✅ `src/shared/entities/ports/jwt_issuer_port.py` — `JWTIssuerPort`
- ✅ `src/shared/frameworks/security/jwt_pyjwt.py` — `PyJWTIssuer`
- ✅ `src/shared/interface_adapters/security/get_current_user.py`, `require_rol.py` —
  `build_get_current_user`, `require_rol`
- ✅ `src/identidad/frameworks/dependencies.py` (editado) — reconstruye
  `require_administrador`/`require_docente` importando de `shared`, misma API pública

### Entities (`src/banco_preguntas/entities/`)
- ✅ `materia.py` — aggregate `Materia`, `nombre` único (INV-BP-00)
- ✅ `banco.py` — aggregate `Banco`, 1:1 con `Materia` (INV-BP-01)
- ✅ `eventos.py` — `MateriaCreada`, `BancoCreado`
- ✅ `errors.py` — `MateriaYaExiste`
- ✅ `ports/materia_repository_port.py`, `ports/banco_repository_port.py`

### Use Cases (`src/banco_preguntas/use_cases/`)
- ✅ `CrearMateriaUseCase` — valida INV-BP-00, crea `Materia` + `Banco` en la misma operación

### Interface Adapters (`src/banco_preguntas/interface_adapters/`)
- ✅ `controllers/materias_controller.py`
- ✅ `gateways/materia_repository.py`, `gateways/banco_repository.py` — `SQLAlchemy*Repository`

### Frameworks (`src/banco_preguntas/frameworks/`)
- ✅ `db/models.py` — `MateriaModel` (nombre unique), `BancoModel` (materia_id FK unique)
- ✅ `api/schemas.py` — `CrearMateriaRequest`, `MateriaResponse`
- ✅ `api/materias_router.py` — `POST /materias`
- ✅ `dependencies.py` — `get_materias_controller`, `require_docente` propio (compuesto desde
  `shared`, sin import cruzado a `identidad`)

### Migraciones
- ✅ `migrations/versions/099d86aa5d0d_materia_banco.py` — tablas `materia`, `banco`,
  generada con `alembic revision --autogenerate` y aplicada contra PostgreSQL local

### Integración
- ✅ `src/app.py` (editado) — `materias_router` registrado

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| POST | `/materias` | Crear materia y su banco asociado | ✅ `require_docente` |

**OpenAPI Docs:** `/docs`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.64/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 3 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 61.61 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% | ≥ 95.0% | ✅ |

Fuente: `quality/reports/inc2/US-2.1.1-quality.json`. Coverage medido sobre
`entities`/`use_cases`/`interface_adapters` de `banco_preguntas` (116/116 statements) —
`frameworks/` excluido del gate por convención del proyecto (`pyproject.toml`).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (5 tests) — `tests/unit/inc2/`
- `test_materia.py`, `test_banco.py` — aggregates (2 tests)
- `test_crear_materia_use_case.py` — use case con fakes de los ports (2 tests)
- `test_materias_controller.py` (1 test)

### Tests de Integración (8 tests) — `tests/integration/inc2/`
- `test_materia_repository_integration.py` (3 tests) — gateways SQLAlchemy contra Postgres
  local real
- `test_materias_api_integration.py` (5 tests) — endpoint FastAPI vía `httpx.AsyncClient`
  (happy path, nombre duplicado, nombre vacío, sin auth, rol insuficiente)

### Escenarios BDD (3 escenarios) — `tests/features/inc2/US-2.1.1-*.feature` + `tests/step_defs/inc2/`
- Docente crea una materia nueva
- Rechazo por nombre duplicado
- Rechazo por nombre vacío (agregado en Fase 1 — precondición de la spec no cubierta por el
  Gherkin original, aprobado por Víctor)

**Todos los tests pasando:** ✅ 148/148 (suite completa del proyecto, incluyendo Identidad
post-refactor)

---

## Migraciones de Base de Datos

- ✅ `migrations/versions/099d86aa5d0d_materia_banco.py`
  - Tabla `materia` (`nombre` único)
  - Tabla `banco` (`materia_id` FK a `materia.id`, único — INV-BP-01)
  - Aplicada contra PostgreSQL local (`alembic upgrade head`)

---

## Decisión Arquitectónica Resuelta con Víctor (antes de implementar)

**JWT/RBAC no existía fuera de `identidad`:** la spec exige rol `docente` en el endpoint, pero
`TipoPerfil`/`JWTIssuerPort`/`get_current_user`/`require_rol` vivían solo en `src/identidad`.
Importarlos directo hubiera violado la regla de `CLAUDE.md` de no-imports-entre-BC. Se evaluaron
3 opciones (import directo como deuda técnica, duplicar el guard por BC, mover a `shared`) y se
eligió moverlos a `shared` — mismo criterio que `ADR-017` (engine de SQLAlchemy). Documentado en
`ADR-019` y en `docs/plans/inc2/US-2.1.1-plan.md` §0.

---

## Archivos Creados/Modificados

**Producción (refactor):** `src/shared/entities/tipo_perfil.py`, `jwt.py`, `errors.py`,
`ports/jwt_issuer_port.py`, `src/shared/frameworks/security/jwt_pyjwt.py`,
`src/shared/interface_adapters/security/get_current_user.py`, `require_rol.py`,
`src/identidad/frameworks/dependencies.py` (editado), `entities/usuario.py` (editado),
`entities/eventos.py` (editado), `entities/errors.py` (editado),
`frameworks/api/schemas.py` (editado), `interface_adapters/controllers/auth_controller.py`
(editado), `usuarios_controller.py` (editado), `use_cases/crear_usuario.py` (editado),
`iniciar_sesion.py` (editado) — ~20 archivos de `identidad` con import actualizado, 5 archivos
originales eliminados (movidos).

**Producción (BC Banco de Preguntas):** `src/banco_preguntas/entities/materia.py`, `banco.py`,
`eventos.py`, `errors.py`, `ports/materia_repository_port.py`, `ports/banco_repository_port.py`,
`use_cases/crear_materia.py`, `interface_adapters/controllers/materias_controller.py`,
`interface_adapters/gateways/materia_repository.py`, `banco_repository.py`,
`frameworks/db/models.py`, `frameworks/api/schemas.py`, `materias_router.py`,
`frameworks/dependencies.py`, `src/app.py` (editado),
`migrations/versions/099d86aa5d0d_materia_banco.py`, `migrations/env.py` (editado) — ~250 líneas.

**Tests:** `tests/unit/inc2/test_materia.py`, `test_banco.py`,
`test_crear_materia_use_case.py`, `test_materias_controller.py`, `_fakes.py`,
`tests/integration/inc2/conftest.py`, `test_materia_repository_integration.py`,
`test_materias_api_integration.py`, `tests/step_defs/inc2/test_us_2_1_1_steps.py`,
`_auth_headers.py`, `tests/features/inc2/US-2.1.1-alta-materia-banco.feature` — ~350 líneas.
Más ~20 archivos de tests de `identidad` con import actualizado (sin cambio de lógica).

**Configuración:** `pyproject.toml` (editado — markers `US-2.1.1`/`crear-materia`).

**Documentación:** `docs/plans/inc2/US-2.1.1-{context,plan}.md`,
`docs/reports/inc2/US-2.1.1-report.md` (este archivo),
`quality/reports/inc2/US-2.1.1-{quality,pylint,cc,mi,coverage}.json`,
`docs/adr/ADR-019-jwt-rbac-en-shared.md`, `CLAUDE.md` (editado), `CHANGELOG.md` (editado).

---

## Criterios de Aceptación

- [x] Docente crea una materia nueva — `Materia` persistida, `Banco` creado automáticamente,
  eventos `MateriaCreada`/`BancoCreado` emitidos
- [x] Rechazo por nombre duplicado — `MateriaYaExiste`, ninguna `Materia` ni `Banco` nuevos
- [x] Rechazo por nombre vacío — 422, ninguna `Materia` ni `Banco` nuevos

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.1.2` — `Comisión.materia` (BC Identidad) referencia `Materia` por puerto en vez de
  `string` libre (técnica, puede ir en paralelo)
- [ ] `US-2.1.3`/`US-2.1.4` — carga de preguntas de opción múltiple y verdadero/falso
  (dependen de `Banco`)
- [ ] RF-04 permanece "Especificado" en `docs/traceability/matrix.md` hasta que también estén
  implementadas `US-2.1.3`, `US-2.1.4` (backend) y `US-2.1.8`, `US-2.1.9`, `US-2.1.11`
  (frontend)

---

## Lecciones Aprendidas

- ⚠️ La spec no anticipaba que el guard de rol (`require_docente`) no existía fuera de
  `identidad` — surgió como ambigüedad de diseño genuina en Fase 2, resuelta con Víctor antes
  de tocar código. Toda US que sea la "primera" en cruzar un concern transversal entre BCs debe
  revisar si ese concern ya está en `shared/` antes de plantear el plan.
- ✅ Tener `ADR-017` como precedente directo (mismo patrón: mover infraestructura transversal a
  `shared/frameworks/`) aceleró la decisión — se aplicó el mismo criterio sin abrir un debate
  de diseño desde cero.
- 💡 Migración Alembic generada con `--autogenerate` en vez de escrita a mano evitó errores de
  transcripción del modelo ORM a SQL.
- 💡 Correr la suite completa de Identidad como baseline antes y después del refactor (no solo
  los tests del BC nuevo) fue lo que dio confianza real de que mover JWT/RBAC no rompió nada.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-02
