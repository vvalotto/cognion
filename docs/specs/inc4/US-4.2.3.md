# US-4.2.3: PreguntaMetadatoConsultaPort hacia Banco de Preguntas

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.2`
**Tipo**: `feat backend` (técnica)
**Agregado principal afectado**: — (consulta de solo lectura, sin comando ni evento)
**Bounded Context**: Analytics (consumidor) — Banco de Preguntas (dato ya existente)

---

## Descripcion (lenguaje de negocio)

Como **sistema (Analytics)**,
quiero **conocer la unidad temática y el tema de cada pregunta respondida**
para **poder agregar la tasa de error por tema que pide el Docente (RF-17)**.

---

## Contexto del dominio

### Problema

El dato ya existe — `PreguntaPlantilla.unidad_tematica`/`.tema`, expuesto como
`MetadatosPregunta` desde `US-ADJ-17`. Falta el contrato propio de Analytics para leerlo sin
importar código de `src/banco_preguntas/` directamente (`BC-analytics-modelo.md` §5).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Port (nuevo, Analytics) | `PreguntaMetadatoConsultaPort` | Único método: `obtener_metadatos(pregunta_ids: list[UUID]) -> dict[UUID, MetadatoPreguntaResumen]` |
| DTO (nuevo, Analytics) | `MetadatoPreguntaResumen` | `unidad_tematica`, `tema` — copia propia de Analytics, no reexporta `MetadatosPregunta` de Banco de Preguntas |
| Adapter (nuevo, Analytics) | adapter in-process | Consulta `pregunta_plantilla` (o el repositorio de Banco de Preguntas que ya expone `MetadatosPregunta`) por lote de `pregunta_ids`, sin N+1 |

---

## Especificacion del comportamiento

### Precondicion

- `pregunta_ids` es una lista de UUIDs, puede estar vacía.

### Postcondicion

- `pregunta_ids` con preguntas existentes (activas o eliminadas — el metadato no depende del
  estado `activa`, `US-4.2.4` necesita agregar también respuestas de preguntas ya eliminadas
  del banco) → `dict` con una entrada por cada `pregunta_id` encontrado.
- `pregunta_ids` con algún id que no existe en `pregunta_plantilla` → esa clave simplemente no
  aparece en el `dict` resultado (no lanza error) — quien consume decide qué hacer con
  metadatos faltantes (`US-4.2.4` los excluye del agregado por tema).
- `pregunta_ids` vacía → `dict` vacío, sin consultar la base.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Analytics nunca importa código de `src/banco_preguntas/` directamente — `PreguntaMetadatoConsultaPort` es el único punto de acceso. |
| — | Una sola consulta por lote (`WHERE id IN (...)`), no una consulta por `pregunta_id` — evita N+1 al procesar todas las respuestas de una materia. |

---

## Criterios de aceptacion

```gherkin
Feature: Consulta de metadatos de pregunta para Analytics (US-4.2.3)

  Scenario: Lote de preguntas existentes
    Given 3 preguntas con unidad_tematica/tema distintos
    When PreguntaMetadatoConsultaPort.obtener_metadatos([id1, id2, id3]) se invoca
    Then devuelve un dict con las 3 entradas, cada una con su unidad_tematica/tema correcto

  Scenario: Lote con un id inexistente
    Given 2 preguntas existentes y 1 id que no corresponde a ninguna
    When se invoca obtener_metadatos con los 3 ids
    Then el dict resultado tiene 2 entradas, sin lanzar error por el id faltante

  Scenario: Lote vacío
    When se invoca obtener_metadatos([])
    Then devuelve un dict vacío
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — mismo patrón de adapter in-process ya usado en el proyecto (`MateriaPort`,
  `EvaluacionDesempenoConsultaPort` de `US-4.1.1`), sin ADR nuevo.

**Capa(s) afectadas:**
- [x] Entities (Analytics) — `PreguntaMetadatoConsultaPort` (nuevo), `MetadatoPreguntaResumen` (DTO)
- [ ] Use Cases — sin cambios (se consume directo desde `ObtenerTasaErrorPorTemaUseCase`, `US-4.2.4`)
- [ ] Interface Adapters — sin cambios
- [x] Frameworks (Analytics) — adapter in-process, cableado en `dependencies.py`
- [ ] Frontend — no aplica a esta US

---

## Fuente de verdad UX

No aplica a esta US — infraestructura de consulta pura, sin pantalla propia.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/analytics/entities/ports/pregunta_metadato_consulta_port.py` | Nuevo — `PreguntaMetadatoConsultaPort`, `MetadatoPreguntaResumen` |
| `src/analytics/frameworks/adapters/pregunta_metadato_consulta_port_in_process.py` | Nuevo |
| `tests/unit/inc4/` | Tests del port/adapter (lote completo, id faltante, lote vacío) |

---

## Referencias

- Modelo de dominio: `docs/design/domain/BC-analytics-modelo.md` §5
- Reutiliza: `MetadatosPregunta` (`US-ADJ-17`)
- Sin dependencia de otra US de esta iteración — junto con `US-4.2.2`, desbloquea `US-4.2.4`
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 2
- Issue: #242

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
