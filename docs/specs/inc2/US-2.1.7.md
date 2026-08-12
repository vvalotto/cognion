# US-2.1.7: Docente filtra el banco por materia, unidad, tema, dificultad e importancia

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-2.1`
**Tipo**: `feat backend`
**Agregado principal afectado**: `PreguntaPlantilla` (read model)
**Bounded Context**: Banco de Preguntas

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **filtrar el banco de una materia por cualquier combinación de unidad temática, tema,
dificultad e importancia**
para **encontrar rápidamente las preguntas que necesito al armar una sesión (RF-06)**.

---

## Contexto del dominio

### Problema

Es la única pieza de la Iteración 1 que es una query pura, sin comando ni evento de dominio
(`BC-banco-preguntas-modelo.md` §3). Depende de que existan preguntas cargadas
(`US-2.1.3`/`US-2.1.4`) para tener sentido, pero funcionalmente no depende de ellas — un banco
vacío devuelve lista vacía.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Query | `FiltrarBanco(materia_id, unidad?, tema?, dificultad?, importancia?)` | Lee `PreguntaPlantilla` activas de la materia, aplica los filtros provistos |

---

## Especificacion del comportamiento

### Precondicion

- Actor autenticado con JWT válido y claim `rol = docente`.
- `materia_id` corresponde a una `Materia` existente.

### Postcondicion

- Lista de `PreguntaPlantilla` con `activa = true` que matchean **todos** los filtros
  provistos (AND, no OR) — los filtros omitidos no restringen el resultado.
- Sin filtros más allá de `materia_id`: devuelve todas las preguntas activas de esa materia.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Solo se devuelven preguntas con `activa = true` — nunca aparecen las dadas de baja (`US-2.1.6`). |
| — | Los filtros son combinables y opcionales — cualquier subconjunto de `{unidad, tema, dificultad, importancia}` es válido, incluido el conjunto vacío. |

---

## Criterios de aceptacion

```gherkin
Feature: Filtrado del banco de preguntas (US-2.1.7)

  Scenario: Filtro combinado por dificultad e importancia
    Given un Banco con preguntas de distinta dificultad e importancia
    When un Docente ejecuta FiltrarBanco(materia_id, dificultad="Alto", importancia="Alto")
    Then el sistema devuelve solo las preguntas activas que matchean ambos filtros

  Scenario: Sin filtros adicionales
    Given un Banco con 5 preguntas activas y 1 inactiva
    When un Docente ejecuta FiltrarBanco(materia_id) sin más filtros
    Then el sistema devuelve las 5 preguntas activas
    And no incluye la pregunta inactiva

  Scenario: Ningún resultado
    Given un Banco sin preguntas de dificultad "Bajo"
    When un Docente ejecuta FiltrarBanco(materia_id, dificultad="Bajo")
    Then el sistema devuelve una lista vacía
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — query CRUD estándar sobre el modelo ya persistido.

**Capa(s) afectadas:**
- [x] Use Cases — `FiltrarBancoUseCase` (o método de consulta directo, sin comando de dominio)
- [x] Interface Adapters — controller, `PreguntaRepositoryPort.filtrar(...)`
- [x] Frameworks — endpoint FastAPI `GET /bancos/{id}/preguntas?unidad=&tema=&dificultad=&importancia=`
- [ ] Frontend — cubierto por `US-2.1.10`

---

## Fuente de verdad UX

No aplica a esta spec (backend puro) — la pantalla correspondiente (`#banco`) se especifica en
`US-2.1.10`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/ports/pregunta_repository_port.py` | Método `filtrar(materia_id, unidad, tema, dificultad, importancia)` |
| `src/banco_preguntas/use_cases/filtrar_banco.py` | Orquesta la consulta |
| `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` | Mapeo de query params |
| `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` | Implementación SQLAlchemy del filtro (`WHERE activa = true AND ...`) |
| `src/banco_preguntas/frameworks/api/preguntas_router.py` | `GET /bancos/{id}/preguntas` |

---

## Referencias

- Relacionada con: `US-2.1.3`, `US-2.1.4` (proveen los datos a filtrar), `US-2.1.6` (excluye inactivas)
- Modelo de dominio: `docs/design/domain/BC-banco-preguntas-modelo.md` (§3, query `FiltrarBanco`)
- Candidatas: `docs/plans/inc2/inc2-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
