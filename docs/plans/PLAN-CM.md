# Plan de Gestión de Configuración (CM) — Cognion

> Estado documental: vigente
> Fuente de verdad para: estructura de CM, baselines, jerarquía documental y quality gates
> Última actualización: 2026-07-13
> Basado en: adaptación del modelo de CM validado en AtaraxiaDive (mismo marco IEDD)

---

## 1. Propósito

Este documento define cómo Cognion gestiona la configuración de su desarrollo: qué se
considera un artefacto versionado (Configuration Item), cómo se agrupan en baselines
formales, qué jerarquía de autoridad resuelve contradicciones entre documentos, qué gates
de calidad y de diseño se aplican en cada nivel de trabajo, y cómo se capitaliza el
aprendizaje generado durante el desarrollo.

Es la fuente de verdad para todo lo anterior. Ante duda operativa sobre "cómo se hace esto
en Cognion", este documento manda — no un recuerdo de cómo se hizo en otro proyecto.

---

## 2. Estructura del proyecto

```
cognion/
├── CHANGELOG.md                   ← ver §7 — Keep a Changelog, actualizado en cada tag de baseline
├── .cm/                          ← Configuration Management
│   ├── baselines/                 ← BL-NNN.md (+ .json de reportes anexos)
│   └── changes/                   ← ver §8 — uso acotado, no registro paralelo
├── .githooks/
│   └── pre-push                   ← activa DesignReviewer, bloquea si CRITICAL
├── .pre-commit-config.yaml        ← black, isort, ruff, CodeGuard (advierte, no bloquea)
├── .github/workflows/              ← CI
├── docs/
│   ├── rf/                         ← RF_v1.md · RNF_v1.md · ARQ_v1.md · PLAN_v1.md (elicitación — no se reescriben retroactivamente)
│   ├── iedd/                       ← marco metodológico IEDD + hipótesis del ensayo (documentos de referencia)
│   ├── architecture/               ← vista de arquitectura vigente (deriva de ARQ_v1 + ADRs)
│   ├── design/
│   │   └── ux/                     ← wireframes-*.md + prototipos/*.html — ver §5, gate obligatorio pre-frontend
│   ├── adr/                        ← ADR-NNN — decisiones arquitectónicas ratificadas + ADR-TEMPLATE.md (ver §6)
│   ├── specs/                      ← incN/US-N.M.K.md — especificación IEDD detallada (precondición/postcondición/invariantes)
│   ├── plans/                      ← incN/ — US candidatas y planes por incremento
│   ├── reports/                    ← reportes de cierre de cada US (10 fases de /implement-us)
│   ├── traceability/matrix.md      ← RF → BC → Incremento → US-IEDD → estado — ver §6b, estados normalizados
│   ├── aprendizajes/               ← HITO-N.md — ver §9, registro separado de aprendizajes del ensayo
│   ├── cm/                         ← este documento, CHECKLIST-INSTALACION.md, WORKFLOW-DESARROLLO.md y PROCEDIMIENTO-UAT.md
│   └── inventario/                 ← mapa documental, si el volumen lo justifica
├── src/<bc>/                       ← backend BC-first — ver §3
├── frontend/                       ← React + TS + Tailwind — ver §4
├── quality/reports/                 ← evidencia codeguard/, designreviewer/, architectanalyst/ (backend)
└── tests/{unit,integration,features,uat}/incN/
```

**Regla de documentos de entrada vs. derivados** (lección explícita del proyecto de
referencia): `docs/rf/` y `docs/aprendizajes/` son documentos de **entrada** — capturan
elicitación y aprendizaje, no se corrigen retroactivamente para parecer vigentes. `docs/adr/`,
`docs/architecture/`, `docs/traceability/` son **derivados** — se actualizan cuando cambia
una decisión ratificada.

---

## 3. Estructura de `src/` — BC-first con Clean Architecture interna

Cognion usa Clean Architecture (ARQ_v1.md) sobre Bounded Contexts: Sesiones (Core),
Banco de preguntas, Identidad, Notificaciones, Analytics.

```
src/<bc>/
├── entities/          → reglas de negocio puras, sin dependencias externas
├── use_cases/          → orquestación de la aplicación; solo conoce entities/
├── interface_adapters/ → controllers, presenters, gateways; solo conoce use_cases/
└── frameworks/         → FastAPI routers, SQLAlchemy, WebSockets — implementa los puertos
```

Regla absoluta (equivalente a la regla hexagonal de AtaraxiaDive):

- `entities/` no importa nada fuera de su propio `entities/`
- `use_cases/` importa `entities/`, nunca `frameworks/` ni `interface_adapters/`
- `interface_adapters/` importa `use_cases/`, nunca `frameworks/` directamente ni al revés
- `frameworks/` implementa contratos definidos por capas internas — nunca las capas internas importan `frameworks/`
- Única excepción: cualquier capa puede importar `shared/entities/` (tipos y utilidades comunes sin lógica de negocio de un BC específico)
- Comunicación entre BCs: por puertos explícitos definidos en `entities/ports/` de cada BC — nunca imports directos entre BCs

DesignReviewer debe configurarse para detectar violaciones de esta regla automáticamente
(ver §10). El mapeo de capas para `[tool.architectanalyst.layers]` usa estos nombres, no los
genéricos `domain/application/infrastructure/api` de un perfil layered estándar — **esto es
exactamente el tipo de fricción de calibración documentada en el proyecto de referencia**:
las herramientas de calidad no derivan estos paths solas, hay que declararlos.

---

## 4. Frontend — estructura y quality gates

El frontend (React + TypeScript + Tailwind + shadcn/ui) **no está cubierto por CodeGuard ni
DesignReviewer** — ambas son herramientas Python-only del paquete `software_limpio`. El
frontend tiene su propio gate, separado:

| Nivel | Herramienta | Modo | Bloquea |
|---|---|---|---|
| Cada commit / PR | ESLint (`npm run lint`) | Manual o CI | Criterio a definir al configurar CI |
| UAT de flujos con frontend | Tests funcionales manuales | Manual | Debe aprobar antes de cerrar el incremento |

### CIs de frontend

Los artefactos de frontend se inventarían igual que los de backend, con prefijo propio:

| Prefijo | Tipo |
|---|---|
| `CI-F##` | Componente / página / hook de frontend |

Se registran en la misma baseline del incremento, en la misma tabla de "Inventario de
Configuration Items" — no en un inventario separado.

### Regla de clasificación de hallazgos de UAT (frontend vs. backend)

Cuando un UAT o una revisión manual encuentra un problema, **clasificar el track antes de
codear**, no después:

- El hallazgo **solo toca `frontend/`** → track informal. Sin spec, sin `/implement-us`.
  Commit descriptivo con referencia al hallazgo (ej: `fix(frontend): ajustar contraste botón [UAT-2.3-04]`).
- El hallazgo **toca cualquier archivo de `src/`** → track formal obligatorio: US-IEDD
  completa → spec → `/implement-us`.
- **Regla de pivote:** si al resolver algo "de UX" la primera acción termina siendo abrir
  `src/`, pivotar al track formal en ese momento — no seguir por el camino informal porque
  ya se empezó así.

Esta distinción evita dos fallas simétricas: sobre-formalizar un ajuste visual trivial, o
sub-formalizar un cambio que en realidad toca lógica de dominio.

---

## 5. Diseño UX — gate obligatorio antes de implementar frontend

Ninguna línea de código de `frontend/` se escribe sin un artefacto de diseño aprobado en
`docs/design/ux/`. Este gate existe porque, en el proyecto de referencia, saltearlo produjo
un incidente real y costoso: una US completa fue implementada, mergeada, y tuvo que
**revertirse por completo** porque el código nunca consultó el prototipo aprobado — la spec
se había escrito mirando el código existente en lugar del diseño (anti-patrón
"spec-validatoria"). El hallazgo se detectó recién en UAT, con 14 gaps críticos.

### Artefactos de `docs/design/ux/`

| Tipo | Formato | Propósito | Consumidor |
|---|---|---|---|
| Prototipo navegable | HTML autocontenido, en `prototipos/` | Validación visual e interactiva antes de especificar | Humano (revisión) |
| Spec de diseño | Markdown (`wireframes-*.md`, `decisiones-frontend.md`), en la raíz de la carpeta | Especificación técnica que la implementación debe seguir | `/implement-us` |

### Proceso (orden no opcional)

```
1. Prototipo HTML navegable
2. Validación humana (visual e interactiva — en el dispositivo real si el escenario de uso lo exige)
3. Iteración hasta aprobación
4. Spec Markdown formal (wireframes-*.md)
5. Commit de ambos artefactos
6. Aprobación humana del Markdown
```

Para Cognion, la validación en dispositivo real es especialmente relevante en el escenario
de sesión en vivo proyectada en el aula (RNF — Usabilidad, escenario de legibilidad en
proyección) — es el equivalente al caso del juez en pileta de AtaraxiaDive: una restricción
de uso físico que debe validarse antes de codear, no inferirse del código.

### Gate obligatorio en la spec de una US

Toda spec de una US que toca `frontend/` debe incluir un campo explícito:

```markdown
## Fuente de verdad UX
- docs/design/ux/wireframes-<pantalla>.md
- docs/design/ux/prototipos/prototipo-<pantalla>.html
```

Una spec de frontend sin este campo **no está completa** — el campo es evidencia de que la
consulta al diseño aprobado ocurrió, no una formalidad.

### Verificación al cerrar un incremento con artefactos UX

El prototipo aprobado *existir* no es suficiente. Al cerrar un incremento que incluyó
artefactos de `docs/design/ux/prototipos/`, hay que comparar pantalla por pantalla la
implementación React contra el prototipo aprobado. Si hay divergencia, se clasifica como
gap (regla de §4) y se resuelve antes de dar el incremento por cerrado.

---

## 6. Jerarquía de fuentes de verdad documental

Ante contradicción entre documentos, este orden de precedencia decide — definido una sola
vez, aquí:

```
Código y tests  >  Baselines (.cm/)  >  ADRs  >  Matriz de trazabilidad  >  CLAUDE.md  >  README.md
```

| Tema | Fuente de verdad | Regla de uso |
|---|---|---|
| Presentación breve | `README.md` | Solo síntesis de entrada, sin detalle |
| Estado operativo actual | `CLAUDE.md` | Resume y enlaza evidencia — no duplica |
| Cierres formales | `.cm/baselines/` | Manda sobre cualquier resumen |
| Decisiones arquitectónicas | `docs/adr/` | Registra decisión y trade-offs; se ratifica antes de consolidarse en `docs/architecture/` |
| Arquitectura vigente | `docs/architecture/` | Debe contrastarse contra `src/` real |
| Diseño UX aprobado | `docs/design/ux/` | Fuente de verdad de la implementación de `frontend/` — ver §5 |
| Trazabilidad | `docs/traceability/matrix.md` | RF → BC → Incremento → US → estado |
| Especificaciones US-IEDD | `docs/specs/` | Input directo de `/implement-us` |
| Workflow de desarrollo | `docs/plans/WORKFLOW-DESARROLLO.md` | Si difiere de CLAUDE.md, manda el workflow |
| Requerimientos funcionales elicitados | `docs/rf/RF_v1.md` | Catálogo base — histórico una vez que hay ADRs/specs que lo detallan |
| Atributos de calidad | `docs/rf/RNF_v1.md` | Fuente de escenarios de calidad |
| Arquitectura de referencia inicial | `docs/rf/ARQ_v1.md` | Punto de partida — pasa a histórico cuando `docs/architecture/` diverge y se reconcilia vía ADR |
| Aprendizajes del ensayo | `docs/aprendizajes/HITO-N.md` | Ver §9 — no reemplaza fuentes vigentes, es evidencia experimental |

### Convención de estado documental (obligatoria en cada documento)

Todo documento de Cognion debe declarar su estado en el encabezado:

```md
> Estado documental: vigente | histórico | evidencia | operativo | derivado | superseded
> Fuente de verdad para: <tema>          (solo si vigente)
> Conservado como evidencia de: <qué>     (solo si histórico/evidencia)
> Última actualización: AAAA-MM-DD
```

Regla: un plan o decisión que quedó obsoleto **no se corrige para parecer vigente** — se
rotula como histórico y se referencia la fuente vigente que lo reemplaza.

### Template de ADR (obligatorio)

Todo ADR de Cognion sigue la misma estructura, definida en `docs/adr/ADR-TEMPLATE.md`:

```markdown
# ADR-NNN — <Título de la decisión>

**Estado:** Propuesto / Aceptado / Superseded
**Fecha:** AAAA-MM-DD

## Contexto
## Opciones Consideradas
## Decisión
## Justificación
## Impacto en Configuración
## Consecuencias
```

La sección **"Impacto en Configuración" es obligatoria para todo ADR que decide stack,
librería o driver** (no para decisiones puramente de dominio) — debe listar explícitamente
qué archivos del proyecto (`pyproject.toml`, `docker-compose.yml`, `.env.example`, etc.)
deben actualizarse como consecuencia de la decisión. Un ADR de stack sin esta sección está
incompleto: es exactamente el problema que un ADR de referencia (AtaraxiaDive ADR-007) dejó
sin resolver — la decisión quedó documentada pero `pyproject.toml` divergió de ella hasta
que alguien lo detectó a mitad de implementación.

### Estados normalizados — Matriz de trazabilidad

`docs/traceability/matrix.md` usa estos cuatro estados, sin excepción — evitar términos
ambiguos como "definido" sin calificar a cuál de los cuatro corresponde:

| Estado | Significado | Autoridad que lo certifica |
|---|---|---|
| **Planificado** | Existe intención en `PLAN_v1.md`, sin especificación formal | `docs/plans/` |
| **Especificado** | Tiene US-IEDD con precondición/postcondición/invariantes | `docs/specs/` |
| **Implementado** | Código integrado en `develop` | Tests unitarios pasando + revisión de código |
| **Validado** | Tests + UAT + baseline de cierre | `.cm/baselines/` |

Un RF puede mapearse a más de un Incremento si su implementación es incremental — en ese
caso, el estado de la matriz es el del Incremento menos avanzado que todavía lo cubre.

---

## 7. Configuration Items (CI) y Baselines

### Qué es un CI

Cualquier artefacto versionado que el CM debe rastrear: puerto, adaptador, migración,
config, test, decisión, plan, componente de frontend, herramienta. Se numeran con prefijo
estable por tipo — el ID no se reutiliza aunque el artefacto cambie:

| Prefijo | Tipo |
|---|---|
| `CI-D##` | Documento / decisión |
| `CI-C##` | Código de backend |
| `CI-F##` | Código de frontend (ver §4) |
| `CI-T##` | Herramienta / configuración de herramienta |

### Cuándo se abre/cierra una Baseline

Una **Baseline (BL-NNN)** se abre en Fase 0 (pre-código) y se cierra al terminar cada
Incremento del `PLAN_v1.md`. A diferencia de AtaraxiaDive (que usa "Subproyecto" como nivel
separado de "Incremento"), en Cognion el **Incremento es la única unidad de baseline** — ver
§14 (Convenciones de nomenclatura). El cierre de baseline coincide siempre con un tag git.

| Momento | Baseline | Tag esperado |
|---|---|---|
| Fase 0 — fundación documental (este momento) | BL-000 | `v0.0.0` → `v0.1.0` al cerrar Fase 0 |
| Cierre de cada Incremento de `PLAN_v1.md` (0 a 6) | BL-001, BL-002, ... | `v0.N.0` |

Ver §13 para la jerarquía completa de trabajo.

### Estructura del archivo de Baseline

```markdown
# BL-NNN — <Nombre del incremento/hito>

| Campo | Valor |
|-------|-------|
| Tipo | Fundacional / Incremento |
| Fecha apertura | AAAA-MM-DD |
| Fecha cierre | AAAA-MM-DD |
| Git tag inicial | ... |
| Git tag cierre | ... |
| Estado | ✅ Completado / 🔶 En curso |
| DoD | <criterio verificable de cierre, tomado del hito de PLAN_v1.md> |

## Descripción
<qué implementó este incremento, una frase>

## Inventario de Configuration Items
<tabla CI | artefacto | tipo | descripción — backend y frontend juntos, una tabla por iteración/US>

## Métricas al cerrar
<tests, cobertura, violations CRITICAL, LOC, resultado de ESLint>

## Decisiones técnicas relevantes
<tabla decisión → contexto — esto reemplaza un registro de cambios separado, ver §8>

## Retrospectiva
### ¿Qué funcionó?
### ¿Qué fue más difícil de lo esperado?
### ¿Qué ajustar en el próximo incremento?
```

La retrospectiva de baseline es un **resumen de cierre** — no reemplaza un HITO de
aprendizaje (§9), que es un análisis profundo de un hallazgo puntual y puede escribirse a
mitad de incremento.

### CHANGELOG.md

`CHANGELOG.md` (raíz del repo) es distinto de la retrospectiva de baseline: la retrospectiva
es interna/técnica (qué funcionó, qué ajustar); el CHANGELOG es de cara a quien usa o lee el
proyecto desde afuera (qué cambió, en qué versión). Formato
[Keep a Changelog](https://keepachangelog.com/es/1.0.0/) +
[Semantic Versioning](https://semver.org/lang/es/):

```markdown
# Changelog

Todos los cambios notables de Cognion se documentan en este archivo.

Formato: Keep a Changelog · Versionado: Semantic Versioning

---

## [Unreleased]

## [0.1.0] - AAAA-MM-DD

### Added
- <funcionalidad nueva del incremento>

### Changed
### Fixed
```

Se actualiza **al cerrar cada Incremento** (mismo momento que el tag git de la baseline, §7),
con una entrada nueva por versión. No se actualiza commit a commit — el detalle de cada
commit ya vive en el historial de git y en la baseline.

---

## 8. Gestión de cambios — decisión explícita

En el proyecto de referencia, `.cm/changes/` quedó definido pero sin uso real: el registro
de cambios terminó viviendo en la sección "Decisiones técnicas relevantes" de cada baseline.

**Decisión para Cognion:** no mantener `.cm/changes/` como registro paralelo. Todo cambio
técnico relevante se documenta directamente en la baseline del incremento en curso, en su
sección "Decisiones técnicas relevantes". Si en la práctica surge la necesidad real de un
registro de cambios independiente (por ejemplo, cambios que no encajan en ningún incremento
abierto), se reabre esta decisión y se actualiza este documento — no se crea la carpeta
"por si acaso".

---

## 9. Registro de aprendizajes — `docs/aprendizajes/`

Cognion es, según `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md` §8,
candidato a ser el **segundo proyecto de control** para contrastar la hipótesis del ensayo
IEDD validada en AtaraxiaDive. Este registro no es documentación accesoria — es donde vive
la evidencia empírica de ese contraste.

### Por qué es una carpeta separada, no una sección de la baseline

La retrospectiva de baseline (§7) resume el cierre de un incremento completo. Un **HITO**
es distinto en tres sentidos:

- Documenta **un hallazgo puntual** (una fricción, un anti-patrón, una hipótesis
  confirmada o refutada) — no un resumen general.
- Puede escribirse **en cualquier momento**, no solo al cerrar un incremento — el hallazgo
  de HITO-29 en AtaraxiaDive (spec-validatoria, §5) ocurrió a mitad de un Subproyecto (equivalente a un Incremento en Cognion).
- Tiene numeración **secuencial única para todo el proyecto**, no por incremento — un HITO
  se referencia por su número desde cualquier otro documento sin ambigüedad temporal.

### Cuándo escribir un HITO

- Una fricción técnica no anticipada por los ADRs o la especificación
- Un anti-patrón detectado en el propio proceso de trabajo (ej: spec escrita mirando código en vez de diseño aprobado)
- Confirmación o refutación de algún punto de la hipótesis del ensayo (`docs/iedd/04-Hipotesis...md`)
- Una decisión metodológica que ajusta el propio proceso IEDD para lo que sigue del proyecto

No se escribe un HITO por cada commit ni por cada corrección menor — es para hallazgos que
alguien más (o el propio Víctor, meses después) necesitaría leer para entender por qué algo
se hizo de una manera determinada, o qué se aprendió que cambió el proceso.

### Estructura

```
docs/aprendizajes/
├── HITO-template.md      ← plantilla, ver más abajo
├── HITO-1-<slug>.md
├── HITO-2-<slug>.md
└── ...
```

### Template

```markdown
# HITO-N — <Título del hallazgo>

| Campo | Valor |
|-------|-------|
| **Documento** | HITO-N — <una línea de clasificación> |
| **Fecha** | AAAA-MM-DD |
| **Incremento / contexto** | <dónde ocurrió> |
| **Relacionado** | <ADRs, HITOs previos, PRs, Issues> |

## Contexto
<qué se estaba haciendo cuando surgió el hallazgo>

## Hallazgo / Análisis
<qué pasó, por qué, causa raíz si aplica>

## Aprendizaje(s)
- **L-N.M:** <aprendizaje concreto, accionable>

## Relación con la hipótesis del ensayo
<qué punto de docs/iedd/04-Hipotesis...md confirma, refuta o matiza este hallazgo — opcional si no aplica>

## Resumen de Aprendizajes
| ID | Aprendizaje | Impacto |
|----|-------------|---------|
| L-N.M | ... | Workflow / Quality / Documentación / Proceso |
```

Cada HITO que tenga relación directa con la hipótesis del ensayo debe citarse desde
`docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md` al actualizarlo, igual
que AtaraxiaDive lo hace en su §5.

---

## 10. Quality Gates por nivel

| Nivel | Herramienta | Modo | Bloquea |
|---|---|---|---|
| Cada commit (backend) | CodeGuard | Automático (pre-commit) | No — solo advierte |
| Cada push (backend) | DesignReviewer | Automático (pre-push) | Sí, si hay CRITICAL |
| Frontend (§4) | ESLint | Manual o CI | A definir |
| Cierre de Incremento | DesignReviewer manual + verificación UX si aplica (§5) | Manual | Confirmar 0 CRITICAL + prototipo implementado |
| UAT (flujo end-to-end del incremento) | Dos capas, entorno propio o staging según el momento — ver `PROCEDIMIENTO-UAT.md` | Manual | Debe aprobar antes de dar el incremento por cerrado |
| Cierre de Baseline | ArchitectAnalyst | **Siempre manual** — el valor está en la lectura consciente del reporte, no en automatizarlo | Informa tendencias, no bloquea |

Notas operativas (lecciones ya pagadas en el proyecto de referencia, aplican igual acá):

- `designreviewer` **siempre** con `--config pyproject.toml` explícito — sin el flag usa
  defaults genéricos (CBO=5, WMC=20) que no reflejan la configuración real del proyecto y
  producen falsos positivos.
- `.githooks/pre-push` no se activa solo al clonar — requiere
  `git config core.hooksPath .githooks` una vez por clon. Documentarlo en `CLAUDE.md`.
- Los umbrales de `[tool.designreviewer]` (`max_cbo`, `max_wmc`, `max_god_object_*`) se
  estiman **al inicio de cada incremento completo**, no US por US — estimaciones optimistas
  generan bloqueos de push a mitad de incremento.

---

## 11. Versionado, Entregas y Builds

### Versionado (Semantic Versioning)

El tag de cada baseline (§7) sigue SemVer con esta semántica específica para Cognion:

| Componente | Dispara en | Ejemplo |
|---|---|---|
| **MAJOR** | Paso de demo/desarrollo a operación real con usuarios reales (docente/estudiantes de una cursada real) | `v0.6.0 → v1.0.0` |
| **MINOR** | Cierre de cada Incremento de `PLAN_v1.md` | `v0.1.0 → v0.2.0` |
| **PATCH** | Un SP-ADJ (§12) o fix posterior a un Incremento ya tagueado | `v1.0.0 → v1.0.1` |

Antes de la primera operación real, todos los tags son `v0.N.0` — no hay releases `1.x`
"de mentira". El salto a `v1.0.0` es una decisión explícita, no automática por conteo de
incrementos.

### Entregas — baseline interna vs. release desplegado

Una **baseline** (`.cm/baselines/BL-NNN.md`) es un cierre de CM: tag + inventario de CIs +
métricas. Un **release desplegado** es distinto: es la baseline efectivamente corriendo en
el entorno de destino (Fly.io u otro). No son automáticamente lo mismo — un incremento
puede cerrar su baseline sin desplegarse de inmediato si no hay motivo de negocio para
hacerlo. Cuando coinciden (deploy inmediato al cerrar), el `CHANGELOG.md` (§7) documenta
ambos eventos en la misma entrada de versión.

### Incrementos de infraestructura como ciudadanos de primera clase

El despliegue, la configuración de CI/CD y demás trabajo de infraestructura **no es una
tarea implícita de cierre** — se trata como un Incremento más, con su propia
precondición/postcondición/invariante y DoD, igual que un incremento de dominio (lección
HITO-34 del proyecto de referencia: tratarlo como tarea de cierre sin DoD propio hace
invisibles los problemas reales del entorno de producción, que es "un oráculo distinto al
entorno de desarrollo").

| Aspecto | Incremento de dominio | Incremento de infraestructura |
|---|---|---|
| Precondición | Estado del modelo de negocio | Estado del entorno y configuración |
| Postcondición | Comportamiento observable del dominio | Servicio accesible y saludable en el entorno destino |
| Invariante | Regla de negocio que no puede violarse | Tests no regresionan · pipeline verde · servicio disponible |
| Quality gate | DesignReviewer · CodeGuard | Pipeline de CI/CD verde · healthcheck 200 |
| Evidencia | Tests BDD + unit + integración | Log del pipeline · respuesta del healthcheck en el entorno destino |

Ejemplo de DoD para un incremento de infraestructura (ej. el propio Incremento 0 de
`PLAN_v1.md`, que incluye CI/CD):

```
Precondición: tag de la baseline anterior en main, tests verdes en local
Postcondición: pipeline de GitHub Actions ejecuta test → build → deploy sin fallos
               y el healthcheck del entorno destino responde 200
Invariante: sin degradación de tests, sin cambios no intencionales en el dominio
```

### CI/CD — pipeline automático (decisión para Cognion)

A diferencia del proyecto de referencia (que terminó con deploy manual `fly deploy` por
pragmatismo, dejando su único workflow de GitHub Actions únicamente para el listener de
`@claude`), Cognion adopta **CI/CD automático real**, consistente con lo ya decidido en
`ARQ_v1.md`:

```
push/PR a develop → GitHub Actions:
  1. lint + type-check (ruff, mypy, eslint)
  2. tests (pytest backend, tests frontend si existen)
  3. designreviewer --config pyproject.toml (bloquea si CRITICAL — redundante con el
     pre-push hook local, pero necesario porque CI corre en un entorno limpio que no
     depende de que el hook esté configurado en la máquina del desarrollador)

merge/tag a main → GitHub Actions adicional:
  4. build de la imagen Docker (multi-stage: frontend build → backend runtime)
  5. deploy automático al entorno de destino (Fly.io u otro, según ítem abierto de ARQ_v1.md)
  6. verificación de healthcheck post-deploy
```

Pasos 1–3 corren en cada push/PR a `develop`. Pasos 4–6 corren solo en merge/tag a `main`
— el deploy automático nunca se dispara desde una branch de feature.

### Empaquetado — convención de Dockerfile

Multi-stage, análogo al del proyecto de referencia pero sin la complejidad de volúmenes
SQLite (Cognion ya decidió PostgreSQL — RNF_v1.md, ARQ_v1.md — por lo que la persistencia
va contra una base de datos administrada, no contra un volumen del contenedor):

```dockerfile
# Stage 1: Frontend build
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --ignore-scripts
COPY frontend/ .
RUN npm run build

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev
COPY src/ ./src/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist
ENV PYTHONPATH=/app/src
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

La imagen no incluye archivos de datos ni migraciones aplicadas — `alembic upgrade head`
corre como paso separado del pipeline de deploy, no dentro del build de la imagen.

---

## 12. SP-ADJ — ajuste técnico y documental antes de cerrar una baseline

Al cierre de cada Incremento (unidad de baseline en Cognion, §7), evaluar
si hay deuda acumulada — técnica o documental — que justifique un **SP-ADJ**: un ciclo corto
de ajuste antes de arrancar el siguiente incremento.

Un SP-ADJ incluye **siempre** un barrido de consistencia documental:

- `docs/architecture/` alineada con la estructura real de `src/`
- `docs/design/ux/` sin prototipos aprobados que el código todavía no implementa (§5)
- `CLAUDE.md` actualizado con el estado real del incremento
- `docs/traceability/matrix.md` sin US sin cerrar
- `docs/adr/` consolidados en `docs/architecture/` si generaron decisiones nuevas

Sin este barrido periódico, la arquitectura documentada y el código real divergen
silenciosamente — es la causa raíz identificada detrás del anti-patrón de §5.

---

## 13. Jerarquía de trabajo

```
Incremento (PLAN_v1.md, 0–6) → Baseline (BL-NNN) + tag git + Milestone GitHub
  └── Iteración (dentro del incremento) → DoD de integración verificable
        └── US-IEDD → GitHub Issue + docs/specs/incN/US-N.M.K.md + branch feature/ + /implement-us
              (+ SP-ADJ entre incrementos si hay deuda acumulada, ver §12)
```

Esta jerarquía formaliza lo que `PLAN_v1.md` ya definió (Incremento → Iteración) y lo conecta
con el mecanismo de baseline y con US-IEDD, que todavía no existían como unidad de trabajo en
ese documento. El detalle operativo completo (branching, PRs, template de Issue, ciclo por
US/Incremento, gate de consulta UX antes de specs de frontend) se define en
`docs/plans/WORKFLOW-DESARROLLO.md` al iniciar el Incremento 0 — este documento es el plan
de CM; el workflow es el procedimiento operativo que lo ejecuta.

---

## 14. Convenciones de nomenclatura

Toda referencia a `spX`/`SP1`/`Subproyecto` de un documento externo (ej. AtaraxiaDive) se
traduce a `incN`/`Incremento` en Cognion — no existe un nivel de Subproyecto separado del
Incremento (ver §7).

| Artefacto | Patrón | Ejemplo | Ubicación |
|---|---|---|---|
| Baseline | `BL-NNN-slug-descriptivo.md` | `BL-001-incremento-0-walking-skeleton.md` | `.cm/baselines/` |
| Configuration Item | `CI-{D\|C\|F\|T}##` | `CI-C08` | tabla dentro de la baseline |
| ADR | `ADR-NNN-slug-en-kebab.md` | `ADR-003-sqlite-vs-postgresql.md` | `docs/adr/` |
| HITO | `HITO-N-SLUG-EN-MAYUSCULAS.md` | `HITO-1-WALKING-SKELETON-FRICCION.md` | `docs/aprendizajes/` |
| US-IEDD | `US-{incremento}.{iteración}.{secuencial}` | `US-2.3.1` | `docs/specs/incN/` |
| Spec de US | `docs/specs/incN/US-N.M.K.md` | `docs/specs/inc2/US-2.3.1.md` | — |
| Branch de US | `feature/US-N.M.K-descripcion-corta` | `feature/US-2.3.1-registrar-respuesta` | kebab-case, máx. 4 palabras, español |
| Branch incremento técnico | `feature/inc-N-descripcion-corta` | `feature/inc-0-fundacion-tecnica` | sin US-IEDD asociada |
| Branch de fix | `fix/descripcion-corta` | `fix/invariante-sesion-nula` | — |
| SP-ADJ | `SP-ADJ-NN` | `SP-ADJ-01` | `docs/plans/sp-adj-NN/` |
| Wireframe UX | `wireframes-<pantalla-o-rol>.md` | `wireframes-docente-banco.md` | `docs/design/ux/` |
| Prototipo UX | `prototipo-<pantalla-o-rol>.html` | `prototipo-docente-banco.html` | `docs/design/ux/prototipos/` |
| Label GitHub | `us-iedd`, `incremento-N`, `blocked`, `in-progress`, `done` | `incremento-2` | Issues |
| Milestone GitHub | `Incremento N — <nombre de PLAN_v1.md>` | `Incremento 2 — Sesión de período abierto` | Milestones |
| Commit (Conventional Commits) | `tipo(scope): descripción [US-N.M.K]` | `feat(entities): agregar aggregate Sesion [US-2.1.1]` | — |

**Nota sobre `SP-ADJ`:** el prefijo conserva "SP" por convención heredada (identifica el
patrón, no una unidad de baseline) — no implica que Cognion tenga un nivel de Subproyecto.

---

## 15. Herramientas requeridas

El detalle completo de instalación (uv, gh, quality-agents, Claude Dev Kit, hooks y
commands de gestión de sesión) vive en `docs/plans/CHECKLIST-INSTALACION.md` — no se
duplica aquí.

---

## 16. Próximo paso

Con el plan de CM, el checklist de instalación y el workflow de desarrollo ya definidos
(`docs/plans/PLAN-CM.md`, `docs/plans/CHECKLIST-INSTALACION.md`, `docs/plans/WORKFLOW-DESARROLLO.md`),
el siguiente paso es ejecutar el checklist de instalación y arrancar el Incremento 0
(Walking Skeleton) de `PLAN_v1.md` siguiendo el ciclo definido en `WORKFLOW-DESARROLLO.md` §6.
