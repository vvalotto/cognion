# US-2.1.2: Comisión referencia Materia por puerto (refactor técnico)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `refactor backend`
**Agregado principal afectado**: `Comisión` (BC Identidad)
**Bounded Context**: Identidad (consumidor) / Banco de Preguntas (dueño de `Materia`)

---

## Descripcion (lenguaje de negocio)

Como **equipo de desarrollo**,
quiero **que `Comisión.materia` deje de ser un `string` libre y referencie la `Materia` dueña
de BC Banco de Preguntas por un puerto de dominio**
para **que exista una única fuente de verdad de qué materias existen, respetando la regla de
`CLAUDE.md` de no hacer imports directos entre BCs**.

---

## Contexto del dominio

### Problema

`Comisión.materia` (`src/identidad/entities/comision.py`) es `string` libre desde BL-002
(Incremento 1). Con `Materia` ahora modelada como Entity con identidad propia y dueña de BC
Banco de Preguntas (`BC-banco-preguntas-modelo.md` §4, hot spot 2), las dos representaciones
del mismo concepto conviven sin relación formal — riesgo de que una comisión quede con un
nombre de materia que no existe como `Materia` real. Se resuelve con un puerto: BC Identidad
define en su propio `entities/ports/` la interfaz que necesita (ej.
`MateriaValidadorPort.existe(materia_id) -> bool` o `obtener(materia_id) -> MateriaDTO`), y un
adaptador en `frameworks/` la implementa llamando a BC Banco de Preguntas — mismo criterio que
`ADR-006` (integración directa Sesiones→Notificaciones), documentado como acoplamiento
consciente en vez de indirección prematura.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (nuevo, en Identidad) | `MateriaPort` | Definido en `src/identidad/entities/ports/` — consulta `Materia` sin importar BC Banco de Preguntas |
| Adapter (nuevo, en Identidad) | `MateriaPortInProcess` | Implementa `MateriaPort` en `frameworks/`, llamada directa in-process al caso de uso `ObtenerMateria` de BC Banco de Preguntas |
| Entity modificada | `Comisión` | `materia: str` → `materia_id: UUID` (referencia a `Materia`) |
| Migración de datos | — | Las comisiones existentes (BL-002) deben mapear su `materia: str` actual a la `Materia` correspondiente por nombre |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.1` implementada — existe al menos una `Materia` por cada valor distinto que hoy tiene
  `Comisión.materia` en la base (las dos materias conocidas).
- Comisiones existentes en la base de BL-002 (creadas en el Incremento 1).

### Postcondicion

- `Comisión.materia_id` referencia una `Materia` real vía `MateriaPort`.
- Toda comisión que existía antes de la migración conserva un `materia_id` válido, resuelto por
  nombre contra las `Materia` creadas en `US-2.1.1`.
- `CrearComision` valida contra `MateriaPort` que la `materia_id` indicada existe —
  `MateriaNoExiste` si no.
- Tests existentes de BC Identidad (`US-1.1.0` y siguientes) siguen en verde tras el refactor.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Ninguna `Comisión` puede quedar con `materia_id` que no resuelva a una `Materia` existente — ni antes ni después de la migración. |
| — | El puerto no permite a Identidad importar directamente ningún módulo de `src/banco_preguntas/` (regla de `CLAUDE.md`, comunicación entre BCs solo por `entities/ports/`). |

---

## Criterios de aceptacion

```gherkin
Feature: Comisión referencia Materia por puerto (US-2.1.2)

  Scenario: Migración de datos existentes
    Given una Comisión persistida en BL-002 con materia = "Ingeniería de Software" (string)
    And una Materia con nombre "Ingeniería de Software" creada en US-2.1.1
    When se ejecuta la migración
    Then la Comisión queda con materia_id apuntando a esa Materia

  Scenario: Alta de comisión valida la materia por el puerto
    Given un Administrador autenticado
    When ejecuta CrearComision(materia_id=<id inexistente>, horario, administrador_id)
    Then el sistema rechaza la operación con MateriaNoExiste

  Scenario: Sin imports directos entre BCs
    Given el código de src/identidad/
    When se revisan sus imports
    Then ningún módulo de src/identidad/ importa directamente src/banco_preguntas/
    And la única comunicación es a través de src/identidad/entities/ports/materia_port.py
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] Sí — mecanismo de comunicación entre BCs (puerto + adaptador in-process, mismo criterio
  que `ADR-006`). No amerita un ADR nuevo por sí solo (reutiliza un patrón ya ratificado), pero
  se documenta la decisión en el comentario de cierre del Issue.

**Capa(s) afectadas:**
- [x] Entities — `Comisión` (Identidad), `MateriaPort` (nuevo, Identidad)
- [x] Use Cases — `CrearComisionUseCase` (valida contra el puerto)
- [x] Interface Adapters — sin cambios de controller (el request ya usa `materia_id` o se ajusta)
- [x] Frameworks — `MateriaPortInProcess` (Identidad), migración Alembic de datos + esquema
- [ ] Frontend — sin impacto (no hay pantalla de alta de Comisión con UI todavía)

---

## Fuente de verdad UX

No aplica — refactor backend puro, sin pantalla nueva ni modificada.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/identidad/entities/comision.py` | `materia: str` → `materia_id: UUID` |
| `src/identidad/entities/ports/materia_port.py` | Puerto nuevo — `existe(materia_id)` / `obtener(materia_id)` |
| `src/identidad/frameworks/adapters/materia_port_in_process.py` | Adaptador — llama al caso de uso de consulta de `Materia` en BC Banco de Preguntas |
| `src/identidad/use_cases/crear_comision.py` | Valida `materia_id` contra `MateriaPort` |
| `src/identidad/frameworks/db/models.py` | Columna `materia` → `materia_id` (FK lógica, sin FK de base entre BCs — solo UUID) |
| `src/identidad/frameworks/db/migrations/` | Migración de esquema + script de datos (mapeo `materia: str` → `Materia` por nombre) |
| `src/banco_preguntas/use_cases/obtener_materia.py` | Caso de uso de solo lectura que el adaptador de Identidad invoca |

---

## Referencias

- Relacionada con: `US-2.1.1` (crea las `Materia` que esta US necesita para migrar), `ADR-006` (precedente de puerto por llamada directa)
- Modelo de dominio: `docs/design/domain/BC-banco-preguntas-modelo.md` (§4, nota de alcance "cruce con BC Identidad")
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
