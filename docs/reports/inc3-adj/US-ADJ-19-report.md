# Reporte de Implementación: US-ADJ-19

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-19 - `LayerViolationsAnalyzer` no detecta ninguna violación
  bajo ninguna configuración (ampliada durante Fase 0: corrección de causa raíz de `US-ADJ-13`)
- **Puntos estimados:** 2
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-03
- **Origen:** investigación de `US-ADJ-13`, que detectó que `[tool.architectanalyst.layers]`
  estaba mal formada y que el analyzer nunca detectaba nada bajo ninguna config probada

---

## Ampliación de alcance (aprobada por Víctor antes de implementar)

La investigación de Fase 0 llegó al código fuente de la herramienta (no solo a probar
configs), y encontró la causa raíz real: `DependencyGraphBuilder` normaliza el prefijo `src.`
al derivar nombres de módulo desde rutas de archivo, pero no aplica la misma normalización a
los imports extraídos del código fuente. Este proyecto importa siempre como `from src.<bc>...`,
así que **ningún import interno se registra jamás** — verificado con código real, el grafo de
dependencias completo del proyecto tiene 0 aristas.

Esto **corrige una conclusión de `US-ADJ-13`** (ya cerrada): la nota agregada a `CLAUDE.md` en
esa US explicaba el "Zone of Pain" como "cada BC es hoja del grafo por diseño arquitectónico
(`Ca=0` siempre)" — explicación plausible pero incorrecta. La causa real es el mismo bug:
`Ca=Ce=0` para *todos* los módulos del proyecto, no solo entre BCs, lo que fuerza
`Instability=0` y colapsa `D = |A + I - 1|` a `D ≈ 1 - A`. La aceptación del falso positivo se
mantiene (no hay nada que arreglar en `src/`), pero la explicación técnica cambia.

---

## Componentes Implementados

### Config
- ✅ `pyproject.toml`: `[tool.architectanalyst.layers]` corregido al formato documentado

### Issue upstream
- ✅ [`vvalotto/software_limpio#77`](https://github.com/vvalotto/software_limpio/issues/77):
  causa raíz real, con reproducción exacta (script Python standalone + config con regla
  imposible de cumplir), impacto sobre 5 analyzers (`LayerViolationsAnalyzer`,
  `CouplingAnalyzer`, `InstabilityAnalyzer`, `AbstractnessAnalyzer`, `DistanceAnalyzer`)

### Documentación
- ✅ `CLAUDE.md`: nota nueva (`LayerViolationsAnalyzer` no confiable) + corrección de la nota
  de `US-ADJ-13`

---

## Métricas de Calidad

| Métrica | Valor | Estado |
|---------|-------|--------|
| `pyproject.toml` válido | Sí (TOML parseable) | ✅ |
| Issue upstream creado | `vvalotto/software_limpio#77`, OPEN | ✅ |
| `CLAUDE.md` documenta ambos hallazgos | Sí | ✅ |

Fuente: `quality/reports/inc3-adj/US-ADJ-19-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests

Sin tests — documentación + config + Issue externo, sin código de producción del proyecto.

Sin BDD (Fase 0).

---

## Archivos Creados/Modificados

### Config
- `pyproject.toml` (`[tool.architectanalyst.layers]`)

### Documentación
- `CLAUDE.md` (nota nueva + corrección de la nota de `US-ADJ-13`)
- `docs/plans/inc3-adj/US-ADJ-19-context.md`
- `docs/plans/inc3-adj/US-ADJ-19-plan.md`
- `docs/reports/inc3-adj/US-ADJ-19-report.md` (este archivo)
- `quality/reports/inc3-adj/US-ADJ-19-quality.json`
- `CHANGELOG.md` (entrada en `[Unreleased] → Fixed`)

### Externo
- Issue [`vvalotto/software_limpio#77`](https://github.com/vvalotto/software_limpio/issues/77)

---

## Criterios de Aceptación

- [x] Issue upstream reproducible — `frameworks = []` (regla imposible de cumplir) da 0
  resultados de `LayerViolationsAnalyzer`, documentado con la causa raíz exacta
- [x] `CLAUDE.md` documenta que la ausencia de resultados de `LayerViolationsAnalyzer` no
  certifica "sin violaciones" — el chequeo no es confiable actualmente
- [x] (ampliación) `CLAUDE.md` corrige la explicación técnica de `US-ADJ-13`

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] **Cierra el Incremento 3-ADJ** — las 8 US-ADJ (`13` a `20`) quedan implementadas.
  Correr `ArchitectAnalyst`/`DesignReviewer` de nuevo para confirmar mejoras globales
  (`US-ADJ-16`/`17`/`18`) y decidir con Víctor la baseline propia (`BL-005` o plegado a la
  apertura del Incremento 4)
- [ ] Seguimiento externo: el Issue `software_limpio#77` queda abierto, sin ETA de fix
  upstream — cuando se resuelva, `[tool.architectanalyst.layers]` ya está en el formato
  correcto para empezar a detectar violaciones reales

---

## Lecciones Aprendidas

- 💡 Reproducir con código real (llamando directamente a `DependencyGraphBuilder.build()`) en
  vez de solo correr la CLI y leer el resumen permitió encontrar la causa raíz exacta en el
  código de la herramienta.
- ⚠️ Una conclusión aceptada en una US anterior puede estar mal fundamentada sin que nadie lo
  note — la explicación "Ca=0 por diseño arquitectónico" era plausible y consistente con la
  regla real del proyecto, lo que la hacía fácil de aceptar sin cuestionar más a fondo.
- 💡 Ampliar el alcance de una US en curso (con aprobación explícita) cuando la investigación
  revela algo más grande que lo especificado es preferible a cerrarla con un hallazgo parcial.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-09-03
