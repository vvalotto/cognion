# Guión — Revisión manual de Víctor (Iteración 1, Incremento 4)

| Campo | Valor |
|---|---|
| Script de siembra | `tests/uat/inc4/guion_manual_iteracion1.sh` |
| Diseño UAT | `quality/reports/uat/inc4/design.md` |
| Evidencia Capa 1/2 | `quality/reports/uat/inc4/evidencia.md` |
| US cubiertas | `US-4.1.1` a `US-4.1.3` (RF-15: Estudiante ve su desempeño) |
| Ejecutor | Víctor Valotto (recorrido navegado por la sesión de Claude Code, con Víctor mirando el panel del navegador en vivo) |
| Fecha | 2026-09-05 |

---

## 0. Antes de empezar

1. Corré el script de siembra desde la raíz del repo:
   ```bash
   tests/uat/inc4/guion_manual_iteracion1.sh
   ```
2. Si el frontend no está levantado, en otra terminal:
   ```bash
   cd frontend && npm run dev
   ```
3. El script imprime al final las credenciales y los ids de esta corrida — completá acá los
   datos reales (van a ser distintos en cada corrida):

| Dato | Valor |
|---|---|
| Frontend | `http://localhost:5173` |
| Estudiante 1 (Juan Pérez) — con desempeño | `_______________________` / `_______________________` |
| Estudiante 2 (Ana López) — sin evaluaciones | `_______________________` / `_______________________` |
| Materia 1 (con desempeño) | `_______________________` |
| Materia 2 (sin evaluaciones) | `_______________________` |

**Nota de alcance:** el dominio actual liga a un Estudiante con una única comisión/materia
(`estudiante.comision_id`, sin muchos-a-muchos) — no hay forma de que un mismo alumno tenga
más de una materia todavía. Por eso el selector de materia de "Mi desempeño" (visible recién
con 2+ materias del mismo estudiante) no se puede ejercitar en esta UAT — el caso "materia sin
evaluaciones" se prueba con una segunda cuenta, no cambiando de materia dentro de la misma
sesión. Esto no es un hallazgo — es una limitación conocida del modelo, fuera del alcance de
`US-4.1.1`-`US-4.1.3`.

**Resultado sembrado en Materia 1 (Estudiante 1)** (fijo, no depende del sorteo — el banco
tiene exactamente 4 preguntas y cada actividad pide las 4):

| | Parcial 1 | Parcial 2 | Acumulado |
|---|---|---|---|
| Correctas | 2 | 2 | 4 |
| Incorrectas | 2 | 2 | 4 |
| Total preguntas | 4 | 4 | 8 |
| % acierto | 50% | 50% | 50% |

---

## 1. Checklist — recorrido en el navegador

Marcá cada paso a medida que lo verificás. Si algo no se comporta como se describe, no lo
corrijas ahora: anotalo en la sección **Hallazgos** (§2) y seguí con el resto del checklist.

- [x] **1.** Login como Estudiante 1 (Juan Pérez).
- [x] **2.** Ir a "Mi desempeño" (`/analytics/mi-desempeno`) — accesible sin pasar por
      `RequireRole` de otro rol (solo Estudiante). Al tener una sola materia, **no** debe
      mostrarse ningún selector — eso es correcto, no un bug (ver nota de alcance arriba).
- [x] **3.** El resumen acumulado muestra **4 correctas / 4 incorrectas / 8 total / 50% de
      acierto / 2 evaluaciones**.
- [x] **4.** El detalle por evaluación lista **2 filas** (Parcial 1 y Parcial 2), cada una con
      **2 correctas / 2 incorrectas**.
- [x] **5.** Recargar la página (F5) → el resumen/detalle se recalculan igual, sin quedar en
      blanco ni con un error.
- [x] **6.** Cerrar sesión, login como Estudiante 2 (Ana López) → ir a "Mi desempeño" → **sin
      evaluaciones finalizadas**, mensaje de estado vacío, sin resumen ni lista (no debe
      quedar pegado mostrando los datos del Estudiante 1).
- [x] **7.** Login como Docente o Administrador y navegar directo a `/analytics/mi-desempeno`
      por URL → debe rechazar el acceso (guard de rol), no mostrar la pantalla del Estudiante.
- [x] **8. (adicional)** Docente: "Mis materias" (`/materias`) y el detalle de una actividad
      (`/actividad-evaluativa/...`) siguen coherentes con los datos sembrados — 1
      finalizada/0 activas reflejado en el detalle de cada Parcial.
- [x] **9. (adicional)** El detalle pregunta por pregunta de una evaluación puntual **no**
      está en "Mi desempeño" — vive en la pantalla de revisión ya existente de Actividad
      Evaluativa (`/mis-actividades/evaluaciones/:id/revision`, `US-3.2.3`/`US-3.4.7`), tal
      como especifica `wireframes-analytics.md` §2.0 ("Fuera de alcance ... Analytics no la
      duplica"). Confirmado por Víctor: no es un hallazgo.

---

## 2. Hallazgos

Clasificación de severidad según `docs/plans/PROCEDIMIENTO-UAT.md` §8:
🔴 Bloqueante · 🟡 Observación · ⚪ Estético.

_Completar uno por hallazgo, o "Ninguno" si el recorrido fue limpio._

| # Paso | Severidad | Descripción |
|---|---|---|
| 1 (previo al checklist) | 🔴 Bloqueante | Ningún formulario de submit-sin-`useEffect` propio (Login, AltaDocente, CambiarPassword, Registro, NuevaMateria — introducidos por `US-ADJ-20`) funcionaba en modo dev: el `AbortController` se creaba en el render en vez de en el `useEffect`, y el doble montaje de `StrictMode` lo abortaba antes de cualquier submit real — el botón "Ingresar"/"Guardar" no hacía nada, sin error visible, porque el catch descartaba el `AbortError` en silencio. **Corregido en la misma sesión**, track informal (solo `frontend/`): el controller ahora se crea dentro del `useEffect`, no en el render. Vitest 242/242 (con un flaky reconfirmado, no relacionado) tras el fix. |
| 2 (previo al checklist) | 🟡 Observación | `tests/uat/inc4/limpiar_uat.sh` (y el mismo patrón preexistente en `tests/uat/inc3/limpiar_uat.sh`) dejaba huérfanos los eventos `RespuestaRegistrada`/`Suspendida`/etc. de una `Evaluacion` al limpiar una corrida anterior, porque el `DELETE` filtraba por `payload->>'actividad_id'` fila a fila y esos eventos no llevan ese campo — solo `EvaluacionIniciada` lo tiene. Eso rompía cualquier consulta que agrupa eventos por `aggregate_id` asumiendo que el primero es `EvaluacionIniciada` (`_contar_evaluaciones`, `VerificarVencimientosUseCase`), con un `KeyError` reportado por el navegador como falso error de CORS. **Corregido en ambos scripts** — ahora borra todos los eventos del stream completo, no fila por fila. |
| 3 | — | No es un hallazgo — confirmado con Víctor: el detalle pregunta por pregunta no está en "Mi desempeño" por diseño (ver checklist, paso 9). |

---

## 3. Conclusión

**Aceptado con observaciones** (2026-09-05). El recorrido completo del checklist (7 pasos
previstos + 2 verificaciones adicionales) pasó sin hallazgos nuevos sobre `US-4.1.1` a
`US-4.1.3`. Los dos problemas reales encontrados durante la preparación de esta UAT (bug de
`AbortController` en 5 formularios de `US-ADJ-20`, y bug de limpieza de eventos en los
scripts de UAT) se corrigieron en la misma sesión, antes de dar el checklist por aprobado —
ninguno de los dos toca `US-4.1.x` ni RF-15. Sin US-ADJ nuevas: el primero es un fix directo
(no amerita spec propia, mismo criterio que otros fixes de UAT ya documentados en `CLAUDE.md`),
el segundo es tooling de test, no código de producción.

Cierra completa la Iteración 1 del Incremento 4 (backend + frontend). Siguiente paso:
actualizar `docs/traceability/matrix.md` (RF-15 → Implementado), `CLAUDE.md` (cierre de la
Iteración 1) y arrancar la Iteración 2 (`US-4.2.1` en adelante, `docs/plans/inc4/inc4-candidatas.md`).
