# Evidencia UAT — Iteración 1 del Incremento 2 "Banco de Preguntas"

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc2/design.md` |
| Fecha ejecución | 2026-08-17 |
| Ejecutor | Sesión de Claude Code, con recorrido en navegador real (Chrome vía claude-in-chrome) |

---

## Capa 1 — pytest + Vitest

```
.venv/bin/pytest -q
270 passed, 31 warnings in 36.37s
```

```
cd frontend && npm test -- --run
Test Files  22 passed (22)
     Tests  103 passed (103)
```

Sin regresiones. Los warnings de pytest son `PytestUnknownMarkWarning` de marcadores BDD
(`filtrar-banco`, `US-2.1.7`, etc.) y un `InsecureKeyLengthWarning` de una clave de test de
19 bytes en `test_jwt_pyjwt.py` — ninguno indica un fallo real.

## Capa 2 — HTTP vía `smoke.sh` extendido

`.claude/skills/run-cognion/smoke.sh` (`.claude/skills/run-cognion/SKILL.md`) se extendió con
el flujo real de Banco de Preguntas. Al ejecutarlo se detectó que el flujo de Identidad estaba
roto desde `US-2.1.2` (2026-08-05): `POST /comisiones` pedía `materia_id` (UUID, resuelto
contra el puerto del BC Banco de Preguntas) en vez del campo `materia` (string) que el driver
todavía mandaba — nadie lo había vuelto a ejercitar de punta a punta desde ese refactor. Se
corrigió reordenando el driver (crear Docente → login Docente → `POST /materias` → `POST
/comisiones` con el `materia_id` resultante) y se documentó el gotcha en
`.claude/skills/run-cognion/SKILL.md`.

Corrida completa, todos los pasos en verde:

```
== Postgres == OK
== Arrancando fake SMTP (puerto 2525) == OK
== Arrancando backend (puerto 8000) == OK
== GET /health == OK (200)
== Bootstrap Administrador (scripts/seed_admin.py, ADR-016) == OK
== POST /identidad/login (administrador) == OK
== POST /usuarios (docente) == OK
== POST /identidad/login (docente) == OK
== POST /materias (docente) == OK
== POST /comisiones == OK
== POST /comisiones/{id}/docentes == OK (200)
== POST /comisiones/{id}/invitaciones (docente) == OK
== POST /identidad/registro con invitación vigente (US-1.1.8) == OK
== POST /identidad/registro con token ya usado (esperado 422) == OK (422)
== POST /usuarios con email duplicado (esperado 409) == OK (409)
== POST /preguntas/opcion-multiple == OK
== POST /preguntas/verdadero-falso == OK
== GET /bancos/{id}/preguntas (sin filtro, deben aparecer ambas) == OK (2 preguntas)
== PUT /preguntas/{id} (editar texto) == OK (texto actualizado)
== DELETE /preguntas/{id} (baja lógica) == OK (204)
== GET /bancos/{id}/preguntas (la eliminada ya no aparece, INV-BP-04) == OK (1 pregunta activa)
== POST /preguntas/opcion-multiple con opciones inválidas (0 correctas) == OK (422)

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

## UAT en navegador real

Se levantó el backend (`uvicorn`, puerto 8000) y el frontend (`npm run dev`, puerto 5173)
persistentes contra Postgres real, se sembró un Administrador y un Docente de prueba
(`uat-inc2-*@fiuner.edu.ar`), y se recorrió el flujo completo en Chrome real (no `fetch`
mockeado) vía `claude-in-chrome`:

1. Login como Docente — OK.
2. Crear materia "Ingeniería de Software" — OK, aparece en el listado con "0 preguntas activas".
3. Cargar pregunta de Opción Múltiple (SOLID/ISP) — OK, aparece en la tabla del banco.
4. Cargar pregunta de Verdadero/Falso (Clean Architecture) — OK, "2 preguntas activas".
5. Filtrar por unidad temática ("Unidad 2") — OK, muestra solo la V/F; "Limpiar filtros"
   restaura ambas.
6. Editar la pregunta de Opción Múltiple (Dificultad Medio → Alto) — OK, formulario
   precargado con los datos existentes, cambio reflejado en la tabla tras guardar.
7. Eliminar la pregunta de Verdadero/Falso — pantalla de confirmación explícita: *"Esta es una
   baja lógica: la pregunta deja de estar disponible para el banco y nuevas sesiones, pero las
   sesiones pasadas que ya la usaron no se ven afectadas."* Tras confirmar, la pregunta
   desaparece de la tabla y el contador baja a "1 pregunta activa".

Sin errores en la consola del navegador ni en el log del backend durante todo el recorrido
(sin gaps de CORS ni de cascada CSS, a diferencia de lo detectado en `US-1.1.9` para BC
Identidad). Único hallazgo, descartado tras verificación: en una ventana angosta (1568px) los
botones "Editar"/"Eliminar" de la tabla del banco quedan fuera del viewport visible — la tabla
tiene scroll horizontal correcto (`overflow-x`) y los botones son completamente accesibles al
desplazar; no es un defecto, es contenido ancho con scroll propio, comportamiento esperado.

**Pendiente:** este recorrido lo hizo la sesión de Claude Code operando el navegador, no
Víctor en persona. Sirve como evidencia funcional adicional (navegador real, no mockeado) pero
no reemplaza la revisión humana de UX que señala este mismo procedimiento en `BL-002`
(hallazgos de diseño que solo un ojo humano detecta). Si Víctor quiere hacer su propia pasada
antes de cerrar la iteración, el entorno queda descrito arriba para levantarlo de nuevo
(`scripts/seed_admin.py` + `npm run dev`).

---

## Criterio de aceptación — resultado

- Capa 1 (pytest + Vitest): ✅ en verde, sin regresiones (270 backend / 103 frontend).
- Capa 2 (HTTP vía `smoke.sh` extendido): ✅ todos los códigos HTTP esperados, sin pérdida de
  datos; se corrigió además un gap preexistente no relacionado con esta US (driver desactualizado
  desde `US-2.1.2`).
- UAT visual en navegador real: ✅ sin hallazgos 🔴 Bloqueantes — recorrido automatizado por la
  sesión, confirmación humana de Víctor pendiente si la quiere agregar antes de cerrar la
  iteración.

**Conclusión:** la Iteración 1 del Incremento 2 (Banco de Preguntas, `US-2.1.1` a `US-2.1.13`)
queda verificada de punta a punta. No cierra BL-003 — eso espera a la Iteración 2 (RF-03).

---

## UAT manual de Víctor en navegador real (2026-08-18) — No conformidades registradas

Pasada humana pendiente al cierre de la sección anterior (ver "Pendiente" arriba). Víctor
recorrió el flujo de Banco de Preguntas en Chrome real contra backend + Postgres locales, con
un usuario Docente sembrado con contraseña conocida, y cargó el contenido real de la materia
"Ingeniería de Software" (70 preguntas de opción múltiple desde
`Preguntas Evaluación Ingeniería de Software.docx`, Módulo 1) para ejercitar el banco con
volumen realista, no solo los 1-2 registros de fixtures previos.

Clasificación de severidad según `docs/plans/PROCEDIMIENTO-UAT.md` §8. Ninguna de las tres es
🔴 Bloqueante — el flujo funcional completo (alta, carga, filtrado, edición, baja) sigue
operando correctamente con 71 preguntas activas en el banco.

| # | No conformidad | Severidad | Track (`PLAN-CM.md` §4) | Resolución |
|---|---|---|---|---|
| NC-1 | El filtro de "Unidad temática"/"Tema" en `Banco.tsx` pedía texto libre, igual que las pantallas de carga/edición antes de `US-ADJ-02` — mismo riesgo de typo fragmentando el filtrado | 🟡 Observación | Informal (solo `frontend/`) | Resuelta en el momento — commit `9f5e00f`, reusa `derivarSugerencias()` sobre el banco actual en un `<datalist>`, mismo patrón de `US-ADJ-02` |
| NC-2 | `Banco.tsx` renderiza la tabla completa sin paginación; con 71 preguntas activas (contenido real cargado en esta UAT) la tabla se vuelve difícil de recorrer — ningún criterio de aceptación de `US-2.1.7`/`US-2.1.10` contempló volumen | 🟡 Observación | Formal (toca `src/`: nueva columna `fecha_creacion`, paginación en el puerto/gateway/endpoint) | Especificada en `docs/specs/ajustes/US-ADJ-03.md` — pendiente de implementación |
| NC-3 | (referencia) `US-ADJ-01` (divergencia visual con el prototipo, `HITO-4`) y `US-ADJ-02` en su alcance original de pantallas de carga/edición (`HITO-5`) siguen especificadas pero no implementadas al momento de esta UAT | — | Formal, ya especificado | Sin cambios — se re-listan aquí solo para que este registro quede completo como snapshot del estado de no conformidades abiertas a 2026-08-18 |

Aprendizaje de escalabilidad (NC-2) documentado en `docs/aprendizajes/HITO-6-BANCO-PREGUNTAS-SIN-PAGINACION-CON-DATOS-REALES.md`.
