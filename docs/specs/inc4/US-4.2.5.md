# US-4.2.5: Docente ve "Desempeño por alumno"

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-4.2`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **elegir una materia, una comisión y un estudiante, y ver su desempeño**
para **hacer seguimiento individual de cualquier alumno sin depender de que él lo comparta
(RF-16)**.

---

## Contexto del dominio

### Problema

`US-4.2.1` ya expone el endpoint; `US-4.2.2` ya expone comisiones/estudiantes. Falta la
pantalla que encadena los tres selectores y reutiliza el componente visual de "Mi desempeño"
(`US-4.1.3`) — el wireframe (§4, hot spot 2) es explícito: **mismo componente**, solo cambia el
origen del `estudiante_id` y los selectores adicionales.

**Selectores en cascada:** elegir Materia acota las Comisiones (`GET
/materias/{materia_id}/comisiones`); elegir Comisión acota los Estudiantes (`GET
/comisiones/{comision_id}/estudiantes`). Antes de elegir un Estudiante, la pantalla muestra un
placeholder ("Elegí un estudiante para ver su desempeño"), sin resumen ni lista
(`wireframes-analytics.md` §3.0).

**Selector de materia (Docente):** a diferencia de `US-4.1.3` (estudiante,
`listarMisMaterias()`), el Docente ya tiene `listarMaterias()` propio (`US-2.1.9`) — reutilizar
ese, no crear uno nuevo.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | funciones tipadas para `GET /materias/{materia_id}/comisiones`, `GET /comisiones/{comision_id}/estudiantes`, `GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno` | Sobre `apiFetch`/`ApiError` existentes |
| Pantalla (nueva) | `DesempenoPorAlumno.tsx` | Selectores en cascada + reutiliza el componente visual de resumen/detalle ya extraído (o a extraer) de `MiDesempeno.tsx` |
| Ruta (nueva) | `/analytics/desempeno-por-alumno` (o path equivalente, a confirmar en el plan) | Protegida con `RequireRole rol="docente"` |

---

## Especificacion del comportamiento

### Precondicion

- `US-4.2.1` y `US-4.2.2` implementadas.
- Docente autenticado.

### Postcondicion

- Al entrar a la pantalla: selector de Materia poblado (`listarMateria()`, `US-2.1.9`), sin
  Comisión/Estudiante elegidos → placeholder, sin resumen ni lista.
- Elegir Materia → pobla el selector de Comisión (`GET /materias/{materia_id}/comisiones`);
  limpia cualquier Comisión/Estudiante elegidos antes.
- Elegir Comisión → pobla el selector de Estudiante (`GET /comisiones/{comision_id}/estudiantes`);
  limpia cualquier Estudiante elegido antes.
- Elegir Estudiante → dispara `GET /analytics/materias/{materia_id}/estudiantes/{estudiante_id}/desempeno`
  → muestra resumen acumulado + detalle por evaluación (mismo componente que `US-4.1.3`), o el
  estado vacío si el estudiante no tiene evaluaciones finalizadas en esa materia.
- Cambiar cualquier selector de nivel superior reinicia los de nivel inferior y el resultado
  mostrado (no debe quedar "pegado" mostrando el desempeño del estudiante anterior).

### Invariantes

| ID | Invariante |
|----|------------|
| — | No se duplica la implementación visual del resumen/detalle entre esta pantalla y "Mi desempeño" — mismo componente, distinto origen de datos (wireframe §4, hot spot 2). |
| — | Sin acceso a esta ruta con rol distinto de `docente` (`RequireRole`, cliente) — el backend ya rechaza con 403 si igual se intenta por API directa. |

---

## Criterios de aceptacion

```gherkin
Feature: Docente ve "Desempeño por alumno" (US-4.2.5)

  Scenario: Recorrido completo en cascada
    Given un Docente en la pantalla "Desempeño por alumno"
    When elige una Materia, luego una Comisión, luego un Estudiante con evaluaciones finalizadas
    Then ve el resumen acumulado y el detalle por evaluación de ese estudiante

  Scenario: Estudiante sin evaluaciones finalizadas
    Given el Docente ya eligió Materia y Comisión
    When elige un Estudiante sin ninguna Evaluacion finalizada en esa materia
    Then ve el mensaje de estado vacío, sin resumen ni lista

  Scenario: Cambiar de Materia reinicia los selectores inferiores
    Given el Docente ya eligió Materia, Comisión y Estudiante, viendo su desempeño
    When cambia el selector de Materia
    Then los selectores de Comisión y Estudiante quedan sin elegir y el resumen desaparece

  Scenario: Acceso sin rol Docente
    Given un Estudiante o Administrador autenticado
    When intenta acceder a la ruta de "Desempeño por alumno"
    Then es redirigido por RequireRole, no ve la pantalla
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — frontend puro, reutiliza `apiFetch`/`RequireRole`/el componente visual ya validado
  en `US-4.1.3`.

**Capa(s) afectadas:**
- [ ] Entities / Use Cases / Interface Adapters / Frameworks (backend) — sin cambios
- [x] Frontend — cliente API (3 funciones nuevas), pantalla `DesempenoPorAlumno.tsx`, ruta
  nueva en `router.tsx` protegida con `RequireRole rol="docente"`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-analytics.md` §3.0 (`#doc-desempeno-alumno`) y §4 (hot spots 1 y 2:
sin pantalla de entrada "elegí materia" separada — el selector vive dentro de la propia
pantalla; mismo componente visual que "Mi desempeño"). Prototipo:
`docs/design/ux/prototipos/analytics-portal-desempeno.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/analytics-api.ts` | Agrega `obtenerDesempenoDeEstudiante(materiaId, estudianteId)` |
| `frontend/src/lib/identidad-api.ts` (o equivalente) | Agrega `listarComisionesPorMateria(materiaId)`, `listarEstudiantesDeComision(comisionId)` |
| `frontend/src/pages/analytics/DesempenoPorAlumno.tsx` | Nueva pantalla |
| `frontend/src/router.tsx` | Ruta nueva, `RequireRole rol="docente"` |
| Tests Vitest correspondientes | Cascada de selectores, estado vacío, reinicio al cambiar de nivel |

---

## Referencias

- Depende de: `US-4.2.1` (#240), `US-4.2.2` (#241)
- Candidatas: `docs/plans/inc4/inc4-candidatas.md` §Iteración 2
- Issue: #244

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
