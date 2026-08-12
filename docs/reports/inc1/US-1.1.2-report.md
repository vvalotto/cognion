# Reporte de Implementación: US-1.1.2

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.2 - Estudiante se registra con un link de invitación válido
- **Puntos estimados:** 5
- **Tiempo real:** ~28 min (fases 0-7, tracking de ejecución del agente, no comparable
  contra esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO (backend) — frontend diferido a una US-IEDD separada
- **Fecha completado:** 2026-07-23

Tercera US de la Iteración 1 (BC Identidad). Con `US-1.1.1` resuelta (generación de
invitación), esta US cierra el flujo de punta a punta de RF-01: un Estudiante que recibe una
invitación vigente completa su registro y queda asignado automáticamente a la comisión del
Docente que lo invitó, sin aprobación adicional. Habilita `US-1.1.3` (rechazo por link
vencido/inválido), que comparte el mismo comando y use case.

---

## Componentes Implementados

### Entities (`src/identidad/entities/`)
- ✅ `usuario.py` (editado) — `Estudiante` gana `comision_id: UUID` (INV-ID-05: nunca existe
  sin comisión); nueva factory `Usuario.crear_estudiante()` — único camino de construcción
  de un `Estudiante`; `Usuario.crear()` genérico ya no admite `TipoPerfil.ESTUDIANTE`
- ✅ `invitacion.py` (editado) — `Invitacion.es_vigente()` (INV-ID-01, INV-ID-03),
  `Invitacion.aceptar()` (marca `usada_en`, valida vigencia primero)
- ✅ `errors.py` (editado) — `InvitacionNoValida` (guard genérico de esta US; `US-1.1.3` lo
  refina en `InvitacionInvalida`/`InvitacionVencida`/`InvitacionYaUsada`, fuera de alcance
  aquí)
- ✅ `eventos.py` (editado) — `InvitacionAceptada`, `UsuarioRegistrado`
- ✅ `ports/invitacion_repository_port.py` (editado) — `obtener_por_token()`, `actualizar()`

### Use Cases (`src/identidad/use_cases/`)
- ✅ `RegistrarEstudianteUseCase` — valida invitación vigente, valida email libre (INV-ID-04),
  hashea password (bcrypt, `ADR-014`), crea Usuario+Estudiante y consume la invitación en la
  misma operación; ninguna invitación se marca usada si el registro se rechaza

### Interface Adapters (`src/identidad/interface_adapters/`)
- ✅ `controllers/registro_controller.py`
- ✅ `gateways/invitacion_repository.py` (editado) — `obtener_por_token()`, `actualizar()`
- ✅ `gateways/usuario_repository.py` (editado) — persiste/reconstruye `comision_id` del
  perfil `Estudiante`

### Frameworks (`src/identidad/frameworks/`)
- ✅ `db/models.py` (editado) — `EstudianteModel.comision_id` (FK a `comision.id`)
- ✅ `api/schemas.py` (editado) — `RegistrarEstudianteRequest`, `RegistroResponse`
- ✅ `api/registro_router.py` — `POST /identidad/registro` (público, sin guard JWT)
- ✅ `dependencies.py` (editado) — `get_registro_controller()`

### Migraciones
- ✅ `migrations/versions/dd44a181d7fc_estudiante_comision_id.py` — columna `comision_id` en
  `estudiante`, aplicada contra Postgres local

### Integración
- ✅ `src/app.py` (editado) — `registro_router` registrado

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| POST | `/identidad/registro` | Registrar Estudiante vía invitación | Público — sin JWT (Estudiante aún no autenticado al registrarse) |

**Respuestas:** `201` (creado), `409` (`EmailYaRegistrado`), `422` (`InvitacionNoValida`)

**OpenAPI Docs:** `/docs`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.91/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 4 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 57.51 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% | ≥ 95.0% | ✅ |
| DesignReviewer | 0 CRITICAL | 0 requerido | ✅ |

Fuente: `quality/reports/inc1/US-1.1.2-quality.json`. Coverage medido sobre
`entities`/`use_cases`/`interface_adapters` de todo el BC Identidad (445/445 statements,
incluye US anteriores) — `frameworks/` excluido del gate por convención del proyecto.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (10 tests nuevos) — `tests/unit/inc1/`
- `test_usuario.py` (editado) — `Usuario.crear_estudiante`, rechazo de `Usuario.crear()`
  genérico para `ESTUDIANTE`
- `test_invitacion.py` (editado) — `es_vigente()`/`aceptar()` (6 tests nuevos)
- `test_registrar_estudiante_use_case.py` — use case con fakes de los ports (6 tests)
- `test_registro_controller.py` (1 test)
- `test_asignar_docente_a_comision_use_case.py` (editado) — fixture migrado a
  `Usuario.crear_estudiante`

### Tests de Integración (3 tests nuevos) — `tests/integration/inc1/`
- `test_invitacion_repository_integration.py` (editado) — `obtener_por_token()`,
  `actualizar()` contra Postgres local real
- `test_usuario_repository_integration.py` (editado) — persistencia de `Estudiante` con
  `comision_id`
- `test_registro_api_integration.py` — endpoint FastAPI vía `httpx.AsyncClient` (4 tests:
  éxito, email duplicado, invitación vencida, token inexistente)

### Escenarios BDD (2 escenarios) — `tests/features/inc1/US-1.1.2-*.feature` + `tests/step_defs/inc1/`
- Registro exitoso con invitación vigente
- Rechazo por email ya registrado

**Todos los tests pasando:** ✅ 77/77 (suite completa del proyecto)

---

## Migraciones de Base de Datos

- ✅ `migrations/versions/dd44a181d7fc_estudiante_comision_id.py`
  - Columna `comision_id` en `estudiante` (FK a `comision.id`, `nullable=False`)
  - Aplicada contra PostgreSQL local (`alembic upgrade head`)

---

## Ajustes de Alcance Resueltos con Víctor (antes del plan)

1. **Sin JWT/guard todavía:** mismo criterio que `US-1.1.1` — el endpoint es público porque
   el Estudiante no tiene sesión al momento de registrarse. Confirmado antes de generar el
   plan.
2. **Frontend diferido:** al revisar `frontend/src` se encontró que es todavía el scaffold
   default de Vite — sin React Router, sin cliente HTTP, sin páginas propias. Implementar
   `Registro.tsx`/`RegistroExito.tsx` "completos" hubiera requerido decidir routing y
   cliente API dentro de esta HU, una decisión de infraestructura no planificada. Se acordó
   cerrar esta US con backend completo y mover el frontend a una US-IEDD separada, una vez
   decidida esa infraestructura base.

---

## Efecto Colateral Controlado — Fixtures de US Anteriores

Restringir `Usuario.crear()` genérico para que rechace `TipoPerfil.ESTUDIANTE` (justificado
por INV-ID-05: un `Estudiante` nunca existe sin `comision_id`) rompió dos fixtures de tests
de US anteriores que usaban ese camino genérico solo para obtener "un usuario que no es
Docente":

- `tests/unit/inc1/test_asignar_docente_a_comision_use_case.py` — migrado a
  `Usuario.crear_estudiante()`.
- `tests/step_defs/inc1/test_us_1_1_0_steps.py` (escenario "usuario que no es Docente") — el
  fixture creaba el Estudiante vía el endpoint genérico `POST /usuarios`, ahora imposible sin
  `comision_id`. Se resolvió creando el `Estudiante` directo por repositorio dentro del
  fixture, sin modificar el lenguaje del escenario Gherkin de `US-1.1.0`.

También se corrigió el orden de `DELETE FROM` en la limpieza de tablas de tests de
integración/BDD (`tests/integration/conftest.py`, `test_us_1_1_0_steps.py`,
`test_us_1_1_1_steps.py`) — no consideraba la nueva FK `estudiante.comision_id`.

---

## Archivos Creados/Modificados

**Producción:** `src/identidad/entities/usuario.py` (editado), `entities/invitacion.py`
(editado), `entities/errors.py` (editado), `entities/eventos.py` (editado),
`entities/ports/invitacion_repository_port.py` (editado), `use_cases/registrar_estudiante.py`,
`interface_adapters/controllers/registro_controller.py`,
`interface_adapters/gateways/invitacion_repository.py` (editado),
`interface_adapters/gateways/usuario_repository.py` (editado), `frameworks/db/models.py`
(editado), `frameworks/api/schemas.py` (editado), `frameworks/api/registro_router.py`,
`frameworks/dependencies.py` (editado), `src/app.py` (editado),
`migrations/versions/dd44a181d7fc_estudiante_comision_id.py` — ~230 líneas.

**Tests:** `tests/unit/inc1/test_usuario.py` (editado), `test_invitacion.py` (editado),
`test_registrar_estudiante_use_case.py`, `test_registro_controller.py`,
`test_asignar_docente_a_comision_use_case.py` (editado), `_fakes.py` (editado),
`tests/integration/inc1/test_invitacion_repository_integration.py` (editado),
`test_usuario_repository_integration.py` (editado), `test_registro_api_integration.py`,
`tests/integration/conftest.py` (editado), `tests/step_defs/inc1/test_us_1_1_2_steps.py`,
`test_us_1_1_0_steps.py` (editado), `test_us_1_1_1_steps.py` (editado),
`tests/features/inc1/US-1.1.2-registro-estudiante.feature` — ~560 líneas.

**Documentación:** `docs/plans/inc1/US-1.1.2-{context,plan}.md`,
`docs/reports/inc1/US-1.1.2-report.md` (este archivo),
`quality/reports/inc1/US-1.1.2-{quality,pylint,cc,mi,coverage}.json`,
`docs/traceability/matrix.md` (editado), `CHANGELOG.md` (editado).

---

## Criterios de Aceptación

- [x] Registro exitoso con invitación vigente — Usuario+Estudiante creados en la misma
  transacción, `comision_id` asignado, invitación marcada usada, eventos
  `InvitacionAceptada`/`UsuarioRegistrado`, sin autenticación automática
- [x] Rechazo por email ya registrado — `EmailYaRegistrado`, invitación no se consume

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] `US-1.1.3` — Estudiante intenta registrarse con link vencido o inválido (refina
  `InvitacionNoValida` en las tres excepciones específicas del `RegistrarEstudianteUseCase`)
- [ ] US-IEDD de infraestructura frontend (router + cliente API) + `Registro.tsx`/
  `RegistroExito.tsx`, diferida de esta US
- [ ] `US-1.1.5` — agregar guard de rol al endpoint de esta US si corresponde (hoy público
  por diseño, no por pendiente de implementar)
- [ ] RF-01 permanece "Especificado" en `docs/traceability/matrix.md` hasta que también esté
  implementada `US-1.1.3`

---

## Lecciones Aprendidas

- ⚠️ Una restricción de invariante en una entidad compartida (`Usuario.crear()`) puede
  romper fixtures de tests de US ya cerradas que dependían del comportamiento genérico
  anterior — conviene `grep` los usos existentes de la entidad antes de cambiar su contrato,
  no solo los archivos que la spec actual lista como "a modificar".
- ⚠️ Agregar una FK nueva a una tabla existente (`estudiante.comision_id`) requiere revisar
  el orden de limpieza (`DELETE FROM`) en **todos** los conftest/step_defs que tocan esas
  tablas, no solo en el nuevo — el error solo aparece al ejecutar la suite completa.
- 💡 Reconocer a tiempo que el frontend no tenía infraestructura base (antes de escribir
  código) evitó tomar una decisión de arquitectura (routing, cliente API) de forma implícita
  dentro de una US que no la pedía explícitamente.
- 💡 Mantener el mismo criterio de alcance ya validado en `US-1.1.1` (endpoint público sin
  JWT) evitó reabrir una decisión ya tomada.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-23
