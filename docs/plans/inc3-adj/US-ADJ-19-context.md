# Contexto de Ejecución — US-ADJ-19

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-19.md`
- **Fuente Arquitectura:** N/A — herramienta de calidad externa, sin impacto en `src/`

## Historia de Usuario
- **ID:** US-ADJ-19
- **Título:** `LayerViolationsAnalyzer` no detecta ninguna violación bajo ninguna configuración
- **Tipo:** Documentación + Issue upstream (sin fix propio — el bug está en la herramienta)
- **Puntos:** 2
- **Prioridad:** Media — señal de calidad que en los hechos nunca se dispara

## Ampliación de alcance decidida con Víctor antes de implementar

La investigación de Fase 0 encontró la **causa raíz real**, más precisa que la de la spec
original (que solo probaba configs y observaba "0 resultados" sin llegar al código de la
herramienta): `DependencyGraphBuilder` (`quality_agents.architectanalyst.metrics.
dependency_graph`) — usado no solo por `LayerViolationsAnalyzer` sino también por
`CouplingAnalyzer`/`InstabilityAnalyzer`/`AbstractnessAnalyzer`/`DistanceAnalyzer` — construye
los nombres de módulo quitando el prefijo `src/` de las **rutas de archivo**, pero no aplica
esa misma normalización a los **imports extraídos del código fuente** (`_extract_imports`).
Este proyecto importa todo como `from src.<bc>...`, así que el filtro
`imp.split(".")[0] in root_packages` compara `"src"` contra los nombres de BC y nunca matchea.

Verificado con código real: `graph.outgoing` tiene **0 aristas en total** para todo el
proyecto — `Ca=Ce=0` para absolutamente todos los módulos, siempre, no solo entre BCs.

**Consecuencia sobre `US-ADJ-13` (ya cerrada):** la nota agregada a `CLAUDE.md` en esa US
("Zone of Pain aceptado como falso positivo porque cada BC es hoja del grafo de dependencias
por diseño, `Ca=0` siempre, por la regla sin imports directos entre BCs") da la explicación
equivocada — no es diseño arquitectónico, es que la herramienta nunca calculó ningún
acoplamiento real para nada en el proyecto. Con `I = Ce/(Ca+Ce)` forzado a 0 en todos los
casos, `D = |A + I - 1|` colapsa a `D ≈ 1 - A`, garantizando CRITICAL en cualquier paquete con
abstracción baja — independientemente de si hay o no un problema de diseño real. **Decisión de
Víctor (2026-09-03): ampliar `US-ADJ-19`** para corregir esa nota además de documentar
`LayerViolationsAnalyzer`, y reportar la causa raíz real (no solo el síntoma) en el Issue
upstream.

## Decisiones de Ejecución
- **BDD:** No — documentación + config + Issue externo, sin código propio del proyecto.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 8, 9 (se saltan 1, 4, 5, 6 y 7 — sin código de producción)

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** N/A
- **Umbrales de calidad:** N/A. Verificación de aceptación: Issue abierto en
  `vvalotto/software_limpio` con la reproducción exacta y la causa raíz real; `CLAUDE.md`
  corregido (nota de `US-ADJ-13` + nota nueva de `US-ADJ-19`); `pyproject.toml` con el formato
  correcto de `[tool.architectanalyst.layers]`.

## Rutas de Artefactos
- Contexto: `docs/plans/inc3-adj/US-ADJ-19-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc3-adj/US-ADJ-19-plan.md`
- Reporte: `docs/reports/inc3-adj/US-ADJ-19-report.md`
- Quality report: `quality/reports/inc3-adj/US-ADJ-19-quality.json`
