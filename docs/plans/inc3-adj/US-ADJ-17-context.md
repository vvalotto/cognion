# Contexto de Ejecución — US-ADJ-17

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-17.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture BC-first,
  perfil `clean-architecture-bc`) — refactor interno del BC Banco de Preguntas, respeta la
  regla de imports (`entities → use_cases → interface_adapters → frameworks`)

## Historia de Usuario
- **ID:** US-ADJ-17
- **Título:** Value Object `MetadatosPregunta` (Data Clump/Primitive Obsession, Banco de
  Preguntas)
- **Tipo:** Refactor backend (sin cambio de comportamiento observable ni de contrato HTTP)
- **Puntos:** 8
- **Prioridad:** Alta — 41/159 (26%) de los warnings de `DesignReviewer src/` concentrados en 3
  archivos con la misma causa raíz

## Decisión de diseño clave (no estaba en la spec, decidida antes de escribir código)

La spec no precisa si el resto del código (routers, gateway) debe pasar a leer
`pregunta.metadatos.texto` en vez de `pregunta.texto`. Inventario real antes de tocar nada:
- **Sitios de lectura** (`pregunta.texto`, `.dificultad`, etc., fuera de la entidad): 42 —
  31 en `pregunta_repository.py`, 11 en `bancos_router.py` (ninguno de los dos está en la
  tabla "Artefactos a modificar" de la spec, que solo lista `entities`/`use_cases`/
  `preguntas_controller.py`/`pregunta_repository.py`).
- **Sitios de construcción** (`.crear(...)`, `.editar(...)`, con los 5 kwargs sueltos): solo
  en `use_cases/` (3 archivos) y en tests (8 archivos, ~1429 líneas). Ningún código de
  producción fuera de `pregunta_plantilla.py` construye la entidad posicionalmente — solo la
  gateway en `_a_entidad`.

**Decisión:** el aggregate pasa a almacenar un único campo `metadatos: MetadatosPregunta`
(reemplaza los 5 campos sueltos del dataclass — necesario para que `DataClumpsAnalyzer` deje
de señalar la entidad), pero expone `texto`/`unidad_tematica`/`tema`/`dificultad`/`importancia`
como `@property` de solo lectura que delegan a `self.metadatos.*`. Esto:
- Resuelve el Data Clump/Primitive Obsession real (constructores/métodos ya no reciben 5
  parámetros sueltos — que es lo que mide el analyzer).
- Evita tocar los 42 sitios de **lectura** en `bancos_router.py`/`pregunta_repository.py`
  (siguen compilando y funcionando sin cambios — la propiedad es transparente).
- Limita el refactor real a: `pregunta_plantilla.py`, `metadatos_pregunta.py` (nuevo), 3
  `use_cases/`, `preguntas_controller.py`, los 3 call-sites de `preguntas_router.py` que
  arman el request hacia el controller (cambian de 5 kwargs a `metadatos=MetadatosPregunta(...)`),
  `_a_entidad`/`guardar`/`actualizar` de la gateway (construyen la entidad — si pasan a usar
  `metadatos=` en vez de 5 kwargs), y los tests que llaman `.crear()`/`.editar()` directamente.

**Fuera de alcance de esta US** (ya lo dice la spec): la persistencia sigue en columnas
individuales — no hay migración de schema. La limpieza completa de Ley de Demeter en la
gateway (`pregunta.dificultad.value` → potencialmente `pregunta.metadatos.dificultad.value`,
3 saltos) es `US-ADJ-18` — con las properties, la gateway ni siquiera necesita cambiar sus
lecturas, así que ese trabajo queda igual de acotado a `US-ADJ-18` como estaba previsto.

## Decisiones de Ejecución
- **BDD:** No — refactorización sin cambio de comportamiento observable (tabla de
  clasificación de Fase 0). Los escenarios Gherkin de la spec ya son de verificación técnica.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se salta 1 y 6 — sin BDD; sí corren 4/5 porque
  hay tests existentes que deben actualizarse a la nueva firma, no solo agregarse)

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** Clean Architecture BC-first — `MetadatosPregunta` vive en
  `entities/` (Value Object, sin dependencias externas), no rompe la regla de capas
- **Umbrales de calidad:** los de siempre del perfil (pylint, CC, MI, coverage — leer de
  `.claude/skills/implement-us/config.json`), más `pytest` completo del BC (o del proyecto) en
  verde y `designreviewer src/ --config pyproject.toml`: `pregunta_plantilla.py` y
  `preguntas_controller.py` sin issues de `PrimitiveObsessionAnalyzer`/`DataClumpsAnalyzer`

## Rutas de Artefactos
- Contexto: `docs/plans/inc3-adj/US-ADJ-17-context.md`
- BDD feature: N/A (skip_bdd)
- Plan: `docs/plans/inc3-adj/US-ADJ-17-plan.md`
- Reporte: `docs/reports/inc3-adj/US-ADJ-17-report.md`
- Quality report: `quality/reports/inc3-adj/US-ADJ-17-quality.json`
