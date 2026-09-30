# Reporte de Implementación: US-ADJ-37 - Descubribilidad — Cambiar contraseña y Cerrar sesión en el menú

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-37 |
| **Título** | Descubribilidad — Cambiar contraseña y Cerrar sesión en el menú |
| **Producto** | cognion |
| **Prioridad** | Última US de la Iteración 1 del Incremento 5-ADJ — la cierra completa |
| **Puntos estimados** | 1 |
| **Fecha inicio** | 2026-09-12 |
| **Fecha fin** | 2026-09-12 |
| **Tiempo real** | ~13 min de tracking (Fases 0, 2-5, 7-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Última US de la Iteración 1 del Incremento 5-ADJ: el bloque de avatar/nombre/rol estático del
header (`AppLayout.tsx`) pasa a un menú desplegable (`UserMenu.tsx`, envuelve `Menu` de
`@base-ui/react/menu`) con dos ítems — "🔑 Cambiar contraseña" y "↩ Cerrar sesión" — que
agregan el único punto de entrada por clic a dos funciones ya implementadas y funcionales
(`CambiarPassword.tsx` de `US-2.2.8`, `clearSession()`) pero que hasta ahora solo eran
alcanzables tecleando la URL de memoria o vía el interceptor 401 automático. Frontend puro,
sin cambios de backend. Mismo menú para los 3 roles.

---

## Componentes Implementados

### Código Fuente (Backend)

Ninguno — US frontend puro.

### Código Fuente (Frontend)

- ✅ `frontend/src/components/UserMenu.tsx` (nuevo) — envuelve `Menu.Root`/`Menu.Trigger`/
  `Menu.Portal`/`Menu.Positioner`/`Menu.Popup`/`Menu.Item` de `@base-ui/react/menu`, mismo
  criterio de `components/ui/button.tsx` (primitivo sin estilar + clases Tailwind del
  proyecto). Recibe `nombre`/`rol` por prop, sin leer `session`/`localStorage` directamente
  (mismo patrón que `AppNav`)
- ✅ `frontend/src/layouts/AppLayout.tsx` — reemplaza el `<div>` estático de avatar/nombre por
  `<UserMenu nombre={nombre} rol={session.rol} />`; se eliminó la lógica de `iniciales()`/
  `ETIQUETA_ROL` de este archivo (se movió a `UserMenu.tsx`, dueño ahora de ese dato de
  presentación)

**Total archivos:** 2 (0 backend, 2 frontend — 1 nuevo, 1 modificado)

---

### Tests

#### Tests Unitarios
- ✅ `frontend/src/components/UserMenu.test.tsx` (nuevo) — 7 tests: trigger con nombre y rol,
  una sola inicial sin apellido, abrir el menú, navegar a Cambiar contraseña, cerrar sesión y
  redirigir a `/login`, mismos dos ítems para los 3 roles (parametrizado)

#### Tests de Integración
- ✅ `frontend/src/layouts/AppLayout.test.tsx` — +1 test: abre el menú de usuario desde el
  header real de `AppLayout` y confirma los dos ítems
- ✅ Los 8 tests preexistentes de `AppLayout.test.tsx` siguen pasando sin cambios

#### Escenarios BDD

No aplica — frontend puro, componente de presentación sin lógica de negocio, mismo criterio
que `US-ADJ-24`/`27`/`28`/`29`/`30`/`35`/`36`.

**Total tests nuevos/actualizados:** 8 nuevos · **Estado:** 390/396 frontend pasando (6
fallos de flake preexistente de contención de CPU en corridas con procesos paralelos,
confirmado ajeno a esta US — los 2 archivos tocados por esta US pasan 17/17 en aislamiento,
igual que los 6 archivos afectados por el flake al correrlos aislados)

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **oxlint** | 0 errores (6 warnings preexistentes, no relacionados) | 0 errores | ✅ |
| **tsc -b** | 0 errores | 0 errores | ✅ |
| **Vitest** (archivos tocados, aislados) | 17/17 | Sin regresiones | ✅ |
| **Coverage `UserMenu.tsx`** | 100% stmts/functions/lines, 87.5% branches | — | ✅ |
| **Coverage `AppLayout.tsx`** | 100% stmts/branches/functions/lines | — | ✅ |

Fuente: `quality/reports/inc5-adj/US-ADJ-37-quality.json`. No aplica CodeGuard/pylint/CC/MI —
sin cambios en `src/` (Python). La rama sin cubrir de `UserMenu.tsx` es el fallback `?? ""` de
`iniciales()` para partes vacías del nombre, inalcanzable en la práctica tras
`.trim().split(/\s+/)` sobre un nombre no vacío (mismo código heredado sin cambios de la
implementación original en `AppLayout.tsx`).

---

## Criterios de Aceptación

- [x] Un usuario autenticado hace clic en su avatar/nombre y ve un menú con "Cambiar
  contraseña" y "Cerrar sesión"
- [x] "Cambiar contraseña" navega a `/mi-cuenta/cambiar-password`
- [x] "Cerrar sesión" limpia la sesión local y redirige a `/login`
- [x] Mismo menú para los 3 roles (Docente, Estudiante, Administrador)

**Estado:** 4/4 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Componente de presentación puro que envuelve un primitivo de `@base-ui/react` — mismo nivel
que `components/ui/button.tsx` envolviendo `@base-ui/react/button` — ubicado en `components/`
(no `components/ui/`) porque compone lógica propia de la aplicación (`session.ts`,
navegación) en vez de ser una primitiva de base reutilizable sin contexto de dominio.

### Flujo de Datos

```
<UserMenu nombre={nombre} rol={session.rol} />
  → Menu.Root (estado open/closed interno de @base-ui/react)
  → Menu.Trigger (avatar + nombre + rol + caret)
  → Menu.Popup
      → Menu.Item render={<Link to="/mi-cuenta/cambiar-password" />}
      → Menu.Item onClick={() => { clearSession(); navigate("/login") }}
```

Sin estado propio del componente (`useState`) — toda la interacción (abrir/cerrar,
highlight, teclado) la maneja `@base-ui/react/menu` internamente.

---

## Cambios no Previstos

Ninguno — implementación siguió el plan aprobado sin desviaciones. El encabezado del popup
muestra nombre + rol (sin email, como especifica el texto de la HU) — el prototipo HTML
(`identidad-autoservicio.html#menu-usuario`) muestra además el email en ese encabezado, dato
no disponible client-side (sin claim de email en el JWT ni endpoint `GET /usuarios/me`). Se
mantuvo el criterio ya establecido en `US-ADJ-28`/`29`/`30` (saludo genérico en las Home sin
ese endpoint) en vez de agregar backend nuevo fuera del alcance declarado de esta US.

---

## Testing Manual Realizado

Recorrido en navegador real (Claude Browser, sesión inyectada vía `localStorage` para saltear
el login): abrir el menú desde el trigger, navegar a "Cambiar contraseña" (confirmado
`/mi-cuenta/cambiar-password` real), y "Cerrar sesión" (confirmado `localStorage` limpio y
redirección a `/login`). Los 3 escenarios manuales del criterio de aceptación verificados
sin hallazgos.

---

## Deuda Técnica

Ninguna introducida por esta US.

---

## Próximos Pasos

### Historias Relacionadas

Ninguna — `US-ADJ-37` cierra completa la Iteración 1 del Incremento 5-ADJ (`US-ADJ-35` a
`37`). Sigue la Iteración 2 (recuperación de contraseña, `US-ADJ-38`/`39`) según
`docs/plans/inc5-adj/inc5-adj-candidatas.md`.

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 33s |
| Plan | 36s |
| Implementación | 94s |
| Tests Unitarios | 278s |
| Tests de Integración | 34s |
| Quality Gates | 96s |
| Documentación | 42s |
| **TOTAL** | **~613s (~10 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`). La mayor parte del tiempo (Tests Unitarios)
correspondió a una corrida de la suite completa de Vitest lanzada para detectar
regresiones, afectada por contención de CPU al correr procesos en paralelo por error —
confirmado sin relación con el código de esta US (mismo patrón ya documentado en
`US-ADJ-35`/`36`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Verificar en navegador real con una sesión inyectada por `localStorage` (sin necesitar el
   backend corriendo) permitió confirmar los 3 escenarios de interacción del criterio de
   aceptación con costo mínimo, mismo criterio de "UAT en navegador real detecta lo que
   Vitest mockeado no ve" ya documentado en el proyecto — en este caso, confirmando en
   positivo que no hay gaps, no detectando uno nuevo.
2. Ejecutar `npx vitest run` de la suite completa solo una vez, en background, y validar los
   fallos re-corriendo únicamente los archivos afectados en aislamiento, confirmó rápido que
   eran el mismo flake de contención de CPU ya documentado en `US-ADJ-35`/`36` sin necesitar
   investigar cada archivo.

### Recomendaciones para Próximas Historias

1. Mismo patrón que `US-ADJ-35`: evitar lanzar más de un proceso de Vitest en paralelo al
   correr la suite completa para verificación — la contención de CPU produce timeouts falsos
   en archivos no relacionados al cambio.
