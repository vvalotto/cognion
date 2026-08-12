# US-2.1.1: Docente da de alta una materia y su banco de preguntas

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `Materia`, `Banco`
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **dar de alta una materia y que se cree automáticamente su banco de preguntas**
para **tener un espacio donde cargar y clasificar las preguntas de esa materia (RF-04, RF-06)**.

---

## Contexto del dominio

### Problema

Sin `Materia` ni `Banco` no hay contra qué cargar una `PreguntaPlantilla` — es la precondición
de todo el resto de la Iteración 1. Hoy se conocen dos materias fijas (Ingeniería de Software,
Gestión de Proyectos), pero el alta es una operación normal del producto, no un seed/fixture
(`BC-banco-preguntas-modelo.md` §4).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `Materia` | `id`, `nombre` único |
| Aggregate | `Banco` | `id`, `materia_id` único (1:1 con `Materia`) |
| Command | `CrearMateria(nombre)` | Crea la materia |
| Command | `CrearBanco(materia_id)` | Crea el banco de esa materia — se ejecuta en el mismo flujo que `CrearMateria`, sin pantalla ni paso separado |
| Domain Event | `MateriaCreada`, `BancoCreado` | Señalan el alta |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- `nombre` no vacío.

### Postcondicion

- `Materia` persistida con `nombre` único.
- `Banco` persistido en la misma operación, con `materia_id` apuntando a la `Materia` recién
  creada.
- Eventos `MateriaCreada`, `BancoCreado`.

### Invariantes

| ID | Invariante |
|----|------------|
| INV-BP-00 | `Materia.nombre` único en todo el sistema — `MateriaYaExiste` si no. |
| INV-BP-01 | A lo sumo un `Banco` por `Materia` — no aplica todavía en esta US (el `Banco` se crea siempre junto con la `Materia`, nunca de forma independiente), pero queda como invariante estructural para el resto de la iteración. |

---

## Criterios de aceptacion

```gherkin
Feature: Alta de materia y banco (US-2.1.1)

  Scenario: Docente crea una materia nueva
    Given un Docente autenticado
    When ejecuta CrearMateria(nombre="Ingeniería de Software")
    Then el sistema persiste la Materia con ese nombre
    And crea automáticamente su Banco asociado
    And se emiten los eventos MateriaCreada y BancoCreado

  Scenario: Rechazo por nombre duplicado
    Given una Materia existente con nombre "Ingeniería de Software"
    When un Docente ejecuta CrearMateria(nombre="Ingeniería de Software")
    Then el sistema rechaza la operación con MateriaYaExiste
    And no se crea ninguna Materia ni Banco nuevos
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — se implementa con la arquitectura existente (Clean Architecture + CRUD, `ARQ_v1.md`).

**Capa(s) afectadas:**
- [x] Entities — `Materia`, `Banco`, eventos `MateriaCreada`/`BancoCreado`
- [x] Use Cases — `CrearMateriaUseCase` (orquesta `CrearMateria` + `CrearBanco` en la misma transacción)
- [x] Interface Adapters — controller, `MateriaRepositoryPort`, `BancoRepositoryPort`
- [x] Frameworks — endpoint FastAPI, modelos SQLAlchemy + migración
- [ ] Frontend — cubierto por `US-2.1.9`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#nueva-materia`) se
especifica en `US-2.1.9`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/materia.py` | Aggregate `Materia` |
| `src/banco_preguntas/entities/banco.py` | Aggregate `Banco` |
| `src/banco_preguntas/entities/eventos.py` | `MateriaCreada`, `BancoCreado` |
| `src/banco_preguntas/entities/ports/materia_repository_port.py` | Puerto de persistencia |
| `src/banco_preguntas/entities/ports/banco_repository_port.py` | Puerto de persistencia |
| `src/banco_preguntas/use_cases/crear_materia.py` | Orquesta INV-BP-00, crea `Materia` + `Banco` en la misma transacción |
| `src/banco_preguntas/interface_adapters/controllers/materias_controller.py` | Validación de entrada, mapeo a use case |
| `src/banco_preguntas/interface_adapters/gateways/materia_repository.py` | Implementación SQLAlchemy |
| `src/banco_preguntas/interface_adapters/gateways/banco_repository.py` | Implementación SQLAlchemy |
| `src/banco_preguntas/frameworks/api/materias_router.py` | Endpoint FastAPI (requiere rol `docente`) |
| `src/banco_preguntas/frameworks/db/models.py` | Modelos SQLAlchemy `materia`, `banco` |
| `src/banco_preguntas/frameworks/db/migrations/` | Migración Alembic |

---

## Referencias

- Relacionada con: `US-2.1.2` (consume `Materia` por puerto desde Identidad), `US-2.1.3`, `US-2.1.4` (dependen de `Banco`)
- Modelo de dominio: `docs/design/domain/BC-banco-preguntas-modelo.md` (§3, §4 `Materia`, `Banco`)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
