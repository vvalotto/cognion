# Evidencia UAT — Incremento 4-ADJ "Portal de Entrada y Validación E2E"

| Campo | Valor |
|-------|-------|
| US | `US-ADJ-31` |
| Fecha de ejecución | 2026-09-07 |
| Ejecutor | Sesión de Claude Code, navegador real (Claude Browser) |
| Entorno | Propio — backend `uvicorn` (puerto 8000) + frontend `vite dev` (puerto 5173), PostgreSQL local |
| Diseño | `quality/reports/uat/inc4-adj/design.md` |

---

## 1. Capa 1 — Regresión automatizada

- **Backend:** `892/892` pytest en verde (unitarios + integración + BDD), sin regresiones.
- **Frontend:** `329/329` Vitest en verde tras el fix (ver §3), `tsc -b` sin errores, `oxlint`
  sin errores (solo warnings preexistentes, sin relación con este cambio).

---

## 2. Capa 2 — Guion E2E en navegador real

Ejecutado de punta a punta, empezando desde `/login`, sin URLs tipeadas salvo las 3
excepciones documentadas al pie. Cuenta inicial: bootstrap del primer Administrador
(`scripts/seed_admin.py`, `ADR-016`) — todo lo demás se creó por clic, sin seeds.

| # | Rol | Acción | Resultado |
|---|-----|--------|-----------|
| 1-2 | Administrador | Login, ve su Home (`Comisiones` / `Alta de Docente` / `Cuentas`) | ✅ |
| — | Administrador | Alta de Docente (`docente-uat-adj31@fiuner.edu.ar`) | ✅ |
| — | Docente | Login, crea Materia "Ingeniería de Software (UAT ADJ31)" | ✅ (necesario antes de la Comisión — ver hallazgo de secuencia, §4) |
| — | Docente | Carga 1 pregunta de opción múltiple + 1 V/F | ✅ tras el fix del bug §3 |
| 3-4 | Administrador | Crea Comisión "Lunes y Miércoles 18-20hs" sobre esa Materia, asigna al Docente | ✅ (la UI no refresca sola tras "Asignar" — hallazgo 🟡, ver §4) |
| — | Docente | Crea actividad de período abierto "Parcial UAT ADJ31" (2 preguntas, 1 intento) | ✅ tras el fix del bug §3 |
| 5-7 | Docente | Actividades → Ver Comisiones → detalle → genera link de invitación | ✅ |
| 8 | Estudiante (nuevo) | Se registra con el link — "Cuenta creada", vinculada a la comisión | ✅ |
| 12-13 | Estudiante | Login, ve "1 pendiente", inicia la evaluación | ✅ |
| 14 | Estudiante | Responde pregunta 1 (V/F, correcta), confirma, suspende | ✅ — "Guardamos tus 1 respuestas" |
| 15 | Estudiante | Reanuda — retoma exactamente en pregunta 2 con la respuesta 1 conservada, responde (opción múltiple, correcta), finaliza | ✅ — idempotencia confirmada |
| 16 | Estudiante | Ve la revisión completa — 2/2 correctas | ✅ |
| 17 | Estudiante | Ve su propio desempeño (Analytics) — 100% acierto | ✅ |
| 18 | Docente | Ve el desempeño de ese alumno elegido (Materia → Comisión → Estudiante) — mismo resultado (100%, 2/2) | ✅ |
| 19 | Docente | Ve la tasa de error por tema de la materia — Unidad 1/Arquitectura y Unidad 2/Event Sourcing, 0 incorrectas cada uno | ✅ |

**Conclusión:** 19/19 pasos completados. **0 hallazgos 🔴 Bloqueantes** tras aplicar el fix
de §3. 2 hallazgos 🟡 Observación registrados en §4, ninguno bloqueante para el cierre de
`BL-007`.

---

## 3. Hallazgo 🔴 Bloqueante — resuelto en la misma sesión

**Síntoma:** al hacer clic en "Guardar pregunta" (opción múltiple y V/F) y en "Crear
actividad", el formulario no hacía nada — sin error visible, sin request de red, el botón
parecía no responder.

**Causa raíz:** mismo patrón ya documentado en `CLAUDE.md` (UAT de cierre de la Iteración 1
del Incremento 4) — el `AbortController` del submit se creaba en el render
(`if (!ref.current) ref.current = new AbortController()`), y en modo dev `StrictMode` monta,
desmonta y remonta los efectos; el cleanup del efecto abortaba ese mismo controller sin
crear uno nuevo, dejando la señal abortada para siempre. El catch descarta `AbortError` en
silencio (`if (signal.aborted) return`), así que no había ningún indicio visible del fallo.

Cuando se corrigió este bug para 5 formularios (`US-ADJ-20`, ver nota de la Iteración 1 del
Incremento 4 en `CLAUDE.md`), la corrección no se auditó contra el resto de los formularios
del proyecto que comparten el mismo patrón — quedaron **7 formularios** sin el fix:

- `frontend/src/pages/banco-preguntas/NuevaPreguntaOpcionMultiple.tsx`
- `frontend/src/pages/banco-preguntas/NuevaPreguntaVerdaderoFalso.tsx`
- `frontend/src/pages/banco-preguntas/EditarPregunta.tsx`
- `frontend/src/pages/actividad-evaluativa/NuevaActividad.tsx`
- `frontend/src/pages/actividad-evaluativa/ExtenderPlazo.tsx`
- `frontend/src/pages/actividad-evaluativa/EditarTituloActividad.tsx`
- `frontend/src/pages/cuentas/ResetearPassword.tsx`

Tres de ellos (`NuevaPreguntaOpcionMultiple`, `NuevaPreguntaVerdaderoFalso`,
`NuevaActividad`) bloqueaban directamente este guion E2E.

**Fix aplicado (track informal, frontend puro, mismo criterio que el fix original de
`US-ADJ-20`):** en cada uno de los 7 archivos, el `useEffect` que solo abortaba el
controller del render se reemplazó por el patrón ya validado en `Login.tsx`/`Registro.tsx`/
etc. — crear un controller nuevo dentro del efecto y reasignarlo al ref:

```tsx
useEffect(() => {
  const controller = new AbortController()
  controladorSubmitRef.current = controller
  return () => controller.abort()
}, [])
```

**Verificación post-fix:** los 3 formularios necesarios para el guion se probaron en
navegador real tras el fix (§2) — todos funcionan. `tsc -b` sin errores, `oxlint` sin
errores nuevos, `329/329` Vitest en verde (sin tests nuevos — no se agregó cobertura
específica para este bug de modo dev, mismo criterio que el fix original de `US-ADJ-20`,
que tampoco agregó test unitario porque el bug solo se manifiesta bajo `StrictMode` en modo
desarrollo, no en producción ni en el entorno de test).

---

## 4. Hallazgos 🟡 Observación

1. **UI no refresca sola tras "Asignar" Docente en el detalle de Comisión**
   (`frontend/src/pages/identidad/ComisionDetalle.tsx`): el `POST
   /comisiones/{id}/docentes` responde `200 OK` y el dato se persiste correctamente
   (confirmado recargando la página), pero la sección "Docentes asignados" no se actualiza
   sin un refresh manual. Frontend puro — track informal, no bloquea el guion. Queda
   pendiente para una sesión de ajuste menor, no crítico para `BL-007`.

2. **Orden real de creación distinto al wireframe/diseño original:** el diseño de
   `US-ADJ-31` (`docs/plans/inc4-adj/inc4-adj-candidatas.md`) listaba "Administrador crea
   Comisión" antes de "Docente crea Materia y carga preguntas" — en la práctica, crear una
   Comisión requiere elegir una Materia ya existente (`POST /comisiones` referencia
   `materia_id`, `US-2.1.2`), así que la Materia debe existir primero. No es una
   inconsistencia de producto — el propio wireframe de "Nueva Comisión"
   (`wireframes-portal-entrada.md` §3.2) ya muestra un selector de Materia obligatorio — fue
   simplemente un supuesto de orden incorrecto en el guion original, corregido durante la
   ejecución (ver tabla de §2, que refleja el orden real). No requiere cambio de código.

Ninguno de los dos hallazgos es 🔴 Bloqueante ni impidió completar el guion.

---

## 5. Confirmación

Guion ejecutado íntegramente por la sesión de Claude Code en navegador real, sin
participación de Víctor en el recorrido paso a paso. **Pendiente: confirmación explícita de
Víctor** sobre esta evidencia antes de dar por cerrado el DoD del Incremento 4-ADJ y avanzar
con el cierre de `BL-007` — mismo criterio de "confirmado por Víctor" que toda UAT anterior
del proyecto.
