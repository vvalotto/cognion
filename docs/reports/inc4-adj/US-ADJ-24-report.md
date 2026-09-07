# Reporte de Implementación: US-ADJ-24 - Administrador crea una Comisión

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-24 |
| **Título** | Administrador crea una Comisión |
| **Producto** | cognion |
| **Prioridad** | Alta — precondición de `US-ADJ-25`/`US-ADJ-26` y de la Validación E2E (`US-ADJ-31`) |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-07 |
| **Fecha fin** | 2026-09-07 |
| **Tiempo real** | ~16 min de tracking (Fases 0-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Segunda US de la Iteración 1a del Incremento 4-ADJ: el Administrador puede ahora crear una
Comisión (Materia + horario) desde la UI, reemplazando el placeholder dejado por `US-ADJ-23`
en `/comisiones/nueva`. Frontend puro — `POST /comisiones` ya aceptaba rol `administrador`
desde `US-1.1.1`, sin cambios de backend. Único componente técnico nuevo: decodificar el claim
`sub` del JWT del lado del cliente para resolver `administrador_id`, campo que el formulario no
le pide al usuario.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — `POST /comisiones` (`materia_id`, `horario`, `administrador_id`) ya aceptaba rol
`administrador` desde `US-1.1.1`.

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/session.ts` — `obtenerUsuarioId()`, decodifica el claim `sub` del JWT
  de la sesión actual
- ✅ `frontend/src/lib/identidad-comisiones-api.ts` — `crearComision(materiaId, horario, signal?)`
- ✅ `frontend/src/pages/identidad/NuevaComision.tsx` (nuevo) — pantalla de alta
- ✅ `frontend/src/pages/identidad/Comisiones.tsx` — botón "+ Nueva Comisión" pasa
  `?materiaId=` al navegar
- ✅ `frontend/src/router.tsx` — `/comisiones/nueva` usa `NuevaComision` en vez de
  `ComisionPlaceholder`

**Total archivos:** 5 (0 backend, 5 frontend)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/lib/session.test.ts` — +5 tests (`obtenerUsuarioId`)
- ✅ `frontend/src/lib/identidad-comisiones-api.test.ts` — +1 test (`crearComision`)
- ✅ `frontend/src/pages/identidad/NuevaComision.test.tsx` (nuevo) — 5 tests

#### Tests de Integración
- ✅ `frontend/src/router.test.tsx` — +2 tests (`/comisiones/nueva` con rol distinto de
  administrador → acceso denegado; con rol administrador → formulario)

**Total tests nuevos:** 13 · **Estado:** 272/273 frontend pasando (1 flake preexistente,
`NuevaPreguntaOpcionMultiple.test.tsx`, sin relación con esta US — timeout intermitente,
pasa aislado, confirmado antes y después de este cambio)

#### Escenarios BDD

No aplica — frontend puro sobre un endpoint ya cubierto por
`tests/integration/inc1/test_comisiones_api_integration.py`, sin comportamiento de dominio
nuevo. Mismo criterio que otras US de frontend puro del proyecto (`US-2.1.10`, `US-3.4.2`).

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (5 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** (comando real de `npm run build`) | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 272/273 (1 flake preexistente) | Sin regresiones | ✅ |
| **Coverage `session.ts`** | 100% stmts/branches/functions/lines | — | ✅ |
| **Coverage `NuevaComision.tsx`** | 90.32% stmts / 81.25% branches / 92.59% lines | — | ✅ |
| **Coverage global frontend (branches)** | 78.74% | ≥ 80% | ⚠️ ver "Cambios no Previstos" |

Fuente: `quality/reports/inc4-adj/US-ADJ-24-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Formulario con Materia (preseleccionada si se llega desde el listado) y Horario (texto
      libre)
- [x] Al crear, navega al detalle de la Comisión recién creada
- [x] Sin asignación de Docente en el mismo formulario (acción separada, `US-ADJ-25`)

**Estado:** 3/3 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Frontend puro, sin componentes de dominio nuevos. `NuevaComision.tsx` sigue el mismo patrón ya
establecido por `NuevaMateria.tsx` (`US-ADJ-20`): `AbortController` creado en `useEffect` (no
en el render) para que el doble montaje de `StrictMode` en dev no aborte el submit siguiente.

### Flujo de Datos

```
Administrador (browser)
  → GET /materias (banco_preguntas, US-2.1.9) — selector de Materia
  → [submit] POST /comisiones (identidad, US-1.1.1, sin cambios)
      administrador_id resuelto de obtenerUsuarioId() (claim `sub` del JWT de sesión)
  → navigate(/comisiones/{id})
```

---

## Cambios no Previstos

- **`administrador_id` sin forma de resolverse en el frontend** (detectado en Fase 2, al
  escribir la spec): `Session` (`session.ts`) solo persistía `token`/`rol`, no el id del
  usuario autenticado — pero el body de `POST /comisiones` lo exige. Resuelto decodificando el
  claim `sub` del JWT client-side (sin verificar firma, el backend ya la valida en cada
  request), sin librería nueva ni endpoint `GET /usuarios/me` — la opción más simple
  consistente con "sin cambios de backend" ya decidido en la spec original.

---

## Testing Manual Realizado

No se hizo un recorrido en navegador real dedicado a esta US — se verificó con la suite
automatizada completa (`tsc -b`, oxlint, Vitest). El recorrido en navegador real queda
cubierto por la Validación E2E consolidada de `US-ADJ-31` (Iteración 2 del incremento), que
ejercita el flujo completo Administrador → crear Comisión → asignar Docente → invitación →
registro de Estudiante en una sola corrida.

---

## Deuda Técnica

- **No introducida por esta US, pero detectada trabajando en ella:** el umbral global de
  cobertura de branches del frontend (`vite.config.ts`, 80%) ya estaba roto en `develop` antes
  de este cambio (78.51%, causado por `Comisiones.tsx` de `US-ADJ-23` sin ningún test) — esta
  US lo mejora levemente (78.74%) pero no lo cierra, está fuera de su alcance. Reportado como
  chip aparte (`task_ec36dcbe`, "Agregar tests a Comisiones.tsx").

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-25` — Administrador asigna un Docente a una Comisión (siguiente en orden — una
      Comisión sin Docente asignado no sirve para generar invitación)
- [ ] `US-ADJ-26` — Docente genera el link de invitación de una Comisión

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 64s |
| Plan | 26s |
| Implementación | 97s |
| Tests Unitarios | 476s |
| Tests de Integración | 273s |
| Quality Gates | 20s |
| Documentación | 64s |
| **TOTAL** | **~1020s (~17 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar el patrón de `AbortController` en `useEffect` de `NuevaMateria.tsx` evitó
   repetir el bug de `StrictMode` ya documentado en `US-ADJ-20`.
2. Verificar la spec contra el wireframe (§3.2 `wireframes-portal-entrada.md`) en Fase 0/2
   detectó el gap de `administrador_id` antes de escribir código, no en QA.

### Recomendaciones para Próximas Historias

1. Al planificar una US que envía un id de "actor" en el body de un POST/PUT, verificar antes
   si el frontend tiene forma de resolverlo — este proyecto no tenía ningún helper de
   decodificación de JWT hasta esta US, a pesar de que varios endpoints ya lo requerían
   (`administrador_id`, `docente_id` en otros formularios).
2. Usar siempre `tsc -b` (no `tsc --noEmit` a secas) para el chequeo de tipos de cierre — ya
   documentado como lección de `US-ADJ-23`, confirmado de nuevo en esta US.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-07.
