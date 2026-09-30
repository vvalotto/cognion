# Plan de Implementación: US-6.3.8 - Estudiante ve las sesiones disponibles, se une y espera en la sala

**Patrón:** React 19 + TypeScript + Vite, sobre el cliente API/canal de `US-6.3.4` (sin cambios de `src/`)
**Producto:** Cognion — frontend

## Decisiones de diseño (Fase 2)

- **Cliente API:** `listarSesionesEnVivo(comisionId?: string, signal?)` — sin `comisionId` no manda el query param
  (el backend resuelve la Comisión del Estudiante). Cambio aditivo; `ComisionDetalleDocente.tsx` sigue igual.
- **Bloque "Sesiones en vivo" en `MisActividades.tsx`** (arriba de la tabla de actividades, mismo lugar, sin menú
  nuevo): tarjetas (`<button>`, accesibles con teclado) con Materia, cantidad de preguntas y `Badge`
  (`estado-en-espera` / `estado-en-curso`). Filtra por la `materiaId` de la pantalla y descarta `finalizada`.
  Estado vacío: "Por ahora no hay sesiones en vivo".
  - **Refresco:** al montar y cada 10 s con `setInterval` dentro de un `useEffect` (cleanup: `clearInterval` + abort del
    pedido en vuelo). Si la pestaña está oculta (`document.visibilityState === "hidden"`) se salta ese ciclo.
  - **Tap:** `unirseASesion` (una sola request en vuelo) → navega a `/mis-sesiones-en-vivo/:sesionId`.
    `422` (`SesionYaFinalizada`) o `404` → mensaje (`role="alert"`) y refresca la lista.
- **Contenedor `SesionEnVivoEstudiante.tsx`** (ruta `/mis-sesiones-en-vivo/:sesionId`, dentro de `AppLayout`):
  al montar llama a `unirseASesion` (reunión idempotente, INV-AEV-06 — cubre recargar sin guardar nada en el
  cliente) y después a `GET estado`. `422 SesionYaFinalizada` al unirse no corta: el `GET estado` decide la etapa.
  `404` → "Esta sesión ya no está disponible" + volver a mis materias.
  - Etapas: `EnEspera` → `sala`; `EnCurso` → `pregunta`; `Finalizada` → `finalizada`. `pregunta` y `finalizada` son
    un texto provisional dentro del contenedor: **`US-6.3.9` las reemplaza** (mismo criterio `US-6.3.6` → `6.3.7`).
  - Canal: `participantes_actualizados` → conteo; `pregunta_presentada` → `pregunta` (transición automática, sin
    botón); `sesion_finalizada` → `finalizada`. `onReconectado` → `GET estado`. `IndicadorConexion` (H8).
  - Lógica de etapas en una función pura (`estudiante/vista-estudiante.ts`), como `vista-proyeccion.ts`.
  - **Doble unión en la primera entrada** (tap + montaje): se acepta. Es idempotente en el servidor y evita guardar
    en el cliente que "ya se unió" (la spec lo pide explícitamente).
- **`SalaEsperaEstudiante.tsx`** (`#est-sala-espera`): "¡Te uniste!", "Esperando que el docente inicie la sesión —
  mirá la proyección del aula", alerta de éxito con "N participantes ya en la sala". **Sin el botón deshabilitado del
  prototipo** (el wireframe §3.2 lo aclara como placeholder): un texto de estado "Esperando al docente…".
- **Rutas:** reemplaza `MiSesionEnVivoPlaceholder`; `_placeholders-en-vivo.tsx` queda sin exports y se borra.

## Componentes a Implementar

- [ ] `lib/sesion-en-vivo-api.ts` — `comisionId` opcional (+ test)
- [ ] `pages/actividad-evaluativa/MisActividades.tsx` — bloque de sesiones, refresco, unirse (+ tests)
- [ ] `pages/actividad-evaluativa/estudiante/vista-estudiante.ts` — etapas (+ tests)
- [ ] `pages/actividad-evaluativa/estudiante/SalaEsperaEstudiante.tsx` (+ test)
- [ ] `pages/actividad-evaluativa/SesionEnVivoEstudiante.tsx` — contenedor (+ test)
- [ ] `router.tsx` — ruta real; borrar `_placeholders-en-vivo.tsx`; `router.test.tsx` ajustado
- [ ] Validar los 10 escenarios de `tests/features/inc6/US-6.3.8-sesiones-sala-estudiante.feature` con Vitest

**Estado:** 0/7 tareas completadas
