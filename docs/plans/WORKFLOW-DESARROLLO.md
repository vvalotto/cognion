# Workflow de Desarrollo — Cognion

> Estado documental: vigente
> Fuente de verdad para: procedimiento operativo de branching, PRs, gestión de Issues/Milestones y ciclo de trabajo por US/Incremento
> Última actualización: 2026-07-20
> Fuente normativa relacionada: `docs/plans/PLAN-CM.md` (política) — este documento es el procedimiento que la ejecuta
> Fuente conceptual: `docs/iedd/05-Fases-y-Gates.md` — este documento instancia, para Cognión,
> el ciclo Dominio → Arquitectura → Modelo → Especificación → Implementación y sus gates
> (`docs/iedd/03-Diagrama_Conceptual.md`); no redefine el modelo conceptual, lo ejecuta

---

## 1. Jerarquía de Trabajo

```
Incremento (PLAN_v1.md, 0–6)  → Baseline (BL-NNN) + tag git (v0.N.0) + Milestone GitHub
  └── Iteración (dentro del incremento)
        └── US-IEDD (US-N.M.K)  → GitHub Issue + docs/specs/incN/US-N.M.K.md + branch feature/
```

No existe un nivel "Subproyecto" separado del Incremento — ver `PLAN-CM.md` §7 y §13. La
Iteración cubre lo que en otros proyectos IEDD podría llamarse "Sprint", pero aquí es
simplemente la subdivisión que ya trae `PLAN_v1.md` dentro de cada Incremento.

**US-IEDD como esquema único de unidad de trabajo.** No todo el trabajo del proyecto es una
feature. También hay spikes (resolver una decisión abierta), PoC (verificar viabilidad
técnica) y artefactos de modelado (event storming, wireframes). En vez de un template distinto
por tipo, las cuatro se especifican con el **mismo esquema US-IEDD** — Precondición,
Postcondición, Invariantes, Criterios de Aceptación — agregando un campo `Tipo` que declara
cuál es y qué cuenta como su Postcondición/DoD. Precedente: en el proyecto de referencia
(AtaraxiaDive), la iteración de fundación técnica pura ya se especificó como US-IEDD con
`Aggregate: ninguno (es infraestructura)` en vez de inventar un template aparte. Un único
esquema, una única mecánica de cierre (GitHub Issue), menos superficie de mantenimiento.
Tabla de DoD por tipo en §2.

**Iteración 0 — Modelado.** Cuando el incremento introduce un BC nuevo o lo extiende de forma
significativa (ver `PLAN_v1.md`, tabla de cada incremento), la primera iteración produce sus
artefactos de diseño — el modelo de dominio del BC (event storming) y, si el BC expone
pantallas nuevas, el prototipo UX correspondiente — como una o más US-IEDD **tipo `Modelado`**,
cada una con su GitHub Issue. Cierran recién cuando Víctor aprueba explícitamente el artefacto
(la aprobación es el comentario que cierra el Issue, no un paso informal aparte). Deben estar
cerradas antes de pasar a la Iteración 1. Procedimiento en §3. Es la instancia operativa del
**gate de modelado** (`docs/iedd/05-Fases-y-Gates.md` §3.2).

---

## 2. Gestión Administrativa (GitHub)

### División de responsabilidades

| Artefacto | Dónde vive | Propósito |
|---|---|---|
| **GitHub Issue** | GitHub Issues | Fuente de verdad del estado — qué hay que hacer, criterios de aceptación, seguimiento |
| **`docs/specs/incN/US-N.M.K.md`** | Repositorio | Especificación US-IEDD — precondición, postcondición, invariantes, input de `/implement-us` |

### Estructura en GitHub

- **Milestones** = uno por Incremento (`Incremento 0 — Walking Skeleton`, `Incremento 1 — Banco de preguntas`, etc.)
- **Labels** = `us-iedd`, `incremento-0`, `incremento-1`, ...
- **Labels de tipo** = `tipo:feature`, `tipo:spike`, `tipo:poc`, `tipo:modelado` — permiten
  filtrar en GitHub sin tocar el esquema de la spec (ver "US-IEDD como esquema único" en §1)
- **Labels de estado** = `backlog`, `in-progress`, `blocked` — ver "Estado del Issue" abajo
- **Sin Project board** — Milestones + Labels alcanzan para desarrollo en solitario

### Estado del Issue

El estado de una unidad de trabajo combina el estado nativo del Issue (`open`/`closed`) con
un label de estado mientras está abierto. No existe label `done`: **cerrar el Issue es la
señal de "terminado"** — tenerla duplicada en un label aparte permite que las dos se
desincronicen (issue cerrado sin el label, o viceversa).

| Estado | Cómo se marca | Significado |
|---|---|---|
| Backlog | Issue abierto + label `backlog` | Creado, especificado, trabajo todavía no arrancó |
| En curso | Issue abierto + label `in-progress` (reemplaza a `backlog`) | Trabajo activo — branch `feature/` o `fix/` abierta |
| Bloqueado | Issue abierto + label `blocked` (reemplaza a `backlog`/`in-progress`) | Depende de una decisión o Issue externo — anotar en un comentario cuál |
| Terminado | Issue **cerrado** (sin label de estado) | DoD cumplido — ver tabla "DoD por Tipo" en §2 |

Un Issue siempre tiene exactamente un label de estado mientras está abierto (nunca dos a la
vez, nunca ninguno) — al cerrarlo se quita el label de estado, el propio cierre ya lo dice
todo.

### Template de Issue (US-IEDD)

```markdown
## Tipo
Feature | Spike | PoC | Modelado

## Descripción
Como <rol>, quiero <acción> para <valor>.
(Spike/PoC: qué pregunta o hipótesis resuelve. Modelado: qué artefacto de diseño produce.)

## Criterios de Aceptación
- [ ] ...

## Precondición
...

## Postcondición
...
(Ver tabla "DoD por Tipo" — qué cuenta como Postcondición cambia según el Tipo declarado.)

## Invariantes
- INV-1: ...
(Spike/PoC/Modelado sin invariantes de dominio: omitir la sección o dejar "N/A".)

## Referencias
- Incremento: N
- Bounded Context: ...
- docs/specs/incN/US-N.M.K.md
```

### DoD por Tipo

El Issue se cierra únicamente cuando su Postcondición declarada se cumple — cerrar el Issue
**es** la comprobación del DoD, no un checklist paralelo. Lo que cuenta como Postcondición
cambia según el Tipo:

| Tipo | Postcondición (qué cierra el Issue) | Evidencia de cierre |
|---|---|---|
| **Feature** | Criterios de aceptación cumplidos, código integrado en `develop` | PR mergeado + `docs/reports/{US_ID}-report.md` |
| **Spike** | Pregunta/decisión resuelta (puede ser negativa) | ADR o nota de decisión enlazada en el comentario que cierra el Issue |
| **PoC** | Viabilidad técnica verificada, sí o no | Código exploratorio + comentario de cierre con el resultado |
| **Modelado** | Artefacto de diseño aprobado explícitamente por Víctor | Doc en `docs/design/domain/` o `docs/design/ux/` + comentario de aprobación en el Issue |

A diferencia de una Feature, un Spike/PoC/Modelado no siempre tiene un build verde que
verifique el cumplimiento — el cierre del Issue requiere una declaración explícita de Víctor
en el comentario de cierre, no solo el merge de un PR.

---

## 3. Ciclo de Elaboración de US por Incremento

Este ciclo es la instancia operativa del **gate de especificación**
(`docs/iedd/05-Fases-y-Gates.md` §3.3, la "Definición de Listo para Especificar"): antes de
escribir cualquier `US-N.M.K.md`, el paso 0 (si aplica) y el paso 3b verifican que el modelo de
dominio y el diseño UX que la spec necesita ya estén aprobados — no se especifica sobre un
artefacto que todavía no existe o que diverge del aprobado (anti-patrón "spec-validatoria",
también tratado como regla general de reingreso en `docs/iedd/03-Diagrama_Conceptual.md` §"La
regla de reingreso").

```
0. [CONDICIONAL — si el Incremento tiene Iteración 0 — Modelado, ver PLAN_v1.md]:
   ejecutar la Iteración 0 ANTES de elaborar candidatas:
   a. Por cada artefacto de diseño necesario, crear una US-IEDD tipo `Modelado` (§2):
      GitHub Issue con label `tipo:modelado` + docs/specs/incN/US-N.0.K.md
      → event storming del BC (agregados, eventos de dominio, comandos, invariantes)
        → docs/design/domain/BC-<bc>-modelo.md
      → si el BC expone pantallas nuevas: prototipo UX (docs/design/ux/prototipos/) +
        spec de wireframes (docs/design/ux/wireframes-*.md) — mismo gate del §5 de PLAN-CM.md
   b. El Issue de cada artefacto cierra solo cuando Víctor lo aprueba explícitamente en el
      comentario de cierre (DoD de tipo `Modelado`, tabla de §2) — no antes
   c. Todas las US-IEDD tipo `Modelado` de la Iteración 0 deben estar cerradas antes de
      continuar al paso 1
   d. No especificar comportamiento nuevo sobre un modelo de dominio que todavía no existe
      o que difiere del aprobado — mismo anti-patrón "spec-validatoria" que en UX (PLAN-CM.md
      §5), aplicado ahora al backend
   e. Actualizar docs/traceability/matrix.md §4: los escenarios RNF que este incremento aborda
      pasan de Planificado a Especificado — el mecanismo concreto que los garantiza ya quedó
      definido en el modelo de dominio/UX aprobado, aunque todavía no esté codeado
1. Elaborar el archivo de US candidatas: docs/plans/incN/incN-candidatas.md
   → Lista todas las US del incremento con descripción, criterios y estimación
   → Las US candidatas referencian el modelo de dominio aprobado en la Iteración 0, no lo
     redescubren
2. Víctor revisa y aprueba (con ajustes si corresponde)
3. Por cada US aprobada:
   a. Crear GitHub Issue con template US-IEDD → asignar Milestone + Labels
   b. **[CONDICIONAL — si la US toca `frontend/`]:** consultar `docs/design/ux/` ANTES de escribir la spec
      → Leer el wireframe y prototipo de la pantalla/rol afectado
      → Comparar con la implementación React actual (`frontend/src/`)
      → Si hay gaps entre la UX aprobada y el código: incorporarlos al scope de esta US
        o abrir una US previa de corrección. No especificar comportamiento nuevo sobre código
        que ya diverge del diseño aprobado (anti-patrón "spec-validatoria" — ver PLAN-CM.md §5).
      → La spec DEBE incluir el campo `## Fuente de verdad UX` con referencias a los
        artefactos consultados. Una spec de frontend sin ese campo no está completa.
   c. Crear docs/specs/incN/US-N.M.K.md con la especificación US-IEDD completa
   d. Actualizar docs/traceability/matrix.md: la(s) fila(s) RF cubiertas por esta US pasan de
      Planificado a Especificado, completando la columna US-IEDD con su ID
4. Las US quedan en estado "backlog" hasta iniciar su Incremento
```

---

## 4. Branching

```
main          ← baselines etiquetadas (v0.1.0, v0.2.0...)
  └── develop ← integración continua — recibe PRs individuales de cada US
        ├── feature/US-N.M.K-descripcion-corta  ← una branch por US-IEDD
        ├── feature/inc-N-descripcion-corta      ← incrementos técnicos sin US
        └── fix/descripcion-corta                ← correcciones
```

Ver `PLAN-CM.md` §13 para el patrón exacto de cada nombre. Reglas:

- Cada US-IEDD tiene su propia branch — PR individual directo a `develop`.
- Los incrementos técnicos (sin US-IEDD, como el Incremento 0) usan `feature/inc-N-*` con commits por tarea.
- `develop` se mergea a `main` **solo** al cerrar un Incremento (Baseline) — nunca directo desde `feature/`.
- Descripción en kebab-case, máximo 4 palabras, en español.

### Commits (Conventional Commits)

```
feat(entities): agregar aggregate ActividadEvaluativa [US-3.1.1]
fix(interface_adapters): corregir endpoint ranking provisional
test(entities): tests unitarios ActividadEvaluativa.cerrar_periodo
docs(adr): ADR-003 decisión SQLite vs PostgreSQL
chore(cm): registrar BL-002 cierre Incremento 2

# Tipos: feat | fix | refactor | test | docs | chore
# Scopes: entities | use_cases | interface_adapters | frameworks | frontend | cm | tests | design
```

---

## 5. Ciclo por US-IEDD

### Orden de arranque (no negociable)

```
1. git checkout -b feature/US-N.M.K-descripcion desde develop
2. Verificar con git branch que el branch activo es el correcto
3. Inicializar TimeTracker: tracker init US-N.M.K → start_phase(0)
   → El archivo .claude/tracking/US-N.M.K-tracking.json debe existir
     ANTES de crear cualquier artefacto
4. Recién entonces arrancar Fase 0
```

> **Antes de iniciar:** verificar que no haya trackers activos de USs anteriores sin cerrar.
> `_find_active_us_id()` retorna el primero con `completed_at == null`.

> **Nota heredada del Claude Dev Kit:** `tracker_cli.py` usa `glob("US-*-tracking.json")` —
> IDs con prefijo distinto a `US-` no son encontrados por las operaciones de fase. Usar
> siempre el prefijo `US-` para los IDs de tracking (nunca `INC-` u otro).

> **Política de tracking:** todas las operaciones sobre `tracker_cli.py` (`init`,
> `start-phase`, `end-phase`, `start-task`, `end-task`, `end`) se ejecutan **estrictamente en
> secuencia, una por vez** — nunca en paralelo sobre el mismo `.claude/tracking/US-*.json`.
> Ejecutar el CLI con el Python local del repositorio (`.venv/bin/python
> .claude/tracking/tracker_cli.py ...`), no con `uv run`.

### Ejecución de fases

```
5. Ejecutar /implement-us US-N.M.K  (10 fases, input: docs/specs/incN/US-N.M.K.md)
   → Cada fase tiene un artefacto físico de output — crearlo con Write, no solo mostrarlo en el chat
   → Único checkpoint de aprobación por fase (config.json): Fase 1 (BDD), Fase 2 (plan) y
     Fase 8 (documentación). Fase 3 (implementación) NO pausa tarea por tarea — ejecuta todo
     el plan aprobado de forma continua, y solo se detiene ante errores reales o ambigüedad
     de diseño no cubierta por el plan.
   → Fases 8 y 9 deben ejecutarse ANTES del commit final, no después
   → El skill no está completo hasta que docs/reports/{US_ID}-report.md exista en disco
6. [AUTO] CodeGuard corre en cada commit (pre-commit hook, advierte, no bloquea)
7. Commits atómicos con referencia: feat(entities): ... [US-N.M.K]
8. Abrir PR hacia develop con /pr → DesignReviewer corre en pre-push (bloquea si CRITICAL)
   → Usar siempre gh pr create --base develop (el default de gh es main)
   → El body del PR NO necesita "Closes #N": el repo mergea a develop, no a main (rama
     default), y GitHub solo autocierra Issues por esa keyword al mergear contra la rama
     default — no funciona en este workflow.
9. Merge del PR con gh pr merge --merge --delete-branch, luego sincronizar el repo local
   (checkout develop, pull --ff-only, borrar branch feature local, fetch --prune).
9a. Cerrar el Issue de la US asociado: comentar con los SHAs de los commits de la US
    (`gh issue comment N --body ...`) y cerrarlo (`gh issue close N --reason completed`) —
    sin pedir confirmación previa, salvo ambigüedad real (Issue no encontrado, más de un
    candidato).
9b. Actualizar docs/traceability/matrix.md: la(s) fila(s) RF cubiertas por esta US pasan de
    Especificado a Implementado.
    → Si el código mergeado es el mecanismo concreto de un escenario RNF (ver la columna ADR
      de la matriz §4 para identificar cuál), esa fila RNF pasa también a Implementado.
```

---

## 6. Ciclo por Incremento

Un Incremento cierra cuando todas sus US-IEDD están mergeadas a `develop` y el DoD de
integración (definido en `PLAN_v1.md` para cada incremento) es verificable de punta a punta.

### Preparación al inicio del incremento

Si el incremento tiene Iteración 0 — Modelado (ver `PLAN_v1.md`), debe estar cerrada — modelo
de dominio y, si corresponde, UX ya aprobados por Víctor — antes de abrir la primera branch
`feature/US-*` del incremento (§3, paso 0).

Antes de la primera US, estimar el crecimiento total del aggregate principal y ajustar
umbrales en `pyproject.toml` para el incremento completo (no US por US) — ver `PLAN-CM.md`
§10, nota sobre umbrales de `[tool.designreviewer]`.

### Cierre del incremento

```
1. Todas las US del Incremento mergeadas a develop (PR individual por US)
2. Verificar DoD de integración (test end-to-end observable, tomado del hito de PLAN_v1.md)
2b. **[CONDICIONAL — si el incremento incluyó artefactos UX en docs/design/ux/prototipos/]:**
    verificar que la implementación React sigue el prototipo aprobado, pantalla por pantalla
    (PLAN-CM.md §5). Si hay divergencia: clasificar como gap (§4 de PLAN-CM.md) y resolverlo
    antes de cerrar el incremento.
3. [MANUAL] Correr DesignReviewer sobre el estado consolidado del incremento:
   designreviewer src/ --config pyproject.toml
   → Si hay CRITICAL: abrir fix/ branch, corregir, PR a develop
4. Registrar en BL-00N activa (ver PLAN-CM.md §7):
   → Agregar CIs nuevos a la tabla de inventario (backend CI-C##, frontend CI-F##)
   → Actualizar métricas del incremento
   → Registrar decisiones técnicas relevantes
5. Evaluar si corresponde un SP-ADJ (deuda técnica o documental acumulada — PLAN-CM.md §12)
6. Si hay hallazgos relevantes que ameriten análisis profundo (fricción, anti-patrón,
   contraste con la hipótesis del ensayo): escribir un HITO en docs/aprendizajes/ (PLAN-CM.md §9)
7. **[CONDICIONAL] Si hay UAT manual:** clasificar cada hallazgo antes de resolverlo
   → Solo toca `frontend/` → track informal, sin spec, sin pipeline de 10 fases
   → Toca cualquier archivo de `src/` → track formal obligatorio: US-IEDD → spec → /implement-us
   → Regla de pivote: declarar el track ANTES de codear (PLAN-CM.md §4)
8. Mini-retrospectiva: ¿qué funcionó? ¿qué ajustar en el próximo incremento?
9. Cerrar Milestone del incremento en GitHub con comentario de DoD verificado
```

**Para incrementos técnicos sin US (ej. Incremento 0 — Walking Skeleton):**

```
1. Branch feature/inc-N-descripcion desde develop
2. Commits por tarea (scaffold, migraciones, health-check, etc.)
3. [AUTO] CodeGuard en cada commit
4. Abrir PR con /pr → DesignReviewer pre-push
5. Merge → verificar DoD
6. Registrar en BL-00N + HITO si hay aprendizajes
```

### Incrementos de infraestructura (despliegue, CI/CD) — ciudadanos de primera clase

Un incremento cuyo contenido es configuración de infraestructura, pipeline de CI/CD o
despliegue (no lógica de dominio) **no se trata como tarea implícita de cierre** — tiene su
propio DoD, análogo a cualquier otro incremento (PLAN-CM.md §11):

```
Precondición: tag de la baseline anterior en main, tests verdes en local
Postcondición: pipeline de GitHub Actions ejecuta test → build → deploy sin fallos
               y el healthcheck del entorno destino responde 200
Invariante: sin degradación de tests, sin cambios no intencionales en el dominio
Evidencia: log del pipeline + respuesta del healthcheck — no un test de dominio
```

Se cierra con el mismo ciclo de branch/PR que un incremento técnico sin US (bloque
anterior), pero su DoD se verifica contra el entorno de destino, no contra `src/` local.

---

## 7. Ciclo por Baseline (cierre de Incremento)

Instancia operativa del **gate de cierre** (`docs/iedd/05-Fases-y-Gates.md` §3.5).

```
1. Todo el Incremento cerrado en develop — Milestone al 100%
2. Correr ArchitectAnalyst manualmente:
   architectanalyst src/ --sprint-id BL-NNN --format json \
     > quality/reports/architectanalyst/BL-NNN-arquitectura.json
   → Leer y analizar el reporte antes de continuar
   → Copiar también a .cm/baselines/BL-NNN-arquitectura.json
3. Registrar métricas en .cm/baselines/BL-NNN.md (formato en PLAN-CM.md §7)
4. UAT — flujo DoD de punta a punta según `PROCEDIMIENTO-UAT.md`:
   a. Diseñar pruebas en quality/reports/uat/incN/design.md
   b. Clasificar cada hallazgo antes de resolverlo (§6 paso 7 de este documento;
      severidad Bloqueante/Observación/Estético — PROCEDIMIENTO-UAT.md §8)
   c. Ejecutar contra el entorno propio (por defecto) o staging (solo en los checkpoints
      de PROCEDIMIENTO-UAT.md §4 — infraestructura/CI-CD, Incremento 5, o pre-producción)
   d. Ejecutar: Capa 1 pytest (flujo de dominio) + Capa 2 HTTP/WS (endpoints/canales observables)
   e. Guardar evidencia en quality/reports/uat/incN/
   f. UAT aprobado (sin hallazgos 🔴 Bloqueantes) → PR mergeado a develop antes de continuar
   g. Actualizar docs/traceability/matrix.md: todas las filas RF y RNF cubiertas por este
      Incremento pasan de Implementado a Validado, referenciando BL-NNN (ya registrada en el
      paso 3) como evidencia. Un escenario RNF con ⚠️ ítem abierto sin resolver NO pasa a
      Validado aunque el Incremento cierre — queda en su estado anterior con la nota vigente.
5. Merge develop → main
   → El merge/tag a main dispara el pipeline de CI/CD: build de imagen Docker + deploy
     automático + verificación de healthcheck (PLAN-CM.md §11) — no se dispara desde develop
6. Tag: git tag v0.N.0 (MINOR — cierre de incremento; ver semántica completa en PLAN-CM.md §11)
   — cerrar Milestone en GitHub
7. Actualizar CHANGELOG.md con la entrada de esta versión (PLAN-CM.md §7)
8. Retrospectiva documentada en BL-NNN.md
```

**ArchitectAnalyst es siempre manual** — su valor está en la lectura consciente del reporte
antes de cerrar el Baseline, no en la automatización (PLAN-CM.md §10).

---

## 8. Quality Gates por Nivel

Instancia operativa del **gate de implementación** (`docs/iedd/05-Fases-y-Gates.md` §3.4).
Ver tabla completa en `PLAN-CM.md` §10. Resumen operativo:

| Nivel | Herramienta | Cuándo | Acción |
|---|---|---|---|
| Commit | CodeGuard | Pre-commit (automático) | Advierte, no bloquea |
| PR a develop | DesignReviewer | Pre-push (automático) | Bloquea si CRITICAL |
| Cierre de Incremento | DesignReviewer manual | Manual, después del último merge | Confirmar cero CRITICAL |
| Cierre de Incremento con UX | Verificación de prototipo | Manual | Implementación debe seguir el diseño aprobado |
| UAT | Tests funcionales | Manual, antes de merge a main | Capa 1 + Capa 2 aprobadas |
| Cierre de Baseline | ArchitectAnalyst | Manual, antes de merge a main | Informa tendencias |

> **Importante:** siempre pasar `--config pyproject.toml` al correr DesignReviewer
> manualmente. Sin él se usan defaults del sistema (CBO=5, WMC=20) que no reflejan la
> configuración del proyecto y muestran resultados inflados.

---

## 9. Relación con `/implement-us`

El skill `/implement-us US-N.M.K` lee `docs/specs/incN/US-N.M.K.md` como input y ejecuta las
10 fases dentro de la branch `feature/US-N.M.K-descripcion`. Al terminar, se abre PR con
`/pr` y se mergea directo a `develop`. Aplica a US-IEDD **tipo `Feature`** — las 10 fases
asumen que hay código de dominio para implementar. Una US tipo `Spike`, `PoC` o `Modelado`
(§1, §2) no corre el pipeline completo: su trabajo se hace y se documenta directamente, y el
Issue cierra con la aprobación de Víctor, no con un PR de `/implement-us`.

```
# Ejemplo Incremento 3 — varias US individuales (BC Actividad Evaluativa, antes "Sesiones")

feature/US-3.1.1-crear-actividad-abierta  → /implement-us → /pr → merge develop
feature/US-3.1.2-set-aleatorio            → /implement-us → /pr → merge develop
feature/US-3.2.1-persistir-respuesta      → /implement-us → /pr → merge develop
...
(última US mergeada) → designreviewer src/ manual → verificar DoD Incremento 3 → mini-retro
```

---

*v1.7 — 2026-07-23. Corrige el gap señalado por v1.6: `Closes #N` **no** cierra el Issue en
este repo porque los PRs mergean a `develop`, no a `main` (rama default) — GitHub solo honra
esa keyword contra la rama default. Se reemplaza por el cierre manual explícito como paso 9a
(comentario con SHAs + `gh issue close`), detectado al cerrar `US-1.1.0` (Issue #5 quedó
abierto tras el merge) y confirmado como paso estándar del ciclo al cerrar `US-1.1.2`
(Issue #7, PR #15). También se documenta que Fase 3 de `/implement-us` no tiene checkpoint de
aprobación por tarea — solo Fases 1, 2 y 8 pausan — decisión tomada explícitamente para
reducir fricción en la ejecución de US ya planificadas y aprobadas.*

*v1.6 — 2026-07-20. Se corrige un gap real en §5 paso 8–9: el pipeline daba por hecho que "el
Issue se cierra automáticamente" al mergear el PR, pero nada garantizaba eso — el commit con
`[US-N.M.K]` no es una keyword de cierre de GitHub. Se agrega la instrucción explícita de
incluir `Closes #N` (número de Issue) en el body del PR, y se fija el checkpoint de aprobación
de Víctor en la apertura del PR (no en cada commit local). Detectado al preparar la ejecución
de `US-1.1.0` a `US-1.1.5`.*

*v1.5 — 2026-07-20. Se referencia explícitamente `docs/iedd/05-Fases-y-Gates.md` como fuente
conceptual: cada ciclo operativo de este documento (Iteración 0 — Modelado en §1, elaboración
de US en §3, quality gates en §8, cierre de Baseline en §7) queda marcado como instancia de un
gate del modelo conceptual (modelado, especificación, implementación, cierre), en vez de
quedar como práctica sin nombre formal. Motivado por la formalización del "gate de
especificación" (Definición de Listo para Especificar) durante la Iteración 1 del Incremento 1
(`US-1.1.0` a `US-1.1.5`).*

*v1.0 — 2026-07-13. Primera versión, adaptada del workflow validado en AtaraxiaDive:
terminología `incN` en vez de `spX`/SP (no hay nivel Subproyecto separado en Cognion — ver
PLAN-CM.md §14), capas Clean Architecture (`entities/use_cases/interface_adapters/frameworks`)
en vez de hexagonal DDD BC-first, y gate de UX + registro de aprendizajes incorporados desde
el inicio en vez de descubiertos sobre la marcha.*

*v1.3 — 2026-07-17. Se generaliza US-IEDD como esquema único de unidad de trabajo (§1, §2):
campo `Tipo` (`Feature | Spike | PoC | Modelado`) en el template de Issue, tabla de DoD por
Tipo (qué cuenta como Postcondición y su evidencia de cierre según el tipo), y labels
`tipo:*`. La Iteración 0 — Modelado (§1, §3 paso 0) deja de aprobarse de forma informal y pasa
a trackearse con GitHub Issues tipo `Modelado`, igual que cualquier otra unidad de trabajo —
el cierre del Issue con la aprobación de Víctor es la comprobación del DoD. Se aclara en §9
que el pipeline de 10 fases de `/implement-us` aplica solo a tipo `Feature`.*

*v1.4 — 2026-07-17. Se define el modelo de estado del Issue (§2, "Estado del Issue"): labels
`backlog` / `in-progress` / `blocked` mientras el Issue está abierto, uno solo a la vez; se
elimina el label `done` por redundante con el estado nativo `closed` — cerrar el Issue ya es
la señal de "terminado" (consistente con "cerrar el Issue es la comprobación del DoD",
v1.3).*

*v1.1 — 2026-07-14. Se incorpora la Iteración 0 — Modelado (§1, §3, §6): event storming del BC
más UX si corresponde, aprobados por Víctor antes de elaborar candidatas de US. Extiende a
dominio/backend la misma lección de AtaraxiaDive que ya motivaba el gate de UX — ver
`PLAN_v1.md`, sección "Modelado de dominio antes de construir, por BC".*

*v1.2 — 2026-07-14. Se agregan los ganchos explícitos de actualización de
`docs/traceability/matrix.md` (§3 pasos 0e y 3d, §5 paso 9b, §7 paso 4g): sin ellos, la matriz
solo se corregía en el barrido de un SP-ADJ (`PLAN-CM.md` §12) — es decir, después de que ya
divergió del código. Ahora RF y RNF avanzan de estado en el mismo commit/paso donde ocurre el
hecho que lo justifica.*
