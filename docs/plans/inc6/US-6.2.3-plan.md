# Plan de Implementación: US-6.2.3 - Read models de ranking e histograma

**Patrón:** clean-architecture, BC `actividad_evaluativa`

## Decisiones de diseño (a confirmar)

1. **Atomicidad evento + proyección** (contrato de la spec). El Use Case escribe la proyección
   (pendiente, sin `commit`) y luego llama a `EventStorePort.append`, cuyo `commit` confirma ambas.
   Gap detectado: `SQLAlchemyEventStore.append` rechaza por `expected_sequence_number` **sin**
   `rollback`; la proyección pendiente quedaría en la sesión y se confirmaría en un `commit`
   posterior. Solución elegida: `ProyeccionesEnVivoPort.descartar_pendientes()` (rollback de la
   sesión), que el Use Case llama en su `except ConcurrenciaOptimistaError` antes de reintentar o
   traducir. **No se toca `SQLAlchemyEventStore`** (evita alterar el comportamiento de los Use Case
   ya cerrados). El camino de `IntegrityError` ya hace `rollback` dentro de `append`.
2. **Dos puertos** (command/query, precedente `US-3.2.4`), en un solo archivo
   `entities/ports/proyecciones_en_vivo_port.py`, con los VOs `ParticipanteEnRanking`
   (`posicion`, `estudiante_id`, `puntaje_acumulado`) y `OpcionDistribuida` (`opcion`, `cantidad`):
   - Escritura: `inicializar_participante(sesion_id, estudiante_id)`,
     `registrar_respuesta(sesion_id, estudiante_id, pregunta_id, opcion, puntaje)`,
     `descartar_pendientes()`.
   - Lectura: `ranking(sesion_id)`, `distribucion(sesion_id, pregunta_id)`,
     `cantidad_respuestas(sesion_id, pregunta_id)`.
3. **Un solo adapter** `SQLAlchemyProyeccionesEnVivo` implementa ambos puertos, con upserts
   atómicos: `INSERT ... ON CONFLICT DO NOTHING` (inicializar) y
   `ON CONFLICT DO UPDATE SET ... = ... + excluded...` (respuesta y contador). Nunca
   leer-modificar-escribir. Orden del ranking: `puntaje_acumulado DESC, ultima_actualizacion ASC,
   estudiante_id ASC`; la posición se calcula al leer.
4. **Modelos ORM** `RankingPorSesionModel` y `DistribucionPorPreguntaModel` en `frameworks/db/models.py`,
   PK compuestas. Migración Alembic reversible sobre el head `e31e7dfcab3a`; `alembic upgrade →
   downgrade → upgrade` verificado contra la DB real.
5. **`UnirseASesionEnVivoUseCase`** recibe el 5° dependiente (`ProyeccionesEnVivoPort`). Solo
   inicializa la fila cuando efectivamente **crea** la participación, antes del `append`; en el
   camino idempotente (ya existía) no la toca, así que un doble join no reinicia el puntaje. Cambia
   la firma → actualizar los 3 tests que lo construyen y `dependencies.py` (grepeado de antemano).
6. **Riesgo de CBO** por el 5° puerto: se verifica en pre-push; plan B, mover la inicialización
   a un helper/servicio de proyección si llega a 11.
7. **Tests unitarios:** `FakeProyeccionesEnVivo` (ambos puertos, aplica de inmediato). La
   atomicidad real y la concurrencia se prueban solo en integración (DB real).
8. **conftest de integración:** limpiar también las dos tablas nuevas.
9. **Sin `.feature`** (`skip_bdd`).

## Tareas

| # | Tarea | Archivo |
|---|---|---|
| 1 | Puertos + VOs | `entities/ports/proyecciones_en_vivo_port.py` |
| 2 | Modelos ORM | `frameworks/db/models.py` |
| 3 | Migración reversible | `migrations/versions/<rev>_read_models_sesion_en_vivo.py` |
| 4 | Adapter SQL | `frameworks/adapters/proyecciones_en_vivo_repository.py` |
| 5 | Modificar `UnirseASesionEnVivoUseCase` + wiring | `use_cases/unirse_a_sesion_en_vivo.py`, `dependencies.py` |
| 6 | Fake + actualizar 3 tests que construyen el use case | `tests/unit/inc6/_fakes.py`, tests existentes |
| 7 | Unit: unirse inicializa, idempotente, descarta al perder carrera | `tests/unit/inc6/` |
| 8 | Integración: ranking/orden/desempate, distribución, 60 concurrentes, atomicidad, migración | `tests/integration/inc6/` (+ `conftest.py`) |
| 9 | Quality gates, documentación, reporte | — |

## Riesgos
- Migración toca la DB local compartida; `tests/integration/` la vacía (sin prueba manual en curso).
- Concurrencia real de 60 respuestas requiere sesiones separadas por tarea en el test.
