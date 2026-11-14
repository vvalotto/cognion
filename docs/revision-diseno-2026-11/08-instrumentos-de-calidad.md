# 08 · Instrumentos de calidad

> Pregunta: ¿los gates y las métricas miden bien, o están condicionando el diseño?

## Qué se miró

- `quality/reports/designreviewer/BL-016-designreviewer.json` y `quality/reports/architectanalyst/BL-016-arquitectura.json`.
- `[tool.designreviewer]`, `[tool.codeguard]` y `.pre-commit-config.yaml`.
- `.github/workflows/ci.yml`.
- Menciones a las métricas dentro del propio código de `src/`.

## Fortalezas

- **Gates en tres momentos** (commit, push, CI) con bloqueo real en tipos, imports y CBO.
- **`import-linter` reemplazó a una herramienta que no detectaba nada**, y la decisión está documentada con su causa.
- **Los falsos positivos conocidos están escritos**, con el enlace al defecto de la herramienta.
- **Dependabot activo** para dependencias.

## Hallazgos

### IQ-01 · El umbral de CBO está moldeando el diseño

- **Vara:** Decisión · **Severidad:** Alta · **Confianza:** Verificado · **Esfuerzo:** S (recalibrar), M (revertir los atajos)
- **Evidencia:** 34 menciones a CBO en docstrings de 25 archivos de `src/`. Ejemplos:
  - [`responder_pregunta_en_vivo.py`](../../src/actividad_evaluativa/use_cases/responder_pregunta_en_vivo.py), línea 82: una función "vive fuera de la clase para no sumar esas entidades y errores a su CBO".
  - `preguntas_controller.py`, línea 48: "el evento se tipa como `object` en esta capa — mismo criterio de reducción de CBO".
- **Por qué importa:** hay código escrito para que la métrica dé bien, no para que el diseño mejore. Sacar una función de la clase no reduce el acoplamiento real del módulo; solo lo esconde del analizador. Tipar como `object` es peor: se pierde información de tipos para ganar un punto. Cuando una medida se vuelve objetivo deja de medir, y esto pasa en el único gate de acoplamiento que bloquea.
- **Recomendación:**
  1. Recalibrar: que el CBO no cuente excepciones ni tipos de datos del propio contexto, o subir el umbral para routers y casos de uso.
  2. Revertir los `object` y devolver los tipos.
  3. Resolver [IM-02](05-implementacion-por-capa.md#im-02--la-traducción-de-errores-a-http-está-repetida-a-mano): con una jerarquía de errores, el acoplamiento que la métrica castiga baja de verdad.

### IQ-02 · 377 advertencias que nadie puede atender

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** en `BL-016`, DesignReviewer reporta 0 bloqueantes y 377 advertencias, con 304 horas estimadas de corrección:
  - 160 de método largo (umbral: 20 líneas), 71 de ellas en `frameworks/` y 61 en `use_cases/`.
  - 103 de Ley de Demeter (umbral: 1).
  - 31 de grupos de datos, 25 de envidia de funcionalidad, 24 de obsesión por primitivos.
- **Por qué importa:** un reporte con 377 ítems no se lee. Las advertencias útiles (las 24 de obsesión por primitivos coinciden con [DM-05](04-dominio-y-event-sourcing.md#dm-05--el-tipo-de-pregunta-se-resuelve-con-primitivos-y-isinstance)) quedan tapadas por ruido: el umbral de 20 líneas castiga funciones con docstrings largos, que este proyecto exige, y Demeter con umbral 1 marca cualquier cadena de atributos en un router.
- **Recomendación:**
  1. Que el total no pueda subir entre baselines (trinquete), en lugar de aspirar a cero.
  2. Excluir docstrings del conteo de método largo, o llevar el umbral a 40.
  3. Apagar Demeter en `frameworks/api/`.

### IQ-03 · Tres instrumentos del cierre de baseline no informan

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - ArchitectAnalyst reporta 8 violaciones críticas en `BL-016`; todas son el falso positivo "Zone of Pain", porque la herramienta calcula `Ca = Ce = 0` para todo el proyecto.
  - `LayerViolationsAnalyzer` nunca detecta violaciones (`CLAUDE.md` lo declara no confiable).
  - El chequeo de tipos de CodeGuard puede quedar mudo por un límite de tiempo de 10 segundos.
- **Por qué importa:** el cierre de baseline incluye un paso obligatorio cuyo resultado se sabe incorrecto de antemano. Un "crítico" que siempre se ignora enseña a ignorar los críticos. `CLAUDE.md` dedica más texto a explicar cómo no malinterpretar estas herramientas que a cualquier regla de diseño.
- **Recomendación:** sacar las métricas de distancia e inestabilidad del cierre hasta que el defecto de la herramienta esté corregido. `import-linter` ya cubre capas y contextos.

### IQ-04 · Lo que corre el CI no es lo que dicen las reglas

- **Vara:** Conformidad · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - `CLAUDE.md`: "validar con `tsc -b` (no `--noEmit` solo)". El CI ejecuta `npx tsc --noEmit` (`ci.yml`, línea 94).
  - El paso del CI se llama "ESLint" y ejecuta `oxlint`.
  - El hook de black usa `python3.12` y `pyproject.toml` apunta a `py311` ([CA-02](02-conformidad-arquitectonica.md#ca-02--la-versión-de-python-validada-no-es-la-que-corre)).
- **Por qué importa:** la regla de `tsc -b` nació de un error que `--noEmit` no detectaba. El CI sigue usando la variante que la regla descarta.
- **Recomendación:** que el CI llame a `npm run build` o a `tsc -b`, y corregir el nombre del paso.

### IQ-05 · No hay análisis automático de seguridad

- **Vara:** Decisión · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** ningún workflow ni hook ejecuta `pip-audit`, `npm audit`, `bandit` ni un escáner de imágenes. Solo Dependabot.
- **Por qué importa:** el sistema guarda datos personales de estudiantes y contraseñas. Los gates miden estructura con mucho detalle y seguridad con nada.
- **Recomendación:** `pip-audit` y `npm audit --omit=dev` en el CI, sin bloquear al principio.

### IQ-06 · El hook de push hay que activarlo a mano en cada clon

- **Vara:** Decisión · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `.githooks/pre-push` requiere `git config core.hooksPath .githooks` (`CLAUDE.md`). El CBO solo se mide ahí y en el CI.
- **Por qué importa:** el aviso de acoplamiento llega tarde, al pushear, cuando el trabajo ya está hecho. `CLAUDE.md` lo reconoce: un controller cerca del umbral "puede bloquear recién al pushear".
- **Recomendación:** un comando único (`make calidad` o un script) que corra lo mismo que el CI, usado en la fase 7 de `implement-us`.

## Juicio

El proyecto invierte mucho en medir y eso es una fortaleza poco habitual. Pero la inversión está desbalanceada: mucha precisión sobre estructura interna (CBO, largo de método, Demeter), ninguna sobre seguridad, y tres instrumentos que no informan. El caso del CBO (IQ-01) es el más importante porque ya cambió código para peor. La regla práctica: un instrumento que no puede fallar por una buena razón, o que falla por una mala, hay que recalibrarlo o retirarlo.
