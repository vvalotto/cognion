# Guión — Revisión manual de Víctor (Iteración 4, Incremento 3)

| Campo | Valor |
|---|---|
| Script de siembra | `tests/uat/inc3/guion_manual_iteracion4.sh` |
| Diseño UAT | `quality/reports/uat/inc3/design-iter4.md` |
| Evidencia de la sesión | `quality/reports/uat/inc3/evidencia-iter4.md` |
| US cubiertas | `US-3.4.1` a `US-3.4.10`, `US-ADJ-09`/`10`/`11` |
| Ejecutor | Víctor Valotto |
| Fecha | _completar al ejecutar_ |

---

## 0. Antes de empezar

1. Corré el script de siembra desde la raíz del repo:
   ```bash
   tests/uat/inc3/guion_manual_iteracion4.sh
   ```
2. Si el frontend no está levantado, en otra terminal:
   ```bash
   cd frontend && npm run dev
   ```
3. El script imprime al final las credenciales y el `actividad_id` de esta corrida — completá
   acá los datos reales (van a ser distintos en cada corrida):

| Dato | Valor |
|---|---|
| Frontend | `http://localhost:5173` |
| Docente (María González) | `_______________________` / `_______________________` |
| Estudiante (Juan Pérez) | `_______________________` / `_______________________` |
| Materia | `_______________________` |
| Actividad | "Parcial 1 — Unidades 1 a 3" |

---

## 1. Checklist — recorrido en el navegador

Marcá cada paso a medida que lo verificás. Si algo no se comporta como se describe, no lo
corrijas ahora: anotalo en la sección **Hallazgos** (§2) y seguí con el resto del checklist.

### Lado Docente

- [ ] **1.** Login como Docente.
- [ ] **2.** Mis materias → entrar a la materia sembrada → el banco muestra 4 preguntas
      (3 V/F + 1 opción múltiple).
- [ ] **3.** Mis actividades → "Parcial 1 — Unidades 1 a 3" aparece en el listado con badge
      **"En curso"**.
- [ ] **4.** Entrar al detalle de la actividad → **"Extender plazo"** → elegir una fecha de
      cierre posterior a la actual → confirmar → el detalle refleja el nuevo plazo de
      inmediato.
- [ ] **5.** Dejar esta pestaña abierta en el detalle de la actividad (se vuelve a usar en el
      paso 14, **después** de que el Estudiante finalice).

### Lado Estudiante

_Abrir una ventana/pestaña de incógnito, o cerrar la sesión del Docente antes de este bloque._

- [ ] **6.** Login como Estudiante.
- [ ] **7.** Mis materias ("1 pendiente") → Mis actividades → badge **"Pendiente de
      responder"**, con el plazo ya extendido en el paso 4.
- [ ] **8.** "Rendir" → responder la primera pregunta → avanza a la 2/2.
- [ ] **9.** ⚠ **Caso clave — recargar la página (F5)** en medio de la evaluación (simula una
      desconexión). Al volver a cargar debe reaparecer:
      - la **misma** pregunta pendiente,
      - con la respuesta previa **ya marcada**,
      - el **mismo set** de preguntas (no debe sortear de nuevo ni perder lo respondido).
      — INV-AE-05/06
- [ ] **10.** "Pausar y salir" → pantalla de evaluación suspendida ("Guardamos tus N
      respuestas") → "Continuar" → retoma exactamente en el mismo punto.
- [ ] **11.** Responder la última pregunta → **"Confirmar y finalizar"** → navega a la
      revisión.
- [ ] **12.** Revisión: verificar el resumen (Correctas/Incorrectas/Total), el texto de la
      propia respuesta y — en las incorrectas — la respuesta correcta.
      _(Si las preguntas aparecen numeradas "0." / "1." en vez de "1." / "2.", es el hallazgo
      ⚪ estético ya conocido — no hace falta volver a reportarlo.)_
- [ ] **13.** Volver al listado de actividades → la tarjeta debe decir **"Finalizada — ver
      revisión"** y llevar directo a la revisión, sin volver a pasar por "Rendir".

### Cierre

_Volver a la pestaña del Docente del paso 5._

- [ ] **14.** **"Cerrar actividad"** (manual) → confirmar → el badge pasa a **"Cerrada"**.
- [ ] **15.** (Opcional) Intentar entrar de nuevo a "Rendir" sobre la actividad ya cerrada
      (con el mismo Estudiante ya finalizado, o uno nuevo) → debe rechazarlo con un mensaje
      claro, no con una pantalla rota o colgada en blanco.

---

## 2. Hallazgos

Clasificación de severidad según `docs/plans/PROCEDIMIENTO-UAT.md` §8:
🔴 Bloqueante · 🟡 Observación · ⚪ Estético.

_Completar uno por hallazgo, o "Ninguno" si el recorrido fue limpio._

| # Paso | Severidad | Descripción |
|---|---|---|
| 8-9 | 🔴 Bloqueante | Estudiante responde Q1 y confirma, avanza a Q2, la selecciona **sin confirmar**, vuelve a Q1 con "Anterior": (a) la pantalla no muestra la respuesta que había confirmado en Q1; (b) al reintentar confirmar Q1 (ya respondida, 1 intento permitido), el backend devuelve 422 `IntentosAgotados` correctamente, pero el frontend corta ahí y **nunca avanza el índice** — queda sin poder seguir. **Corregido** — `US-ADJ-12`, Issue [#199](https://github.com/vvalotto/cognion/issues/199): `EvaluacionResponse` ahora expone `respuestas_confirmadas` (contenido de la respuesta vigente por pregunta, sin `es_correcta`); `RendirEvaluacion.tsx` prellena la selección en modo solo lectura al revisitar una pregunta ya respondida y el botón navega (o finaliza) sin reintentar `registrarRespuesta`. 739/739 tests backend, 229/229 frontend, mypy limpio, DesignReviewer 0 CRITICAL. |

---

## 3. Conclusión

_Completar al terminar: aceptado / aceptado con observaciones / rechazado, y si corresponde
abrir un track formal (US-ADJ) para algún hallazgo._
