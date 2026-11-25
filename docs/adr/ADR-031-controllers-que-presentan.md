# ADR-031 — Los controllers presentan: devuelven tipos de salida propios y los routers no importan el dominio

**Estado:** Aceptado
**Fecha:** 2026-11-25
**Origen:** Issue [#667](https://github.com/vvalotto/cognion/issues/667), hallazgos `IM-01` y `CA-03` de la revisión de diseño (`docs/revision-diseno-2026-11/`); decidido con Víctor en la Iteración 2 del Incremento 12. Relacionado con `ADR-028` (unidad de trabajo), `ADR-029` (errores de dominio) y `ADR-030` (ubicación de los repositorios). Lo implementa `US-12.2.4` (Issue [#671](https://github.com/vvalotto/cognion/issues/671)).

---

## Contexto

El informe dice que los controllers "no cumplen ninguna función" y que la traducción de entidad a respuesta está en los routers. La medición del 2026-11-25 lo confirma con matices:

| Qué | Medición |
|---|---|
| Controllers | 29 clases (Identidad 12, Actividad Evaluativa 11, Banco 3, Analytics 3), 1.459 líneas, 75 métodos (el informe contaba 32 controllers y 74 métodos) |
| Métodos de una sola sentencia (delegar y devolver) | 67 de 75 (89 %) |
| Métodos con más de una sentencia | 8, y **no son pasamanos**: `registrar_estudiante` consulta un repositorio y un puerto y usa `assert` para condiciones de negocio; `listar_comisiones_por_materia` filtra por docente y levanta errores de dominio. Es lógica de aplicación en el lugar equivocado |
| Agrupación | Cada uno de los 76 casos de uso pertenece a exactamente un controller; la fábrica del controller arma sus casos de uso con los colaboradores compartidos (`event_store`, puertos) en un solo lugar |
| Presenters | No existe ninguno |
| Routers | 20 routers, 3.254 líneas, 75 endpoints. 9 funciones auxiliares (211 líneas) arman la respuesta, más el mapeo dentro de los endpoints |
| Lo que importan los routers de `entities/` | 105 nombres de `errors.py` (los elimina `ADR-029`) y 36 de otras entidades: 21 son plomería de autenticación (`JWTPayload`, `TipoPerfil`) y **13 son tipos del dominio** (`ActividadEvaluativaEnVivo`, `Usuario`, `Evaluacion`, `RevisionEvaluacion`…); uno importa incluso un puerto (`PreguntaConsultaPort`) |

El informe recomendaba "darle trabajo a la capa" **si se resolvía `IM-02`**. Con `ADR-029` esa condición se cumple. Y con `ADR-028` y `ADR-029`, lo que hoy hace un controller además de delegar (confirmar la transacción y traducir errores) deja de ser suyo.

Se comprobó que **FastAPI valida un `dataclass` simple contra el `response_model` de Pydantic sin código extra** (incluso convierte una `tuple` en `list`): el mapeo a mano se escribe una sola vez.

## Opciones Consideradas

| Opción | Qué es | Costo y riesgo |
|---|---|---|
| **A. Darle trabajo a la capa** | El mapeo de entidad a respuesta pasa de los routers a la capa de controllers; el controller devuelve un tipo de salida simple y el router lo declara como `response_model` | Se modifican 29 controllers (75 métodos) y se mueve código que ya existe; 33 archivos de test se ajustan. Tamaño total parecido al actual. Presión sobre el umbral de CBO de los controllers |
| **B. Eliminarla** | Los routers llaman a los casos de uso | Se borran 29 archivos y 33 tests; las fábricas pasan de 29 a 76. Los routers siguen importando los 13 tipos del dominio, así que `CA-03` queda sin resolver, y `interface_adapters/` queda vacía: habría que reescribir la regla de cuatro capas |
| **C. No cambiar nada** | Documentar que son pasamanos aceptado | Costo cero, pero 1.459 líneas de pasamanos y `CA-03` abierto |

## Decisión

**Los controllers hacen la presentación: reciben el resultado del caso de uso y devuelven un tipo de salida propio, un `dataclass` sin Pydantic ni entidades, armado por funciones de presentación de `interface_adapters/presenters/`. Los routers declaran ese tipo como `response_model` y dejan de importar tipos del dominio. La lógica de aplicación que hoy está en 8 métodos de controllers pasa a casos de uso.**

## Justificación

- **Resuelve `IM-01` y `CA-03` a la vez.** La capa deja de ser pasamanos porque presenta, y las entidades ya no cruzan a `frameworks/`. B resuelve solo el primero: sus routers seguirían importando las entidades.
- **Conserva la arquitectura de cuatro capas** que el proyecto usa como referencia (también como material de enseñanza), en vez de dejar vacía la tercera.
- **El costo es mover código existente, no escribir una capa nueva:** las 9 funciones auxiliares de los routers y el mapeo de los endpoints se mudan a `presenters/`. FastAPI valida el `dataclass` contra el esquema de Pydantic, que sigue en `frameworks/api/schemas.py` como declaración de la API.
- **Se descarta B** por dejar `CA-03` abierto y vaciar una capa, y **C** por no cumplir el criterio de salida de la iteración.
- **Los 8 métodos con lógica pasan a casos de uso con cualquiera de las opciones:** un controller no decide ni consulta. Es una regla de esta decisión.
- **La plomería de autenticación queda permitida en los routers** (`JWTPayload` y `TipoPerfil`, de `shared/entities/`): es el tipo de la dependencia de seguridad, no un dato del dominio.

## Impacto en Configuración

- `src/<bc>/interface_adapters/presenters/` (nuevo en los cuatro contextos con controllers): funciones `presentar_*` y los `dataclass` de salida.
- Los 29 controllers devuelven tipos de salida; los 20 routers pierden sus funciones auxiliares (211 líneas) y sus imports de tipos del dominio y de puertos. Las fábricas de `frameworks/dependencies.py` no cambian.
- Los 8 métodos con lógica (`registrar_estudiante`, `listar_comisiones_por_materia`, `listar_estudiantes`, `obtener_comision`, `suspender_evaluacion`, `finalizar_evaluacion`, `resetear_password`, `confirmar`) pasan a casos de uso nuevos o existentes.
- `pyproject.toml`: un contrato de `import-linter` que prohíbe a `src.*.frameworks.api` importar de `src.*.entities`, con `JWTPayload` y `TipoPerfil` de `shared` como únicas excepciones declaradas (más las dos de `ADR-029`).
- `tests/unit/inc12/test_guardas_con_excepciones.py`: una guarda con la lista de imports del dominio en los routers (13 tipos hoy) que `US-12.2.4` vacía.
- `.claude/skills/implement-us/customizations/clean-architecture-bc.json` y `phases/phase-3-implementation.md`: se agrega el `Presenter` y se aclara que el router no importa el dominio.
- `CLAUDE.md` (regla de capas), `docs/architecture/` (vista de componentes y transversal) y `docs/design/domain/`.
- **Orden:** `US-12.2.4` va después de `US-12.2.2` y `US-12.2.3`, que tocan los mismos routers y los mismos repositorios.

## Consecuencias

- ✅ Ninguna entidad del dominio llega a FastAPI: el contrato de la API depende del esquema de `frameworks/` y no de la forma interna de las entidades.
- ✅ El mapeo de entidad a respuesta se puede probar sin levantar FastAPI.
- ✅ Los controllers dejan de ser una capa que existe porque la arquitectura la nombra: ahora presentan.
- ⚠️ **Hay más tipos:** unos 13 tipos del dominio llegan hoy a los routers y cada uno necesita su salida; se compensa porque el mapeo ya existe y solo se muda.
- ⚠️ **El umbral de CBO de los controllers puede apretar** (los controllers ya se partieron para no pasarlo, `IQ-01`): el mapeo va en funciones de `presenters/`, no en los controllers, y los controllers importan funciones y no clases. `US-12.2.6` recalibra el umbral al final.
- ⚠️ **Es un cambio ancho:** 29 controllers, 20 routers y 33 archivos de test. Por eso va después de `US-12.2.2` y `US-12.2.3`, y corre la suite completa y Playwright.
- ⚠️ Los dos puertos que hoy importa un router (`PreguntaConsultaPort`, `EstudianteConsultaPort`) pasan a ser colaboradores del controller o de un caso de uso.
