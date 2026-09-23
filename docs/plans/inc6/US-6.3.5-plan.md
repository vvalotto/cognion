# Plan de Implementación: US-6.3.5 - Docente crea la sesión en vivo y abre la sala de espera

**Patrón:** React 19 + TypeScript + Vite, sobre el cliente API/canal de `US-6.3.4`
**Producto:** Cognion — frontend

## Decisión de diseño (Fase 2)

- **Gap frontend (no de backend):** `ComisionDetalleResponse` (`identidad-comisiones-api.ts`)
  gana `materiaId` — el backend ya lo devuelve, solo faltaba mapearlo. Necesario para resolver
  el nombre de Materia en la sala de espera (`GET estado` de la sesión solo trae `comisionId`).
- **Formulario (`NuevaSesionEnVivo.tsx`):** mismo patrón de datos que `NuevaActividad.tsx` —
  resuelve Materia vía `obtenerComision(comisionId)` → `materiaId` → `listarMaterias()` (find),
  banco vía `filtrarBanco(materia.bancoId)` + `derivarSugerencias()` para las opciones de
  Unidad temática/Tema (`<Select>`, mismo criterio que `NuevaActividad`, no `<datalist>` — la
  spec cita ambos precedentes y el código real de `NuevaActividad` usa `<Select>`). Sin
  selector de Comisión — `comisionId` de la ruta.
- **Sala de espera (`SalaEsperaDocente.tsx`):** al montar, `obtenerEstadoSesion(sesionId)` +
  `listarParticipantes(sesionId)`; si `estado === "en_curso"` → navega a la proyección
  (placeholder todavía, `US-6.3.6`); si `"finalizada"` → vuelve a la Comisión. Resuelve
  Materia vía `obtenerComision(estado.comisionId)` → `listarMaterias()`. Usa
  `useCanalSesionEnVivo` (primer consumidor real): `onMensaje` reemplaza la lista completa de
  participantes en `participantes_actualizados`, ignora otros tipos; `onReconectado` vuelve a
  pedir `listarParticipantes`. Indicador "Reconectando…" inline (chip discreto, H8) — solo esta
  pantalla lo necesita por ahora, se extrae a componente compartido recién cuando
  `US-6.3.6`/`6.3.7` lo repitan (evita abstracción prematura).
- **"Iniciar sesión":** `iniciarSesion(sesionId)`; **doble click no duplica request** (botón
  deshabilitado mientras la promesa está en vuelo, mismo patrón que otros formularios);
  `422 SesionYaIniciada` navega igual a la proyección (idempotencia de cara al usuario, no es
  un error visible).
- **`ComisionDetalleDocente.tsx`:** botón "+ Nueva sesión en vivo" (navega al formulario) +
  bloque "Sesiones en vivo activas" (`listarSesionesEnVivo(comisionId)`, filtra client-side
  `estado !== "finalizada"`) con `Badge` + "Continuar" (→ sala si `en_espera`, → proyección
  placeholder si `en_curso`).
- **Badge:** variante nueva `estado-en-espera` (ámbar) en `badge.tsx`; `estado-en-curso` ya
  existe, se reutiliza.
- **Rutas:** reemplaza los 2 placeholders de `US-6.3.4`
  (`/sesiones-en-vivo/comisiones/:comisionId/nueva`, `/sesiones-en-vivo/:sesionId/sala`) por
  las pantallas reales. Las otras 2 rutas (`proyeccion`, `mis-sesiones-en-vivo`) quedan con
  placeholder hasta `US-6.3.6`/`6.3.8`.

## Componentes a Implementar

### 1. Cliente API (gap frontend)

- [ ] `frontend/src/lib/identidad-comisiones-api.ts` — `ComisionDetalleResponse` gana
  `materiaId: string`, `mapearDetalle` lo completa

### 2. Formulario de nueva sesión

- [ ] `frontend/src/pages/actividad-evaluativa/NuevaSesionEnVivo.tsx` (nuevo) — breadcrumb,
  campos (unidad/tema opcionales vía `<Select>`, cantidad de preguntas, tiempo límite),
  validación de cliente, `crearSesion`, manejo de 404/422 con el `detail` del servidor

### 3. Sala de espera

- [ ] `frontend/src/pages/actividad-evaluativa/SalaEsperaDocente.tsx` (nuevo) — datos de la
  sesión, chips de participantes, canal WebSocket, indicador de reconexión, "Iniciar sesión"

### 4. Comisión — botón y bloque de sesiones activas

- [ ] `frontend/src/pages/actividad-evaluativa/ComisionDetalleDocente.tsx` (ampliado) — botón
  "+ Nueva sesión en vivo", bloque "Sesiones en vivo activas"
- [ ] `frontend/src/components/ui/badge.tsx` — variante `estado-en-espera`

### 5. Rutas

- [ ] `frontend/src/router.tsx` — reemplaza 2 placeholders por las pantallas reales, quita los
  2 exports ya no usados de `_placeholders-en-vivo.tsx`

### 6. Tests

- [ ] `NuevaSesionEnVivo.test.tsx`, `SalaEsperaDocente.test.tsx`,
  `ComisionDetalleDocente.test.tsx` (ampliado), `router.test.tsx` (ampliado)
- [ ] `tests/features/inc6/US-6.3.5-crear-sesion-sala-espera.feature` — validado contra Vitest,
  sin step_defs

**Estado:** 0/12 tareas completadas
