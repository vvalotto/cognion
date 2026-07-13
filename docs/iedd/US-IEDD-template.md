# US-NNN: [Título de la Historia de Usuario]

**Estado**: `Especificada` | `En progreso` | `Implementada` | `Verificada`
**Iteracion / Sprint**: `SP-N` | `INC-N.N` | `SP-ADJ-N`
**Tipo**: `feat backend` | `feat frontend` | `refactor` | `fix` | `docs`
**Agregado principal afectado**: [nombre del agregado DDD]
**Bounded Context**: [nombre del contexto delimitado]

---

## Descripcion (lenguaje de negocio)

Como **[actor/rol]**,
quiero **[acción o capacidad]**
para **[beneficio o valor de negocio]**.

---

## Contexto del dominio

### Problema

[Descripción breve del gap o situación que esta US resuelve, en términos del dominio.]

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Aggregate | `[nombre]` | [qué representa] |
| Value Object | `[nombre]` | [qué encapsula] |
| Domain Event | `[nombre]` | [qué señala] |
| Port | `[nombre]` | [contrato que define] |
| Command | `[nombre]` | [operación que dispara] |

---

## Especificacion del comportamiento

### Precondicion

- [Estado que debe existir para que la operación sea válida]
- [Condición adicional si aplica]

### Postcondicion

- [Estado garantizado si la operación se ejecutó correctamente]
- [Evento generado o estado secundario]

### Invariantes

| ID | Invariante |
|----|------------|
| INV-N.N-01 | [Condición que debe ser verdadera siempre, antes y después de cualquier operación] |
| INV-N.N-02 | [Condición que nunca puede violarse — si se viola, la operación se rechaza] |

---

## Criterios de aceptacion

```gherkin
Feature: [título de la funcionalidad]

  Scenario: [caso principal — camino feliz]
    Given [precondición en lenguaje de negocio]
    When  [acción del actor]
    Then  [resultado esperado — refleja la postcondición]
    And   [evento generado o estado secundario]

  Scenario: [caso de rechazo — invariante o precondición violada]
    Given [estado que viola una precondición o invariante]
    When  [misma acción del actor]
    Then  [el sistema rechaza la operación con [mensaje/razón]]

  Scenario: [caso borde — si aplica]
    Given [condición límite]
    When  [acción]
    Then  [comportamiento esperado en el límite]
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — se implementa con la arquitectura existente
- [ ] Sí → crear `ADR-NNN` antes de implementar

**Capa(s) afectadas:**
- [ ] Domain — entidades, value objects, eventos, puertos
- [ ] Application — comandos, handlers, queries
- [ ] Infrastructure — repositorios, adaptadores, servicios externos
- [ ] API — routers, schemas, responses
- [ ] Frontend — páginas, componentes, stores, hooks

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/[bc]/domain/[archivo].py` | [descripción del cambio] |
| `src/[bc]/application/[archivo].py` | [descripción del cambio] |
| `src/[bc]/infrastructure/[archivo].py` | [descripción del cambio] |
| `src/[bc]/api/[archivo].py` | [descripción del cambio] |
| `frontend/src/[ruta]/[archivo].tsx` | [descripción del cambio] |

---

## Referencias

- Relacionada con: `US-NNN`, `ADR-NNN`
- Modelo de dominio: `docs/design/domain-model.md` (sección: [nombre])
- Arquitectura: `docs/design/architecture.md`

---

## Notas de implementacion

> [Campo opcional — completar solo si hay decisiones técnicas relevantes
> que el desarrollador debe conocer antes de implementar.
> NO es el lugar para describir código, sino para aclarar restricciones
> o contexto que la especificación no cubre.]

---

*Template versión 2.0 — IEDD + Claude Dev Kit — Mayo 2026*
