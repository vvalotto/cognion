# Workflow de Desarrollo — Cognion

> Estado documental: vigente
> Fuente de verdad para: procedimiento operativo de branching, PRs, gestión de Issues/Milestones y ciclo de trabajo por US/Incremento
> Última actualización: 2026-07-13
> Fuente normativa relacionada: `docs/cm/PLAN-CM.md` (política) — este documento es el procedimiento que la ejecuta

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

---

## 2. Gestión Administrativa (GitHub)

### División de responsabilidades

| Artefacto | Dónde vive | Propósito |
|---|---|---|
| **GitHub Issue** | GitHub Issues | Fuente de verdad del estado — qué hay que hacer, criterios de aceptación, seguimiento |
| **`docs/specs/incN/US-N.M.K.md`** | Repositorio | Especificación US-IEDD — precondición, postcondición, invariantes, input de `/implement-us` |

### Estructura en GitHub

- **Milestones** = uno por Incremento (`Incremento 0 — Walking Skeleton`, `Incremento 1 — Banco de preguntas`, etc.)
- **Labels** = `us-iedd`, `incremento-0`, `incremento-1`, ..., `blocked`, `in-progress`, `done`
- **Sin Project board** — Milestones + Labels alcanzan para desarrollo en solitario

### Template de Issue (US-IEDD)

```markdown
## Descripción
Como <rol>, quiero <acción> para <valor>.

## Criterios de Aceptación
- [ ] ...

## Precondición
...

## Postcondición
...

## Invariantes
- INV-1: ...

## Referencias
- Incremento: N
- Bounded Context: ...
- docs/specs/incN/US-N.M.K.md
```

---

## 3. Ciclo de Elaboración de US por Incremento

```
1. Elaborar el archivo de US candidatas: docs/plans/incN/incN-candidatas.md
   → Lista todas las US del incremento con descripción, criterios y estimación
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
feat(entities): agregar aggregate Sesion [US-2.1.1]
fix(interface_adapters): corregir endpoint ranking provisional
test(entities): tests unitarios Sesion.cerrar_periodo
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
   → Fase 2 (plan): esperar aprobación explícita antes de continuar
   → Fase 8 (documentación): ídem
   → Fases 8 y 9 deben ejecutarse ANTES del commit final, no después
   → El skill no está completo hasta que docs/reports/{US_ID}-report.md exista en disco
6. [AUTO] CodeGuard corre en cada commit (pre-commit hook, advierte, no bloquea)
7. Commits atómicos con referencia: feat(entities): ... [US-N.M.K]
8. Abrir PR hacia develop con /pr → DesignReviewer corre en pre-push (bloquea si CRITICAL)
   → Usar siempre gh pr create --base develop (el default de gh es main)
9. Merge del PR — Issue se cierra automáticamente
```

---

## 6. Ciclo por Incremento

Un Incremento cierra cuando todas sus US-IEDD están mergeadas a `develop` y el DoD de
integración (definido en `PLAN_v1.md` para cada incremento) es verificable de punta a punta.

### Preparación al inicio del incremento

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
`/pr` y se mergea directo a `develop`.

```
# Ejemplo Incremento 2 — varias US individuales

feature/US-2.1.1-crear-sesion-abierta   → /implement-us → /pr → merge develop
feature/US-2.1.2-set-aleatorio          → /implement-us → /pr → merge develop
feature/US-2.2.1-persistir-respuesta    → /implement-us → /pr → merge develop
...
(última US mergeada) → designreviewer src/ manual → verificar DoD Incremento 2 → mini-retro
```

---

*v1.0 — 2026-07-13. Primera versión, adaptada del workflow validado en AtaraxiaDive:
terminología `incN` en vez de `spX`/SP (no hay nivel Subproyecto separado en Cognion — ver
PLAN-CM.md §14), capas Clean Architecture (`entities/use_cases/interface_adapters/frameworks`)
en vez de hexagonal DDD BC-first, y gate de UX + registro de aprendizajes incorporados desde
el inicio en vez de descubiertos sobre la marcha.*
