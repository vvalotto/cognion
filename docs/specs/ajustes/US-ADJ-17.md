# US-ADJ-17: Value Object `MetadatosPregunta` (Data Clump/Primitive Obsession, Banco de Preguntas)

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica`
**Tipo**: `refactor backend` (sin cambio de comportamiento observable ni de contrato HTTP)
**Agregado principal afectado**: `PreguntaPlantillaOpcionMultiple`, `PreguntaPlantillaVerdaderoFalso`
**Bounded Context**: Banco de Preguntas
**Origen**: `DesignReviewer src/` (revisión de esta sesión) — 3 archivos concentran 41/159
warnings (26% del total) con la misma causa raíz.

---

## Descripcion (lenguaje de negocio)

Como **desarrollador del proyecto**,
quiero **agrupar los 5 campos de metadatos de una pregunta (`texto`, `unidad_tematica`, `tema`,
`dificultad`, `importancia`) en un único Value Object**
para **eliminar el Data Clump que hoy se repite idéntico en `entities`, `use_cases` y
`interface_adapters` del Banco de Preguntas, y que `DesignReviewer` señala en 3 archivos
distintos**.

---

## Contexto del dominio

### Problema

`DesignReviewer src/` detecta el mismo `DataClumpsAnalyzer`/`PrimitiveObsessionAnalyzer` en:

- `entities/pregunta_plantilla.py` (14 issues): `crear`/`editar` de ambos tipos de pregunta
  reciben `{texto, unidad_tematica, tema, dificultad, importancia}` como 5 parámetros sueltos
  (más `respuesta_correcta`/`opciones` según el tipo).
- `interface_adapters/controllers/preguntas_controller.py` (12 issues): los 3 métodos de carga
  y edición reciben el mismo conjunto de parámetros y los reenvían sin transformar al use case.
- `interface_adapters/gateways/pregunta_repository.py` (15 issues, parcialmente — el resto es
  `US-ADJ-18`): `guardar`/`actualizar` acceden a `pregunta.dificultad.value`/
  `pregunta.importancia.value` como cadenas de profundidad 2 (Ley de Demeter) porque no hay un
  objeto intermedio que exponga esos valores ya resueltos.

`PrimitiveObsessionAnalyzer` señala específicamente los 3 parámetros `str`
(`texto`, `unidad_tematica`, `tema`) como candidatos a Value Object en 6 métodos distintos (3
por cada tipo de pregunta, mismo patrón). `DataClumpsAnalyzer` confirma que el conjunto completo
de 5-6 campos aparece junto en `crear`/`editar` de ambos tipos y en el controller.

### Alcance del fix

Introducir `MetadatosPregunta` (Value Object, `dataclass(frozen=True)` en
`entities/pregunta_plantilla.py` o un módulo propio `entities/metadatos_pregunta.py`) con
`texto: str`, `unidad_tematica: str`, `tema: str`, `dificultad: Dificultad`,
`importancia: Importancia`. Reemplaza esos 5 parámetros sueltos por un único parámetro
`metadatos: MetadatosPregunta` en:

- `PreguntaPlantillaOpcionMultiple.crear`/`.editar`, `PreguntaPlantillaVerdaderoFalso.crear`/`.editar`
- Los 4 Use Case de carga/edición (`CargarPreguntaOpcionMultipleUseCase`,
  `CargarPreguntaVerdaderoFalsoUseCase`, `EditarPreguntaUseCase` — verificar si hay uno o dos)
- `PreguntasController` (los 3 métodos listados arriba)

**Fuera de alcance de esta US:** la persistencia (`SQLAlchemyPreguntaRepository`) sigue
guardando columnas individuales en la tabla `pregunta_plantilla` — no hay migración de schema.
El repositorio arma/desarma `MetadatosPregunta` al mapear entidad↔modelo, lo que reduce (pero no
elimina del todo) sus propios issues — la limpieza completa del repositorio es `US-ADJ-18`.

Los schemas Pydantic de la API (`CargarPreguntaOpcionMultipleRequest`, etc.) **no cambian** — el
JSON de request/response sigue siendo el mismo (5 campos sueltos), evitando romper el contrato
HTTP y el frontend. El Value Object se arma en el controller, a partir de los campos del schema,
antes de invocar el Use Case.

---

## Especificacion del comportamiento

### Precondicion

- `PreguntaPlantillaOpcionMultiple.crear`/`.editar` y `PreguntaPlantillaVerdaderoFalso.crear`/
  `.editar` reciben 5 parámetros de metadatos sueltos.
- `PreguntasController` reenvía los mismos 5 parámetros sueltos a los Use Case.

### Postcondicion

- Ambas entidades y sus Use Case reciben `metadatos: MetadatosPregunta` en vez de 5 parámetros
  sueltos.
- `PreguntasController` arma `MetadatosPregunta` desde el body del request (schema sin cambios)
  antes de invocar el Use Case.
- El comportamiento observable no cambia: mismos endpoints, mismos request/response JSON,
  mismas invariantes (INV-BP-02/03 sobre `opciones`, sin invariantes adicionales sobre
  `respuesta_correcta`).
- `DesignReviewer src/` corrido de nuevo: los issues de `PrimitiveObsessionAnalyzer`/
  `DataClumpsAnalyzer` en `pregunta_plantilla.py` y `preguntas_controller.py` bajan a 0.

### Invariantes

Ninguna invariante de dominio nueva — `MetadatosPregunta` es un agrupador estructural, no
agrega validación propia (las validaciones existentes, si las hay sobre estos campos, se
mantienen donde están).

---

## Criterios de aceptacion

```gherkin
Feature: Value Object MetadatosPregunta reemplaza el Data Clump (US-ADJ-17)

  Scenario: Cargar una pregunta de opción múltiple sigue funcionando igual
    Given un request válido a POST /preguntas/opcion-multiple (mismo JSON que antes)
    When el controller arma MetadatosPregunta y llama al Use Case
    Then la pregunta se crea igual que antes del refactor, mismo response JSON

  Scenario: Editar una pregunta sigue funcionando igual
    Given un request válido a PUT /preguntas/{id}
    When el controller arma MetadatosPregunta y llama al Use Case
    Then la pregunta se edita igual que antes del refactor, mismo response JSON

  Scenario: DesignReviewer confirma la reducción de issues
    Given el refactor aplicado a entities/use_cases/controller
    When se corre designreviewer src/ --config pyproject.toml
    Then pregunta_plantilla.py y preguntas_controller.py no aparecen con issues de
      PrimitiveObsessionAnalyzer ni DataClumpsAnalyzer
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — Value Object dentro de una capa `entities` ya existente, sin cambio de contrato de
      API ni de schema de base de datos.

**Capa(s) afectadas:**
- [x] Backend — `src/banco_preguntas/entities/`, `use_cases/`, `interface_adapters/controllers/`
- [ ] Frontend — sin cambios (contrato HTTP idéntico)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/entities/pregunta_plantilla.py` (o módulo nuevo `metadatos_pregunta.py`) | `MetadatosPregunta` nuevo; `crear`/`editar` de ambos tipos reciben `metadatos` en vez de 5 parámetros |
| `src/banco_preguntas/use_cases/cargar_pregunta_opcion_multiple.py`, `cargar_pregunta_verdadero_falso.py`, `editar_pregunta.py` | Reciben/propagan `MetadatosPregunta` |
| `src/banco_preguntas/interface_adapters/controllers/preguntas_controller.py` | Arma `MetadatosPregunta` desde el schema antes de invocar el Use Case |
| `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` | Ajustado para desarmar/armar `MetadatosPregunta` al mapear con el modelo SQLAlchemy (sin cambio de columnas) |
| Tests unitarios/integración de `banco_preguntas` afectados | Actualizados a la nueva firma |

---

## Referencias

- Relacionada con: `US-ADJ-18` (mismo cluster de `DesignReviewer`, otro analyzer sobre el
  mismo archivo de gateway)
- Detectada durante: revisión de `DesignReviewer src/` en la sesión de cierre de `BL-004`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
