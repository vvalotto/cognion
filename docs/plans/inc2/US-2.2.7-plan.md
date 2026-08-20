# Plan de Implementación: US-2.2.7 - Administrador ve el detalle de una cuenta y resetea/desbloquea (UI)

**Patrón:** React 19 + TypeScript + Vite (frontend puro, sin capas Clean Architecture)
**Producto:** cognion (frontend)

## Componentes a Implementar

### 1. Cliente API (`frontend/src/lib/cuentas-api.ts`)
- [x] Agregar `CuentaDetalleResponse` (extiende `CuentaResponse` con `creadoEn`, `comisionId`)
  — mapea snake_case del backend (`creado_en`, `comision_id`) a camelCase, mismo criterio que
  `banco-preguntas-api.ts`
- [x] `obtenerCuenta(id: string): Promise<CuentaDetalleResponse>` — `GET /usuarios/{id}`
- [x] `resetearPassword(id: string, passwordNueva: string): Promise<CuentaDetalleResponse>` —
  `POST /usuarios/{id}/resetear-password`, body `{ password_nueva: passwordNueva }`

### 2. `frontend/src/pages/CuentaDetalle.tsx`
- Reemplaza `CuentaDetallePlaceholder` en `/cuentas/:usuarioId`
- Breadcrumb "Administración › Cuentas › {nombre}"
- Alerta destructiva (`role="alert"`, mismo estilo que `EliminarPregunta.tsx`) si
  `bloqueada = true`, explicando el motivo (3 intentos fallidos consecutivos)
- Datos: email, rol, estado, comisión (solo si `perfil === "estudiante"` y `comisionId` no es
  null), fecha de creación
- Botón único "Resetear contraseña y desbloquear" → navega a
  `/cuentas/:usuarioId/resetear-password`
- Sin edición de nombre/email/comisión (fuera de alcance, según spec)

### 3. `frontend/src/pages/ResetearPassword.tsx`
- Ruta nueva `/cuentas/:usuarioId/resetear-password`
- Aviso (alerta de advertencia, no destructiva): "Esta acción también desbloquea la cuenta"
- Formulario: nueva contraseña, confirmar contraseña (`Input` type="password", `Label`, mismo
  patrón que `EditarPregunta.tsx`)
- Validación de cliente antes de llamar al backend: ≥ 8 caracteres, coincidencia entre ambos
  campos — mensajes de error en el mismo estilo `role="alert"` que `EditarPregunta.tsx`
- "Resetear contraseña" (`Button variant="destructive"`, mismo criterio que
  `EliminarPregunta.tsx` — destructiva por el impacto) → ejecuta `resetearPassword`, navega a
  `/cuentas/:usuarioId/reseteada` pasando `nombre` por `location.state` (mismo patrón que
  `AltaDocenteExito.tsx`)
- "Cancelar" (`Button variant="outline"`) → vuelve a `/cuentas/:usuarioId` sin llamar al backend

### 4. `frontend/src/pages/CuentaReseteada.tsx`
- Ruta nueva `/cuentas/:usuarioId/reseteada`
- Confirmación: nombre de la cuenta (desde `location.state`, con fallback genérico si no está
  presente — mismo patrón que `AltaDocenteExito.tsx`), mensaje de éxito (contraseña reseteada +
  cuenta desbloqueada)
- Botón "Volver al listado de cuentas" → navega a `/cuentas`

### 5. Integración de rutas (`frontend/src/router.tsx`)
- [x] Reemplazar el placeholder existente en `/cuentas/:usuarioId` por `CuentaDetalle`
- [x] Agregar `/cuentas/:usuarioId/resetear-password` → `ResetearPassword`
- [x] Agregar `/cuentas/:usuarioId/reseteada` → `CuentaReseteada`
- Las tres protegidas con `RequireRole rol="administrador"` (mismo criterio que `/cuentas`)
- Quitar `CuentaDetallePlaceholder` de `_placeholders.tsx` si queda sin otros usos — hecho

**Estado:** ✅ COMPLETADO
**Fecha completado:** 2026-08-20

## Métricas de Tiempo

| Fase | Elapsed |
|------|---------|
| Fase 0 — Validación de Contexto | 34s |
| Fase 1 — Escenarios BDD | 95s |
| Fase 2 — Plan de Implementación | 73s |
| Fase 3 — Implementación (5 tareas) | 104s |
| Fase 4 — Tests Unitarios | 410s |
| Fase 5 — Tests de Integración (n/a, frontend puro — cubierta por `router.test.tsx`) | 19s |
| Fase 6 — Validación BDD | 4s |
| Fase 7 — Quality Gates | 61s |
| **Total (Fases 0–7)** | **~13 min** |

## Lecciones Aprendidas

- ✅ Agrupar tres pantallas (detalle, formulario de reseteo, confirmación) en una sola US,
  mismo criterio que `US-2.1.11`, mantuvo el flujo completo revisable de punta a punta sin
  fragmentar el review.
- 💡 `ResetearPassword.tsx` resuelve el nombre de la cuenta con su propio `obtenerCuenta()` en
  vez de recibirlo por `location.state` desde `CuentaDetalle` — permite entrar directo a
  `/cuentas/:id/resetear-password` (deep link, recarga de página) sin perder el nombre para la
  pantalla de confirmación.
- ⚠️ El test de integración preexistente `router.test.tsx` para `/cuentas/:usuarioId` verificaba
  el placeholder de `US-2.2.6` con el fetch mock genérico (`[]`); al reemplazar la pantalla real
  hubo que actualizarlo con un mock de `CuentaDetalleResponse` completo — un recordatorio de que
  los tests de integración de rutas quedan acoplados al contrato de datos de la pantalla que
  navegan, no solo a la ruta.
