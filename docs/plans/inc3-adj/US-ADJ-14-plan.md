# Plan de Implementación: US-ADJ-14 - Reordenar `frontend/src/pages/` por Bounded Context

**Patrón:** N/A — refactor mecánico de organización de archivos frontend
**Producto:** cognion
**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-09-03

## Métricas de Tiempo

Tracking vía `.claude/tracking/tracker_cli.py` (`.claude/tracking/US-ADJ-14-tracking.json`).
Fases 1, 4, 5 y 6 omitidas (refactor sin comportamiento nuevo, sin tests nuevos). Tiempo real
acumulado sin comparación contra estimación humana (`PRIN-001`).

## Lecciones Aprendidas

- 💡 Un script con mapeo nombre→BC + regex (`@/pages/(Nombre)(?![A-Za-z0-9_])`) sobre todo
  `frontend/src/**/*.{ts,tsx}` resolvió los 34 imports a actualizar en una sola pasada, sin
  editar archivo por archivo — más rápido y sin riesgo de olvidar uno de los 32 tests.
  `git mv` archivo por archivo (en vez de mover el directorio completo) preservó el historial
  de cada archivo individual.
  - ✅ Medir el baseline de `vitest run` *antes* de mover nada (41 archivos / 229 tests) dio
  una comparación exacta post-refactor, sin depender de memoria ni de "se ve bien".

## Baseline antes del refactor
- `npx vitest run`: 41 test files, 229 tests, todos en verde.

## Componentes a Implementar

### 1. Crear subcarpetas y mover pantallas (`.tsx` + `.test.tsx` al lado)
- [x] `pages/identidad/`: `Login`, `LoginError`, `LoginCuentaBloqueadaError`, `Registro`,
  `RegistroError`, `RegistroExito`, `AltaDocente`, `AltaDocenteExito`, `CambiarPassword`
- [x] `pages/cuentas/`: `Cuentas`, `CuentaDetalle`, `ResetearPassword`, `CuentaReseteada`
- [x] `pages/banco-preguntas/`: `Materias`, `NuevaMateria`, `Banco`, `NuevaPreguntaTipo`,
  `NuevaPreguntaOpcionMultiple`, `NuevaPreguntaVerdaderoFalso`, `EditarPregunta`,
  `EliminarPregunta`
- [x] `pages/actividad-evaluativa/`: `MateriasActividades`, `Actividades`, `NuevaActividad`,
  `ActividadDetalle`, `EditarTituloActividad`, `ExtenderPlazo`, `CerrarActividad`,
  `MisMaterias`, `MisActividades`, `FueraDePeriodo`, `RendirEvaluacion`,
  `EvaluacionSuspendida`, `RevisionEvaluacion`
- [x] `pages/` (raíz): `_placeholders.tsx` queda sin mover — sigue teniendo un consumidor
  (`InicioPlaceholder`, usado en `router.tsx`), confirmado con `git mv` (33 pantallas, todas
  con `.tsx`; 30 con `.test.tsx` al lado — `Actividades` y `MateriasActividades` nunca tuvieron
  test propio)

### 2. Actualizar imports
- [x] `router.tsx`: 33 imports `@/pages/NombrePagina` → `@/pages/<bc>/NombrePagina`
- [x] `Login.tsx`: imports internos a `LoginError`/`LoginCuentaBloqueadaError` actualizados a
  `@/pages/identidad/LoginError` y `@/pages/identidad/LoginCuentaBloqueadaError`
- [x] 32 archivos `*.test.tsx` que importan su propia página bajo prueba vía
  `@/pages/NombrePagina` → `@/pages/<bc>/NombrePagina`

Script Python con mapeo nombre→BC + regex sobre `@/pages/(Nombre)(?![A-Za-z0-9_])`, aplicado a
todo `frontend/src/**/*.{ts,tsx}`. 34 archivos modificados (router.tsx + Login.tsx + 32 tests).

## Verificación (reemplaza Fases 1/4/5/6 — sin tests nuevos, sin comportamiento nuevo)

- [x] `npx vitest run`: 41 test files / 229 tests, todos en verde — idéntico al baseline
  medido antes del refactor
- [x] `npx tsc -b --noEmit`: 0 errores
- [x] `npx oxlint`: 0 errores, mismos 4 warnings preexistentes (uno de ellos con el path
  actualizado — `pages/actividad-evaluativa/RendirEvaluacion.test.tsx`)
- [x] Ninguna URL cambia — `router.tsx` sigue definiendo los mismos `path`, solo cambiaron los
  imports (confirmado por diff — ningún `path:` tocado)

**Estado:** 4/4 tareas completadas
