# 07 · Verificación y testeabilidad

> Pregunta: ¿los tests prueban lo que importa, y la cobertura dice la verdad?

## Qué se miró

- Cantidad y distribución de tests en `tests/` y `frontend/`.
- `coverage.json` agregado por contexto y capa, y `[tool.coverage]` en `pyproject.toml`.
- `.github/workflows/ci.yml`, `tests/integration/conftest.py` y `frontend/vite.config.ts`.

No se ejecutó la suite.

## Fortalezas

- **Pirámide sana.** 1.197 tests unitarios, 674 de integración y 636 escenarios BDD. Los unitarios no tocan la base.
- **Dobles escritos a mano antes que mocks.** Solo 17 archivos de test usan `Mock` o `patch`, sobre unos 380. Los tests verifican comportamiento, no llamadas.
- **BDD atado a la especificación.** 113 archivos `.feature`, uno por historia, citados como evidencia en la matriz de trazabilidad.
- **La arquitectura tiene tests.** `test_guarda_arquitectura.py` prueba que cada contrato de `import-linter` detecta una violación sembrada.
- **Frontend con test por página.** 84 archivos de test para 94 páginas, más 9 circuitos de Playwright para la sesión en vivo.

## Hallazgos

### VT-01 · El 97 % de cobertura no mide el 37 % del código

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - `pyproject.toml`, línea 173: `omit = ["tests/*", "src/*/frameworks/*"]`.
  - `frameworks/` suma 8.447 de las 22.696 líneas del backend.
  - `fail_under = 0`: la cobertura no bloquea nada.
- **Por qué importa:** lo que queda sin medir es donde este informe encontró más problemas: routers con traducción de errores a mano ([IM-02](05-implementacion-por-capa.md#im-02--la-traducción-de-errores-a-http-está-repetida-a-mano)), adaptadores entre contextos ([AC-01](03-acoplamiento-entre-contextos.md#ac-01--ningún-contexto-publica-una-interfaz-el-consumidor-se-acopla-a-sus-internos)), el event store y el canal WebSocket. Los tests de integración ejercitan ese código, pero no se sabe cuánto. El número que se informa en cada baseline describe las capas internas, no el sistema.
- **Recomendación:** medir todo `src/` e informar dos números (capas internas y `frameworks/`). Fijar `fail_under` unos puntos por debajo del valor actual de cada uno.

### VT-02 · El umbral de cobertura y los circuitos E2E del frontend no corren en el CI

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - `vite.config.ts` define umbrales de 80 %, pero solo aplican con `npm run test:coverage`. El CI corre `npm run test` (`ci.yml`, línea 98).
  - Ningún workflow ejecuta Playwright.
- **Por qué importa:** el frontend concentra la mayor cantidad de correcciones del proyecto (29 de los 81 commits `fix`, ver [PR-01](11-proceso-iedd.md#pr-01--un-tercio-del-trabajo-especificado-es-retrabajo-detectado-en-uat)) y es donde el control automático es más débil. Los circuitos que prueban la sesión en vivo de punta a punta dependen de que alguien los corra a mano.
- **Recomendación:** `npm run test:coverage` en el CI, y un job de Playwright sobre la composición que ya levanta `imagen-smoke.yml`.

### VT-03 · La base de desarrollo está protegida por una regla, no por un mecanismo

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `tests/integration/conftest.py` ejecuta `DELETE FROM` sobre las tablas de la base que indique `DATABASE_URL`, sin comprobar cuál es. `CLAUDE.md` lo cubre con una regla operativa ("usar siempre una base descartable inline"), escrita después de que se vaciara la base de desarrollo.
- **Por qué importa:** una regla escrita depende de que quien corre los tests, persona o asistente, la recuerde cada vez. Ya falló una vez.
- **Recomendación:** que el `conftest.py` aborte si el nombre de la base no termina en `_test`. Son cinco líneas y vuelven innecesaria la regla.

### VT-04 · Los tests están organizados por incremento, no por lo que prueban

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** L (reorganizar), S (indexar)
- **Evidencia:**
  - `tests/unit/` tiene 11 carpetas `incN/`; los archivos se llaman por historia (`test_us_adj_63_hash_async.py`).
  - `fly.toml` se conserva, según su propio encabezado, "porque tests del Incremento 8 verifican su contenido", aunque Fly.io ya no se usa.
- **Por qué importa:**
  - Para saber qué tests cubren el agregado `Evaluacion` hay que buscar en todas las carpetas. La organización responde a "¿cuándo se escribió?", que solo importa para la trazabilidad, y no a "¿qué protege?", que importa cada vez que se cambia código.
  - Los tests de `fly.toml` verifican un archivo, no un comportamiento, y obligan a mantener un artefacto muerto.
- **Recomendación:** no mover todo. Ubicar los tests nuevos por contexto y capa (`tests/unit/<bc>/<capa>/`) y dejar la referencia a la historia en un marcador de pytest, que la matriz puede seguir consultando. Borrar los tests de `fly.toml` junto con el archivo.

### VT-05 · No hay prueba repetible de carga ni de historial

- **Vara:** Decisión · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:** el escenario de rendimiento tiene una sola medición (`quality/reports/uat/inc6/rendimiento-cierre.json`), tomada en desarrollo. No hay prueba con datos de varios años.
- **Por qué importa:** una medición única no detecta regresiones, y los hallazgos IM-06 y AC-03 afectan justo lo que no se vuelve a medir.
- **Recomendación:** convertir la medición en un script versionado que se corre al cerrar cada baseline con tag, contra la composición Docker.

## Juicio

La estrategia de tests es de lo mejor del proyecto: pirámide correcta, dobles propios, BDD trazado y arquitectura con tests. Los hallazgos son de medición y de mecanismo: el número de cobertura promete más de lo que mide, los controles del frontend no están conectados al CI, y la protección de la base depende de la memoria de quien ejecuta.
