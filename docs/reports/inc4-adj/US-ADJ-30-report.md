# Reporte de Implementación: US-ADJ-30 - Home del Administrador

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-30 |
| **Título** | Home del Administrador |
| **Producto** | cognion |
| **Prioridad** | Alta — última US de la Iteración 1b, la cierra completa |
| **Puntos estimados** | 2 |
| **Fecha inicio** | 2026-09-07 |
| **Fecha fin** | 2026-09-07 |
| **Tiempo real** | ~13 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Cuarta y última US de la Iteración 1b: reemplaza `InicioPlaceholder` por una Home real para el
rol Administrador, con 3 cards de acceso directo (Comisiones, Alta de Docente, Cuentas). A
diferencia de Docente/Estudiante, el Administrador nunca pasaba por `/` — el login lo mandaba
directo a `/docentes/nuevo` desde `US-1.1.9`. Se corrigió `RUTA_POST_LOGIN.administrador` a
`/`, y como los 3 roles quedaron apuntando al mismo destino, se simplificó eliminando la tabla
`RUTA_POST_LOGIN` en favor de `navigate("/")` directo. **Cierra completa la Iteración 1b del
Incremento 4-ADJ** — ningún rol depende ya de `InicioPlaceholder` en el flujo normal de login.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro.

### Código Fuente (Frontend)

- ✅ `frontend/src/pages/HomeAdministrador.tsx` (nuevo) — saludo genérico + 3 cards de acceso
- ✅ `frontend/src/pages/Inicio.tsx` — agrega la rama `rol === "administrador"`
- ✅ `frontend/src/pages/identidad/Login.tsx` — `RUTA_POST_LOGIN.administrador` → `/`;
  simplificación: se elimina la tabla `RUTA_POST_LOGIN` (redundante con los 3 roles
  apuntando a `/`) en favor de `navigate("/")` directo

**Total archivos:** 3 (0 backend, 3 frontend)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/pages/HomeAdministrador.test.tsx` (nuevo) — 5 tests (saludo, 3 cards,
  navegación por clic y teclado)
- ✅ `frontend/src/pages/Inicio.test.tsx` — actualizado: Administrador ahora ve
  `HomeAdministrador`; agregado test del fallback defensivo sin rol reconocido
- ✅ `frontend/src/pages/identidad/Login.test.tsx` — actualizado: login de administrador
  redirige a `/` (antes `/docentes/nuevo`)

#### Tests de Integración
- ✅ `frontend/src/router.test.tsx` — `/` con sesión administrador renderiza la Home (no más
  placeholder), +1 test de navegación real por clic (mockeando `GET /usuarios` para la
  pantalla de Cuentas de destino)

**Total tests nuevos/actualizados:** 16 · **Estado:** 329/329 frontend pasando, sin
regresiones

#### Escenarios BDD

No aplica — frontend puro, mismo criterio que `US-ADJ-24`/`27`/`28`/`29`.

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (5 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** (comando real de `npm run build`) | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa) | 329/329 | Sin regresiones | ✅ |
| **Coverage `HomeAdministrador.tsx`** | 100% stmts/lines/functions, 50% branches (mismo patrón aceptado en las otras 2 homes) | — | ✅ |
| **Coverage `Inicio.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |
| **Coverage `Login.tsx`** | 94.59% stmts / 87.5% branches / 96.96% lines (línea sin cubrir preexistente, rethrow de error no-`ApiError`, no relacionada al cambio de esta US) | — | ✅ |
| **Coverage global frontend (branches)** | 79.74% | ≥ 80% | ⚠️ ver "Deuda Técnica" |

Fuente: `quality/reports/inc4-adj/US-ADJ-30-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] 3 cards: Comisiones, Alta de Docente, Cuentas
- [x] Click en cada card navega a la ruta ya existente
- [x] `RUTA_POST_LOGIN[administrador]` apunta a `/`

**Estado:** 3/3 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Idéntico a `US-ADJ-28`/`29`. Único ajuste adicional: `Login.tsx` simplificado — al quedar los
3 roles con el mismo destino post-login, mantener una tabla `Record<Rol, string>` era
indirección sin beneficio (regla del proyecto: no premature abstraction).

### Flujo de Datos

```
Login exitoso → setSession(...) → navigate("/")
Ruta índice (/)
  → <Inicio /> lee getSession()?.rol
      "docente"        → <HomeDocente />
      "estudiante"      → <HomeEstudiante />
      "administrador"   → <HomeAdministrador /> (3 cards)  ← agregado en esta US
      (sin rol)          → <InicioPlaceholder /> (fallback defensivo, no debería ocurrir)
  → click en card → navigate(card.to)
```

---

## Cambios no Previstos

- **Simplificación de `RUTA_POST_LOGIN`** (detectada al implementar la tarea 3): no estaba en
  el plan original como ítem separado, pero es consecuencia directa del cambio pedido — con
  los 3 roles apuntando a `/`, mantener la tabla habría sido código muerto en potencia (un
  `Record` de 3 entradas idénticas). Se eliminó en la misma tarea.
- **Ajuste de `router.test.tsx`** (Fase 4): igual que en `US-ADJ-29`, agregar la Home del
  Administrador introdujo ambigüedad de texto entre el ítem del `AppNav` y las cards
  ("Comisiones", "Cuentas") — corregido con `getAllByText`/`getByRole` según el caso, mismo
  patrón ya aplicado en `US-ADJ-29`. También se mockeó `GET /usuarios` para el test de
  navegación a Cuentas, que antes no lo necesitaba.

---

## Testing Manual Realizado

No se hizo un recorrido en navegador real dedicado a esta US — verificado con la suite
automatizada completa. El recorrido en navegador real, incluyendo el login real de
Administrador → Home → Comisiones/Cuentas, queda cubierto por `US-ADJ-31`.

---

## Deuda Técnica

- **No introducida por esta US, pero sigue presente:** umbral global de cobertura de branches
  del frontend (80%) sigue roto — 79.74% tras esta US. Mismo chip abierto (`task_ec36dcbe`).

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-31` — Validación E2E consolidada del MVP (Iteración 2, última del incremento) —
  ahora puede recorrer el flujo completo desde un login real navegando por clic, incluidas
  las 3 homes recién implementadas

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 10s |
| Plan | 324s |
| Implementación | 104s |
| Tests Unitarios | 219s |
| Tests de Integración | 13s |
| Quality Gates | 92s |
| Documentación | 28s |
| **TOTAL** | **~790s (~13 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Anticipar el problema de ambigüedad de texto en `router.test.tsx` (documentado como
   recomendación en el reporte de `US-ADJ-29`) hizo que corregirlo en esta US fuera mecánico,
   no una sorpresa.
2. Eliminar código que queda redundante en el momento (la tabla `RUTA_POST_LOGIN`) en vez de
   dejarlo "por las dudas" mantiene el código fiel al estado real del sistema.

### Recomendaciones para Próximas Historias

1. Con las 3 homes completas, `US-ADJ-31` (Validación E2E) ya puede ejercitar el camino real
   login → función para los 3 roles sin depender de URLs tipeadas — vale la pena revisar el
   guion de esa US contra las homes reales antes de ejecutarla.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-07.
