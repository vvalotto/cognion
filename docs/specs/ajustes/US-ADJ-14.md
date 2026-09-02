# US-ADJ-14: Reordenar `frontend/src/pages/` por Bounded Context

**Estado**: `Especificada`
**Iteracion / Sprint**: `Incremento 3-ADJ — Adecuación Técnica`
**Tipo**: `refactor frontend` (movimiento de archivos + imports, sin cambio de comportamiento)
**Agregado principal afectado**: ninguno — no toca dominio
**Bounded Context**: transversal (las 4 áreas de frontend: Identidad, Banco de Preguntas,
Actividad Evaluativa, Cuentas)
**Origen**: conversación de esta sesión sobre la estructura del proyecto de frontend, antes de
cerrar el Incremento 3.

---

## Descripcion (lenguaje de negocio)

Como **desarrollador del proyecto**,
quiero **que `frontend/src/pages/` esté organizado por Bounded Context, igual que `lib/` y que
`src/` del backend**
para **encontrar y mantener las pantallas de cada área sin recorrer un directorio plano de más
de 30 archivos, sobre todo antes de que los Incrementos 4 a 7 agreguen más**.

---

## Contexto del dominio

### Problema

`frontend/src/lib/` ya está modularizado por BC desde hace varios incrementos
(`actividad-evaluativa-api.ts`, `banco-preguntas-api.ts`, `cuentas-api.ts`,
`identidad-estudiante-api.ts`) — y el propio backend organiza `src/<bc>/` desde el Incremento 1.
`frontend/src/pages/`, en cambio, es un directorio plano con 33 pantallas (67 archivos contando
tests) sin ninguna agrupación, acumuladas incremento tras incremento sin reorganizarse.

### Alcance del fix

Puro reordenamiento mecánico — mover archivos a subcarpetas por BC y actualizar los imports que
los referencian (`router.tsx`, y cualquier test que importe una página con un path relativo
distinto de `@/pages/NombrePagina`). **Sin cambiar**:

- Ninguna ruta de URL (`router.tsx` sigue definiendo los mismos `path`).
- Ningún componente, lógica, ni test — solo su ubicación en el árbol de archivos.
- El alias `@/pages/*` sigue resolviendo mediante `vite.config.ts`/`tsconfig`, así que los
  imports pasan de `@/pages/Login` a `@/pages/identidad/Login` (path completo actualizado en
  cada `import`).

### Agrupación propuesta (a confirmar con Víctor al implementar)

| Carpeta | Pantallas |
|---|---|
| `pages/identidad/` | `Login`, `LoginError`, `LoginCuentaBloqueadaError`, `Registro`, `RegistroError`, `RegistroExito`, `AltaDocente`, `AltaDocenteExito`, `CambiarPassword` |
| `pages/cuentas/` | `Cuentas`, `CuentaDetalle`, `ResetearPassword`, `CuentaReseteada` |
| `pages/banco-preguntas/` | `Materias`, `NuevaMateria`, `Banco`, `NuevaPreguntaTipo`, `NuevaPreguntaOpcionMultiple`, `NuevaPreguntaVerdaderoFalso`, `EditarPregunta`, `EliminarPregunta` |
| `pages/actividad-evaluativa/` | `MateriasActividades`, `Actividades`, `NuevaActividad`, `ActividadDetalle`, `EditarTituloActividad`, `ExtenderPlazo`, `CerrarActividad`, `MisMaterias`, `MisActividades`, `FueraDePeriodo`, `RendirEvaluacion`, `EvaluacionSuspendida`, `RevisionEvaluacion` |
| `pages/` (raíz, sin BC propio) | `_placeholders.tsx` (si sigue teniendo consumidores tras `US-3.4.7`, revisar si ya quedó obsoleto) |

---

## Especificacion del comportamiento

### Precondicion

- `frontend/src/pages/` plano, 33 pantallas sin agrupar.

### Postcondicion

- Cada pantalla vive en `pages/<bc>/NombrePagina.tsx` (+ su `.test.tsx` al lado, mismo criterio
  que hoy).
- `router.tsx` y todo test que importe una página usan el path nuevo.
- `npx vitest run` y `npx tsc -b --noEmit` en verde, mismo conteo de tests que antes del
  reordenamiento (ningún test se pierde ni se duplica).
- Ninguna URL de la aplicación cambia — verificado navegando manualmente las rutas principales
  después del refactor (no hace falta UAT formal, es un refactor sin cambio de comportamiento).

### Invariantes

Ninguna — no hay cambio de dominio.

---

## Criterios de aceptacion

```gherkin
Feature: pages/ organizado por BC (US-ADJ-14)

  Scenario: La suite completa sigue en verde tras el movimiento
    Given frontend/src/pages/ reorganizado en subcarpetas por BC
    When se corre npx vitest run y npx tsc -b --noEmit
    Then ambos terminan sin errores, mismo número de tests que antes del refactor

  Scenario: Ninguna URL cambia
    Given la aplicación reorganizada corriendo en el navegador
    When se navega a cualquier ruta ya existente (ej. /materias, /mis-actividades/materias)
    Then la pantalla correspondiente se renderiza igual que antes del refactor
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [x] No — refactor de organización de archivos, sin cambio de comportamiento ni de contrato.

**Capa(s) afectadas:**
- [x] Frontend — `frontend/src/pages/*`, `frontend/src/router.tsx`, tests asociados
- [ ] Backend — sin cambios

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `frontend/src/pages/*.tsx`, `*.test.tsx` | Movidos a `pages/<bc>/` según la tabla de agrupación |
| `frontend/src/router.tsx` | Imports actualizados a los nuevos paths |
| Tests que importen páginas fuera de su propio directorio (si los hay) | Imports actualizados |

---

## Referencias

- Relacionada con: la organización ya existente de `frontend/src/lib/` (por BC) y de
  `src/<bc>/` en el backend
- Detectada durante: conversación de esta sesión sobre estructura de frontend, antes del cierre
  del Incremento 3

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
