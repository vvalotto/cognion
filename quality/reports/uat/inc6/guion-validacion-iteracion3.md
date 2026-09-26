# Guion de validación de Víctor — Incremento 6, Iteración 3 (modo en vivo)

Tramo 2 de `US-6.3.10` (ver `design-iteracion3.md`). Los 8 circuitos automáticos ya comprobaron el flujo
completo en navegador real (`evidencia-iteracion3.md`). Este guion cubre **solo lo que la emulación no puede
juzgar**: un celular real y la proyección en un monitor o proyector. Tiempo estimado: 20-30 minutos.

## 1. Preparar (una vez)

Celular y computadora en la **misma red Wi-Fi**. En la computadora, dos terminales desde la raíz del repo:

```bash
.venv/bin/uvicorn src.app:app --port 8000
```

```bash
cd frontend && VITE_API_BASE_URL=http://192.168.1.63:5173/api npm run dev -- --host
```

(Si la IP cambió: `ipconfig getifaddr en0`. El celular habla solo con Vite, que reenvía al backend — no hace
falta tocar CORS.)

Sembrar datos de prueba sin borrarlos al final (deja una Materia con preguntas de los tres tipos, una
Comisión, un Docente y 6 Estudiantes):

```bash
cd frontend && E2E_CONSERVAR_DATOS=1 npx playwright test e2e/07-pocos-participantes.spec.ts
```

Credenciales en `frontend/e2e/.estado/datos.json` (contraseña de todos: `Password123!UatE2e`).
Al terminar: `tests/uat/inc6/limpiar_uat.sh <prefijo>` (el prefijo está en ese mismo archivo).

## 2. Proyección (computadora conectada al monitor o proyector, pantalla completa)

Entrar como el Docente en `http://localhost:5173`, ir a la Comisión y crear una sesión (tema "Opcion
multiple", 3 preguntas, 30 s).

| # | Qué mirar | ✅ / ❌ | Nota |
|---|---|---|---|
| P1 | Desde el fondo del aula (o a varios metros) se lee el enunciado, "Pregunta N de total" y el temporizador | | |
| P2 | Los cuatro colores de las cajas se distinguen entre sí a distancia, y el texto dentro de cada caja se lee (**en especial azul y verde**, ver hallazgo H3) | | |
| P3 | No aparece scroll en ninguna pantalla (pregunta, opciones, histograma, ranking, podio) | | |
| P4 | El histograma deja claro cuál era la correcta (borde blanco + ✓) | | |
| P5 | El podio se entiende de un vistazo | | |

## 3. Celular real (como un Estudiante, en `http://192.168.1.63:5173`)

| # | Qué hacer / mirar | ✅ / ❌ | Nota |
|---|---|---|---|
| C1 | Iniciar sesión, entrar a la materia: la tarjeta "Sesiones en vivo" aparece sola (hasta 10 s) | | |
| C2 | Unirse: "¡Te uniste!" con el conteo; pasa solo a la pregunta cuando el Docente inicia | | |
| C3 | Las tarjetas se tocan cómodas con el pulgar, sin errar de tarjeta | | |
| C4 | El resultado aparece enseguida al tocar; no se puede tocar dos veces | | |
| C5 | Apagar el Wi-Fi del celular unos segundos con la pregunta abierta y volver a prenderlo: aparece "Reconectando…", vuelve a la pregunta con el tiempo restante y se puede responder | | |
| C6 | Bloquear la pantalla del celular y desbloquearla en medio de la sesión: sigue en la etapa correcta | | |
| C7 | Al final: "Quedaste N° con X puntos" y el Top 3 | | |
| C8 | Desde que el Docente cierra la pregunta, el histograma aparece en la proyección en menos de 1 s (a ojo) | | |

## 4. Plantilla de hallazgos

| Id | Severidad (🔴 / 🟡 / ⚪) | Pantalla | Qué pasó | Qué esperabas |
|---|---|---|---|---|
| | | | | |

Severidades: `docs/plans/PROCEDIMIENTO-UAT.md` §8. Un 🔴 frena el cierre de la iteración.

## 5. Decisiones tomadas (2026-09-26)

- **H3 — contraste de las cajas de opción: opción b.** Azul `#287aaa` y verde `#378257` (≥ 4,5:1, antes 3,57 y
  3,73); rojo y amarillo sin cambios. Mismos colores en las tarjetas del celular. En P2, mirar que se sigan
  distinguiendo los cuatro colores a distancia.
- **H4 — enunciado de 30 px con las opciones a la vista: opción a** (se mantiene). En P1, confirmar a ojo que se
  lee desde el fondo; si no, se sube.
