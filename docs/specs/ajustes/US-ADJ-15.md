# US-ADJ-15: Fix de `coverage_report_path` en `[tool.architectanalyst]`

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica`
**Tipo**: `config` (una línea, verificada)
**Agregado principal afectado**: ninguno
**Bounded Context**: ninguno — transversal (herramienta de calidad)
**Origen**: `CoverageAnalyzer` de `ArchitectAnalyst` viene reportando "no se encontró
`coverage.json`" en `BL-002`, `BL-003` y `BL-004`, aunque el archivo se generaba correctamente
con `pytest --cov`. Investigación de esta sesión, fix verificado contra `src/` real.

---

## Descripcion (lenguaje de negocio)

Como **responsable del proceso de calidad**,
quiero **que `ArchitectAnalyst` encuentre `coverage.json` cuando ya existe**
para **que `CoverageAnalyzer` deje de reportar un warning vacío en cada baseline y aporte el
dato real de cobertura al análisis**.

---

## Contexto del dominio

### Problema

`CoverageAnalyzer` (`quality_agents.architectanalyst.metrics.coverage_analyzer`) resuelve la
ruta del reporte así:

```python
report_path_str = getattr(config, "coverage_report_path", "coverage.json")
report_path = project_path / report_path_str
```

`project_path` es el primer `PATH` posicional que recibe el CLI — en este proyecto siempre
`src/` (`architectanalyst src/ --config pyproject.toml`). Con el default
`coverage_report_path = "coverage.json"`, la herramienta busca `src/coverage.json`, que nunca
existe — `pytest --cov=src --cov-report=json` escribe `coverage.json` en la **raíz del repo**
(ubicación estándar de `pytest-cov`), no dentro de `src/`.

**Verificado en esta sesión:** generando `coverage.json` en la raíz y configurando
`coverage_report_path = "../coverage.json"` (relativo a `src/`, sube un nivel a la raíz),
`CoverageAnalyzer` pasó de `warning` ("no se encontró...") a `info` ("Cobertura de tests: 98.9%
(dentro del umbral mínimo de 80.0%)") — dato real, no aproximado.

### Alcance del fix

Una línea en `pyproject.toml`. Ningún cambio de código ni de pipeline — `coverage.json` ya se
genera hoy con `pytest --cov=src --cov-report=json` (usado en el cierre de `BL-004`); falta
correr ese comando *antes* de `architectanalyst` en el procedimiento de cierre de baseline
(documentar el orden, no automatizarlo todavía).

---

## Especificacion del comportamiento

### Precondicion

- `coverage.json` generado en la raíz del repo (`pytest --cov=src --cov-report=json`).
- `[tool.architectanalyst]` sin `coverage_report_path` (usa el default `"coverage.json"`,
  resuelto contra `src/`).

### Postcondicion

- `[tool.architectanalyst]` con `coverage_report_path = "../coverage.json"`.
- `architectanalyst src/ --config pyproject.toml` (corrido después de generar `coverage.json`)
  reporta `CoverageAnalyzer` en `info` con el porcentaje real, no en `warning` de archivo no
  encontrado.
- `docs/plans/PROCEDIMIENTO-UAT.md` o `CLAUDE.md` (notas operativas de quality gates) documenta
  el orden: generar `coverage.json` antes de correr `architectanalyst` al cerrar una baseline.

### Invariantes

Ninguna — no hay cambio de dominio.

---

## Criterios de aceptacion

```gherkin
Feature: CoverageAnalyzer encuentra coverage.json (US-ADJ-15)

  Scenario: Cobertura real reportada tras generar coverage.json
    Given coverage.json generado en la raíz del repo
    And [tool.architectanalyst] con coverage_report_path = "../coverage.json"
    When se corre architectanalyst src/ --config pyproject.toml
    Then CoverageAnalyzer reporta severidad info con el porcentaje real de cobertura
    And no aparece el warning "No se encontró el archivo de cobertura"
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — config de una línea, sin cambio de comportamiento del sistema.

**Capa(s) afectadas:**
- [x] Documentación/config — `pyproject.toml`, nota de procedimiento en `CLAUDE.md`

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `pyproject.toml` | `[tool.architectanalyst]`: agregar `coverage_report_path = "../coverage.json"` |
| `CLAUDE.md` | Nota operativa: generar `coverage.json` antes de correr `architectanalyst` al cerrar baseline |

---

## Referencias

- Relacionada con: `US-ADJ-13` (mismo archivo de config, otro hallazgo)
- Detectada durante: sesión de cierre de `BL-004` + planificación de `Incremento 3-ADJ`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
