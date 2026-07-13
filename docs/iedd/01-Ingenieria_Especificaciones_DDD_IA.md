# Ingeniería de Especificaciones Basada en Dominio

DDD + Ingeniería de Especificaciones + IA como traductor de comportamiento

---

## 1. Planteo del problema

Durante décadas la enseñanza y práctica del software se organizó alrededor de los lenguajes de programación.

El proceso típico era:

```
lenguaje → programación → sistema
```

Este enfoque tiene dos limitaciones:

- pone el foco en la implementación
- oculta el problema central del software: la especificación del comportamiento del sistema

La mayor dificultad del software está en:

- especificar correctamente el sistema
- diseñar su comportamiento
- verificar su corrección

no en escribir código.

La aparición de la IA generativa hace visible esta realidad: la implementación puede automatizarse parcialmente, la especificación no.

---

## 2. La tesis central

La ingeniería de software puede reinterpretarse como una disciplina compuesta por cinco capas:

```
Dominio
  ↓
Modelo
  ↓
Especificación
  ↓
Arquitectura
  ↓
Implementación
```

En este marco:

- Domain-Driven Design proporciona la construcción del modelo del dominio
- la ingeniería de especificaciones formaliza el comportamiento esperado
- la arquitectura organiza el sistema para implementar la especificación
- la IA actúa como traductor entre especificación e implementación

---

## 3. El aporte de Domain-Driven Design

DDD propone que el software debe construirse a partir de un modelo explícito del dominio.

Conceptos fundamentales:

- entidades
- objetos de valor
- agregados
- servicios de dominio
- eventos
- contextos delimitados
- lenguaje ubicuo

El objetivo es capturar las reglas del dominio. El modelo define comportamiento, restricciones e invariantes. Por lo tanto el modelo del dominio puede interpretarse como una especificación conceptual del sistema.

---

## 4. Ingeniería de especificaciones

La ingeniería de especificaciones describe con precisión el comportamiento esperado de un sistema.

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

Esta descripción define comportamiento sin referirse a ninguna tecnología.

---

## 5. La IA como traductor de especificaciones

Los modelos de lenguaje permiten transformar descripciones de alto nivel en implementaciones.

Flujo conceptual:

```
modelo del dominio
  ↓
especificación del comportamiento
  ↓
IA
  ↓
implementación ejecutable
```

La IA funciona como un compilador conceptual. La calidad del resultado depende de:

- claridad del modelo
- precisión de la especificación
- ausencia de ambigüedad

---

## 6. Cambio de foco en la ingeniería de software

Antes: programar sistemas.

Ahora: modelar, especificar y diseñar sistemas.

La actividad principal del ingeniero pasa a ser:

- comprender el dominio
- construir el modelo
- definir el comportamiento esperado
- diseñar la arquitectura que lo realiza
- eliminar ambigüedades

La implementación pasa a ser derivable.

---

## 7. Consecuencias para la enseñanza

Orden tradicional:

```
lenguajes → programación → diseño
```

Orden propuesto:

```
dominio → modelo → especificación → arquitectura → implementación
```

Los estudiantes deben entrenarse primero en:

- modelado conceptual
- lenguaje ubicuo
- especificación de comportamiento
- decisiones de arquitectura
- identificación de ambigüedades

antes de centrarse en lenguajes específicos.

---

## 8. Un nuevo rol para la ingeniería de software

La ingeniería de software puede definirse como:

> la disciplina que modela dominios complejos y especifica sistemas capaces de representar y ejecutar ese modelo.

Los lenguajes de programación pasan a ser medios de materialización.

---

## 9. Síntesis conceptual

```
Dominio real
  ↓
Modelo (DDD)
  ↓
Especificación
  ↓
Arquitectura
  ↓
IA como traductor
  ↓
Sistema ejecutable
```

---

## 10. Conclusión

La aparición de herramientas de generación de código basadas en IA no elimina la necesidad de ingeniería de software.

Por el contrario, enfatiza su núcleo:

- comprender sistemas complejos
- construir modelos conceptuales
- especificar comportamientos con precisión

En este contexto, enfoques como Domain-Driven Design adquieren una nueva relevancia, ya que proporcionan el marco para construir modelos que pueden transformarse en sistemas ejecutables.
