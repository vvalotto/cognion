# Plan de Implementación: US-6.3.6 - Docente proyecta la pregunta, muestra las opciones y la cierra

**Patrón:** React 19 + TypeScript + Vite, sobre el cliente API/canal de `US-6.3.4` (sin cambios de `src/`)
**Producto:** Cognion — frontend

## Decisiones de diseño (Fase 2)

- **Contenedor `ProyeccionSesionEnVivo`** (ruta `/sesiones-en-vivo/:sesionId/proyeccion`, dentro de
  `StageLayout`): estado `vista` con `etapa` ∈ `cargando | pregunta-sola | pregunta-opciones | cerrada |
  finalizada` más los datos de la pregunta (índice 0-based, enunciado, tipo, opciones, tiempo límite,
  `inicioOpcionesMs`, conteo, total de participantes, cantidad de preguntas) y, para `US-6.3.7`, el
  `resultado` recibido en `pregunta_cerrada`/`sesion_finalizada`.
  - `calcularVista(estado)` (función pura): `en_espera` → redirige a la sala; `en_curso` con
    `opcionesMostradas=false` → `pregunta-sola`; `opcionesMostradas=true` y no cerrada →
    `pregunta-opciones`; `preguntaActualCerrada` → `cerrada`; `finalizada` → `finalizada`.
  - Se ejecuta al montar y en cada `onReconectado` (`GET estado`).
  - Mensajes del canal: `pregunta_presentada` → `pregunta-sola` de la nueva pregunta;
    `opciones_mostradas` → `pregunta-opciones` con inicio = `Date.now()` al recibirlo;
    `conteo_respuestas_actualizado` → conteo (solo si el índice coincide);
    `participantes_actualizados` → total; `pregunta_cerrada` → `cerrada`; `sesion_finalizada` →
    `finalizada`.
  - Etapas `cerrada`/`finalizada`: **placeholder mínimo dentro del contenedor** (texto), punto de
    extensión para `US-6.3.7` — esta US no las diseña.
- **Acciones y recuperación:** "Mostrar opciones" / "Cerrar pregunta" con guard de request en vuelo
  (doble click = una sola request). La etapa siguiente llega por el canal; si en 2 s no cambió, se
  recalcula con `GET estado` (timer cancelado si el mensaje llega). `422` (`OpcionesYaMostradas`,
  `PreguntaYaCerrada`) → recalcula con `GET estado`. `AbortController` creado en `useEffect`
  (lección `US-ADJ-20`), nunca en el render.
- **Temporizador (`lib/temporizador-pregunta.ts`):** `segundosRestantes(limite, inicioMs, ahoraMs)`
  acotado a ≥ 0, `formatearTemporizador` (`MM:SS`), hook `useSegundosRestantes` con `setInterval`.
  En vivo el inicio es el reloj local al recibir `opciones_mostradas`; tras recargar es
  `Date.parse(opcionesMostradasEn)`. Informativo: en 0 no cierra nada.
- **Opciones (`lib/opciones-en-vivo.ts`):** `opcionesEnVivo(tipo, opciones)` → lista `{texto, color}`:
  V/F → "Verdadero" `b` / "Falso" `c` (H1); N opciones → `a,b,c,d` cíclico (H2, la tercera de 3 ocupa
  el ancho completo). Colores vía `var(--stage-color-*)` en `style` (Tailwind no ve clases
  dinámicas); texto oscuro sobre amarillo (`c`), como el prototipo. **Sin ninguna marca de correcta.**
- **Chip "Reconectando…" (H8):** segundo consumidor real → se extrae `IndicadorConexion.tsx`
  compartido; `SalaEsperaDocente` pasa a usarlo (cambio mínimo, sus tests deben seguir verdes).
- **Legibilidad (§1.1):** enunciado `text-[40px]` (30 px en la etapa con opciones, según prototipo),
  eyebrow ≥ 20 px en mayúsculas, temporizador y opciones ≥ 26 px, columna única centrada. Se verifica
  en navegador real (`US-6.3.10`); jsdom no calcula estilos.
- **Eyebrow:** "Pregunta {índice+1} de {total}".

## Componentes a Implementar

### 1. Librerías compartidas (con `US-6.3.9`)

- [ ] `frontend/src/lib/opciones-en-vivo.ts` (+ test) — mapa opción → color, V/F, N opciones
- [ ] `frontend/src/lib/temporizador-pregunta.ts` (+ test) — cálculo, formato y hook

### 2. Componente compartido

- [ ] `frontend/src/components/IndicadorConexion.tsx` (+ test) — chip "Reconectando…"
- [ ] `SalaEsperaDocente.tsx` — usa el componente extraído

### 3. Etapas y contenedor

- [ ] `frontend/src/pages/actividad-evaluativa/proyeccion/StagePreguntaSola.tsx` (+ test)
- [ ] `frontend/src/pages/actividad-evaluativa/proyeccion/StagePreguntaOpciones.tsx` (+ test)
- [ ] `frontend/src/pages/actividad-evaluativa/ProyeccionSesionEnVivo.tsx` (+ test) — máquina de
  etapas, canal, acciones, recuperación

### 4. Rutas

- [ ] `frontend/src/router.tsx` — reemplaza el placeholder de proyección; se quita
  `ProyeccionSesionEnVivoPlaceholder` de `_placeholders-en-vivo.tsx`; `router.test.tsx` ajustado

### 5. Validación BDD

- [ ] Los 10 escenarios de `tests/features/inc6/US-6.3.6-proyeccion-pregunta-opciones.feature`
  cubiertos por Vitest (sin step_defs), más los casos extra: etapa por estado (`EnEspera` →
  sala, cerrada, finalizada) y `422` con recálculo

## Dependencias y puntos de integración

- `mostrarOpciones`, `cerrarPregunta`, `obtenerEstadoSesion` (`sesion-en-vivo-api.ts`);
  `useCanalSesionEnVivo` (`US-6.3.4`) — sin cambios. Sin cambios de backend.

**Estado:** 0/10 tareas completadas
