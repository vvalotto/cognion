# Diseño de Pruebas UAT — Incremento 6 "Sesión en vivo", Iteración 3

| Campo | Valor |
|-------|-------|
| Incremento | 6 |
| Iteración | 3 (frontend del modo en vivo: RF-08, RF-09, RF-10 con pantallas) |
| US cubiertas | US-6.3.0 a US-6.3.9, verificadas por US-6.3.10 |
| Entorno | Propio (máquina de desarrollo, PostgreSQL local, `npm run dev` con `StrictMode`). Staging (Fly.io, WSS real) sigue pendiente (`PROCEDIMIENTO-UAT.md` §4) |
| Fecha diseño | 2026-09-25 |

## Objetivo

Tener evidencia de que el Docente conduce una sesión en vivo completa **desde las pantallas reales** —
proyección y celulares — y de que los casos que Vitest con `WebSocket` y `fetch` falsos no ve (contratos
reales del backend, `StrictMode`, reconexión, recarga, legibilidad a 1920×1080) funcionan en un navegador
real. Hito del Incremento 6: "el docente conduce una sesión en vivo completa en el aula".

## Estrategia — dos tramos (decisión de Víctor, 2026-09-25)

1. **Tramo automático, sin intervención:** circuitos E2E con **Playwright** (`frontend/e2e/`) contra el
   backend y el frontend reales. Cada actor corre en un contexto de navegador aislado, con su propia
   sesión: el Docente en proyección (1920×1080) y cada Estudiante en un celular emulado (375×812,
   táctil). Siembra por API con prefijo único por corrida y limpieza al final (`limpiar_uat.sh`).
   Reemplaza el recorrido manual en navegador de escritorio que pedía la spec.
2. **Tramo de validación de Víctor:** con los circuitos en verde, prueba en persona lo que la emulación no
   puede juzgar: **celular real** (tacto, colores a distancia, red Wi-Fi) y **proyector/monitor**.
   Guion: `quality/reports/uat/inc6/guion-validacion-iteracion3.md`.

Más la regresión (Capa 1): `npm run test:coverage`, `oxlint`, `tsc -b`.

## Circuitos automáticos

| # | Archivo | Circuito | Criterio |
|---|---|---|---|
| 1 | `01-sesion-completa.spec.ts` | Login real por pantalla, entrada por clic desde la Comisión, 3 Estudiantes, 3 preguntas (mostrar → responder → cerrar → histograma → ranking automático a los 6 s → avanzar), final | Cada pantalla pasa sola a la siguiente; podio = acumulados que vio cada Estudiante, en orden; resultado final correcto en cada celular; ≤ 1 socket abierto por pantalla (sin bucle por `StrictMode`); histograma < 1 s desde el cierre |
| 2 | `02-tipos-de-pregunta.spec.ts` | Verdadero/Falso y tres opciones | V/F: 2 cajas (`b`/`c`), 2 tarjetas, respuesta booleana, histograma de 2 barras con la correcta marcada; 3 opciones: la tercera a ancho completo en proyección y celular, histograma de 3 barras |
| 3 | `03-finalizar-antes.spec.ts` | Finalizar en la pregunta 1 de 3 | Podio y resultado final; la sesión deja de figurar como activa para Docente y Estudiante |
| 4 | `04-union-tardia.spec.ts` | Unirse con la pregunta presentada y con las opciones ya a la vista | Tarjeta "En curso"; espera de opciones o tarjetas directo; el conteo suma a los tardíos |
| 5 | `05-bordes-al-responder.spec.ts` | 5 s de límite: doble toque, toque tarde, no responder | Un solo `POST`; "Se acabó el tiempo" (H5); temporizador en 0 no cierra; "No respondiste (+0)" (H4); el celular no revela ranking |
| 6 | `06-reconexion-y-recarga.spec.ts` | Corte del canal del Estudiante mientras se muestran las opciones; corte del Docente al cerrar; F5 en cada etapa de ambos | "Reconectando…" aparece y desaparece; recupera etapa, tiempo y avance sin perder la participación; respaldo de 2 s del cierre; F5 vuelve a la misma etapa con sus datos |
| 7 | `07-pocos-participantes.spec.ts` | Sin participantes y con uno solo | Se conduce igual; "Nadie participó"; ranking y podio de un puesto |
| 8 | `08-legibilidad.spec.ts` | Medición en el navegador de las pantallas `stage-*` y de las tarjetas | Enunciado ≥ 40 px, eyebrow ≥ 18 px, temporizador y opciones ≥ 26 px, texto sobre fondo ≥ 7:1, sin scroll a 1920×1080; tarjetas ≥ 44 px. Contraste de las cajas de color: se mide e informa, sin bloquear |

Los cortes de conexión se simulan con `page.routeWebSocket` (cierre del canal con código 4000 y rechazo
de las reconexiones durante el corte), sin tocar la red del sistema.

## Uso

```bash
cd frontend
npm run test:e2e                                   # los 8 circuitos (levanta backend y frontend si no están)
npx playwright test e2e/06-reconexion-y-recarga.spec.ts   # uno solo
npx playwright show-report ../quality/reports/uat/inc6/playwright-report
E2E_CONSERVAR_DATOS=1 npm run test:e2e             # no limpia los datos sembrados
```

Requiere PostgreSQL local arriba. No usa `pytest` (no vacía la base local).

## Alcance (honestidad del método)

- Celular **emulado** (viewport, táctil, user agent), no un dispositivo real: tacto, legibilidad a distancia y
  red Wi-Fi quedan para el tramo de Víctor.
- Una sola máquina: la carga de 60 concurrentes ya se midió en `US-6.2.9`; acá se verifica la experiencia.
- Staging con WSS real detrás de un proxy sigue pendiente.

## Criterio de aceptación

Los 8 circuitos en verde en 3 corridas seguidas + regresión sin fallos + validación de Víctor sin 🔴
Bloqueantes sin resolver (`PROCEDIMIENTO-UAT.md` §8).
