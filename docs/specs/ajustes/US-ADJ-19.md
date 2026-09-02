# US-ADJ-19: `LayerViolationsAnalyzer` no detecta ninguna violación bajo ninguna configuración

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica`
**Tipo**: `documentación + Issue upstream` (sin fix propio — el bug está en la herramienta,
no en este repo)
**Agregado principal afectado**: ninguno
**Bounded Context**: ninguno — transversal (herramienta de calidad)
**Origen**: investigación de esta sesión al revisar `[tool.architectanalyst.layers]` mientras
se armaba `US-ADJ-13`.

---

## Descripcion (lenguaje de negocio)

Como **responsable del proceso de calidad**,
quiero **saber si el chequeo "siempre CRITICAL, no configurable" de violaciones de capas
realmente funciona**
para **no confiar en una señal de calidad que en los hechos nunca se dispara, y decidir con
conocimiento si vale la pena seguir dependiendo de ella**.

---

## Contexto del dominio

### Problema

`LayerViolationsAnalyzer` (`quality_agents.architectanalyst.metrics.layer_violations_analyzer`)
se documenta como el único chequeo de `ArchitectAnalyst` que es "siempre CRITICAL, threshold=0,
no configurable" cuando detecta un import que viola la dirección de dependencias declarada en
`[tool.architectanalyst.layers]`.

**Hallazgo 1 — config actual mal formada.** `pyproject.toml` tiene:

```toml
[tool.architectanalyst.layers]
entities = ["src/*/entities"]
use_cases = ["src/*/use_cases"]
interface_adapters = ["src/*/interface_adapters"]
frameworks = ["src/*/frameworks"]
```

El schema real (`LayersConfig.rules: Dict[str, List[str]]`) espera **nombre de capa → lista de
nombres de capa permitidos** (ej. `entities = []`, `use_cases = ["entities"]`), no globs de
rutas de archivo. La config actual no tiene sentido para el analizador — cada valor debería ser
un nombre de capa (`"entities"`, `"use_cases"`, etc.), no un patrón de ruta.

**Hallazgo 2 — corregido el formato, sigue sin detectar nada.** Se probó
`entities = []`, `use_cases = ["entities"]`, `interface_adapters = ["use_cases", "entities"]`,
`frameworks = ["interface_adapters", "use_cases", "entities"]` (el formato exacto del ejemplo
del propio docstring de la herramienta) contra `src/` real: **0 resultados** de
`LayerViolationsAnalyzer`, ni violaciones ni ninguna otra señal.

**Hallazgo 3 — se descartó "el proyecto está limpio" con una regla imposible.** Se forzó
`frameworks = []` (prohibiendo que la capa `frameworks` dependa de cualquier otra) — en los
hechos, todo `frameworks/dependencies.py` de cada BC importa `use_cases`/`entities` para armar
el composition root, así que con esa regla **tendría que haber decenas de violaciones**.
Resultado: **seguía en 0**. Esto descarta que el proyecto simplemente no tenga violaciones —
confirma que el analizador no está detectando ningún edge de dependencia entre capas bajo
ninguna configuración probada, ni siquiera una diseñada para fallar.

### Alcance

No se investigó la causa raíz dentro del código de `quality_agents` (fuera de un análisis
puntual de esta sesión) — podría ser un problema de cómo `DependencyGraphBuilder` resuelve
nombres de módulo dotted en este layout de proyecto (`src.<bc>.<capa>.<modulo>`), o un bug en
`_find_layer`. No se intenta un fix local: es una herramienta externa
(`.venv/lib/.../quality_agents/`), mismo criterio que los 2 bugs ya reportados este incremento
(`vvalotto/software_limpio#70`, `#71` — timeout de mypy sin cache, reportes parciales de
CodeGuard).

**Consecuencia inmediata:** el gate de "Cierre de Baseline: ArchitectAnalyst (Siempre manual)"
de `CLAUDE.md` no puede seguir asumiendo que la ausencia de resultados de
`LayerViolationsAnalyzer` significa "sin violaciones de capas" — significa "el chequeo no
corrió efectivamente". La regla de imports entre capas (`CLAUDE.md`, "Arquitectura interna —
reglas no negociables") sigue enforced por revisión de código humana/asistida, no por esta
herramienta.

---

## Especificacion del comportamiento

### Precondicion

- `[tool.architectanalyst.layers]` mal configurado (globs en vez de nombres de capa).
- Nadie sabe que `LayerViolationsAnalyzer` no detecta nada — se asumía "sin violaciones".

### Postcondicion

- Issue abierto en `vvalotto/software_limpio` (mismo repo que `#70`/`#71`) describiendo la
  reproducción exacta (config con regla imposible de cumplir, 0 resultados).
- `CLAUDE.md` documenta: `LayerViolationsAnalyzer` no es una fuente de verdad confiable
  actualmente — la regla de imports entre capas se sostiene por revisión de código, no por este
  chequeo automatizado, hasta que el bug se resuelva upstream.
- `[tool.architectanalyst.layers]` se corrige al formato documentado (nombres de capa, no
  globs) — aunque no detecte nada hoy, deja la config lista para cuando se resuelva el bug
  upstream, y evita que alguien la "arregle" de nuevo hacia el formato incorrecto por
  desconocimiento.

### Invariantes

Ninguna — no hay cambio de dominio ni de código propio del proyecto.

---

## Criterios de aceptacion

```gherkin
Feature: LayerViolationsAnalyzer documentado como no confiable (US-ADJ-19)

  Scenario: Issue upstream reproducible
    Given una regla de capas imposible de cumplir (frameworks = [])
    When se corre architectanalyst src/ --config pyproject.toml
    Then LayerViolationsAnalyzer reporta 0 resultados
    And el Issue en software_limpio documenta esta reproducción exacta

  Scenario: CLAUDE.md no asume falsamente "sin violaciones"
    Given un lector de CLAUDE.md llega a la sección de quality gates de cierre de baseline
    When busca qué certifica la ausencia de resultados de LayerViolationsAnalyzer
    Then encuentra que el chequeo no es confiable actualmente, con el Issue de referencia
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — no cambia ninguna regla de arquitectura del proyecto, solo corrige la confianza
      depositada en una herramienta de verificación externa.

**Capa(s) afectadas:**
- [x] Documentación/config — `CLAUDE.md`, `pyproject.toml` (formato de `[tool.architectanalyst.layers]`)

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `pyproject.toml` | `[tool.architectanalyst.layers]`: corregir al formato nombre-de-capa (aunque no detecte nada hoy) |
| `CLAUDE.md` | Nota: `LayerViolationsAnalyzer` no confiable, regla de imports sostenida por revisión de código; referencia al Issue upstream |
| Issue en `vvalotto/software_limpio` | Reporte del bug, con reproducción exacta |

---

## Referencias

- Relacionada con: `US-ADJ-13` (mismo archivo de config, otro analyzer), `vvalotto/software_limpio#70`/`#71` (mismo patrón de bug de herramienta reportado upstream este incremento)
- Detectada durante: sesión de cierre de `BL-004` + planificación de `Incremento 3-ADJ`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
