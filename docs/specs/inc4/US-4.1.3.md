# US-4.1.3: Estudiante ve la pantalla "Mi desempeño"

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.1`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **ver mi desempeño en una materia elegida, con resumen acumulado y detalle por
evaluación**
para **saber cómo me está yendo en la cursada sin pedírselo al docente (RF-15)**.

---

## Contexto del dominio

### Problema

`US-4.1.2` ya expone `GET /analytics/materias/{materia_id}/mi-desempeno`. Falta la pantalla que
lo consume — cierra completa la Iteración 1 del Incremento 4.

**Selector de materia:** reutiliza `GET /identidad/estudiante/materias`
(`listarMisMaterias()`, `identidad-estudiante-api.ts`, ya existente desde `US-3.4.5`) — sin
endpoint nuevo. Si el estudiante cursa una sola materia, el selector no se muestra (mismo
criterio que el resto de los selectores de una sola opción en el proyecto).

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | `analytics-api.ts` | `obtenerMiDesempeno(materiaId)` sobre `apiFetch`/`ApiError` (`US-1.1.6`) |
| Cliente API reutilizado | `identidad-estudiante-api.ts` | `listarMisMaterias()`, sin cambios |
| Pantalla (nueva) | `MiDesempeno.tsx` | `#est-desempeno` — selector de materia, `.summary-bar` (resumen), lista de `.eval-item` (detalle) |
| Ruta (nueva) | `/analytics/mi-desempeno` | Protegida `RequireRole rol="estudiante"` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.1.2` implementada.
- Estudiante autenticado (rol `estudiante`).

### Postcondicion

- Estudiante con una sola materia: la pantalla carga directo el desempeño de esa materia, sin
  selector visible.
- Estudiante con más de una materia: selector de materia (`<select>`), por defecto la primera;
  cambiar la selección vuelve a pedir el desempeño de la materia elegida.
- Con `evaluaciones` no vacío: `.summary-bar` con correctas/incorrectas acumuladas, % de
  acierto, cantidad de evaluaciones; lista de `.eval-item` por evaluación, más reciente
  primero (`wireframes-analytics.md` §2.0).
- Con `evaluaciones` vacío (estudiante sin ninguna evaluación finalizada en esa materia):
  mensaje de estado vacío ("Todavía no finalizaste ninguna evaluación de esta materia"), sin
  `.summary-bar` ni lista (§2.0, fila "Estado vacío").
- Error de red/servidor: mensaje de error genérico, sin romper el resto de la UI (mismo patrón
  que el resto de las pantallas del proyecto).

### Invariantes

| ID | Invariante |
|----|------------|
| — | La pantalla nunca navega a la revisión pregunta por pregunta de una evaluación puntual — esa ya existe en Actividad Evaluativa (`#est-revision`), Analytics no la duplica (`wireframes-analytics.md` §4, hot spot 3). |

---

## Criterios de aceptacion

```gherkin
Feature: Estudiante ve "Mi desempeño" (US-4.1.3)

  Scenario: Estudiante con una sola materia y evaluaciones finalizadas
    Given un Estudiante autenticado que cursa una sola materia, con evaluaciones finalizadas
    When entra a /analytics/mi-desempeno
    Then ve el resumen acumulado y el detalle por evaluación de esa materia, sin selector

  Scenario: Estudiante con más de una materia
    Given un Estudiante autenticado que cursa dos materias
    When entra a /analytics/mi-desempeno y cambia la materia seleccionada
    Then el resumen y el detalle se actualizan para la materia recién elegida

  Scenario: Materia sin evaluaciones finalizadas
    Given un Estudiante autenticado sin evaluaciones finalizadas en la materia elegida
    When ve la pantalla
    Then ve el mensaje de estado vacío, sin resumen ni lista

  Scenario: Acceso sin rol Estudiante
    Given un Docente autenticado
    When intenta entrar a /analytics/mi-desempeno
    Then es redirigido (RequireRole), no ve la pantalla
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — sigue el patrón ya establecido de cliente API + `RequireRole` + componentes
  reutilizados (`.summary-bar`, `.eval-item` nuevo pero mismo criterio visual que
  `wireframes-actividad-evaluativa.md`).

**Capa(s) afectadas:**
- [ ] Backend — sin cambios
- [x] Frontend — `frontend/src/lib/analytics-api.ts` (nuevo), `frontend/src/pages/
  MiDesempeno.tsx` (nueva), `frontend/src/router.tsx` (ruta nueva)

---

## Fuente de verdad UX

`docs/design/ux/wireframes-analytics.md` §2.0 (`#est-desempeno`). Prototipo:
`docs/design/ux/prototipos/analytics-portal-desempeno.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/analytics-api.ts` | Nuevo — `obtenerMiDesempeno(materiaId)` |
| `frontend/src/pages/MiDesempeno.tsx` | Nueva — pantalla `#est-desempeno` |
| `frontend/src/router.tsx` | Ruta `/analytics/mi-desempeno`, `RequireRole rol="estudiante"` |

---

## Referencias

- Depende de: `US-4.1.2` (#233)
- Wireframes: `docs/design/ux/wireframes-analytics.md` §2.0
- Cierra completa la Iteración 1 del Incremento 4
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 1

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
