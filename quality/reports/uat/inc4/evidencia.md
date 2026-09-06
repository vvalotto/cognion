# Evidencia UAT — Iteración 1 del Incremento 4 "Portal del estudiante y Analytics"

| Campo | Valor |
|-------|-------|
| Diseño | `quality/reports/uat/inc4/design.md` |
| Fecha ejecución | 2026-09-05 |
| Ejecutor | Sesión de Claude Code (Capa 1 + Capa 2) + revisión manual en navegador con Víctor mirando en vivo |

---

## Capa 1 — pytest + Vitest

```
.venv/bin/pytest -q
775 passed, 66 warnings in 229.01s (0:03:49)
```

```
cd frontend && npx vitest run
Test Files  43 passed (43)
     Tests  242 passed (242)
```

Sin regresiones. Los warnings de pytest son los mismos ya documentados en iteraciones
anteriores (`PytestUnknownMarkWarning` de marcadores BDD, `InsecureKeyLengthWarning` de una
clave de test, deprecaciones internas de `pytest-bdd`) — ninguno indica un fallo real.

## Capa 2 — HTTP vía `smoke.sh` extendido

`.claude/skills/run-cognion/smoke.sh` se extendió con el flujo de Analytics
(`US-4.1.1` a `US-4.1.3`), reutilizando la `Evaluacion` `Finalizada` que ya deja sembrada el
flujo de Actividad Evaluativa (2 preguntas V/F, ambas con `respuesta_correcta=false`, el
estudiante contestó `true` a las dos). Corrida completa, todos los pasos en verde:

```
== Flujo de Analytics — desempeño del Estudiante (Incremento 4, Iteración 1, RF-15) ==
== GET /analytics/materias/{materia_id}/mi-desempeno (estudiante, con una Evaluacion finalizada, US-4.1.2) ==
OK (1 evaluación, 0 correctas, 2 incorrectas)
== GET /analytics/materias/{materia_id}/mi-desempeno con rol docente (esperado 403, RBAC) ==
OK (403)
...
== GET /analytics/materias/{materia_id}/mi-desempeno (estudiante2, sin Evaluacion finalizada) ==
OK (lista vacía, resumen en cero)

SMOKE TEST OK — server bajado y datos de prueba limpiados.
```

El resto de la corrida (Identidad, Cuentas, Actividad Evaluativa, Banco de Preguntas, ya
cubiertos en iteraciones anteriores) sigue en verde sin cambios — log completo en
`/tmp/smoke-inc4-iter1.log` (ejecución local, no versionado).

---

## Criterio de aceptación — resultado

- Capa 1 (pytest + Vitest): ✅ en verde, sin regresiones (775 backend / 242 frontend).
- Capa 2 (HTTP vía `smoke.sh` extendido): ✅ los tres casos (detalle + resumen con datos
  reales, rechazo por rol, materia sin evaluaciones) responden con los valores esperados.
- UAT visual en navegador real: ✅ **aceptado con observaciones** — ver
  `quality/reports/uat/inc4/guion-manual-iteracion1.md` §3 (Conclusión). Recorrido completo
  con Víctor mirando el panel del navegador en vivo, 7/7 pasos del checklist + 2
  verificaciones adicionales (pantallas del Docente, detalle por pregunta fuera de alcance
  por diseño), sin hallazgos nuevos sobre `US-4.1.1`-`US-4.1.3`.

**Dos problemas reales encontrados y corregidos durante la preparación de esta UAT** (no son
hallazgos de `US-4.1.x` — ver detalle en `guion-manual-iteracion1.md` §2):
1. 🔴 Los 5 formularios sin `useEffect` propio (`US-ADJ-20`: Login, AltaDocente,
   CambiarPassword, Registro, NuevaMateria) no funcionaban en modo dev — `StrictMode`
   abortaba el `AbortController` creado en el render antes de cualquier submit real. Corregido
   moviendo la creación del controller al `useEffect`.
2. 🟡 `tests/uat/inc4/limpiar_uat.sh` y `tests/uat/inc3/limpiar_uat.sh` dejaban huérfanos los
   eventos de una `Evaluacion` al limpiar corridas anteriores (el `DELETE` no capturaba
   `RespuestaRegistrada`, que no lleva `actividad_id` en el payload). Corregido en ambos
   scripts.

**Conclusión:** cierra completa la Iteración 1 del Incremento 4 (backend + frontend, RF-15).
Siguiente paso: actualizar `docs/traceability/matrix.md` (RF-15 → Implementado) y `CLAUDE.md`,
y arrancar la Iteración 2 (`US-4.2.1` en adelante).
