# Incremento 12 — Proceso de trabajo para las mejoras de calidad de diseño

> Fecha: 2026-11-15 · Estado: **aprobado por Víctor el 2026-11-15**
> Origen: [`docs/revision-diseno-2026-11/`](../../revision-diseno-2026-11/README.md) (60 hallazgos sobre la `1.0.0`)
> Alcance y orden de trabajo: [`inc12-candidatas.md`](inc12-candidatas.md)
> Base: [`WORKFLOW-DESARROLLO.md`](../WORKFLOW-DESARROLLO.md) y [`PLAN-CM.md`](../PLAN-CM.md). Este documento solo dice lo que cambia o se agrega para este incremento.

## Decisiones que lo enmarcan

Tomadas con Víctor el 2026-11-15:

| # | Decisión |
|---|---|
| 1 | **Congelación funcional.** No entra ningún cambio funcional a `develop` hasta que exista una versión estable con estas adecuaciones. El Incremento 11 (Mejoras funcionales, Issues #616 a #619) queda postergado. |
| 2 | **Una sola línea de código.** Todo entra por `develop`. No hay un branch paralelo de mejoras. |
| 3 | **Numeración.** Este incremento es el 12 y se ejecuta antes que el 11. Las historias son `US-12.M.K`. |
| 4 | **Dos baselines.** `v1.0.1` al cierre de la Iteración 2 y `v1.1.0` al cierre de la Iteración 4. El Incremento 11 pasa a apuntar a `v1.2.0`. |
| 5 | **Herramienta.** Las historias que tocan `src/` se implementan con `/implement-us`, como siempre. |

## Qué se puede mergear a `develop` durante el incremento

| Permitido | No permitido |
|---|---|
| Historias de este incremento | Funcionalidad nueva (Incremento 11, `RF-18`) |
| Corrección de un defecto de la `1.0.0` detectado en uso real | Mejoras de comportamiento "ya que estamos" |
| Documentación y herramientas del propio incremento | Hallazgos que no estén en `inc12-candidatas.md` |

Si al trabajar aparece un problema nuevo, se anota como candidato en `inc12-candidatas.md` y se decide en el cierre de la iteración. No se corrige en el momento.

Un defecto de la `1.0.0` que no pueda esperar a la baseline siguiente se publica como PATCH (`PLAN-CM.md` §11) y toma el número libre que siga; la baseline intermedia se corre un número.

## Ramas

- Una rama por iteración (`feature/inc-12-iter-N-descripcion`) cuando sus historias tocan los mismos archivos. Precedente: Iteración 4 del Incremento 9.
- Una rama por historia (`feature/US-12.M.K-descripcion`) cuando son independientes.
- Ninguna rama vive más que su iteración. PR siempre con `--base develop`.
- `develop → main` solo en las dos baselines.

## Ciclo de cada iteración

Cada iteración recorre cinco pasos, en este orden. No se abre un paso sin cerrar el anterior.

| Paso | Qué se hace | Qué deja | Quién decide |
|---|---|---|---|
| 1. Confirmar | Verificar en el código o ejecutando cada hallazgo de la iteración, sobre todo los *Inferido* | Estado actualizado en la tabla de seguimiento: confirmado, ajustado o descartado | Víctor aprueba la lista |
| 2. Decidir | Escribir el ADR de cada elección de diseño de la iteración | ADR aceptado **antes** de escribir specs | Víctor |
| 3. Guardar | Escribir el contrato o el test que falla, con la lista explícita de excepciones | Guarda en el CI; la lista de excepciones es el trabajo pendiente | — |
| 4. Migrar | Una historia por unidad de cambio, con `/implement-us`. Cada historia borra sus excepciones | PR a `develop` con la suite en verde | — |
| 5. Cerrar | Regresión completa, criterio de salida medido, seguimiento actualizado | Iteración cerrada o baseline | Víctor |

### Paso 1 — Confirmar

El informe no ejecutó la suite ni la aplicación, y 10 hallazgos están marcados *Inferido*. Antes de invertir en un hallazgo hay que verlo.

- Un hallazgo confirmado sigue.
- Un hallazgo ajustado cambia su alcance o su esfuerzo, y se anota por qué.
- Un hallazgo descartado se cierra con la evidencia que lo desmiente. Descartar es un resultado válido.

### Paso 2 — Decidir

Lleva ADR toda historia donde haya más de una solución razonable. Las que ya se conocen están marcadas en `inc12-candidatas.md`. El ADR se aprueba antes de escribir la spec, para que la spec no discuta diseño.

### Paso 3 — Guardar

Es la regla central del incremento: **la regla se escribe antes que el código que la cumple**.

1. Se agrega el contrato de `import-linter` o el test que expresa el diseño buscado.
2. Lo que hoy lo incumple se declara como excepción, línea por línea, con un comentario "pendiente de migrar".
3. Se agrega el caso de violación sembrada en `tests/unit/inc9/test_guarda_arquitectura.py` o su equivalente, para probar que la guarda falla cuando debe.
4. La guarda entra a `develop` en verde.

Desde ese momento el código nuevo ya no puede empeorar, y lo que falta está a la vista. Precedente: `ADR-026` y su contrato.

No todo hallazgo admite una guarda automática. Cuando no la admite, la historia lo dice y explica con qué se verifica.

### Paso 4 — Migrar

Cada historia sigue el ciclo de `WORKFLOW-DESARROLLO.md` §5 (rama, tracker, `/implement-us`, PR, cierre del Issue), con estas diferencias.

**En `/implement-us`:**

- En la Fase 0, paso 7, la historia se clasifica como "Refactorización (sin cambio de comportamiento)" y se confirma `no-bdd`. Las Fases 1 y 6 no se ejecutan.
- Una historia que sí cambia comportamiento observable (por ejemplo `IM-04`, que agrega una autorización) conserva BDD.
- En la Fase 2, el plan lista primero los tests que protegen el comportamiento y después los cambios.
- En la Fase 7, además de los gates habituales, se corre `uv run lint-imports` y se verifica que la historia borró las excepciones que le tocaban.

**En la spec.** A la plantilla habitual se le agregan cuatro campos:

| Campo | Contenido |
|---|---|
| `**Hallazgo de origen**` | Identificador del informe (`AC-01`) y enlace al capítulo |
| `## Comportamiento que no cambia` | Qué hace hoy el sistema en la zona tocada y qué tests existentes lo prueban. Si no hay tests suficientes, la historia empieza por escribirlos |
| `## Guarda` | El contrato o test que esta historia hace pasar, y las excepciones que borra |
| `## Criterio de salida` | Una medida verificable: un comando y el resultado esperado |

El campo `**Tipo**` dice `refactor` y el título describe el estado final, no la tarea.

**Regla de regresión.** Antes de tocar código se corre la suite completa sobre una base descartable y se anota el resultado. Al terminar se corre de nuevo. Los dos resultados van en el reporte de la historia. Un test que cambia de resultado sin que la spec lo anticipe detiene la historia.

**Tracks.** La regla del proyecto no cambia:

| Toca | Track |
|---|---|
| `src/` | Formal: Issue, spec, `/implement-us` |
| Solo `frontend/` | Informal: commit descriptivo, con verificación en navegador real |
| CI, `deploy/`, `scripts/`, configuración de herramientas | Herramientas: rama y PR, sin `/implement-us` |
| Solo `docs/` | Documental: rama y PR |

En los cuatro tracks el cambio cita el hallazgo que cierra, en el commit y en la tabla de seguimiento.

**Gate de UX.** Ninguna historia de este incremento cambia lo que el usuario ve. Si al implementar una resulta que sí, se detiene y pasa por el gate de `CLAUDE.md`.

### Paso 5 — Cerrar

La iteración cierra cuando:

1. Todas sus historias están mergeadas a `develop`.
2. La suite completa está en verde: unitarios, integración, BDD, Vitest y Playwright.
3. Se midió el criterio de salida de la iteración y se cumple.
4. La tabla de seguimiento refleja el estado real de cada hallazgo.
5. Se revisaron los candidatos nuevos anotados durante la iteración.

Las Iteraciones 2 y 4 cierran además con baseline (ver abajo).

## Trazabilidad

Hay un solo lugar donde se ve el avance: la tabla de seguimiento de [`inc12-candidatas.md`](inc12-candidatas.md#seguimiento-por-hallazgo).

- Cada hallazgo tiene un estado: *Pendiente*, *Confirmado*, *En curso*, *Cerrado*, *Descartado* o *No se hace*.
- *Cerrado* lleva la historia y el PR. *Descartado* y *No se hace* llevan el motivo o el ADR.
- El informe de `docs/revision-diseno-2026-11/` no se modifica: es la foto del 2026-11-14.

La cadena completa es: hallazgo → historia (`US-12.M.K`) → commits con `[US-12.M.K]` → PR → fila de seguimiento.

## Baselines

El cierre sigue `WORKFLOW-DESARROLLO.md` §7, con una diferencia en el UAT: como no hay funcionalidad nueva, el UAT es **de regresión**. Recorre los circuitos de la `1.0.0` en navegador real y busca diferencias, no aceptación de algo nuevo.

| Baseline | Cierra | Versión | Qué garantiza |
|---|---|---|---|
| `BL-018` | Iteraciones 1 y 2 | `v1.0.1` | Riesgos de operación y de datos cerrados; red de seguridad de tests ampliada |
| `BL-019` | Iteraciones 3 y 4 | `v1.1.0` | Eventos y fronteras entre contextos resueltos; versión estable |

## Criterio de "versión estable"

Es la condición que levanta la congelación funcional. Se cumple cuando se dan las cinco:

1. **Alcance.** Los 11 hallazgos de severidad Alta están en *Cerrado* o *Descartado*. Los 35 de severidad Media están en *Cerrado*, *Descartado* o *No se hace* con su decisión registrada.
2. **Guardas.** Los contratos de `import-linter` no tienen excepciones pendientes de migrar. Solo quedan las que un ADR acepta como definitivas.
3. **Regresión.** Suite completa en verde y UAT de regresión aprobado en navegador real.
4. **Uso.** La versión estuvo instalada y se usó en al menos una clase real o un ensayo completo (evaluación de período abierto y sesión en vivo), sin defectos graves.
5. **Baseline.** `BL-019` registrada y `v1.1.0` publicada.

Los hallazgos de severidad Baja no condicionan la estabilidad. Se cierran si quedan en el camino de una historia.

## Lo que este proceso no hace

- No crea una variante de `/implement-us` para refactorización. Si los cuatro campos de la spec resultan incómodos después de `BL-018`, se evalúa entonces.
- No agrega gates nuevos al commit ni al push. Las guardas de este incremento viven en el CI, dentro de `import-linter` y de la suite.
- No reabre el informe. Lo que el informe no revisó (lista en su [capítulo 13](../../revision-diseno-2026-11/13-plan-priorizado.md#no-revisado)) sigue sin revisar.
