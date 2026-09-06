# US-4.2.2: ComisionConsultaPort — comisiones por materia y estudiantes por comisión

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.2`
**Tipo**: `feat backend` (técnica)
**Agregado principal afectado**: — (consulta de solo lectura, sin comando ni evento)
**Bounded Context**: Identidad (query nueva) + Analytics (adapter in-process consumidor)

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **que el sistema sepa qué comisiones tiene una materia y qué estudiantes integran una
comisión**
para **poder elegir en cascada Materia → Comisión → Estudiante en las pantallas de desempeño
(RF-16, RF-17)**.

---

## Contexto del dominio

### Problema

`BC-analytics-modelo.md` §5 detectó en el modelado que ni `ComisionRepositoryPort` ni
`UsuarioRepositoryPort` (Identidad) resuelven hoy "comisiones de una materia" ni "estudiantes
de una comisión" — ambos solo exponen `obtener_por_id`. Es un puerto de consulta nuevo de
punta a punta, no una extensión de uno existente.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (nuevo, Identidad) | `ComisionQueryPort` | `listar_comisiones_por_materia(materia_id)`, `listar_estudiantes(comision_id)` — separado de `ComisionRepositoryPort` (altas/persistencia) por responsabilidad command/query, mismo criterio que `CuentaQueryPort` (`US-2.2.2`) |
| Adapter (nuevo, Identidad) | `SQLAlchemyComisionQueryRepository` | Implementa `ComisionQueryPort` contra las tablas `comision`/`estudiante` existentes |
| Endpoints (nuevos, Identidad) | `GET /materias/{materia_id}/comisiones`, `GET /comisiones/{comision_id}/estudiantes` | Rol `docente` — pueblan los selectores del frontend (`US-4.2.5`) |
| Port (nuevo, Analytics) | `ComisionConsultaPort` (`BC-analytics-modelo.md` §5) | Mismos dos métodos, propio de Analytics — no importa el port de Identidad directamente |
| Adapter (nuevo, Analytics) | adapter in-process | Implementa `ComisionConsultaPort` invocando el `ComisionQueryPort` de Identidad in-process (mismo patrón que `MateriaPort`/`MateriaConsultaPort`) |

---

## Especificacion del comportamiento

### Precondicion

- Docente autenticado (JWT válido, rol `docente`) para los endpoints HTTP.
- `materia_id`/`comision_id` existen.

### Postcondicion

- `GET /materias/{materia_id}/comisiones` → 200 con `list[ComisionResumen]` (`id`, `horario`)
  de todas las comisiones de esa materia. Materia sin comisiones → 200 con lista vacía.
- `GET /comisiones/{comision_id}/estudiantes` → 200 con `list[UUID]` (o
  `list[EstudianteResumen]` con `id`/`nombre`, a definir en el plan de implementación según lo
  que necesite realmente `US-4.2.5`) — roster de la comisión. Comisión sin estudiantes → 200
  con lista vacía.
- `materia_id`/`comision_id` inexistente → 404.
- Sin JWT válido → 401. Rol distinto de `docente` → 403.
- `ComisionConsultaPort.listar_comisiones_por_materia`/`.listar_estudiantes` (Analytics) devuelven
  el mismo resultado que su endpoint HTTP equivalente, sin ida y vuelta por HTTP (in-process).

### Invariantes

| ID | Invariante |
|----|------------|
| — | `ComisionQueryPort` es de solo lectura — no reemplaza ni modifica `ComisionRepositoryPort`, coexisten (command/query). |
| — | Analytics nunca importa código de `src/identidad/` directamente — `ComisionConsultaPort` es el único punto de acceso, mismo patrón arquitectónico que el resto de comunicación entre BCs. |

---

## Criterios de aceptacion

```gherkin
Feature: Consulta de comisiones por materia y estudiantes por comisión (US-4.2.2)

  Scenario: Materia con comisiones
    Given una materia X con 2 comisiones
    When un Docente hace GET /materias/X/comisiones
    Then recibe 200 con las 2 comisiones (id, horario)

  Scenario: Comisión con estudiantes
    Given una comisión con 3 estudiantes inscriptos
    When un Docente hace GET /comisiones/{comision_id}/estudiantes
    Then recibe 200 con los 3 estudiantes

  Scenario: Comisión sin estudiantes
    Given una comisión recién creada, sin inscripciones
    When un Docente hace GET /comisiones/{comision_id}/estudiantes
    Then recibe 200 con lista vacía

  Scenario: Materia inexistente
    Given un id de materia que no existe
    When un Docente hace GET /materias/{id-inexistente}/comisiones
    Then recibe 404

  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /materias/X/comisiones
    Then recibe 403

  Scenario: Analytics consume el adapter in-process
    Given el mismo estado de datos que el primer escenario
    When ComisionConsultaPort.listar_comisiones_por_materia(X) se invoca in-process
    Then devuelve el mismo resultado que el endpoint HTTP equivalente
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — primer puerto de consulta cross-BC de Identidad hacia Analytics con separación
  command/query explícita desde el diseño (evita el patrón de CRITICAL de CBO ya visto en
  `US-2.1.2`/`US-2.1.5`/`US-2.1.6`/`US-2.1.7`/`US-2.2.2` al forzar una query nueva dentro de un
  repositorio de escritura existente). No amerita ADR nuevo — mismo patrón ya usado y
  documentado (`CuentaQueryPort`, `MateriaConsultaPort`).

**Capa(s) afectadas:**
- [x] Entities (Identidad) — `ComisionQueryPort` (nuevo), `ComisionResumen`/`EstudianteResumen` (DTOs, si aplica)
- [ ] Use Cases (Identidad) — probablemente no requiere Use Case nuevo si el controller llama al port directo (a confirmar en el plan — mismo criterio liviano que otras queries de listado)
- [x] Interface Adapters (Identidad) — controller nuevo o extendido para los 2 endpoints
- [x] Frameworks (Identidad) — `SQLAlchemyComisionQueryRepository`, rutas nuevas
- [x] Entities (Analytics) — `ComisionConsultaPort` (nuevo)
- [x] Frameworks (Analytics) — adapter in-process, cableado en `dependencies.py`
- [ ] Frontend — no aplica a esta US (consumido recién en `US-4.2.5`/`US-4.2.6`)

---

## Fuente de verdad UX

No aplica a esta US — infraestructura de consulta pura, sin pantalla propia.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/ports/comision_query_port.py` | Nuevo — `ComisionQueryPort` |
| `src/identidad/frameworks/adapters/sqlalchemy_comision_query_repository.py` | Nuevo |
| `src/identidad/interface_adapters/controllers/` | Endpoints nuevos (controller propio o extensión de uno existente, a definir en el plan) |
| `src/identidad/frameworks/api/` | Rutas `GET /materias/{materia_id}/comisiones`, `GET /comisiones/{comision_id}/estudiantes` |
| `src/analytics/entities/ports/comision_consulta_port.py` | Nuevo — `ComisionConsultaPort` |
| `src/analytics/frameworks/adapters/comision_consulta_port_in_process.py` | Nuevo |
| `tests/unit/inc4/` y `tests/integration/inc4/` | Tests de ambos ports/adapters y de los 2 endpoints |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §5
- Sin dependencia de otra US de esta iteración — junto con `US-4.2.3`, desbloquea `US-4.2.4` y `US-4.2.5`
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 2
- Issue: #241

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
