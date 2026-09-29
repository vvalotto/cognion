# Plan de Implementación: US-ADJ-57 - Cada Docente ve y opera solo sobre las materias de sus Comisiones

**Patrón:** Clean Architecture BC-first (entities → use_cases → interface_adapters → frameworks)
**Producto:** cognion — cruza 4 BC: Identidad (fuente de verdad), Banco de Preguntas, Actividad
Evaluativa, Analytics

## Mapa de la brecha actual (exploración de código, Fase 2)

Ningún endpoint filtra hoy por la asignación Docente↔Comisión — el sistema nació con "Docente
único". Detalle completo por BC:

### Identidad (dueña de `Comision.docentes_asignados`)
- `GET /materias/{materia_id}/comisiones` (`materias_comisiones_router.py`) — devuelve **todas**
  las comisiones de la materia, sin filtrar por el Docente que llama.
- `GET /comisiones/{comision_id}` y `GET /comisiones/{comision_id}/estudiantes`
  (`comisiones_router.py`) — cualquier Docente puede pedir el detalle/roster de cualquier
  Comisión.
- `POST /comisiones/{comision_id}/invitaciones` (`invitaciones_router.py`) — valida que
  `body.docente_id` (el invitado) esté asignado, pero no que el **Docente que llama** lo esté.
- `ComisionQueryPort`/`SQLAlchemyComisionQueryRepository` ya tiene `tiene_comisiones_asignadas`
  (bool, cualquier comisión) pero **no** un método para verificar pertenencia a una comisión o
  materia puntual — necesario para que los otros 3 BC lo consuman.

### Banco de Preguntas
- `GET /materias` (`ListarMateriasUseCase`) — sin `docente_id`, lista todo.
- `POST /preguntas/opcion-multiple`, `POST /preguntas/verdadero-falso`, `PUT /preguntas/{id}`,
  `DELETE /preguntas/{id}`, `GET /bancos/{id}/preguntas` — ninguno verifica que el Docente esté
  asignado a la materia del banco.
- `ComisionConsultaPort` propio: un solo método (`tiene_comisiones`, uso interno de
  `EliminarMateriaUseCase`), y su adapter consulta `ComisionModel` de Identidad **directo**
  (no vía el gateway de Identidad, a diferencia de los otros dos BC) — se corrige de paso.

### Actividad Evaluativa
- Actividades de período abierto (`GET /actividades`, `GET /actividades/{id}`,
  `POST /actividades`, `PATCH .../periodo`, `PATCH .../titulo`, `POST .../cerrar`) — ninguna
  verifica materia del Docente; `POST /actividades` además acepta `comisiones_ids` sin validar
  que sean comisiones del Docente.
- Sesiones en vivo (`crear`, `iniciar`, `cancelar`, `mostrar-opciones`, `cerrar-pregunta`,
  `avanzar`, `finalizar`, `participantes`) — ninguna verifica que la Comisión sea del Docente
  que llama (`ComisionNoAutorizada` ya existe como error de dominio, sin uso todavía).
- `ComisionConsultaPort` propio: un solo método (`obtener_materia_id`), sin verificación de
  pertenencia de Docente.

### Analytics
- Los 6 endpoints de reportes (desempeño por estudiante/comisión, tasa de error, evolución
  temporal ×2, ranking de preguntas falladas, completitud) — ninguno inyecta siquiera al
  usuario autenticado (`get_current_user`) más allá del rol; el propio código documenta el gap
  como "hot spot de autorización" ya aceptado, que esta US cierra.
- `ComisionConsultaPort` propio: solo lectura de comisiones/estudiantes, sin verificación de
  pertenencia.

## Diseño acordado

**Primitiva única en Identidad** (`ComisionQueryPort` + `SQLAlchemyComisionQueryRepository`,
usa la tabla de asociación `comision_docentes` ya existente):
- `docente_pertenece_a_comision(docente_id, comision_id) -> bool`
- `docente_tiene_comision_en_materia(docente_id, materia_id) -> bool`

**Cada BC consumidor** amplía su propio `ComisionConsultaPort` con exactamente los métodos que
necesita (copia propia con DTOs propios, mismo criterio ya usado en el proyecto — nunca import
directo entre BCs), delegando en un adapter in-process a las 2 primitivas de arriba:
- Banco de Preguntas: `esta_asignado_a_materia` (el banco se gatea a nivel materia, no por
  comisión — una pregunta no pertenece a una comisión).
- Actividad Evaluativa: `esta_asignado_a_materia` (actividades de período abierto) +
  `esta_asignado_a_comision` (sesiones en vivo, y validar cada id de `comisiones_ids` al crear
  una actividad restringida).
- Analytics: `esta_asignado_a_materia` + `esta_asignado_a_comision` (reportes por comisión).

**Identidad, sus propios endpoints:** no necesitan las 2 primitivas nuevas — ya tienen la
`Comision` completa con `docentes_asignados` cargado; alcanza con inyectar el usuario
autenticado y filtrar/rechazar con ese campo ya disponible.

**Error de dominio → 403:** cada BC define su propio error (ej.
`MateriaNoAutorizada`/`ComisionNoAutorizada`, ya existe en Actividad Evaluativa) mapeado a 403
en el router — decisión ya tomada por Víctor en la spec (403, no 404).

**Administrador:** ningún endpoint tocado le agrega una verificación — sigue viendo/operando
todo (los guards que ya admiten `require_docente_o_administrador` separan la rama por rol; los
que son `require_docente` puro no lo afectan).

## Entrega (decisión de Víctor, Fase 2)

4 PRs secuenciales, mismo Issue #443 y misma US-ADJ-57, cada uno mergeado a `develop` antes de
arrancar el siguiente: **Identidad → Banco de Preguntas → Actividad Evaluativa → Analytics**.
Cada PR incluye su propio ciclo de tests (unitarios + integración + BDD del subconjunto que le
toca) y su propio quality gate. El `.feature` completo de Fase 1 (9 escenarios, cruza los 4 BC)
se valida entero recién al final, con los 4 PRs ya mergeados.

## Componentes a Implementar

### 1. Identidad — primitiva de pertenencia (base de todo lo demás)
- [x] `src/identidad/entities/ports/comision_query_port.py` — 2 métodos abstractos nuevos
- [x] `src/identidad/interface_adapters/gateways/comision_query_repository.py` — implementación
  vía `comision_docentes` (join, sin traer la entidad completa)
- [x] `src/identidad/frameworks/api/materias_comisiones_router.py` — inyecta `usuario`; Docente
  sin ninguna comisión en la materia → 403; con al menos una → filtra el listado a las propias
  (Administrador sin cambios)
- [x] `src/identidad/frameworks/api/comisiones_router.py` — `obtener_comision` y
  `listar_estudiantes`: Docente no asignado a esa comisión puntual → 403
- [x] `src/identidad/frameworks/api/invitaciones_router.py` — `generar_invitacion`: el Docente
  que llama debe estar asignado a `comision_id` (además del chequeo ya existente sobre
  `body.docente_id`)

**Hallazgo importante (blast radius de tests existentes):** los fixtures `docente_headers`/
`docente_headers()` usados en ~60 archivos de test generan un JWT de un Docente **sin fila en
la base y sin ninguna comisión asignada**. Antes de esta US eso no importaba (sin chequeo de
pertenencia); ahora, cada test que use ese fixture contra uno de los 4 endpoints tocados
necesita un Docente realmente asignado. Se identificaron y corrigieron 9 archivos afectados
(7 de integración + BDD verificados en aislado, más 2 encontrados recién en la corrida completa
de la suite — `test_us_4_2_2_steps.py` y `test_us_adj_23_steps.py`/`test_us_adj_25_steps.py`
usan un helper local `_headers_docente()` distinto del fixture, invisible al grep inicial):
- `tests/integration/inc4/test_comisiones_query_router.py`
- `tests/integration/inc1/test_invitaciones_api_integration.py`
- `tests/step_defs/inc1/test_us_1_1_1_steps.py` (+ ajuste de expectativa 422→403 en el
  escenario "Rechazo por Docente no asignado", donde el llamador y el destino son la misma
  persona — la autorización se resuelve antes que la validación de negocio original)
- `tests/step_defs/inc1/test_us_1_1_2_steps.py`, `test_us_1_1_3_steps.py`
- `tests/step_defs/inc5-adj/test_us_adj_36_steps.py`
- `tests/step_defs/inc4-adj/test_us_adj_26_steps.py` (mismo ajuste 422→403)
- `tests/step_defs/inc4/test_us_4_2_2_steps.py` (+ fix de `_limpiar_tablas()`, faltaba
  `DELETE FROM comision_docentes` antes de `DELETE FROM comision`)
- `tests/step_defs/inc4-adj/test_us_adj_23_steps.py`, `test_us_adj_25_steps.py` (escenarios
  `@regression` que asumían "cualquier Docente" — se corrigieron para asignar y usar un
  Docente real)

**Metodología de verificación:** grep dirigido para detectar candidatos + corrida completa de
`pytest tests/unit/ tests/integration/ tests/step_defs/` para confirmar que no queda ninguno
suelto (el grep por sí solo no alcanza — hay helpers locales con nombres distintos al fixture
compartido). Confirmado con `git stash` que el único fallo restante
(`test_rechazo_fuera_del_período_vigente`) es el flake preexistente ya documentado en
`CLAUDE.md`, ajeno a esta US — y que la "inestabilidad FK" al correr archivos BDD sueltos
combinados (no la suite completa) ya existía antes de esta US.

### 2. Banco de Preguntas
- [x] `src/banco_preguntas/entities/ports/comision_consulta_port.py` — `esta_asignado_a_materia`
- [x] `src/banco_preguntas/frameworks/adapters/comision_consulta_port_in_process.py` — reescribir
  para delegar en `SQLAlchemyComisionQueryRepository` de Identidad (hoy consulta `ComisionModel`
  directo — se corrige de paso, mismo patrón que Actividad Evaluativa/Analytics)
- [x] `src/banco_preguntas/use_cases/listar_materias.py` — `docente_id: UUID | None`, filtra si
  se indica
- [x] `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py`,
  `cargar_pregunta_verdadero_falso.py`, `editar_pregunta.py`, `eliminar_pregunta.py` — reciben
  `docente_id`, verifican `esta_asignado_a_materia` antes de mutar, `MateriaNoAutorizada` (403)
- [x] `FiltrarBancoUseCase` — mismo chequeo antes de listar
- [x] Controllers/routers (`materias_router.py`, `preguntas_router.py`, `bancos_router.py`) —
  inyectan `usuario`, pasan `docente_id` solo si el rol es Docente
- [x] `src/banco_preguntas/frameworks/dependencies.py` — cablea el puerto ampliado

### 3. Actividad Evaluativa
- [x] `src/actividad_evaluativa/entities/ports/comision_consulta_port.py` —
  `esta_asignado_a_materia` + `esta_asignado_a_comision`
- [x] `src/actividad_evaluativa/frameworks/adapters/comision_consulta_port_in_process.py` —
  agrega los 2 métodos delegando en Identidad
- [x] Use cases de actividades (`listar`, `obtener`, `crear`, `modificar_periodo`,
  `modificar_titulo`, `cerrar`) — `docente_id` + chequeo de materia; `crear` además valida cada
  id de `comisiones_ids` con `esta_asignado_a_comision`
- [x] Use cases de sesiones en vivo (`crear`, `iniciar`, `cancelar`, `mostrar_opciones`,
  `cerrar_pregunta_actual`, `avanzar_siguiente_pregunta`, `finalizar`, `listar_participantes`) —
  `docente_id` + `esta_asignado_a_comision`, reutilizando el error `ComisionNoAutorizada` ya
  existente en `entities/errors.py`
- [x] Routers (`actividades_router.py`, `sesiones_en_vivo_router.py`) — inyectan `usuario` donde
  falta
- [x] `src/actividad_evaluativa/frameworks/dependencies.py` — cablea el puerto ampliado en los 2
  controllers afectados

### 4. Analytics
- [x] `src/analytics/entities/ports/comision_consulta_port.py` — `esta_asignado_a_materia` +
  `esta_asignado_a_comision`
- [x] `src/analytics/frameworks/adapters/comision_consulta_port_in_process.py` — agrega los 2
  métodos (ya delega en el gateway de Identidad, solo se suman los métodos)
- [x] Los 7 use cases de reportes (`ObtenerDesempenoEstudianteUseCase` incluido — compartido
  con el Estudiante, `docente_id` opcional) — `docente_id` + chequeo (materia siempre; comisión
  cuando el reporte la recibe)
- [x] `analytics_router.py` — inyecta `usuario` en los endpoints que no lo tenían
- [x] `frameworks/dependencies.py` — sin cambios de wiring salvo
  `ObtenerEvolucionTemporalEstudianteUseCase` (gana `comision_consulta`, no tenía ningún puerto
  de Comisión antes)

**Blast radius de tests:** ~15 archivos entre `tests/unit/inc4/` (fakes + firmas de
`execute()`), `tests/integration/inc4/` (6 archivos de router, reusan
`asignar_docente_a_materia`/`asignar_docente_a_comision_existente` de
`tests/integration/conftest.py` — el segundo helper es nuevo, variante que asigna sobre una
Comisión ya creada por el propio test) y `tests/step_defs/inc4/` (6 archivos, mismo patrón +
fix del mismo bug de orden de `DELETE` — faltaba `DELETE FROM comision_docentes` antes de
`DELETE FROM comision` — ya visto en `US-ADJ-57` de Actividad Evaluativa). 4 escenarios
`.feature` ajustados de 422 a 403 (`US-4.2.4`, `US-ADJ-44`, `US-ADJ-45`, `US-ADJ-46`): la
autorización por Comisión se resuelve antes que la validación de negocio "pertenece a la
materia" cuando el Docente no está asignado a ninguna de las dos — mismo criterio ya aplicado
en Identidad/Actividad Evaluativa.

## Integración
- [x] Sin tablas ni eventos nuevos — solo lectura de `comision_docentes`
- [x] `docs/architecture/20-context-map-integrations.md` actualizado con la ampliación del
  puerto de Analytics
- [ ] Los circuitos E2E de `US-6.3.10` (`frontend/e2e/`) deben seguir en verde — pendiente de
  correr como regresión final
- [ ] El `.feature` cruzado de Fase 1 (`tests/features/inc6-adj/US-ADJ-57-docente-solo-sus-materias.feature`,
  9 escenarios, cruza los 4 BC) sigue sin `step_defs` — validación final pendiente, ahora que
  las 4 olas están mergeadas

**Estado:** 28/28 tareas de implementación completadas (secciones 1-4). Quedan dos ítems de
verificación final antes de cerrar la US: el `.feature` cruzado y la regresión E2E de
`US-6.3.10`.
