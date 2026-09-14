# US-ADJ-50: Docente ve el ranking de "Preguntas más falladas"

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver un listado ordenado de las preguntas con mayor tasa de error, con su enunciado, de
toda la materia o de una comisión puntual**
para **detectar preguntas puntuales problemáticas, no solo temas (RF-22)**.

---

## Contexto del dominio

### Problema

`US-ADJ-46` ya expone `GET /analytics/materias/{materia_id}/ranking-preguntas-falladas?comision_id=`.
Falta la pantalla que lo consume — mismo patrón visual que `DesempenoPorTema.tsx` (`US-4.2.6`),
a nivel de pregunta individual en vez de tema.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | `obtenerRankingPreguntasFalladas(materiaId, comisionId?)` | Sobre `apiFetch`/`ApiError`, reutiliza `listarComisionesPorMateria` (`US-4.2.5`) |
| Pantalla (nueva) | `RankingPreguntasFalladas.tsx` | Selectores Materia (siempre) → Comisión (opcional, default "Toda la materia"), listado `.ranking-row` numerado |
| Ruta (nueva) | `/analytics/ranking-preguntas-falladas` | Protegida con `RequireRole rol="docente"`, entrada directa en `AppNav.tsx` |

---

## Especificacion del comportamiento

### Precondicion

- `US-ADJ-46` implementada.
- Docente autenticado.

### Postcondicion

- Al entrar: selector de Materia poblado (`listarMateria()`, `US-2.1.9`), selector de Comisión
  en "Toda la materia" por defecto → dispara la consulta sin `comision_id`.
- Elegir Materia → pobla el selector de Comisión (`GET /materias/{id}/comisiones`, `US-4.2.2`)
  y reconsulta con "Toda la materia".
- Elegir una Comisión puntual → reconsulta con `comision_id`.
- Resultado: una `.ranking-row` por pregunta, numerada por posición (índice + 1 en la lista ya
  ordenada), ordenada por tasa de error descendente: enunciado (truncado a una línea),
  unidad/tema, cantidad de presentaciones, % de tasa de error con el mismo código de color de
  severidad que `.tema-row` (`US-4.2.6`: ≥50% rojo, 20-49% ámbar, <20% verde).
- Materia (o comisión elegida) sin ninguna pregunta presentada todavía → mensaje de estado
  vacío, sin listado.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Los umbrales de color (50%/20%) son de UI, no de dominio — mismo criterio que `US-4.2.6`. |
| — | Cambiar de Materia reinicia la Comisión a "Toda la materia" (mismo criterio que `US-4.2.6`). |
| — | La numeración del ranking es puramente de presentación (posición en la lista ya ordenada por el backend) — no un campo que viaje en la respuesta. |

---

## Criterios de aceptacion

```gherkin
Feature: Docente ve "Preguntas más falladas" (US-ADJ-50)

  Scenario: Materia completa por defecto
    Given un Docente entra a "Preguntas más falladas" y elige una Materia con respuestas vigentes
    When la pantalla carga
    Then ve el listado numerado ordenado por tasa de error descendente, agregado de toda la materia

  Scenario: Acotar a una comisión
    Given el Docente ya ve el listado de la materia completa
    When elige una Comisión puntual
    Then el listado se recalcula solo con las respuestas de esa comisión

  Scenario: Color por severidad
    Given una pregunta con tasa de error del 60%, otra del 30% y otra del 10%
    When se renderiza el listado
    Then la primera se ve en rojo, la segunda en ámbar y la tercera en verde

  Scenario: Materia sin preguntas presentadas
    Given una Materia sin ninguna Respuesta vigente
    When el Docente la elige
    Then ve el mensaje de estado vacío, sin listado

  Scenario: Acceso sin rol Docente
    Given un Estudiante o Administrador autenticado
    When intenta acceder a la ruta de "Preguntas más falladas"
    Then es redirigido por RequireRole, no ve la pantalla
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — frontend puro, mismo patrón exacto de `DesempenoPorTema.tsx` (`US-4.2.6`) a nivel de
  pregunta individual.

**Capa(s) afectadas:**
- [ ] Backend — sin cambios
- [x] Frontend — cliente API (1 función nueva), pantalla `RankingPreguntasFalladas.tsx`,
  primitiva `.ranking-row` (reusa el estilo de `.tema-row` donde alcance), ruta nueva en
  `router.tsx` protegida con `RequireRole rol="docente"`, entrada nueva en `AppNav.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-analytics.md` §3.4 (`#doc-ranking-preguntas`). Prototipo:
`docs/design/ux/prototipos/analytics-portal-desempeno.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/analytics-api.ts` | Agrega `obtenerRankingPreguntasFalladas(materiaId, comisionId?)` |
| `frontend/src/pages/analytics/RankingPreguntasFalladas.tsx` | Nueva pantalla |
| `frontend/src/components/` | Primitiva `.ranking-row` (o componente `RankingRow`) |
| `frontend/src/router.tsx` | Ruta nueva, `RequireRole rol="docente"` |
| `frontend/src/components/AppNav.tsx` | Entrada "Preguntas más falladas" |
| Tests Vitest correspondientes | Cambio de materia/comisión, color por severidad, estado vacío |

---

## Referencias

- Depende de: `US-ADJ-46`, `US-4.2.5`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#360](https://github.com/vvalotto/cognion/issues/360)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
