# Marco Conceptual de 5 Capas

---

## 1. Visión general

El desarrollo de soluciones digitales puede entenderse como un **ciclo de refinamiento** entre
cinco capas conceptuales — no como una cadena que se recorre una sola vez:

```
Dominio → Arquitectura → Modelo → Especificación → Implementación
   ↑                        ↑            ↑              │
   └────────────────────────┴────────────┴──────────────┘
              retornos gobernados por gate
```

El **primer descenso** — la primera vez que un Bounded Context nuevo entra al ciclo — recorre
las cinco capas en ese orden. Pero cualquier capa puede revelar, más adelante, la necesidad de
volver a una capa anterior: una decisión arquitectónica que solo se hace visible al
implementar, un modelo que resulta incompleto al especificar, un requerimiento que aparece
recién al modelar. Ese retorno no es una excepción del proceso — es parte de él, siempre que
reingrese por el mismo gate que la primera vez (artefacto actualizado, aprobación explícita).

Diagrama completo, con los retornos representados y su evidencia empírica:
`docs/iedd/03-Diagrama_Conceptual.md`. Disciplina de gates que gobierna cada flecha (forward y
de retorno): `docs/iedd/05-Fases-y-Gates.md`.

La inteligencia artificial puede intervenir principalmente en las capas inferiores del
descenso (Especificación → Implementación), sin reemplazar las superiores.

---

## 2. Dominio

El dominio representa la realidad que el sistema intenta modelar.

Incluye:

- actores
- procesos
- reglas del negocio
- lenguaje propio del área
- restricciones del mundo real

El objetivo en esta capa es comprender el problema y el contexto. No existe todavía ninguna
decisión tecnológica.

---

## 3. Arquitectura (fundacional)

A diferencia de la formulación original de este marco, la Arquitectura fundacional se ubica
**antes** del Modelo, no después de la Especificación. La razón es de precondición, no de
preferencia estilística: no se puede modelar un dominio con rigor sin saber si el sistema usa
Event Sourcing o CRUD, si es síncrono o asíncrono, monolito o distribuido — esas decisiones
determinan qué significa siquiera "aggregate" o "evento" en términos operativos.

Incluye, en este primer paso:

- estilo arquitectónico (ej. Clean Architecture, hexagonal)
- stack tecnológico
- patrones de persistencia y comunicación
- decisiones fundacionales documentadas como ADR

Esta arquitectura fundacional se decide **una vez por proyecto** — no se repite por Bounded
Context. Decisiones arquitectónicas puntuales que emergen después (al modelar, especificar o
implementar un BC específico) son **retornos** a esta capa, no una segunda pasada de la misma
naturaleza — ver `docs/iedd/03-Diagrama_Conceptual.md` §"Por qué el ciclo, y no la cadena".

**Límite importante:** la arquitectura fundacional habilita el modelado, no lo dicta. Los
conceptos de dominio (qué es un aggregate, qué invariantes tiene) se derivan del negocio, no
de la tecnología elegida — eso es lo que distingue esta secuencia de un anti-patrón tech-first
(`HITO-29`, spec-validatoria, es justamente el fracaso de este límite en la dirección
opuesta: implementación dictando especificación).

---

## 4. Modelo

El modelo es una representación conceptual del dominio, construida sobre la arquitectura
fundacional ya decidida.

Aquí aparece el aporte central de Domain-Driven Design (DDD):

- entidades
- objetos de valor
- agregados
- eventos
- servicios de dominio
- contextos delimitados
- lenguaje ubicuo

El modelo captura principalmente:

- reglas del dominio
- invariantes
- comportamiento esperado

---

## 5. Especificación

La especificación describe el comportamiento que el sistema debe implementar.

Incluye:

- operaciones
- precondiciones
- postcondiciones
- invariantes
- estados
- eventos

Ejemplo conceptual:

```
Entidad: Cuenta
  Invariante: saldo ≥ 0

Operación: transferir
  Precondición:  saldo_origen ≥ monto
  Postcondición: saldo_origen disminuye
                 saldo_destino aumenta
```

La especificación define **QUÉ** debe hacer el sistema, no **CÓMO** hacerlo.

---

## 6. Implementación

La implementación materializa el sistema en tecnología concreta.

Incluye:

- código
- bases de datos
- APIs
- interfaces
- infraestructura

Aquí aparecen lenguajes de programación, frameworks, compiladores y entornos de ejecución.

Con la aparición de la IA, parte de esta capa puede generarse automáticamente a partir de la
especificación.

---

## 7. El rol de la IA

La IA puede actuar como traductor entre especificación e implementación — la última capa del
descenso, no una capa aparte del ciclo:

```
Dominio → Arquitectura → Modelo → Especificación → IA → Implementación
```

La calidad del resultado depende de:

- claridad del modelo
- precisión de la especificación
- ausencia de ambigüedad

---

## 8. Consecuencias para la Ingeniería de Software

Este marco permite reinterpretar la ingeniería de software como la disciplina que transforma
conocimiento de un dominio en sistemas ejecutables mediante modelos y especificaciones
precisas, **refinados en ciclos** en vez de en una sola pasada.

Los lenguajes de programación pasan a ser tecnologías de implementación, no el núcleo de la
disciplina. El núcleo pasa a incluir, además del modelado y la especificación, el gobierno
explícito de cuándo y cómo el ciclo vuelve atrás.

---

## 9. Consecuencias para la enseñanza

Orden tradicional:

```
lenguajes → programación → diseño
```

Orden propuesto para el primer descenso:

```
dominio → arquitectura → modelo → especificación → implementación
```

— con la aclaración explícita de que, en un proyecto real, este orden no se recorre una sola
vez: se enseña también a reconocer cuándo un hallazgo en una capa posterior exige volver a una
capa anterior, y a hacerlo sin saltear el gate de aprobación.

Esto permite formar profesionales capaces de:

- comprender sistemas complejos
- modelar dominios sobre una arquitectura ya fundada
- especificar comportamiento
- reconocer y gobernar retornos del ciclo, en vez de tratarlos como fallas del proceso
- utilizar IA como herramienta de implementación
