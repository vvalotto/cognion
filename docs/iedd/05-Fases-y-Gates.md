# Fases y Gates del método IEDD

---

## 1. Propósito

Los documentos `01`–`03` describen el ciclo conceptual de IEDD (Dominio → Arquitectura →
Modelo → Especificación → Implementación, con retornos gobernados por gate — ver
`03-Diagrama_Conceptual.md`). Este documento formaliza la pieza operativa que completa ese
ciclo: **un gate no es una etapa del plan, es una condición de salida explícita** — un
artefacto que un humano aprueba antes de que la capa siguiente pueda empezar a producir el
suyo, y la misma condición que se vuelve a cumplir cuando el ciclo retorna a una capa ya
visitada.

Este documento nace de una observación concreta durante Cognión (Incremento 1, Iteración 1):
antes de poder escribir la primera especificación US-IEDD de tipo `feature` del proyecto, hubo
que verificar que un conjunto de precondiciones ya estuviera resuelto — modelo de dominio
aprobado, diseño UX aprobado, ADRs ratificados, RF trazable. Esa verificación no estaba escrita
en ningún lado como regla general, solo como práctica implícita repartida entre varios
documentos. Se generaliza acá.

---

## 2. El principio general

> **Ninguna capa empieza a producir su artefacto mirando el trabajo en curso de la capa
> siguiente, y ninguna capa siguiente empieza a trabajar sin el artefacto aprobado de la
> anterior — incluso cuando esa capa anterior ya se había visitado antes.**

Cada capa del ciclo IEDD tiene:

- un **artefacto de salida** (documento o código verificable),
- un **criterio de aprobación** (qué lo hace "listo"),
- un **responsable de aprobarlo** (quién certifica que el criterio se cumplió),
- y un carácter **bloqueante o advisory** (si detiene el avance o solo lo señala).

Cuando alguno de estos cuatro elementos falta, el gate es implícito — y un gate implícito no
se hace cumplir, se olvida. La experiencia de AtaraxiaDive documenta el costo de eso, tanto en
el primer descenso como en los retornos:

- **`HITO-29` (spec-validatoria):** especificar después de implementar introduce sesgos
  invisibles en la cobertura de casos — el código termina especificado mirando el código
  existente, no el diseño aprobado. Es un retorno (Implementación → Especificación) que
  esquivó el gate en vez de pasar por él.
- **`HITO-26` (cobertura asimétrica de modelado):** un event storming ejecutado solo para un BC
  dejó a los demás subrepresentados, generando especificaciones incompletas que emergieron
  como deuda técnica varios incrementos después — un retorno tardío y costoso a Modelo.
- **`HITO-27` (deriva documental):** cuando especificación e implementación avanzan en
  paralelo sin gate de consistencia, la deriva no se detecta hasta una revisión humana
  explícita.

Los tres hallazgos comparten la misma causa raíz: un retorno del ciclo avanzó sin pasar de
nuevo por el gate de la capa a la que volvía.

---

## 3. Mapa de fases y gates

### 3.1 Gate de proyecto (una vez, al lanzamiento)

Precede a cualquier incremento. Se ejecuta una sola vez.

| Fase | Artefacto de salida | Gate | Aprueba |
|---|---|---|---|
| Elicitación de RF | `RF_v1.md` | Requerimientos verificados por el humano, sin ambigüedad de alcance | Responsable de producto/dominio |
| Atributos de calidad | `RNF_v1.md` | Escenarios de calidad priorizados y validados | Responsable de producto/dominio |
| Arquitectura de referencia | `ARQ_v1.md` + ADRs iniciales | Drivers arquitectónicos verificados contra RF/RNF; stack y estilo decididos | Arquitecto/responsable técnico |
| Plan de incrementos | `PLAN_v1.md` | Orden de incrementos justificado por riesgo/dependencia, no por importancia percibida | Responsable técnico |

Estos artefactos no se reescriben retroactivamente — decisiones posteriores se documentan como
revisiones fechadas o ADRs nuevos (ver `CLAUDE.md` — jerarquía documental). La Arquitectura de
referencia es, en el ciclo de `03-Diagrama_Conceptual.md`, el nodo "Arquitectura" en su primera
visita — el resto de sus visitas son retornos (§3.6).

### 3.2 Gate de modelado (por Bounded Context)

Se ejecuta cada vez que un incremento introduce un BC nuevo, o lo extiende de forma
significativa. Es la **Iteración 0** de ese incremento — y el punto donde el ciclo entra por
primera vez al nodo "Modelo" para ese BC, ya con la Arquitectura fundacional resuelta.

| Fase | Artefacto de salida | Gate | Aprueba |
|---|---|---|---|
| Modelo de dominio | Event storming del BC: aggregates, eventos, comandos, invariantes | Aprobación explícita en el comentario de cierre del Issue de modelado | Responsable de dominio |
| Diseño UX (si el BC expone pantallas nuevas) | Prototipo navegable + spec de wireframes | Aprobación explícita, validada en dispositivo real si el escenario lo exige | Responsable de producto/UX |

**Regla dura:** ninguna línea de código de dominio ni de frontend se escribe sin que ambos
artefactos (el que aplique) estén aprobados. Es el mismo gate que `CLAUDE.md` ya documenta
como "Gate de diseño UX", generalizado acá también al modelo de dominio.

### 3.3 Gate de especificación (por unidad de trabajo)

Se ejecuta antes de escribir cada `US-N.M.K.md` — la "Definición de Listo para Especificar":

| Condición | Verifica que… |
|---|---|
| Modelo de dominio del BC aprobado (3.2) | Existan aggregates, comandos, eventos e invariantes con ID de los que la spec pueda tomar contenido, no inventarlo |
| Diseño UX aprobado, si la US toca `frontend/` | Exista el campo `## Fuente de verdad UX` con artefacto real que referenciar |
| ADRs de las decisiones que la US necesita, ya ratificados | La spec documente comportamiento decidido, no decida arquitectura sobre la marcha |
| RF fuente identificado (o justificación explícita si la US no tiene RF propio) | La spec sea trazable hacia atrás, no una funcionalidad inventada |
| Entrada en la tabla de candidatas del incremento (comando/evento/actor) | La partición de trabajo entre US ya esté acordada, no se improvise US por US |

**Postcondición del gate:** la US-IEDD queda escrita en `docs/specs/incN/`, el RF/RNF que
cubre pasa de *Planificado* a *Especificado* en la matriz de trazabilidad, y el Issue de
GitHub correspondiente queda creado en estado `backlog`.

### 3.4 Gate de implementación (por US)

| Fase | Artefacto de salida | Gate | Bloquea |
|---|---|---|---|
| Commit | Código en capas `entities/use_cases/interface_adapters/frameworks` | CodeGuard (pre-commit) | No — solo advierte |
| Push | Mismo código | DesignReviewer (pre-push) | Sí, si CRITICAL |
| PR a `develop` | Código + tests | lint + tests + DesignReviewer (CI) | Sí |
| Merge a `develop` | RF pasa de *Especificado* a *Implementado* en la matriz | Revisión de código + tests unitarios pasando | — |

### 3.5 Gate de cierre (por Incremento/Baseline)

| Fase | Artefacto de salida | Gate | Aprueba |
|---|---|---|---|
| UAT | Tests funcionales Capa 1 (pytest) + Capa 2 (HTTP) | Debe aprobar antes de merge a `main` — no basta con que cada US pase sus propios tests | Responsable de producto |
| Cierre de Incremento | `.cm/baselines/BL-NNN.md` + tag `vN.N.0` | DesignReviewer manual, 0 CRITICAL requerido; RF pasa de *Implementado* a *Validado* | Responsable técnico |
| Deploy | Build Docker + healthcheck en el entorno real | CI/CD (GitHub Actions), bloqueante | Automático, verificado por responsable técnico |
| Cierre de Baseline | Reporte de tendencias | ArchitectAnalyst — siempre manual | Informa, no bloquea — es en sí mismo un disparador típico de retorno (§3.6) |

### 3.6 Retornos — cuándo y cómo el ciclo vuelve atrás

A diferencia de 3.1–3.5 (que describen el primer descenso), esta sección describe los
**retornos**: cualquier capa puede revelar la necesidad de volver a una capa anterior ya
visitada. Un retorno es legítimo si y solo si reingresa por el mismo gate que la primera vez.

| Retorno observado | Significado conceptual | Evidencia | Gate que se vuelve a cumplir |
|---|---|---|---|
| Modelo → Arquitectura | El modelado revela una necesidad estructural que la arquitectura fundacional no previó | Generalización del patrón — sin HITO puntual todavía, ver `03-Diagrama_Conceptual.md` | Nuevo ADR ratificado antes de que el modelo que lo motivó se dé por cerrado |
| Implementación → Arquitectura | Un driver arquitectónico solo se revela al construir u operar en producción | `HITO-11`: un quality gate catalizó una decisión arquitectónica documentada como ADR nuevo | Nuevo ADR ratificado antes de que el código que lo motivó se dé por cerrado |
| Implementación → Especificación | La verificación (tests, UAT) revela que la spec no cubría un caso real | `HITO-20`: UAT reveló invariantes correctos pero incompletos ante variantes no anticipadas | La spec se corrige y se re-versiona; recién entonces se ajusta el código |
| Especificación → Modelo | Escribir la spec revela un vacío o precondición no cubierta por el modelo aprobado | Esta sesión: `US-1.1.0`, sin RF propio, derivada del modelo al escribir las specs de la Iteración 1 | El modelo de dominio se actualiza y se re-aprueba antes de completar la spec |
| Modelo → Dominio | Modelar revela que falta conocimiento de dominio — un RF no elicitado todavía | `BC-identidad-modelo.md` §11: modelar BC Identidad reveló que faltaba RF-19 (cambio de contraseña) | Elicitación de RF dedicada, RF-19 agregado a `RF_v1.md` con fecha, antes de incorporarlo al modelo |

**Lo que distingue un retorno sano de deriva documental (`HITO-27`) o spec-validatoria
(`HITO-29`) no es que el retorno exista — es si pasó por el gate o lo esquivó.** Un retorno que
ajusta el artefacto de la capa anterior y lo re-aprueba es ciclo de refinamiento. Un retorno
que ajusta silenciosamente el código, o la spec, sin volver a tocar el artefacto de la capa
que originó el problema, es deuda técnica documentada como si fuera trabajo terminado.

---

## 4. Vista integrada

Diagrama completo (con nodos, primer descenso y retornos representados):
`docs/iedd/03-Diagrama_Conceptual.md`.

```
        ┌─────────────────────────── retornos, vía gate (§3.6) ───────────────────────────┐
        │                                                                                   │
        ▼                                                                                   │
Dominio → Arquitectura → Modelo → Especificación → Implementación → UAT → Cierre de Incremento
 (§3.1)      (§3.1)       (§3.2)       (§3.3)            (§3.4)              (§3.5)
```

El primer descenso (§3.1 → §3.5) es el camino por defecto para un Bounded Context nuevo. Los
gates de proyecto (§3.1) no se repiten; los de modelado, especificación, implementación y
cierre sí, una vez por BC/US/Incremento respectivamente — y cualquiera de ellos puede
disparar un retorno a una capa anterior, gobernado por la misma regla (§3.6).

---

## 5. Aplicación en Cognión (caso de validación)

| Gate conceptual | Documento operativo en Cognión |
|---|---|
| Gate de proyecto (§3.1) | `docs/rf/RF_v1.md`, `RNF_v1.md`, `ARQ_v1.md`, `PLAN_v1.md` |
| Gate de modelado (§3.2) | `docs/design/domain/`, `docs/design/ux/` — "Gate de diseño UX" en `CLAUDE.md` |
| Gate de especificación (§3.3) | `docs/specs/incN/`, `docs/iedd/US-IEDD-template.md`, `docs/traceability/matrix.md` |
| Gate de implementación (§3.4) | Tabla "Quality gates" en `CLAUDE.md`, `docs/plans/WORKFLOW-DESARROLLO.md` |
| Gate de cierre (§3.5) | `docs/plans/PROCEDIMIENTO-UAT.md`, `.cm/baselines/`, `docs/plans/PLAN-CM.md` |
| Retornos (§3.6) | `docs/design/domain/BC-identidad-modelo.md` §§5–9, 11 (hot spots resueltos con Víctor durante el modelado; RF-19 elicitado a mitad de proyecto) |

El primer ciclo completo del gate de especificación (§3.3) se ejecutó en el Incremento 1,
Iteración 1 (`US-1.1.0` a `US-1.1.5`, `docs/specs/inc1/`) — es la evidencia empírica que
motivó formalizar este documento, análoga en su función a los HITOs de AtaraxiaDive citados
en §2 y §3.6.

---

## 6. Uso de este documento

`docs/plans/WORKFLOW-DESARROLLO.md` no duplica esta definición — la referencia. Cuando el
workflow operativo cambie (nuevos quality gates, nuevo procedimiento de UAT), este documento
solo cambia si cambia el **modelo conceptual** de fases, gates y retornos, no cada vez que
cambia un detalle de ejecución en Cognión.

---

*Documento `05` de la serie conceptual IEDD — complementa `02-Marco_Conceptual_5_Capas.md` y
`03-Diagrama_Conceptual.md` con la dimensión de gobierno (gates y retornos) del ciclo Dominio →
Arquitectura → Modelo → Especificación → Implementación.*
