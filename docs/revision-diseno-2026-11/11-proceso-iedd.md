# 11 · Proceso IEDD

> Pregunta: ¿el proceso produce calidad a un costo razonable?

## Qué se miró

- `docs/iedd/05-Fases-y-Gates.md`, las fases del skill `implement-us` y `CLAUDE.md`.
- Historia de git: 1.204 commits y 250 merges entre 2026-06-24 y 2026-11-13.
- `docs/specs/` (176 especificaciones), `.cm/baselines/` y `docs/aprendizajes/`.
- `quality/reports/metricas/implement-us-tiempos.json`.

Se evalúa el proceso por lo que dejó en el repositorio. No se observó ninguna sesión de trabajo.

## Fortalezas

- **Trazabilidad de punta a punta.** De un requerimiento se llega a su historia, su especificación, sus escenarios BDD, su reporte y su baseline. Es raro verlo completo, y acá está.
- **Gates humanos explícitos antes de escribir código**: modelado por contexto, diseño de UX aprobado, especificación. El gate de UX nació de un error real en un proyecto anterior y está justificado por escrito.
- **El proceso aprende.** Nueve documentos `HITO` registran errores con su causa, y varias reglas de `CLAUDE.md` citan el incidente que las originó.
- **Velocidad medida.** 102 historias con mediana de 29,7 minutos de implementación asistida.
- **Integración disciplinada.** Rama por historia, PR a `develop`, rama protegida, commits con convención.

## El proceso en números

| Indicador | Valor |
|---|---|
| Especificaciones escritas | 176 |
| De ajuste (`docs/specs/ajustes/`) | 62 (35 %) |
| Historias medidas por `implement-us` | 102, de las cuales 40 son de ajuste |
| Commits `fix` | 81; 29 de ellos en `frontend` |
| Commits por tipo | `docs` 280 · `feat` 237 · `chore` 159 · `test` 106 · `fix` 81 |
| Documentación | 85.089 líneas, contra 22.696 de backend |

## Hallazgos

### PR-01 · Un tercio del trabajo especificado es retrabajo detectado en UAT

- **Vara:** Decisión · **Severidad:** Alta · **Confianza:** Verificado (las cifras), Inferido (la causa) · **Esfuerzo:** M
- **Evidencia:**
  - 62 de 176 especificaciones son de ajuste, y 40 de las 102 historias medidas.
  - El ámbito con más correcciones es `frontend` (29 de 81), y sus hallazgos van por un camino informal sin especificación.
  - Las iteraciones de ajuste (`3-ADJ` a `7-ADJ`) siguen a casi todos los incrementos funcionales.
- **Por qué importa:** cada historia pasa por diez fases y varios gates, y aun así uno de cada tres ciclos corrige algo que esos gates no vieron. Los gates automáticos miden estructura (tipos, capas, CBO); los defectos que escapan son de comportamiento visible e integración, y los encuentra una persona mirando la pantalla, al final. Es el control más caro y el más tardío.
- **Recomendación:** mover la detección hacia antes, con controles que ataquen esa clase de defecto:
  1. Contrato generado entre backend y frontend ([FE-01](09-frontend.md#fe-01--el-contrato-con-el-backend-se-copia-a-mano)).
  2. Playwright en el CI ([VT-02](07-verificacion-y-testeabilidad.md#vt-02--el-umbral-de-cobertura-y-los-circuitos-e2e-del-frontend-no-corren-en-el-ci)).
  3. Clasificar cada ajuste por causa (especificación incompleta, diseño de UX, integración, regresión) y medir la proporción por incremento. Hoy el dato existe y no se usa.

### PR-02 · Todos los gates humanos los pasa la misma persona

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - El equipo es unipersonal: quien especifica, aprueba el diseño, revisa el PR, ejecuta la UAT y cierra la baseline es la misma persona, y el código lo escribe un asistente.
  - `BL-015` se cerró "sin UAT formal", contra la regla del propio proceso.
- **Por qué importa:** un gate vale por la independencia de quien lo pasa. Con una sola persona, la revisión de PR y la UAT comparten los mismos supuestos que la especificación. Y cuando hay apuro, el gate que se omite es el manual. Este informe encontró varios problemas (IM-03, AC-01, DM-01) que una segunda mirada habría visto antes.
- **Recomendación:**
  1. Una revisión independiente automatizada como gate del PR: otro asistente, sin el contexto de la implementación, que revise contra la especificación y las reglas de arquitectura.
  2. Para baselines con tag, una UAT hecha por alguien que no escribió la especificación: un ayudante o un grupo de alumnos. Además es material de cátedra.

### PR-03 · El peso documental es alto para un equipo de uno

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:**
  - 766 archivos Markdown y 85.089 líneas, casi cuatro veces el backend.
  - `docs` es el tipo de commit más frecuente (280, contra 237 de `feat`).
  - Por historia se generan especificación, plan y reporte: `docs/plans/` tiene 340 archivos, `docs/reports/` 157 y `docs/specs/` 176.
- **Por qué importa:** la documentación que se genera una vez y nadie vuelve a leer no molesta. La que tiene que seguir siendo cierta sí cuesta, y ya hay señales de que no se llega a mantenerla ([capítulo 12](12-documentacion.md)). El proyecto es además un caso de validación del método, y eso justifica más evidencia de la habitual; pero conviene separar qué es evidencia y qué es documentación viva.
- **Recomendación:** dos categorías explícitas. **Evidencia** (planes, reportes, trackers): se genera, se archiva, no se mantiene ni se audita. **Documentación viva** (arquitectura, ADR, instalación, `CLAUDE.md`, `README.md`): pocos documentos, con dueño y con revisión en cada cierre.

### PR-04 · Las lecciones se guardan como reglas escritas, no como mecanismos

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S por regla
- **Evidencia:** `CLAUDE.md` acumula reglas nacidas de incidentes, cada una con su explicación:
  - "`designreviewer` siempre con `--config pyproject.toml`".
  - "`architectanalyst` siempre con `--config`" y "generar `coverage.json` antes".
  - "Usar siempre una base descartable inline".
  - "Nunca `prettier --write`".
  - "El hook no se activa solo al clonar".
- **Por qué importa:** cada regla es una carga para quien ejecuta, y su cumplimiento depende de que se lea. El archivo crece con cada incidente (287 líneas) y es el contexto que el asistente carga en cada sesión. Casi todas estas reglas pueden reemplazarse por algo que no se pueda hacer mal.
- **Recomendación:** por cada regla operativa, preguntar si puede ser un mecanismo:
  - Un script `calidad.sh` que llame a las herramientas con sus opciones y en su orden.
  - La guarda del `conftest.py` ([VT-03](07-verificacion-y-testeabilidad.md#vt-03--la-base-de-desarrollo-está-protegida-por-una-regla-no-por-un-mecanismo)).
  - Un hook que rechace commits con reformateo masivo en `frontend/`, en lugar de la prohibición escrita de `prettier`.
  - Un paso de instalación que configure `core.hooksPath`.

### PR-05 · Las métricas del proceso se dejaron de tomar

- **Vara:** Conformidad · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `implement-us-tiempos.json` tiene 102 historias; la última empezó el 2026-09-15 (Incremento 5-ADJ). Los incrementos 6 a 10 no están.
- **Por qué importa:** el proyecto valida un método. Los incrementos sin medir incluyen el más complejo (sesión en vivo) y los de despliegue, que son los que dirían si el método se sostiene fuera del caso fácil.
- **Recomendación:** regenerar el reporte con los trackers existentes y agregarlo al cierre de baseline.

### PR-06 · El plan original quedó chico y la nomenclatura lo arrastra

- **Vara:** Conformidad · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `PLAN_v1.md` define 7 incrementos (0 a 6) y el proyecto va por el 10.1. La versión publicada es `1.0.0` con `RF-07` y `RF-18` del alcance v1 sin implementar. `CLAUDE.md` todavía dice "Incremento (PLAN_v1.md, 0–6)".
- **Por qué importa:** replanificar es sano. Pero "v1" significa dos cosas distintas (el alcance definido y la versión publicada), y eso confunde qué falta.
- **Recomendación:** un `PLAN_v2.md` corto que diga qué es `1.x`, qué pasó con `RF-07` y `RF-18`, y qué sigue.

## Juicio

El proceso logra lo que se propone: trazabilidad completa y un producto que funciona, con un equipo de una persona. Su costo está en dos lugares: detecta tarde los defectos de comportamiento (PR-01) y produce más texto del que se puede mantener cierto (PR-03, PR-04). Ninguno de los dos se resuelve agregando gates; se resuelven cambiando controles manuales y reglas escritas por mecanismos automáticos.
