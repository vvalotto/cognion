# US-ADJ-13: Documentar "Zone of Pain" de ArchitectAnalyst como falso positivo aceptado

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica` (no planificado originalmente,
ver `docs/plans/inc3-adj/inc3-adj-candidatas.md`)
**Tipo**: `documentación + config` (sin cambios de código)
**Agregado principal afectado**: ninguno — no toca dominio
**Bounded Context**: ninguno — transversal (herramienta de calidad)
**Origen**: retro de `BL-002` (2026-07-29), `BL-003` (2026-08-23) y `BL-004` (2026-09-02),
las tres señalando el mismo hallazgo sin resolverlo. Investigación de esta sesión
(`inc3-adj-candidatas.md` §"Investigación previa").

---

## Descripcion (lenguaje de negocio)

Como **responsable del proceso de calidad del proyecto**,
quiero **dejar de ver el mismo "falso positivo" de ArchitectAnalyst señalado sin acción en tres
baselines consecutivas**
para **que el reporte de cierre de cada incremento distinga ruido conocido de señales nuevas
genuinas**.

---

## Contexto del dominio

### Problema

`architectanalyst src/ --sprint-id BL-00N` reporta 5 críticos "Zone of Pain"
(`DistanceAnalyzer`, D > 0.5) en `identidad`, `settings`, `shared`, `banco_preguntas` y
`actividad_evaluativa` — uno por cada BC/paquete raíz del proyecto, desde que existen. La retro
de `BL-002` propuso "recalibrar los umbrales"; `BL-003` repitió la misma nota sin aplicarla;
`BL-004` la repitió otra vez con un 5to módulo nuevo.

**Investigación de esta sesión (2026-09-02):** se probó la recalibración más obvia,
`analysis_depth=2` (parámetro real de la herramienta, pensado para "arquitecturas hexagonales
con namespace de app" según su propio docstring). Resultado contra `src/` real: los críticos
**subieron de 5 a 15** — con depth=2 cada BC se parte en
`entities`/`use_cases`/`interface_adapters`/`frameworks`, y las tres últimas capas de cada BC no
tienen ninguna clase abstracta (los 18 puertos `ABC` del proyecto viven solo en
`entities/ports/`), así que cada una da D=1.00 CRITICAL por separado en vez de diluirse en el
promedio del paquete raíz.

**Causa raíz real:** no faltan abstracciones (los puertos ya están correctamente declarados
`ABC` en los 3 BCs). El problema es estructural: `DistanceAnalyzer` mide
`D = |Abstractness + Instability - 1|`, y cada BC de este proyecto es una hoja del grafo de
dependencias por diseño (`Ca=0` siempre — la regla "sin imports directos entre BCs" garantiza
que nada más importe un BC concreto), lo que fija `Instability≈0`. Como los puertos abstractos
son una minoría chica frente al resto del código concreto de cada BC (`entities`, `use_cases`,
controllers, modelos SQLAlchemy), `Abstractness` también es bajo. Ninguna granularidad de
análisis cambia esa proporción — es inherente a una arquitectura de BCs verticales con puertos,
no un defecto de diseño real.

Tampoco existe en la herramienta una forma de silenciar el chequeo *solo* para estos 5
paquetes — la única perilla es `[tool.architectanalyst.checks]` (`distance`/`god_package`/
`relational_cohesion` = `true`/`false`), que es todo o nada para el proyecto completo, y
apagarla perdería la señal si algún día aparece un God Package genuino en un módulo transversal.

### Alcance del fix

**Decisión (confirmada con Víctor, 2026-09-02): aceptar como falso positivo permanente, sin
tocar la config real de `[tool.architectanalyst]`** (`analysis_depth` queda en su default,
`checks.*` quedan todos en `true`). Se documenta explícitamente para que:

1. Ninguna retro futura vuelva a proponer "recalibrar" sin revisar antes esta spec.
2. El reporte de cierre de cada baseline cite este documento en vez de repetir el análisis.

Además, se aprovecha para **corregir dos claves inválidas** detectadas en
`[tool.architectanalyst]` de `pyproject.toml` — no relacionadas con el falso positivo en sí,
pero descubiertas en la misma investigación: `paths = ["src"]` y
`history_db = "quality/reports/architectanalyst/history.db"` no son campos reconocidos por
`ArchitectAnalystConfig` (el campo real es `db_path`, y `paths` no existe — el CLI ya recibe el
path por argumento posicional). Cada corrida de `architectanalyst` emite
`[tool.architectanalyst] clave desconocida ignorada: '...'` por cada una, sin que nadie lo haya
corregido en 3 baselines.

---

## Especificacion del comportamiento

### Precondicion

- `pyproject.toml` tiene `[tool.architectanalyst]` con `paths`/`history_db` (claves inválidas,
  ignoradas silenciosamente con warning).
- `CLAUDE.md` no documenta el "Zone of Pain" como aceptado — cada baseline lo redescubre.

### Postcondicion

- `pyproject.toml`: `paths` eliminado (el CLI ya recibe `src/` por argumento); `history_db`
  renombrado a `db_path` (campo real, mismo valor).
- `architectanalyst src/ --config pyproject.toml` ya no emite ningún warning de "clave
  desconocida ignorada".
- `CLAUDE.md` (sección de quality gates o notas operativas) documenta: los 5 críticos "Zone of
  Pain" de paquete raíz de BC (`identidad`, `settings`, `shared`, `banco_preguntas`,
  `actividad_evaluativa`) son un falso positivo aceptado permanentemente, con referencia a esta
  spec y a la investigación que descarta la recalibración por profundidad.

### Invariantes

Ninguna — no hay cambio de dominio.

---

## Criterios de aceptacion

```gherkin
Feature: Zone of Pain documentado como falso positivo aceptado (US-ADJ-13)

  Scenario: pyproject.toml sin claves inválidas
    Given pyproject.toml antes de este fix tenía paths/history_db en [tool.architectanalyst]
    When se corre architectanalyst src/ --config pyproject.toml
    Then no aparece ningún warning "clave desconocida ignorada"

  Scenario: CLAUDE.md documenta el falso positivo aceptado
    Given un lector de CLAUDE.md llega a la sección de quality gates
    When busca "Zone of Pain" o "ArchitectAnalyst"
    Then encuentra la explicación de por qué los 5 críticos de paquete raíz son aceptados,
      y por qué analysis_depth no es la solución
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — es documentación + corrección de config inválida, sin cambio de comportamiento real
      (las claves corregidas nunca tuvieron efecto).

**Capa(s) afectadas:**
- [ ] Backend — sin cambios de código
- [ ] Frontend — sin cambios
- [x] Documentación/config — `CLAUDE.md`, `pyproject.toml`

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `pyproject.toml` | `[tool.architectanalyst]`: eliminar `paths`, renombrar `history_db` → `db_path` |
| `CLAUDE.md` | Nota en quality gates: Zone of Pain aceptado permanentemente, referencia a esta spec |

---

## Referencias

- Relacionada con: retro `BL-002`/`BL-003`/`BL-004`, `US-ADJ-15` (mismo archivo de config,
  otro campo), `US-ADJ-19` (mismo archivo de config, otro analyzer con problema distinto)
- Detectada durante: sesión de cierre de `BL-004` + planificación de `Incremento 3-ADJ`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
