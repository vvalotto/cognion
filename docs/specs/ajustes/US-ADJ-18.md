# US-ADJ-18: Refactor `SQLAlchemyPreguntaRepository` (Feature Envy/Ley de Demeter/Long Method)

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica`
**Tipo**: `refactor backend` (sin cambio de comportamiento observable)
**Agregado principal afectado**: ninguno de dominio — solo el gateway de persistencia
**Bounded Context**: Banco de Preguntas
**Origen**: `DesignReviewer src/` (revisión de esta sesión) — el archivo con más issues
concentrados del proyecto (15/159).

---

## Descripcion (lenguaje de negocio)

Como **desarrollador del proyecto**,
quiero **que `SQLAlchemyPreguntaRepository` deje de tener métodos de más de 20 líneas con
cadenas de acceso de profundidad 2**
para **que el archivo con más deuda técnica concentrada del proyecto (15 issues) sea legible y
mantenible al agregar un tercer tipo de pregunta en el futuro (RF-07, Incremento 7)**.

---

## Contexto del dominio

### Problema

`DesignReviewer src/` reporta en `pregunta_repository.py`:

- **`FeatureEnvyAnalyzer`** (3 issues): `guardar` accede 20 veces a `pregunta` vs 2 a `self`;
  `_a_entidad` accede 21 veces a `modelo` vs 0 a `self`; `actualizar` accede 9 veces a
  `pregunta` vs 2 a `self`. Los 3 métodos tienen un `if isinstance(...)/else` que arma el
  objeto destino (modelo o entidad) campo por campo, distinto según el tipo concreto de
  pregunta — la lógica vive en el repositorio en vez de en un mapeador dedicado por tipo.
- **`LongMethodAnalyzer`** (4 issues): `guardar` (40 líneas), `filtrar` (42), `_a_entidad`
  (33), `actualizar` (23) — los 4 por encima del umbral de 20, todos por el mismo patrón de
  branching por tipo.
- **`LawOfDemeterAnalyzer`** (6 issues): `pregunta.dificultad.value`/`pregunta.importancia.value`
  (profundidad 2) repetidos en `guardar` (líneas 48-49, 66-67) y `actualizar` (líneas 172-173);
  `PreguntaPlantillaModel.activa.is_` en `filtrar` (línea 101, caso distinto — comparación
  SQLAlchemy, no aplica el mismo fix).
- **`LongParameterListAnalyzer`** (1 issue): `filtrar` con 7 parámetros (ya conocido, ver nota
  abajo).

### Alcance del fix

1. **Extraer un mapeador privado por tipo concreto** para `guardar`/`actualizar`/`_a_entidad`:
   `_modelo_desde_verdadero_falso(pregunta) -> PreguntaPlantillaModel`,
   `_modelo_desde_opcion_multiple(pregunta) -> PreguntaPlantillaModel`, y sus inversos
   `_entidad_desde_modelo_verdadero_falso`/`_entidad_desde_modelo_opcion_multiple` — cada
   `if isinstance(...)` pasa a llamar al método correspondiente en vez de armar el objeto
   inline. Reduce las 4 violaciones de `LongMethodAnalyzer` (cada método resultante queda corto)
   y las 3 de `FeatureEnvyAnalyzer` (el acceso "envidioso" queda en un método cuyo único
   propósito es leer el objeto origen, lo cual dejaría de ser señalado como tal una vez que
   `guardar`/`actualizar` en sí mismos ya no concentran ese acceso).
2. **Resolver la Ley de Demeter de `dificultad`/`importancia`**: agregar una property de solo
   lectura en `PreguntaPlantillaOpcionMultiple`/`PreguntaPlantillaVerdaderoFalso` — o, si
   `US-ADJ-17` ya introdujo `MetadatosPregunta`, en ese Value Object — que exponga
   `dificultad_valor`/`importancia_valor` (los `.value` ya resueltos), para que el repositorio
   escriba `pregunta.dificultad_valor` (profundidad 1) en vez de `pregunta.dificultad.value`
   (profundidad 2). Alternativa equivalente: que `MetadatosPregunta` (`US-ADJ-17`) exponga estos
   valores directamente si esta US se implementa después de esa.
3. **`filtrar` con 7 parámetros**: fuera de alcance de este refactor puntual — ya está cubierto
   conceptualmente por el mismo patrón de Value Object que `US-ADJ-17` (un futuro
   `FiltroBanco` agruparía los parámetros opcionales de filtrado), pero esta US no lo
   implementa — se deja anotado como posible continuación, no como parte del criterio de
   aceptación de esta US.

**Depende de `US-ADJ-17`** solo para el punto 2 si se decide exponer la property en
`MetadatosPregunta` en vez de en cada entidad — a resolver al implementar, según cuál de las
dos ya esté mergeada.

---

## Especificacion del comportamiento

### Precondicion

- `guardar`/`actualizar`/`_a_entidad` de `SQLAlchemyPreguntaRepository` arman el objeto destino
  inline dentro de un `if isinstance(...)/else`, por encima del umbral de líneas.
- `pregunta.dificultad.value`/`pregunta.importancia.value` accedidos como cadena de profundidad
  2 en 3 lugares.

### Postcondicion

- `guardar`/`actualizar`/`_a_entidad` delegan el armado del objeto destino a un mapeador privado
  por tipo concreto — cada método resultante queda por debajo de 20 líneas.
- El repositorio accede a `dificultad`/`importancia` con profundidad 1 (vía property nueva),
  sin cadenas `.dificultad.value`/`.importancia.value`.
- Ningún test de integración de `banco_preguntas` cambia su aserción — el comportamiento
  persistido es idéntico (mismas columnas, mismos valores).
- `DesignReviewer src/` corrido de nuevo: `pregunta_repository.py` baja de 15 a ≤ 2 issues
  (el de `filtrar`/7 parámetros queda, fuera de alcance de esta US).

### Invariantes

Ninguna invariante de dominio nueva — refactor de la capa de persistencia, sin tocar
`entities`/`use_cases` salvo la property nueva (getter puro, sin efectos secundarios).

---

## Criterios de aceptacion

```gherkin
Feature: SQLAlchemyPreguntaRepository refactorizado (US-ADJ-18)

  Scenario: Guardar y leer una pregunta de cada tipo sigue funcionando igual
    Given una PreguntaPlantillaOpcionMultiple y una PreguntaPlantillaVerdaderoFalso válidas
    When se guardan y luego se recuperan vía el repositorio
    Then los datos recuperados son idénticos a los guardados, mismo comportamiento que antes
      del refactor

  Scenario: DesignReviewer confirma la reducción de issues
    Given el refactor aplicado a pregunta_repository.py
    When se corre designreviewer src/ --config pyproject.toml
    Then pregunta_repository.py no aparece con issues de LongMethodAnalyzer ni
      FeatureEnvyAnalyzer, y las 6 violaciones de LawOfDemeterAnalyzer sobre
      dificultad/importancia desaparecen
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — refactor interno de un gateway ya existente, sin cambio de contrato de
      `PreguntaRepositoryPort` ni de schema de base de datos.

**Capa(s) afectadas:**
- [x] Backend — `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py`,
      property nueva en `entities/pregunta_plantilla.py` (o `MetadatosPregunta` si
      `US-ADJ-17` ya existe)
- [ ] Frontend — sin cambios

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/banco_preguntas/interface_adapters/gateways/pregunta_repository.py` | Mapeadores privados por tipo concreto en `guardar`/`actualizar`/`_a_entidad` |
| `src/banco_preguntas/entities/pregunta_plantilla.py` (o `MetadatosPregunta` de `US-ADJ-17`) | Property `dificultad_valor`/`importancia_valor` |
| Tests de integración de `banco_preguntas` afectados | Sin cambio de aserciones, solo confirmar que siguen en verde |

---

## Referencias

- Relacionada con: `US-ADJ-17` (mismo cluster de `DesignReviewer`, posible dependencia sobre
  dónde vive la property de valores resueltos)
- Detectada durante: revisión de `DesignReviewer src/` en la sesión de cierre de `BL-004`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
