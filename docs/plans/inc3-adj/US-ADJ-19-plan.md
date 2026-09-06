# Plan de Implementación: US-ADJ-19 - `LayerViolationsAnalyzer` no confiable (+ corrección de causa raíz de `US-ADJ-13`)

**Patrón:** N/A — documentación + config + Issue upstream
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-03

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (`.claude/tracking/US-ADJ-19-tracking.json`).
Fases 1/4/5/6/7 omitidas (sin código de producción). Tiempo real sin comparación contra
estimación humana (`PRIN-001`).

## Lecciones Aprendidas

- 💡 Reproducir con código real (`DependencyGraphBuilder.build()` directo, no solo correr
  `architectanalyst` y leer el resumen) permitió encontrar la causa raíz exacta en el código
  de la herramienta, en vez de quedarse en "0 resultados, no sabemos por qué" — mismo nivel de
  rigor que `US-ADJ-13`/`15`, pero esta vez llegando hasta el archivo fuente del bug.
- ⚠️ **Una conclusión aceptada en una US anterior (`US-ADJ-13`) puede estar mal fundamentada
  sin que nadie lo note** hasta investigar un problema relacionado en profundidad — la
  explicación "Ca=0 por diseño arquitectónico" era plausible y consistente con la regla real
  del proyecto ("sin imports directos entre BCs"), lo que la hacía fácil de aceptar sin
  cuestionar. Vale la pena, al aceptar un falso positivo de una herramienta, preguntarse si la
  explicación es la única posible antes de darla por buena.
- 💡 Ampliar el alcance de una US en curso (con aprobación explícita) cuando la investigación
  revela algo más grande que lo especificado es preferible a cerrar la US con un hallazgo
  parcial y dejar la documentación de otra US (`US-ADJ-13`) con una explicación incorrecta.

## Componentes a Implementar

### 1. Config — `pyproject.toml`
- [x] `[tool.architectanalyst.layers]`: corregir al formato documentado (nombre de capa → capas
  permitidas), aunque no detecte nada hoy — deja la config lista para cuando se resuelva el bug
  upstream y evita que alguien la "arregle" de nuevo hacia el formato incorrecto

### 2. Issue upstream — `vvalotto/software_limpio`
- [x] Abrir Issue con la causa raíz real: `DependencyGraphBuilder._extract_imports` no
  normaliza el prefijo `src.` de los imports del código fuente, mientras que
  `_path_to_module` sí lo quita de las rutas de archivo — el filtro
  `imp.split(".")[0] in root_packages` nunca matchea en un proyecto que importa como
  `from src.<pkg>...`. Afecta a `LayerViolationsAnalyzer` (0 violaciones siempre) y también a
  `CouplingAnalyzer`/`InstabilityAnalyzer`/`AbstractnessAnalyzer`/`DistanceAnalyzer` (`Ca`/`Ce`
  en 0 para todo el proyecto, no solo entre BCs). Incluir reproducción exacta (script Python
  standalone) y la corrección de la falsa conclusión de `US-ADJ-13`.

### 3. Documentación — `CLAUDE.md`
- [x] Nota nueva: `LayerViolationsAnalyzer` no confiable — la regla de imports entre capas se
  sostiene por revisión de código, no por este chequeo, hasta que el bug se resuelva upstream
- [x] **Corregir** la nota de `US-ADJ-13` ("Zone of Pain aceptado... Ca=0 siempre por diseño")
  — la causa raíz real es el mismo bug de `DependencyGraphBuilder`, no diseño arquitectónico.
  La aceptación del falso positivo se mantiene (sigue siendo cierto que no hay nada que
  arreglar en `src/`), pero la explicación técnica cambia.

## Verificación (sin código de producción — Fases 4/5/6/7 no aplican)

- [x] `pyproject.toml` válido (TOML parseable)
- [x] Issue creado y accesible en `vvalotto/software_limpio`
- [x] `CLAUDE.md` documenta ambos hallazgos, localizable buscando "LayerViolationsAnalyzer" o
  "DependencyGraphBuilder"

Issue: [`vvalotto/software_limpio#77`](https://github.com/vvalotto/software_limpio/issues/77).

**Estado:** 6/6 tareas completadas
