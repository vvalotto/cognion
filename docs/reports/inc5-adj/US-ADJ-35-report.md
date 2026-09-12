# Reporte de Implementación: US-ADJ-35 - Toggle mostrar/ocultar contraseña

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-35 |
| **Título** | Toggle mostrar/ocultar contraseña |
| **Producto** | cognion |
| **Prioridad** | Alta — primera US de la Iteración 1, `US-ADJ-36` depende de su componente |
| **Puntos estimados** | 1 |
| **Fecha inicio** | 2026-09-12 |
| **Fecha fin** | 2026-09-12 |
| **Tiempo real** | ~28 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Primera US de la Iteración 1 del Incremento 5-ADJ: agrega un componente compartido
`PasswordInput` que envuelve `Input` con un botón de mostrar/ocultar (íconos `Eye`/`EyeOff`),
y reemplaza los 10 inputs `type="password"` repartidos en los 5 formularios existentes del
sistema (`Login.tsx`, `Registro.tsx`, `CambiarPassword.tsx`, `AltaDocente.tsx`,
`cuentas/ResetearPassword.tsx`) por ese componente. Frontend puro, sin cambios de backend ni
de validación existente. Habilita `US-ADJ-36` (indicador de fortaleza de contraseña), que
reutiliza este mismo componente.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro.

### Código Fuente (Frontend)

- ✅ `frontend/src/components/PasswordInput.tsx` (nuevo) — envuelve `Input` con botón de
  toggle interno (`useState`), mismas props que `Input` vía spread
- ✅ `frontend/src/pages/identidad/Login.tsx` — reemplaza `login-password`
- ✅ `frontend/src/pages/identidad/Registro.tsx` — reemplaza `registro-password` y
  `registro-confirmar-password`
- ✅ `frontend/src/pages/identidad/CambiarPassword.tsx` — reemplaza `password-actual`,
  `password-nueva` y `password-confirmacion` (import de `Input` eliminado, quedó sin uso)
- ✅ `frontend/src/pages/identidad/AltaDocente.tsx` — reemplaza `alta-docente-password` y
  `alta-docente-confirmar-password`
- ✅ `frontend/src/pages/cuentas/ResetearPassword.tsx` — reemplaza `password-nueva` y
  `password-confirmacion` (import de `Input` eliminado, quedó sin uso)

**Total archivos:** 6 (0 backend, 6 frontend — 1 nuevo, 5 modificados)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/components/PasswordInput.test.tsx` (nuevo) — 4 tests: arranca oculto,
  alterna a texto visible sin perder el valor, vuelve a ocultar, propaga props adicionales
  (`id`, `required`, `onChange`)

#### Tests de Integración
- ✅ `frontend/src/pages/identidad/Login.test.tsx` — +1 test: el toggle no pierde el valor
  tipeado ni rompe el submit del formulario real
- ✅ Los 26 tests preexistentes de las 5 pantallas modificadas siguen pasando sin cambios
  (usan `getByLabelText`, compatible con el nuevo wrapper sin tocar el DOM del `Label`)

#### Escenarios BDD

No aplica — frontend puro, componente de presentación sin lógica de negocio, mismo criterio
que `US-ADJ-24`/`27`/`28`/`29`/`30`.

**Total tests nuevos/actualizados:** 5 nuevos · **Estado:** 380/384 frontend pasando (4
fallos de flake preexistente de contención de CPU en corridas con procesos paralelos,
confirmado ajeno a esta US — los 2 archivos afectados en cada corrida cambiaban entre sí y
pasan 100% en aislamiento)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (6 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** | 0 errores | 0 errores | ✅ |
| **Vitest** (suite completa, corrida aislada) | 380/384 | Sin regresiones | ✅ |
| **Coverage `PasswordInput.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |
| **Coverage `Login.tsx`** | 94.59% stmts / 87.5% branches / 96.96% lines | — | ✅ (preexistente) |
| **Coverage `Registro.tsx`** | 90.24% stmts / 80% branches / 92.1% lines | — | ✅ (preexistente) |
| **Coverage `CambiarPassword.tsx`** | 95.74% stmts / 83.33% branches / 97.72% lines | — | ✅ (preexistente) |
| **Coverage `AltaDocente.tsx`** | 86.48% stmts / 78.57% branches / 88.23% lines | — | ✅ (preexistente) |
| **Coverage `ResetearPassword.tsx`** | 88.09% stmts / 75% branches / 94.44% lines | — | ✅ (preexistente) |

Fuente: `quality/reports/inc5-adj/US-ADJ-35-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python).

---

## Criterios de Aceptación

- [x] Los 10 inputs `type="password"` de los 5 formularios existentes tienen un botón de
  mostrar/ocultar
- [x] El toggle no pierde el valor tipeado ni recarga el formulario
- [x] El ícono/estado del botón refleja si el contenido está visible u oculto

**Estado:** 3/3 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Componente de presentación puro (`useState` local, sin estado global ni dependencia de
dominio) — mismo nivel que `Select`/`Input` en `components/ui/`, pero ubicado en
`components/` (no `components/ui/`) porque compone un componente `ui/` existente en vez de
ser una primitiva de base.

### Flujo de Datos

```
<PasswordInput {...props} />
  → useState(visible=false)
  → <Input type={visible ? "text" : "password"} {...props} />
  → <button onClick={() => setVisible(v => !v)}><Icon /></button>
```

Sin cambios de estado fuera del componente — el `value`/`onChange` del formulario padre se
pasan intactos vía spread, el toggle es puramente visual.

---

## Cambios no Previstos

Ninguno — implementación siguió el plan aprobado sin desviaciones.

---

## Testing Manual Realizado

No se hizo un recorrido en navegador real dedicado a esta US — verificado con la suite
automatizada (unitarios + integración sobre las 5 pantallas reales). Recomendado revisar
visualmente en conjunto con `US-ADJ-36` (indicador de fortaleza), cuando ambos cambios sean
visibles juntos en los mismos formularios.

---

## Deuda Técnica

Ninguna introducida por esta US.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-36` — Contraseña segura (política ampliada) — reutiliza `PasswordInput` para el
  indicador de fortaleza (prop `mostrarFortaleza`)
- [ ] `US-ADJ-37` — Descubribilidad (menú de usuario) — independiente, sin dependencia de esta US

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 28s |
| Plan | 36s |
| Implementación | 164s |
| Tests Unitarios | 64s |
| Tests de Integración | 374s |
| Quality Gates | 727s |
| Documentación | 255s |
| **TOTAL** | **~1730s (~29 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`). La mayor parte del tiempo (Quality Gates, Integración)
correspondió a corridas de la suite completa de Vitest, afectadas por contención de CPU al
correr procesos en paralelo por error — confirmado sin relación con el código de esta US.

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Usar `getByLabelText` en los tests preexistentes (en vez de seleccionar por tipo de input)
   hizo que los 26 tests de las 5 pantallas siguieran pasando sin ningún ajuste — el wrapper
   nuevo no rompió ninguna asociación label↔input.
2. Eliminar el import de `Input` que quedó sin uso en `CambiarPassword.tsx`/
  `ResetearPassword.tsx` en el momento (no dejarlo "por las dudas") evitó un warning de lint
  innecesario.

### Recomendaciones para Próximas Historias

1. Al correr la suite completa de Vitest para verificación, evitar lanzar más de un proceso
   de Vitest en paralelo — la contención de CPU produce timeouts falsos en archivos no
   relacionados al cambio, generando ruido para diagnosticar regresiones reales.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-12.
