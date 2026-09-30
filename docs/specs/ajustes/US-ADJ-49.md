# US-ADJ-49: Docente ve la evolución temporal de un estudiante y de su comisión

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver un gráfico con la evolución del % de aciertos de un estudiante, comparado contra
el promedio de su comisión, actividad tras actividad**
para **detectar tendencias que un número acumulado no muestra (RF-21)**.

---

## Contexto del dominio

### Problema

`US-ADJ-45` ya expone los dos endpoints de evolución temporal (individual y de comisión). Falta
el gráfico, accesible únicamente desde el drill-down de `US-ADJ-48` — no es una entrada directa
del menú de Analytics (`wireframes-analytics.md` §3.3).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | `obtenerEvolucionTemporalEstudiante(materiaId, estudianteId)` | Sobre `apiFetch`/`ApiError` |
| Cliente API (nuevo) | `obtenerEvolucionTemporalComision(materiaId, comisionId)` | Ídem, mismo cliente |
| Pantalla (nueva) | `EvolucionTemporal.tsx` | Gráfico de línea SVG, 2 series simultáneas |
| Ruta (nueva) | `/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId/evolucion` | Protegida con `RequireRole rol="docente"`, accesible solo desde el detalle de `US-ADJ-48`, no desde `AppNav.tsx` |

---

## Especificacion del comportamiento

### Precondicion

- `US-ADJ-45` y `US-ADJ-48` implementadas (el drill-down origina desde el detalle de estudiante
  de esta última).
- Docente autenticado.

### Postcondicion

- Breadcrumb de 3 niveles: "Analytics › Desempeño por comisión › {Estudiante} — Evolución
  temporal".
- Gráfico de línea en SVG, eje Y 0–100%, eje X = actividades rendidas en orden cronológico
  (etiquetadas por `titulo_actividad`) — dos series: el estudiante elegido (línea sólida, azul)
  y el promedio de la comisión (línea punteada, verde), ambas de sus respectivos endpoints de
  `US-ADJ-45`.
- Leyenda debajo del gráfico, color + nombre de cada serie.
- **Caso límite — 1 sola evaluación**: un solo punto, sin línea (ni para el estudiante ni para
  el promedio si solo una actividad tiene datos).
- **Caso límite — actividad sin rendir**: la actividad simplemente no aparece en el eje X para
  ese estudiante — nunca un punto en 0% ni un hueco marcado.
- Sin ninguna evaluación finalizada (estudiante y comisión): gráfico vacío con mensaje de
  estado vacío, sin ejes sin sentido.

### Invariantes

| ID | Invariante |
|----|------------|
| — | Las dos series se dibujan sobre el mismo eje X — actividades presentes en una serie pero no en la otra simplemente no tienen punto en esa serie, sin interpolar ni forzar alineación artificial. |
| — | Esta pantalla nunca es una entrada directa del menú — solo se llega desde el drill-down de `US-ADJ-48`. |

---

## Criterios de aceptacion

```gherkin
Feature: Evolución temporal individual vs. comisión (US-ADJ-49)

  Scenario: Serie completa con varias actividades
    Given un estudiante con 4 evaluaciones finalizadas y su comisión con datos de esas mismas actividades
    When el Docente entra desde el drill-down de "Desempeño por comisión"
    Then ve un gráfico de línea con 2 series, eje X etiquetado por título de actividad

  Scenario: Una sola evaluación
    Given un estudiante con una única Evaluacion finalizada
    When se renderiza el gráfico
    Then se ve un solo punto, sin línea, para esa serie

  Scenario: Actividad no rendida por el estudiante
    Given una actividad que la comisión sí rindió pero el estudiante elegido no
    When se renderiza el gráfico
    Then esa actividad no aparece en el eje X de la serie del estudiante

  Scenario: Acceso sin rol Docente
    Given un Estudiante o Administrador autenticado
    When intenta acceder directamente a la ruta de evolución temporal
    Then es redirigido por RequireRole, no ve la pantalla
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — frontend puro, gráfico SVG hecho a mano (mismo criterio del proyecto de no sumar
  una librería de gráficos para un solo gráfico de línea simple).

**Capa(s) afectadas:**
- [ ] Backend — sin cambios
- [x] Frontend — cliente API (2 funciones nuevas), pantalla `EvolucionTemporal.tsx`, 1 ruta
  nueva anidada bajo `desempeno-por-comision`, sin entrada en `AppNav.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-analytics.md` §3.3 (`#doc-evolucion-temporal`). Prototipo:
`docs/design/ux/prototipos/analytics-portal-desempeno.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/analytics-api.ts` | Agrega `obtenerEvolucionTemporalEstudiante`, `obtenerEvolucionTemporalComision` |
| `frontend/src/pages/analytics/EvolucionTemporal.tsx` | Nueva pantalla |
| `frontend/src/pages/analytics/DesempenoResumenDetalle.tsx` | Agrega el link/botón hacia la evolución temporal desde el detalle de estudiante (`US-ADJ-48`) |
| `frontend/src/router.tsx` | 1 ruta nueva, `RequireRole rol="docente"` |
| Tests Vitest correspondientes | Serie completa, 1 sola evaluación, actividad no rendida, estado vacío |

---

## Referencias

- Depende de: `US-ADJ-45`, `US-ADJ-48`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#359](https://github.com/vvalotto/cognion/issues/359)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
