# ADR-026 — Acoplamiento de los adaptadores in-process a datos de otro BC: read model de Analytics como única excepción

**Estado:** Aceptado
**Fecha:** 2026-11-08
**Origen:** Issue [#498](https://github.com/vvalotto/cognion/issues/498), hallazgo de `BL-012`; decidido con Víctor en la Iteración 0 del Incremento 9. Relacionado con `ADR-006` (integración entre BC), `ADR-014` (Event Sourcing/CQRS) y el Issue [#497](https://github.com/vvalotto/cognion/issues/497) (`import-linter` en el CI).

---

## Contexto

Los BC se comunican por puertos y la regla escrita se cumple en la forma: los 32 imports entre BC viven en `frameworks/adapters/*_port_in_process.py`. Pero varios de esos adaptadores no usan la superficie pública del BC proveedor: **llegan a sus internals**. El caso más riesgoso son los **modelos ORM** (`frameworks.db.models`) de otro BC: un cambio de esquema en el proveedor rompe al consumidor sin que ningún test del proveedor lo advierta, porque el acoplamiento por datos es invisible para el chequeo por puertos.

Relevamiento del 2026-11-08 (32 imports entre BC):

| Qué usa del otro BC | Cantidad |
|---|---|
| Modelos ORM (`frameworks.db.models`) | 6 |
| Gateways y repositorios (`interface_adapters`) | 11 |
| Casos de uso (`use_cases`) | 4 |
| Entidades (`entities`) | 6 |
| Puertos del event store (`entities.ports`) | 2 |
| Otros adaptadores y canales (`frameworks`) | 3 |

Los 6 imports de modelos ORM se reparten así:

| Adaptador | Lee modelos de |
|---|---|
| `analytics/.../evaluacion_desempeno_consulta_port_in_process.py` | `actividad_evaluativa` |
| `analytics/.../sesion_en_vivo_desempeno_consulta_port_in_process.py` | `actividad_evaluativa` |
| `analytics/.../pregunta_metadato_consulta_port_in_process.py` | `banco_preguntas` |
| `banco_preguntas/.../comision_consulta_port_in_process.py` | `identidad` |
| `actividad_evaluativa/.../estudiante_consulta_port_in_process.py` | `identidad` |
| `identidad/.../evaluacion_consulta_port_in_process.py` | `actividad_evaluativa` |

## Opciones consideradas

- **Aceptar todo como "read model compartido".** Costo cero, pero deja sin control el riesgo de esquema en los seis casos, también en los que no son lecturas de un read model.
- **Prohibir todo acceso a datos de otro BC.** Cada proveedor expone puertos de consulta y los consumidores migran. Es lo más limpio, pero toca casi todos los BC y obliga a reconstruir lo que `analytics` hace por diseño.
- **Híbrido.** Aceptar el acceso a datos solo donde es parte del diseño (el read model de Analytics, CQRS) y corregir el resto. Elegida.

## Decisión

**Analytics es la única excepción explícita**: sus adaptadores de lectura pueden leer modelos ORM, entidades y el event store de otros BC. **Ningún otro BC** lee los modelos ORM de otro: los tres casos que hoy lo hacen se migran para usar los gateways o casos de uso públicos del proveedor.

### Excepción de Analytics y sus límites

- Solo desde adaptadores de lectura de `analytics/frameworks/adapters/*_port_in_process.py`, y solo de lo que leen hoy: modelos de `actividad_evaluativa` (evaluaciones y sesiones en vivo) y de `banco_preguntas` (metadatos de preguntas), entidades de `actividad_evaluativa` y el puerto del event store.
- Solo lectura: Analytics nunca escribe en tablas de otro BC.
- Ampliar la excepción a otro modelo o a otro BC requiere una enmienda a este ADR.

### Casos a migrar

| Adaptador | Debe pasar a usar |
|---|---|
| `banco_preguntas/.../comision_consulta_port_in_process.py` | el gateway o caso de uso de consulta de comisiones de `identidad` |
| `actividad_evaluativa/.../estudiante_consulta_port_in_process.py` | el gateway o caso de uso de consulta de estudiantes de `identidad` |
| `identidad/.../evaluacion_consulta_port_in_process.py` | un puerto de consulta que exponga `actividad_evaluativa` |

### Cómo se migra (con cuidado)

- Un adaptador por vez, cada uno como su propia US, sin mezclar.
- Antes de cambiar el código, un test de caracterización que fije el comportamiento actual del adaptador; la migración no puede cambiarlo.
- Si el proveedor no expone todavía lo que el consumidor necesita, se agrega en el proveedor primero (con sus tests) y recién después se cambia el consumidor.
- Se planifican después de [#497](https://github.com/vvalotto/cognion/issues/497), para que `import-linter` haga cumplir la regla y no vuelva a aparecer.

### Fuera del alcance de este ADR

Los demás imports entre BC (gateways, casos de uso y entidades que no son modelos ORM) **no cambian** con esta decisión. Son referencias a clases del proveedor, menos frágiles que las tablas pero igualmente internas. El contrato de `import-linter` de #497 define qué se permite de ellos y, si hace falta, esa discusión se registra en una enmienda o en un ADR nuevo.

## Justificación

Analytics es un read model por diseño (CQRS, `ADR-014`): su función es leer datos de otros BC, y forzarlo a pedirlos por puertos de consulta reconstruiría esos datos en cada proveedor sin ganar aislamiento real. En cambio, los otros tres casos no tienen esa justificación y son pocos y localizados, así que corregirlos es barato en relación con el riesgo que eliminan. Los modelos ORM son la parte más frágil del acoplamiento: ahí es donde un cambio de esquema rompe al vecino sin aviso.

## Impacto en configuración

- `pyproject.toml`: el contrato de `import-linter` de #497 debe codificar la excepción de Analytics (qué archivos pueden importar `frameworks.db.models` de otro BC) y prohibirla en el resto.
- `docs/architecture/` (catálogo de BC y context map): reflejar la excepción de Analytics y los tres casos pendientes.
- `CLAUDE.md`: sin cambios por ahora; se agrega una línea en la regla de imports cuando el contrato de #497 esté activo.

## Consecuencias

- ✅ El riesgo de esquema queda acotado a un lugar conocido y documentado, y el resto de los BC dejan de depender de las tablas ajenas.
- ✅ La regla se puede hacer cumplir automáticamente (#497) en lugar de depender de la revisión de código.
- ⚠️ Analytics sigue acoplado al esquema de `actividad_evaluativa` y `banco_preguntas`: un cambio ahí exige revisar sus adaptadores de lectura.
- ⚠️ Hasta que se migren los tres casos, siguen existiendo; esta decisión los declara deuda con plan, no los elimina.
- ⚠️ Los gateways, casos de uso y entidades de otro BC siguen referenciándose directamente hasta que #497 defina su contrato.
