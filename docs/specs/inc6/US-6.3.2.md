# US-6.3.2: Listar las sesiones en vivo de una Comisión

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feature backend` (consulta — sin comando ni evento de dominio)
**Agregado principal afectado**: — (lectura sobre los streams de `ActividadEvaluativaEnVivo`)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Estudiante o Docente**,
quiero **ver qué sesiones en vivo hay disponibles para mi Comisión**,
para **entrar a la que está en marcha sin que nadie me pase un enlace**.

---

## Contexto del dominio

### Problema

El backend permite crear, unirse, conducir y consultar **una** sesión conociendo su `sesion_id`, pero **no hay
forma de descubrir sesiones**. Las pantallas aprobadas lo exigen en dos lugares:

- **Estudiante** (`§3.1`, `#est-sesiones`): "sesiones en `EnEspera` o `EnCurso` de la Comisión donde está
  inscripto", en la misma pantalla que las actividades de período abierto.
- **Docente** (`US-6.3.0`, H6): recuperar la sesión activa de una Comisión si cerró la pestaña o se cayó el
  navegador — hoy solo se llega a la sala justo después de crearla.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Query | `ListarSesionesEnVivo(comision_id, estados)` | Sesiones de una Comisión filtradas por estado |
| Puerto (nuevo) | `SesionesEnVivoQueryPort` | Consulta de lectura (CQRS), separada del `EventStorePort` |
| Adapter (nuevo) | `SQLAlchemySesionesEnVivoQueryRepository` | Lee la tabla `events`: comisión del primer evento y estado del último — mismo criterio que `EvaluacionActivaQueryPort` (`US-3.2.4`), sin proyección sincronizada; válido a esta escala (una sesión activa por Comisión a la vez) |
| Use case (nuevo) | `ListarSesionesEnVivoUseCase` | Resuelve la Comisión según el rol, consulta y completa el nombre de la Materia (`MateriaConsultaPort`, ya existente) |
| Endpoint (nuevo) | `GET /sesiones-en-vivo` | Ver reglas |

### Endpoint

`GET /sesiones-en-vivo?comision_id=<uuid>&estado=EnEspera&estado=EnCurso`

| Rol | `comision_id` | Comportamiento |
|---|---|---|
| `estudiante` | ignorado si coincide, **`403` si es otra** | Se usa **su** Comisión (`EstudianteConsultaPort.obtener_comision_id`, ya existente). Sin Comisión → lista vacía |
| `docente` | **obligatorio** (`422` si falta) | Sesiones de esa Comisión. Sin ownership de sesión (la spec de `US-6.1.x` no lo define) |
| otros | — | `403` |

- `estado` es repetible; **por defecto `EnEspera` y `EnCurso`** (las `Finalizada` no se listan por defecto: no hay
  "sesiones pasadas" en el modo en vivo, `§3.1`).
- Orden: **más recientes primero**.

### Respuesta (lista; vacía si no hay)

`{ id, comision_id, materia_id, materia_nombre, cantidad_preguntas, tiempo_limite_por_pregunta_segundos, estado, unidad_tematica, tema, creada_en }`

---

## Especificacion del comportamiento

### Precondicion

- `US-6.1.2` (creación) y `US-6.2.7` (para que exista `Finalizada` por API).

### Postcondicion

- Ninguna escritura. Sin evento, sin migración.

### Excepciones

| Excepción | Condición | HTTP |
|---|---|---|
| — | `estudiante` con `comision_id` de otra Comisión | 403 |
| — | `docente` sin `comision_id` | 422 |
| — | rol no permitido | 403 |

### Observación fuera de alcance (pre-existente)

`UnirseASesionEnVivo` **no valida que el Estudiante pertenezca a la Comisión de la sesión** (`US-6.1.3` solo
verifica que exista y que no esté finalizada). Esta US limita lo que cada Estudiante **ve**, no lo que puede
**alcanzar** conociendo un `sesion_id`. Se registra como ítem abierto para decidir con Víctor (posible `US-ADJ`).

---

## Criterios de aceptacion

```gherkin
Feature: Listar las sesiones en vivo de una Comisión (US-6.3.2)

  Scenario: El Estudiante ve las sesiones activas de su Comisión
    Given una sesión EnEspera y otra EnCurso de la Comisión del Estudiante
    When el Estudiante lista las sesiones
    Then recibe las dos, con el nombre de la Materia y el estado

  Scenario: El Estudiante no ve las de otra Comisión
    Given una sesión activa de otra Comisión
    When el Estudiante lista las sesiones
    Then no aparece

  Scenario: Las sesiones finalizadas no se listan por defecto
    Given una sesión Finalizada de la Comisión
    When el Estudiante lista las sesiones
    Then no aparece

  Scenario: El Docente recupera la sesión activa de una Comisión
    Given una sesión EnCurso de la Comisión
    When el Docente lista las sesiones pasando la Comisión
    Then recibe esa sesión con su estado

  Scenario: El Docente puede pedir también las finalizadas
    Given una sesión Finalizada de la Comisión
    When el Docente lista con estado Finalizada
    Then recibe esa sesión

  Scenario: El Docente debe indicar la Comisión
    Given un Docente autenticado
    When lista las sesiones sin comision_id
    Then el sistema responde 422

  Scenario: El Estudiante no puede pedir otra Comisión
    Given un Estudiante autenticado
    When lista las sesiones pasando la comision_id de otra Comisión
    Then el sistema responde 403

  Scenario: Sin sesiones
    Given una Comisión sin sesiones activas
    When se listan
    Then la respuesta es una lista vacía

  Scenario: Orden por recientes
    Given dos sesiones activas creadas en momentos distintos
    When se listan
    Then la más reciente aparece primero
```

---

## Impacto arquitectonico

- [ ] No — consulta sobre el event store, mismo patrón que `US-3.2.4`. Si el volumen creciera, migrar a proyección es reversible.

**Capa(s) afectadas:**
- [x] Entities — `SesionesEnVivoQueryPort`
- [x] Use Cases — `ListarSesionesEnVivoUseCase`
- [x] Interface Adapters — método en `SesionesEnVivoQueryController` (ya tiene 3 use cases: **vigilar CBO**; si roza el umbral, controller propio)
- [x] Frameworks — endpoint, schema, adapter, wiring
- [ ] Frontend — consume `US-6.3.5` (Docente) y `US-6.3.8` (Estudiante)

---

## Fuente de verdad UX

No aplica — backend. El uso está en `wireframes-actividad-evaluativa-en-vivo.md` §3.1 y en `US-6.3.0` (H6).

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/ports/sesiones_en_vivo_query_port.py` | Puerto (nuevo) |
| `src/actividad_evaluativa/frameworks/adapters/sesiones_en_vivo_query_repository.py` | Adapter (nuevo) |
| `src/actividad_evaluativa/use_cases/listar_sesiones_en_vivo.py` | Use case (nuevo) |
| `src/actividad_evaluativa/interface_adapters/controllers/sesiones_en_vivo_query_controller.py` | Método |
| `src/actividad_evaluativa/frameworks/api/sesiones_en_vivo_router.py`, `schemas.py`, `dependencies.py` | Endpoint, schema, wiring |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.3.2*.feature` + step defs | Unitarios, HTTP, BDD |

---

## Referencias

- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §13 (queries), §14
- Precedente: `EvaluacionActivaQueryPort` (`US-3.2.4`), `ActividadesQueryController` (`US-3.4.2`)
- Depende de: `US-6.1.2`, `US-6.2.7`
- Consumida por: `US-6.3.5`, `US-6.3.8`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
