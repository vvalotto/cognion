# Reporte de Implementación: US-1.1.7

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.7 - Docente/Administrador/Estudiante inicia sesión desde la UI
- **Puntos estimados:** 3
- **Tiempo real:** ~24 min (fases 0-9, tracking de ejecución del agente, no comparable contra
  esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-07-27

Segunda US de la Iteración 2 (frontend de Identidad), primera que consume la infraestructura de
`US-1.1.6` con el flujo más simple del wireframe (login: una sola pantalla con dos estados,
sin pasos intermedios como el registro). Cierra `RF-02` en frontend.

---

## Componentes Implementados

### Componentes UI base (shadcn/ui)
- ✅ `frontend/src/components/ui/input.tsx` (nuevo) — vía `npx shadcn add input`
- ✅ `frontend/src/components/ui/label.tsx` (nuevo) — vía `npx shadcn add label`

### Pantallas de Login (`frontend/src/pages/`)
- ✅ `LoginError.tsx` (nuevo) — alerta inline con el mensaje genérico de credenciales
  inválidas (§2.2 `wireframes-identidad.md`); no distingue email inexistente de contraseña
  incorrecta
- ✅ `Login.tsx` (nuevo) — formulario controlado (email/contraseña), consume
  `POST /identidad/login` vía `apiFetch`; éxito guarda la sesión (`setSession`) y redirige por
  rol (`administrador` → `/docentes/nuevo`; `docente`/`estudiante` → `/`); error limpia la
  contraseña y muestra `LoginError` en la misma tarjeta (decisión de diseño confirmada con
  Víctor: no es una ruta separada)

### Integración
- ✅ `frontend/src/pages/_placeholders.tsx` (editado) — agrega `InicioPlaceholder` (destino
  post-login de docente/estudiante), quita `LoginPlaceholder` (reemplazado por la pantalla real)
- ✅ `frontend/src/router.tsx` (editado) — `/login` deja de ser placeholder; ruta `index`
  agregada bajo `AppLayout`

---

## Métricas de Calidad

Umbrales adaptados a stack frontend (TypeScript/React) — sin perfil dedicado en el skill, ver
`docs/plans/inc1/US-1.1.7-context.md`.

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| ESLint/oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Vitest | 21/21 pasan | 100% pasan | ✅ |
| Cobertura (statements) | 96.96% | ≥80% (referencia) | ✅ |
| Cobertura (branches) | 86.66% | ≥80% (referencia) | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc1/US-1.1.7-quality.json`)

---

## Tests Implementados

### Tests Unitarios (2 tests)
- `LoginError.test.tsx` (1 test) — muestra el mensaje genérico de credenciales inválidas

### Tests de Integración (18 tests, 4 archivos nuevos/actualizados)
- `Login.test.tsx` (4 tests) — login exitoso (administrador → `/docentes/nuevo`,
  docente/estudiante → `/`), credenciales inválidas (limpia contraseña, mantiene email),
  email inexistente (mismo tratamiento que credenciales inválidas)
- `router.test.tsx` (2 tests, 1 actualizado) — `/login` renderiza la pantalla real de Login
  dentro de `AuthLayout` (antes verificaba el placeholder, ya no existe)
- Suite completa del proyecto (suma de todas las US de frontend): 21/21 tests

### Escenarios BDD (3 escenarios) — `tests/features/inc1/US-1.1.7-login-ui.feature`
- Login exitoso
- Login rechazado por credenciales inválidas
- Login rechazado por email inexistente

Sin runner Gherkin dedicado para TypeScript — los 3 escenarios están cubiertos 1:1 por
`Login.test.tsx` (ver Fase 6).

**Todos los tests pasando:** ✅ 21/21 (suite frontend completa)

---

## Archivos Creados/Modificados

### Código de producción
- `frontend/src/components/ui/input.tsx` (nuevo)
- `frontend/src/components/ui/label.tsx` (nuevo)
- `frontend/src/pages/LoginError.tsx` (nuevo)
- `frontend/src/pages/Login.tsx` (nuevo)
- `frontend/src/pages/_placeholders.tsx` (editado)
- `frontend/src/router.tsx` (editado)

### Tests
- `frontend/src/pages/LoginError.test.tsx` (nuevo)
- `frontend/src/pages/Login.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (editado)
- `tests/features/inc1/US-1.1.7-login-ui.feature` (nuevo)

### Documentación
- `docs/plans/inc1/US-1.1.7-context.md`
- `docs/plans/inc1/US-1.1.7-plan.md`
- `docs/reports/inc1/US-1.1.7-report.md` (este archivo)
- `quality/reports/inc1/US-1.1.7-quality.json`
- `CHANGELOG.md` (entrada `[US-1.1.7]`)
- `docs/traceability/matrix.md` (RF-02 → Implementado)
- `docs/plans/inc1/inc1-candidatas.md` (US-1.1.7 tachada como cerrada)

---

## Criterios de Aceptación

- [x] Login exitoso guarda el JWT y redirige a la vista correspondiente al rol
- [x] Login rechazado por credenciales inválidas muestra el error genérico
- [x] Login rechazado por email inexistente muestra la misma pantalla de error (no filtra
      existencia de cuentas)

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-1.1.8` (Estudiante se registra desde la UI con un link de invitación)
- [ ] Implementar `US-1.1.9` (Administrador da de alta un Docente desde la UI) — construye
      la ruta `/docentes/nuevo` a la que hoy redirige `Login.tsx` para `administrador`
- [ ] Abrir BL-002 una vez cerradas `US-1.1.8` y `US-1.1.9` (criterio de cierre de baseline,
      `docs/plans/PLAN-CM.md` §7)

---

## Lecciones Aprendidas

- 💡 El CLI de `shadcn` (`npx shadcn add`) resolvió mal el alias `@/` y escribió los archivos
  en un directorio literal `frontend/@/` en vez de `frontend/src/`; se detectó y corrigió
  moviendo los archivos a la ruta correcta antes de continuar — vale la pena verificar
  `git status` después de cualquier instalación vía este CLI.
- ✅ Reutilizar el patrón de `router.test.tsx` de `US-1.1.6` como test de integración
  (sin crear un archivo de integración separado) evitó duplicar cobertura.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-27
