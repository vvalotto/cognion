# Plan de Implementación: US-6.3.7 - Docente proyecta histograma, ranking y resultado final; avanza o finaliza

**Patrón:** React 19 + TypeScript + Vite, sobre el contenedor de `US-6.3.6` (sin cambios de `src/`)
**Producto:** Cognion — frontend

## Decisiones de diseño (Fase 2)

- **Máquina de etapas (`vista-proyeccion.ts`):** la etapa `cerrada` de `US-6.3.6` se reemplaza por
  `histograma` y `ranking`. `pregunta_cerrada` y el `GET estado` con la pregunta cerrada llevan siempre a
  `histograma` (el cliente no recuerda si ya había pasado al ranking — es presentación, spec); el paso a
  `ranking` es una transición local (`verRanking`), sin comando. `finalizada` sigue igual.
  La vista gana `comisionId` (para "Volver a la Comisión") y `opcionesTexto` del resultado
  (`respuestaCorrecta.opciones`).
- **Histograma completo (`lib/opciones-en-vivo.ts`):** `filasHistograma(tipo, respuestaCorrecta, distribucion)` →
  `{texto, color, cantidad, esCorrecta}` para **todas** las opciones: claves `"0"…"n-1"` en opción múltiple,
  `"verdadero"`/`"falso"` en V/F; las que faltan en `distribucion` van en 0. La correcta sale de
  `contenido.opcion_indice` o `contenido.valor`. Mismos colores que las cajas (reusa `opcionesEnVivo`).
- **`lib/ranking-en-vivo.ts`:** `top3(ranking)` — ordena por `posicion` y corta en 3 (compartido con `US-6.3.9`).
- **`StageHistograma`:** barras con ancho proporcional al máximo, la correcta con contorno blanco y `✓`;
  `setTimeout` de `SEGUNDOS_HISTOGRAMA = 6` que llama `onVerRanking` (limpiado al desmontar);
  botón "Ver ranking ahora".
- **`StageRanking`:** Top 3 (nombre + puntaje) o "Nadie participó"; "Siguiente pregunta" solo si
  `indice + 1 < cantidadPreguntas`; "Finalizar sesión" siempre, estilo distinto (outline).
- **`StageFinal`:** podio en orden visual 2°–1°–3° con alturas distintas (solo los puestos que existan),
  "¡Gracias por participar!", "Nadie participó" con 0, enlace discreto "‹ Volver a la Comisión"
  (`/actividad-evaluativa/comisiones/{comisionId}`, H7).
- **Contenedor:** `avanzarPregunta` (espera `pregunta-sola`) y `finalizarSesion` (espera `finalizada`)
  reutilizan `ejecutar` de `US-6.3.6` (una request en vuelo, recálculo a los 2 s, `422` → recalcula).
  Al recalcular con la sesión finalizada, el ranking se pide a `GET .../ranking`.
- **Top 3 en todas las pantallas:** decisión de Víctor (2026-09-21).

## Componentes a Implementar

- [ ] `lib/opciones-en-vivo.ts` — `filasHistograma` (+ tests)
- [ ] `lib/ranking-en-vivo.ts` — `top3` (+ tests)
- [ ] `proyeccion/vista-proyeccion.ts` — etapas `histograma`/`ranking`, `comisionId`, `opcionesTexto` (+ tests ajustados)
- [ ] `proyeccion/StageHistograma.tsx` (+ test, fake timers)
- [ ] `proyeccion/StageRanking.tsx` (+ test)
- [ ] `proyeccion/StageFinal.tsx` (+ test)
- [ ] `ProyeccionSesionEnVivo.tsx` — etapas nuevas, avanzar/finalizar, ranking final al recargar (+ test)
- [ ] Validar los 13 escenarios de `tests/features/inc6/US-6.3.7-histograma-ranking-podio.feature` con Vitest

**Estado:** 0/8 tareas completadas
