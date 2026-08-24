# US-2.1.9: Docente ve el listado de materias y da de alta una nueva

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat backend + frontend`
**Agregado principal afectado**: `Materia`, `Banco` (consulta, sin cambios de invariantes)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver el listado de materias y dar de alta una nueva desde la UI**
para **acceder al banco de cada materia y crear materias nuevas sin usar la API directamente
(RF-04)**.

---

## Contexto del dominio

### Problema

`POST /materias` existe desde `US-2.1.1`, pero **no existe `GET /materias`** — gap detectado
en `US-2.1.8` (Fase 2, planificación): la spec original de esta US asumía que el listado ya
estaba implementado. Sin `GET /materias` ningún Docente puede ver sus materias desde la UI, y
sin esta US tampoco puede operar `POST /materias` desde la aplicación real. Decisión de
Víctor (2026-08-14): incorporar `GET /materias` al alcance de esta misma US en vez de abrir
un ciclo backend separado — es un único endpoint de consulta, sin invariantes nuevas.

El wireframe aprobado (`US-2.0.2`) muestra la cantidad de preguntas activas por materia en la
grilla — eso requiere que el backend calcule ese conteo, no solo listar `Materia`. Ningún
puerto expone hoy un método de listado ni de conteo:

| Puerto | Método nuevo | Motivo |
|---|---|---|
| `MateriaRepositoryPort` | `listar() -> list[Materia]` | No existe ningún método de listado |
| `BancoRepositoryPort` | `obtener_por_materia_id(materia_id) -> Banco \| None` | 1:1 con `Materia` (INV-BP-01), pero no hay forma de resolverlo desde el lado de `Materia` |

El conteo de preguntas activas **no** agrega un método nuevo a `PreguntaRepositoryPort` —
reutiliza `filtrar(banco_id)` (`US-2.1.7`) y toma `len(...)` del resultado, evitando ensanchar
ese puerto solo para un conteo.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Endpoint nuevo | `GET /materias` | Lista materias con `id`, `nombre`, `banco_id` y `cantidad_preguntas_activas`; rol `docente` |
| Endpoint existente | `POST /materias` | Ya existe (`US-2.1.1`), sin cambios |
| Use Case nuevo | `ListarMateriasUseCase` | Orquesta `MateriaRepositoryPort.listar()` + `BancoRepositoryPort.obtener_por_materia_id()` + `PreguntaRepositoryPort.filtrar()` (para el conteo) por cada materia |
| Cliente API | `banco-preguntas-api.ts` (`US-2.1.8`) | Se agrega `listarMaterias()` — no existía, fue excluida explícitamente de `US-2.1.8` por este mismo gap |

---

## Especificacion del comportamiento

### Precondicion

- `US-2.1.8` implementada.
- Docente autenticado (rol `docente`).

### Postcondicion

- `GET /materias` devuelve la lista completa de materias con `id`, `nombre`, `banco_id` y
  `cantidad_preguntas_activas` (rol `docente`).
- Grilla de materias renderizada con el nombre y cantidad de preguntas activas de cada una.
- Alta exitosa de materia → vuelve al listado con la nueva materia visible.
- Nombre duplicado → error inline en el formulario, sin pantalla propia (mismo criterio de
  simplicidad que otros errores de formulario en Identidad).

### Invariantes

| ID | Invariante |
|----|------------|
| — | El formulario no permite enviar un nombre vacío (validación de cliente, la regla de negocio la aplica el backend). |
| — | `cantidad_preguntas_activas` cuenta solo preguntas con `activa = true` (mismo criterio que `filtrar()`, `US-2.1.7` — INV-BP-04, baja lógica no vuelve a aparecer). |

---

## Criterios de aceptacion

```gherkin
Feature: Listado y alta de materias (US-2.1.9)

  Scenario: Ver el listado de materias
    Given un Docente autenticado con materias existentes
    When navega a la pantalla de materias
    Then ve una tarjeta por cada materia con su cantidad de preguntas activas

  Scenario: Alta exitosa de materia
    Given un Docente autenticado en el listado de materias
    When completa el formulario de nueva materia con un nombre no usado
    Then el sistema crea la materia y su banco
    And vuelve al listado, mostrando la materia nueva

  Scenario: Rechazo por nombre duplicado
    Given una materia existente con nombre "Ingeniería de Software"
    When un Docente intenta crear una materia con ese mismo nombre
    Then el sistema muestra un error inline en el formulario
    And no navega fuera de la pantalla de alta

  Scenario: GET /materias devuelve la cantidad de preguntas activas por materia
    Given una materia con 3 preguntas activas y 1 pregunta eliminada (baja lógica)
    When se hace GET /materias
    Then la materia aparece en la respuesta con cantidad_preguntas_activas = 3
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — `GET /materias` reutiliza el patrón de puertos/use case/controller/router ya
  establecido por `US-2.1.1`/`US-2.1.7`; el conteo reutiliza `PreguntaRepositoryPort.filtrar()`
  en vez de agregar un método nuevo a ese puerto.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/Materias.tsx`, `frontend/src/pages/NuevaMateria.tsx`
- [x] Backend — `entities/ports/materia_repository_port.py`,
  `entities/ports/banco_repository_port.py`, `use_cases/listar_materias.py`,
  `interface_adapters/controllers/materias_controller.py`,
  `interface_adapters/gateways/materia_repository.py`,
  `interface_adapters/gateways/banco_repository.py`, `frameworks/api/materias_router.py`,
  `frameworks/api/schemas.py`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-banco-preguntas.md` §2.1 (`#materias`), §2.2 (`#nueva-materia`).
Prototipo navegable: `docs/design/ux/prototipos/banco-preguntas-carga-filtrado.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/ports/materia_repository_port.py` | Método nuevo `listar() -> list[Materia]` |
| `src/banco_preguntas/entities/ports/banco_repository_port.py` | Método nuevo `obtener_por_materia_id(materia_id) -> Banco \| None` |
| `src/banco_preguntas/use_cases/listar_materias.py` (nuevo) | `ListarMateriasUseCase` — orquesta materia + banco + conteo de preguntas activas (`filtrar()`) por cada materia |
| `src/banco_preguntas/interface_adapters/controllers/materias_controller.py` | Método nuevo `listar_materias()` |
| `src/banco_preguntas/interface_adapters/gateways/materia_repository.py` | Implementa `listar()` |
| `src/banco_preguntas/interface_adapters/gateways/banco_repository.py` | Implementa `obtener_por_materia_id()` |
| `src/banco_preguntas/frameworks/api/materias_router.py` | `GET /materias` (rol `docente`) |
| `src/banco_preguntas/frameworks/api/schemas.py` | `MateriaListItemResponse` (id, nombre, banco_id, cantidad_preguntas_activas) |
| `frontend/src/lib/banco-preguntas-api.ts` | Agregar `listarMaterias()` (excluida de `US-2.1.8` por este gap) |
| `frontend/src/pages/Materias.tsx` | Grilla de materias, tarjeta "Nueva materia" |
| `frontend/src/pages/NuevaMateria.tsx` | Formulario de alta — campo nombre, validación inline de duplicado |
| `frontend/src/router.tsx` | Reemplazar el placeholder de `/materias` por las pantallas reales |

---

## Referencias

- Relacionada con: `US-2.1.1` (backend original), `US-2.1.7` (patrón de `filtrar()`
  reutilizado para el conteo), `US-2.1.8` (infraestructura, precondición; gap de
  `GET /materias` detectado ahí)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md` §Iteración 1 — Frontend

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
