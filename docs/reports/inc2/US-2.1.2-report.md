# Reporte de Implementación: US-2.1.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.2 - Comisión referencia Materia por puerto (refactor técnico)
- **Puntos estimados:** 3
- **Tiempo real:** ~1h 34min (Fases 0–7, tracking de ejecución del agente — no comparable
  contra esfuerzo humano, nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-05

Segunda US de la Iteración 1 del Incremento 2 (BC Banco de Preguntas), pero de refactor técnico
sobre BC Identidad. Cierra el "hot spot" dejado abierto en la Iteración 0 (event storming,
`BC-banco-preguntas-modelo.md` §4): `Comisión.materia` deja de ser un `string` libre y pasa a
referenciar la `Materia` dueña de Banco de Preguntas por un puerto de dominio, sin imports
directos entre BCs. Amplió su alcance en Fase 2 más allá de lo descripto en la spec original:
`RegistrarEstudianteUseCase` también dependía de `Comision.materia` (para
`RegistroResponse.materia`, user-facing), no solo `CrearComisionUseCase`.

---

## Componentes Implementados

### Banco de Preguntas — lectura de `Materia` por id (nuevo, solo lectura)
- ✅ `src/banco_preguntas/entities/ports/materia_repository_port.py` (editado) —
  `obtener_por_id(materia_id) -> Materia | None`
- ✅ `src/banco_preguntas/interface_adapters/gateways/materia_repository.py` (editado) —
  implementación en `SQLAlchemyMateriaRepository`
- ✅ `src/banco_preguntas/use_cases/obtener_materia.py` — `ObtenerMateriaUseCase`, invocado
  in-process por el adaptador de Identidad

### Identidad — entities
- ✅ `src/identidad/entities/comision.py` (editado) — `Comision.materia: str` →
  `Comision.materia_id: UUID`
- ✅ `src/identidad/entities/ports/materia_port.py` — `MateriaDTO`, `MateriaPort` (ABC)
- ✅ `src/identidad/entities/errors.py` (editado) — `MateriaNoExiste`
- ✅ `src/identidad/entities/eventos.py` (editado) — `ComisionCreada.materia: str` →
  `materia_id: UUID`

### Identidad — use_cases
- ✅ `src/identidad/use_cases/crear_comision.py` (editado) — valida `materia_id` contra
  `MateriaPort`, `MateriaNoExiste` si no resuelve
- ✅ `src/identidad/use_cases/registrar_estudiante.py` (editado) — ya no depende de
  `MateriaPort` ni de `ComisionRepositoryPort`; devuelve `(Usuario, InvitacionAceptada,
  UsuarioRegistrado)`. La resolución del nombre de materia para `RegistroResponse.materia`
  se movió a `RegistroController` (ver "Fix de CBOAnalyzer post quality-gate" más abajo)

### Identidad — interface_adapters
- ✅ `src/identidad/interface_adapters/gateways/comision_repository.py` (editado) — mapea
  `materia_id`
- ✅ `src/identidad/interface_adapters/controllers/comisiones_controller.py` (editado) —
  `crear_comision(materia_id, ...)`
- ✅ `src/identidad/interface_adapters/controllers/registro_controller.py` (editado) — recibe
  `ComisionRepositoryPort` y `MateriaPort`; tras invocar `RegistrarEstudianteUseCase`, resuelve
  comisión → `materia_id` → nombre para `RegistroResponse.materia` (movido acá desde el use
  case, ver "Fix de CBOAnalyzer post quality-gate")

### Identidad — frameworks
- ✅ `src/identidad/frameworks/db/models.py` (editado) — `ComisionModel.materia_id: UUID`
  (columna simple, sin `ForeignKeyConstraint` entre esquemas de BCs)
- ✅ `src/identidad/frameworks/adapters/materia_port_in_process.py` — `MateriaPortInProcess`,
  único punto de Identidad que importa `src.banco_preguntas` (mismo criterio que `ADR-006`)
- ✅ `src/identidad/frameworks/api/schemas.py` (editado) — `CrearComisionRequest.materia_id`,
  `ComisionResponse.materia_id`
- ✅ `src/identidad/frameworks/api/comisiones_router.py` (editado) — 422 con `MateriaNoExiste`
- ✅ `src/identidad/frameworks/dependencies.py` (editado) — wiring de `MateriaPortInProcess`

### Migraciones
- ✅ `migrations/versions/295bc74948c3_comision_materia_id.py` — agrega `materia_id`, backfill
  por nombre (`UPDATE ... FROM materia WHERE comision.materia = materia.nombre`), `NOT NULL`,
  elimina `materia`. Verificada con round-trip real (`upgrade head` → `downgrade -1` →
  `upgrade head`) contra PostgreSQL local.

---

## API Endpoints (modificados)

| Método | Ruta | Cambio | Auth |
|--------|------|--------|------|
| POST | `/comisiones` | `materia: str` → `materia_id: UUID`; 422 si `MateriaNoExiste` | ✅ `require_administrador` |

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.81/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 6 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 53.5 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% | ≥ 95.0% | ✅ |

Fuente: `quality/reports/inc2/US-2.1.2-quality.json`. Coverage medido sobre
`entities`/`use_cases`/`interface_adapters` de ambos BCs afectados (257/257 statements) —
`frameworks/` excluido del gate por convención del proyecto (`pyproject.toml`); el adaptador
`MateriaPortInProcess` y `ComisionModel` se validan vía tests de integración. mypy sobre
`src/` completo: sin issues.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (6 nuevos + 8 actualizados) — `tests/unit/`
- `test_obtener_materia_use_case.py` (2 tests, nuevo)
- `_fakes.py` (inc1: `FakeMateriaPort`; inc2: `FakeMateriaRepository.obtener_por_id`)
- `test_comision.py`, `test_crear_comision_use_case.py` (+ caso `MateriaNoExiste`),
  `test_comisiones_controller.py`, `test_registrar_estudiante_use_case.py`,
  `test_registro_controller.py`, `test_asignar_docente_a_comision_use_case.py`,
  `test_generar_invitacion_use_case.py`, `test_invitaciones_controller.py` — actualizados para
  `materia_id: UUID`

### Tests de Integración (1 nuevo + 7 actualizados) — `tests/integration/`
- `test_materia_port_in_process_integration.py` (2 tests, nuevo) — adaptador contra Postgres
  local real
- `test_comision_repository_integration.py`, `test_comisiones_api_integration.py` (+ caso 422
  materia inexistente), `test_invitaciones_api_integration.py`, `test_registro_api_integration.py`,
  `test_auth_api_integration.py`, `test_invitacion_repository_integration.py`,
  `test_usuario_repository_integration.py` — actualizados

### Escenarios BDD (4 nuevos) — `tests/features/inc2/US-2.1.2-*.feature` + `tests/step_defs/inc2/`
- Migración de datos existentes (reproduce el backfill de la migración sobre datos
  "pre-US-2.1.2" con una columna temporal)
- Alta de comisión con `materia_id` válido
- Alta de comisión valida la materia por el puerto (rechazo `MateriaNoExiste`)
- Sin imports directos entre BCs (chequeo estático vía AST sobre `src/identidad/`)

### Regresión de step_defs preexistentes (5 archivos actualizados) — `tests/step_defs/inc1/`
- `test_us_1_1_0_steps.py`, `test_us_1_1_1_steps.py`, `test_us_1_1_2_steps.py`,
  `test_us_1_1_3_steps.py`, `test_us_1_1_4_steps.py` — usaban `POST /comisiones` con
  `"materia"` string; ahora crean una `Materia` real vía `POST /materias` antes de crear la
  comisión (o usan un `materia_id` arbitrario cuando la creación es directa por repositorio,
  sin pasar por la validación del puerto)

**Todos los tests pasando:** ✅ 158/158 (suite completa del proyecto)

---

## Migraciones de Base de Datos

- ✅ `migrations/versions/295bc74948c3_comision_materia_id.py`
  - Agrega `comision.materia_id UUID` (nullable), backfill por nombre, `NOT NULL`, elimina
    `comision.materia`
  - Sin `ForeignKeyConstraint` entre `comision.materia_id` y `materia.id` (decisión explícita
    de la spec — no FK de base entre esquemas de BCs)
  - Verificada con round-trip real contra PostgreSQL local (`upgrade head` → `downgrade -1` →
    `upgrade head`)

---

## Decisión de Alcance Resuelta en Fase 2 (antes de implementar)

**`RegistrarEstudianteUseCase` no estaba en el alcance original de la spec:** la spec de
`US-2.1.2` solo mencionaba `CrearComisionUseCase` como consumidor de `MateriaPort`. Al planificar
se detectó que `RegistrarEstudianteUseCase` (`src/identidad/use_cases/registrar_estudiante.py`)
también devolvía `comision.materia` (string) para poblar `RegistroResponse.materia` — el nombre
de materia que ve el Estudiante al registrarse. Se amplió el plan para inyectar `MateriaPort`
también ahí, resolviendo el nombre en vez de romper el contrato existente. Documentado en
`docs/plans/inc2/US-2.1.2-plan.md`.

---

## Fix de CBOAnalyzer post Quality Gates (detectado en `/pr`, antes del merge)

El plan de Fase 2 no corrió `DesignReviewer` explícitamente (los Quality Gates de Fase 7 cubren
pylint/CC/MI/coverage, no acoplamiento — ver tabla de métricas). Al ejecutar `git push` en la
Fase de PR, el hook `.githooks/pre-push` bloqueó con 1 CRITICAL: inyectar `MateriaPort` en
`RegistrarEstudianteUseCase` (para resolver `comision.materia_id` → nombre, decisión de la
sección anterior) llevó su `CBOAnalyzer` a CBO=11 (umbral `max_cbo=10` de `pyproject.toml`) —
la clase ya estaba exactamente en el umbral antes de esta US.

**Fix aplicado:** la resolución de nombre de materia es un detalle de presentación de
`RegistroResponse`, no de la regla de negocio "registrar un Estudiante que acepta una
invitación". Se movió esa responsabilidad a `RegistroController`:
- `RegistrarEstudianteUseCase.execute` deja de depender de `ComisionRepositoryPort` y
  `MateriaPort` — su firma de retorno pasa de `tuple[Usuario, str, InvitacionAceptada,
  UsuarioRegistrado]` a `tuple[Usuario, InvitacionAceptada, UsuarioRegistrado]` (sin campo de
  materia). CBO vuelve a 10, dentro del umbral.
- `RegistroController` ahora recibe `ComisionRepositoryPort` y `MateriaPort` además del use
  case; tras invocar `execute`, resuelve `comision_id` (del evento `InvitacionAceptada`) →
  `materia_id` → nombre, y arma la tupla de 4 elementos que espera `registro_router.py` (sin
  cambios en el endpoint ni en `RegistroResponse`).

Verificado con mypy (sin issues), suite completa (158/158) y `DesignReviewer --config
pyproject.toml` (0 CRITICAL, 28 advertencias — deuda técnica preexistente no introducida por
esta US) antes de pushear. Documentado también en la descripción del PR #62.

---

## Archivos Creados/Modificados

**Producción (nuevo):** `src/banco_preguntas/use_cases/obtener_materia.py`,
`src/identidad/entities/ports/materia_port.py`,
`src/identidad/frameworks/adapters/__init__.py`,
`src/identidad/frameworks/adapters/materia_port_in_process.py`,
`migrations/versions/295bc74948c3_comision_materia_id.py`.

**Producción (editado):** `src/banco_preguntas/entities/ports/materia_repository_port.py`,
`interface_adapters/gateways/materia_repository.py`, `src/identidad/entities/comision.py`,
`errors.py`, `eventos.py`, `use_cases/crear_comision.py`, `registrar_estudiante.py`,
`interface_adapters/gateways/comision_repository.py`,
`interface_adapters/controllers/comisiones_controller.py`,
`interface_adapters/controllers/registro_controller.py`, `frameworks/db/models.py`,
`frameworks/api/schemas.py`, `frameworks/api/comisiones_router.py`, `frameworks/dependencies.py`.

**Tests (nuevos):** `tests/unit/inc2/test_obtener_materia_use_case.py`,
`tests/integration/inc1/test_materia_port_in_process_integration.py`,
`tests/features/inc2/US-2.1.2-comision-materia-port.feature`,
`tests/step_defs/inc2/test_us_2_1_2_steps.py`.

**Tests (editados):** `tests/unit/inc1/_fakes.py`, `test_comision.py`,
`test_crear_comision_use_case.py`, `test_comisiones_controller.py`,
`test_registrar_estudiante_use_case.py`, `test_registro_controller.py`,
`test_asignar_docente_a_comision_use_case.py`, `test_generar_invitacion_use_case.py`,
`test_invitaciones_controller.py`, `tests/unit/inc2/_fakes.py`,
`tests/integration/inc1/test_comision_repository_integration.py`,
`test_comisiones_api_integration.py`, `test_invitaciones_api_integration.py`,
`test_registro_api_integration.py`, `test_auth_api_integration.py`,
`test_invitacion_repository_integration.py`, `test_usuario_repository_integration.py`,
`tests/step_defs/inc1/test_us_1_1_0_steps.py` a `test_us_1_1_4_steps.py`.

**Documentación:** `docs/plans/inc2/US-2.1.2-{context,plan}.md`,
`docs/reports/inc2/US-2.1.2-report.md` (este archivo),
`quality/reports/inc2/US-2.1.2-{quality,pylint,cc,mi,coverage}.json`,
`docs/architecture/20-context-map-integrations.md` (editado — nueva relación Identidad → Banco
de Preguntas), `docs/design/domain/BC-banco-preguntas-modelo.md` (editado — hot spot resuelto),
`CHANGELOG.md` (editado).

---

## Criterios de Aceptación

- [x] Migración de datos existentes — Comisión con `materia` string queda con `materia_id`
  apuntando a la `Materia` correspondiente por nombre
- [x] Alta de comisión valida la materia por el puerto — `CrearComision` rechaza con
  `MateriaNoExiste` si `materia_id` no resuelve
- [x] Sin imports directos entre BCs — `src/identidad/` no importa ningún módulo de
  `src/banco_preguntas/` fuera de `MateriaPortInProcess` (`frameworks/adapters/`)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-2.1.3`/`US-2.1.4` — carga de preguntas de opción múltiple y verdadero/falso (dependen
  de `Banco`, no de esta US)
- [ ] RF-04/RF-05/RF-06 permanecen "Especificado" en `docs/traceability/matrix.md` hasta el
  cierre de la Iteración 1 completa (backend + frontend) y su UAT

---

## Lecciones Aprendidas

- ⚠️ El alcance real fue mayor al descripto en la spec: `RegistrarEstudianteUseCase` también
  dependía de `Comision.materia` (para `RegistroResponse.materia`, user-facing). Detectado en
  Fase 2 (planning) antes de escribir código — evitó una regresión no cubierta en la spec
  original. Toda US de refactor sobre un campo de una Entity debe grepear todos los consumidores
  del campo, no solo los mencionados en la spec.
- ⚠️ El blast radius de tests fue mayor al anticipado: 5 archivos de step_defs de Identidad
  preexistentes (`US-1.1.0` a `US-1.1.4`) usaban `POST /comisiones` con `"materia"` string y
  necesitaron crear una `Materia` real primero. Ninguno estaba listado en la spec de `US-2.1.2`
  por pertenecer a otra US — encontrados recién al correr la suite completa en Fase 6, no por
  grep previo dirigido solo a los archivos "obvios".
- ✅ La ausencia de `ForeignKeyConstraint` entre `comision.materia_id` y `materia.id` (decisión
  explícita de la spec, "sin FK de base entre BCs") simplificó los tests de repositorio: no fue
  necesario crear una `Materia` real para testear `SQLAlchemyComisionRepository` de forma
  aislada, solo para los flujos que pasan por `CrearComisionUseCase` (que sí valida contra
  `MateriaPort`).
- 💡 Verificar la migración con un round-trip real (`upgrade head` → `downgrade -1` →
  `upgrade head`) contra Postgres local, antes de escribir el resto del código que depende de
  la columna, detectó temprano que el backfill SQL era sintácticamente correcto.
- 💡 Reutilizar `alembic revision --autogenerate` para el diff de esquema (igual que en
  `US-2.1.1`) y completar a mano solo el backfill de datos evitó errores de transcripción.
- ⚠️ El plan de Fase 2 no anticipó el impacto en acoplamiento (CBO) de inyectar un puerto
  nuevo en una clase ya cercana al umbral — los Quality Gates de Fase 7 miden pylint/CC/MI/
  coverage pero no corren `DesignReviewer` explícitamente; recién el hook de `pre-push` lo
  detectó, ya en la fase de PR. Toda US que agregue una dependencia a un use case debería
  correr `DesignReviewer --config pyproject.toml` en la Fase de Quality Gates, no solo confiar
  en el pre-push como red de seguridad tardía.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-05
