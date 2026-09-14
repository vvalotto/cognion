# US-ADJ-48: Docente ve "Desempeño por comisión" con drill-down

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-5-ADJ.4`
**Tipo**: `feat frontend`
**Agregado principal afectado**: — (BC sin aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver una tabla con el % de aciertos y las actividades pendientes de cada estudiante de
una Comisión, y poder entrar al detalle de uno y de ahí a una evaluación puntual**
para **priorizar a quién atender sin salir de una sola pantalla (RF-20)**.

---

## Contexto del dominio

### Problema

`US-ADJ-44` ya expone `GET /analytics/materias/{materia_id}/comisiones/{comision_id}/desempeno`
y amplió el guard de `GET /evaluaciones/{id}/revision`. Falta la pantalla con sus dos niveles de
drill-down — cierra el par backend→frontend de RF-20.

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Cliente API (nuevo) | `obtenerDesempenoPorComision(materiaId, comisionId)` | Sobre `apiFetch`/`ApiError`, reutiliza `listarComisionesPorMateria` (`US-4.2.5`) |
| Pantalla (nueva) | `DesempenoPorComision.tsx` | Selectores Materia → Comisión (cascada, mismo patrón que `US-4.2.5`/`US-4.2.6`), tabla ordenable |
| Pantalla (reutilizada) | `DesempenoResumenDetalle.tsx` (`US-4.2.5`) | Detalle del estudiante elegido (drill-down 1°) — mismo componente que ya usa `DesempenoPorAlumno.tsx`, sin duplicar |
| Pantalla (nueva) | `RevisionEvaluacionDocente.tsx` (o reutilización directa del componente de revisión ya existente bajo una ruta nueva) | Drill-down 2° nivel — revisión completa de una evaluación puntual, mismo componente visual que `#est-revision` (`US-3.2.3`) pero accedido por un Docente |
| Ruta (nueva) | `/analytics/desempeno-por-comision` | Protegida con `RequireRole rol="docente"` |
| Ruta (nueva) | `/analytics/desempeno-por-comision/materias/:materiaId/comisiones/:comisionId/estudiantes/:estudianteId` | Drill-down 1°, misma protección |
| Ruta (nueva) | `/analytics/desempeno-por-comision/.../evaluaciones/:evaluacionId/revision` | Drill-down 2°, misma protección |

---

## Especificacion del comportamiento

### Precondicion

- `US-ADJ-44` implementada (endpoint + guard ampliado de revisión).
- Docente autenticado.

### Postcondicion

- Al entrar: selector de Materia (`listarMateria()`, `US-2.1.9`) → selector de Comisión
  (`GET /materias/{id}/comisiones`, `US-4.2.2`) → tabla al elegir ambos.
- Tabla: una fila por estudiante — Nombre, % Aciertos acumulado (`Sin datos` en cursiva si
  `null`, nunca "0%"), Actividades pendientes (resaltado en ámbar si > 0) — ordenable por
  columna (click en el encabezado).
- Click en una fila → navega al drill-down 1°: reusa `DesempenoResumenDetalle.tsx` con los
  datos de `GET /analytics/materias/{id}/estudiantes/{id}/desempeno` (`US-4.2.1`, sin cambios).
- Click en una `.eval-item` del detalle → navega al drill-down 2°: revisión completa de esa
  evaluación (`GET /evaluaciones/{id}/revision`, guard ampliado de `US-ADJ-44`) — mismo
  componente visual de `#est-revision`, sin pantalla nueva desde cero (reutilizar el
  componente/JSX de la pantalla de revisión del Estudiante, parametrizado por rol si hiciera
  falta distinguir breadcrumb).
- Comisión sin ningún estudiante con evaluaciones finalizadas: la tabla se muestra igual, todos
  en "Sin datos" (mismo criterio de `US-ADJ-44`).

### Invariantes

| ID | Invariante |
|----|------------|
| — | `null` en `porcentaje_aciertos_acumulado` se renderiza siempre como "Sin datos" en cursiva — nunca como "0%" ni se omite la fila. |
| — | Cambiar de Materia reinicia la Comisión seleccionada (mismo criterio que `US-4.2.6`). |

---

## Criterios de aceptacion

```gherkin
Feature: Desempeño por comisión con drill-down (US-ADJ-48)

  Scenario: Tabla con estados mixtos
    Given un Docente elige una Materia y una Comisión con estudiantes en distinto estado
    When la pantalla carga
    Then ve una fila por estudiante, con "Sin datos" para quien no tiene evaluaciones finalizadas

  Scenario: Drill-down al detalle de un estudiante
    Given la tabla ya cargada
    When el Docente hace click en una fila
    Then ve el detalle de ese estudiante (resumen + lista de evaluaciones)

  Scenario: Drill-down a la revisión de una evaluación puntual
    Given el Docente está en el detalle de un estudiante
    When hace click en una evaluación finalizada
    Then ve la revisión completa pregunta por pregunta, igual que la vería el propio estudiante

  Scenario: Acceso sin rol Docente
    Given un Estudiante o Administrador autenticado
    When intenta acceder a "Desempeño por comisión"
    Then es redirigido por RequireRole, no ve la pantalla
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — frontend puro, reutiliza `apiFetch`/`RequireRole`/`DesempenoResumenDetalle.tsx`
  (`US-4.2.5`) y el componente de revisión ya existente de Actividad Evaluativa.

**Capa(s) afectadas:**
- [ ] Backend — sin cambios
- [x] Frontend — cliente API (1 función nueva), pantalla `DesempenoPorComision.tsx`, 3 rutas
  nuevas en `router.tsx` protegidas con `RequireRole rol="docente"`, entrada nueva en
  `AppNav.tsx`

---

## Fuente de verdad UX

`docs/design/ux/wireframes-analytics.md` §3.2 (`#doc-desempeno-comision`) y §4 (hot spot 2: la
vista de detalle de estudiante es el mismo componente visual que `#doc-desempeno-alumno`,
`US-4.2.5`). Prototipo: `docs/design/ux/prototipos/analytics-portal-desempeno.html`.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/lib/analytics-api.ts` | Agrega `obtenerDesempenoPorComision(materiaId, comisionId)` |
| `frontend/src/pages/analytics/DesempenoPorComision.tsx` | Nueva pantalla |
| `frontend/src/router.tsx` | 3 rutas nuevas, `RequireRole rol="docente"` |
| `frontend/src/components/AppNav.tsx` | Entrada "Desempeño por comisión" |
| Tests Vitest correspondientes | Tabla con estados mixtos, ambos drill-down, RBAC |

---

## Referencias

- Depende de: `US-ADJ-44`, `US-4.2.1` (#240), `US-4.2.5`
- Candidatas: `docs/plans/inc5-adj/inc5-adj-candidatas.md` §Iteración 4
- Issue: [#358](https://github.com/vvalotto/cognion/issues/358)

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
