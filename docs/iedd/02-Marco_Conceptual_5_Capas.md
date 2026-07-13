# Marco Conceptual de 5 Capas

---

## 1. Visión general

El desarrollo de soluciones digitales puede entenderse como una cadena de transformación conceptual:

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

Cada capa transforma conocimiento del dominio en algo cada vez más ejecutable.

La inteligencia artificial puede intervenir principalmente en las capas inferiores, sin reemplazar las superiores.

---

## 2. Dominio

El dominio representa la realidad que el sistema intenta modelar.

Incluye:

- actores
- procesos
- reglas del negocio
- lenguaje propio del área
- restricciones del mundo real

El objetivo en esta capa es comprender el problema y el contexto. No existe todavía ninguna decisión tecnológica.

---

## 3. Modelo

El modelo es una representación conceptual del dominio.

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

## 4. Especificación

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

## 5. Arquitectura

La arquitectura define cómo organizar el sistema para implementar la especificación.

Incluye decisiones sobre:

- separación en componentes
- límites de contexto
- persistencia
- comunicación entre servicios
- manejo de eventos
- escalabilidad
- resiliencia

La arquitectura conecta el modelo conceptual con la implementación técnica.

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

Con la aparición de la IA, parte de esta capa puede generarse automáticamente a partir de la especificación.

---

## 7. El rol de la IA

La IA puede actuar como traductor entre especificación e implementación.

Flujo conceptual:

```
Dominio
  ↓
Modelo
  ↓
Especificación
  ↓
IA
  ↓
Implementación
```

La calidad del resultado depende de:

- claridad del modelo
- precisión de la especificación
- ausencia de ambigüedad

---

## 8. Consecuencias para la Ingeniería de Software

Este marco permite reinterpretar la ingeniería de software como la disciplina que transforma conocimiento de un dominio en sistemas ejecutables mediante modelos y especificaciones precisas.

Los lenguajes de programación pasan a ser tecnologías de implementación, no el núcleo de la disciplina.

---

## 9. Consecuencias para la enseñanza

Orden tradicional:

```
lenguajes → programación → diseño
```

Orden propuesto:

```
dominio → modelo → especificación → arquitectura → implementación
```

Esto permite formar profesionales capaces de:

- comprender sistemas complejos
- modelar dominios
- especificar comportamiento
- utilizar IA como herramienta de implementación
