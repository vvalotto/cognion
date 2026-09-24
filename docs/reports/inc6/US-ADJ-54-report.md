# Reporte de Implementación: US-ADJ-54

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-54 — Esperas asincrónicas correctas en los tests del frontend (Issue #433)
- **Puntos estimados:** 3
- **Tiempo real:** ver `.claude/tracking/US-ADJ-54-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-24
- **Origen:** Fase 7 de `US-6.3.7` — tests que fallaban al azar al verificar un valor que llega después del elemento.

---

## Barrido

Dos patrones de texto sobre `frontend/src/**/*.test.tsx` + revisión de cada componente (¿el elemento esperado puede
existir antes que el dato verificado?). Detalle y motivo de cada descarte en `docs/plans/inc6/US-ADJ-54-plan.md`.

| | Casos | Corregidos | Descartados |
|---|---|---|---|
| A — `expect(await findBy…).toHave…` | 32 | 4 | 28 (alertas: aparecen ya con su texto) |
| B — `await findBy…` + `expect` sincrónico sin nuevo `await` | 16 | 2 | 14 (mismo render o mismo pedido) |
| **Total** | **48** | **6** | **42** |

## Tests corregidos

| Test | Carrera |
|---|---|
| `cuentas/EditarCuenta.test.tsx` | Formulario dibujado vacío antes de que llegue la cuenta |
| `banco-preguntas/EditarMateria.test.tsx` | Igual, con la materia |
| `identidad/EditarComision.test.tsx` | Igual, con la comisión |
| `actividad-evaluativa/MateriasActividades.test.tsx` | Fila con `…`, conteos en otro pedido |
| `actividad-evaluativa/ComisionesDeMateria.test.tsx` | Igual, resumen por comisión en pedidos aparte (dos filas) |
| `actividad-evaluativa/RendirEvaluacion.test.tsx` | "Finalizar evaluación" existe deshabilitado antes de habilitarse |

Corrección: `await waitFor(() => expect(<elemento>).<matcher>(<dato>))` con un comentario que explica la espera.
**Ningún archivo de producción modificado.**

## Verificación

| Comando | Corridas | Resultado |
|---|---|---|
| `npm run test` | 3 (127 / 106 / 141 s) | 639/639 en las 3 |
| `npm run test:coverage` | 3 (129 / 126 / 162 s) | 639/639 en las 3 — cobertura 92,32% / 83,03% |

`tsc -b` y `oxlint` 0 errores. Evidencia: `quality/reports/inc6/US-ADJ-54-verificacion.txt`.

## Criterios de Aceptación

✅ los casos confirmados esperan el dato (y 3 más que encontró el barrido) · ✅ barrido documentado · ✅ 6 corridas
seguidas en verde · ✅ solo cambian archivos de test.

## Limitaciones

El barrido es heurístico: no garantiza que no existan carreras con otra forma (por ejemplo, `getBy` sin ningún `findBy`
previo). Si vuelve a aparecer un fallo aleatorio, revisar primero ese caso con el mismo criterio.

## Fuera de alcance (sin cambios)

- "Cargando…" en `EditarCuenta`/`EditarMateria`/`EditarComision` mientras llega el dato (decisión de UX).
- `cleanup` automático global en `src/test/setup.ts`: el barrido no mostró que hiciera falta.

## Lecciones Aprendidas

- `findBy*` espera a que el elemento **exista**, no a que tenga el valor: si el componente lo dibuja antes del dato,
  la verificación va en `waitFor`.
- Un componente que dibuja la tabla con `…` o el formulario vacío mientras carga es la señal para esperar el dato en el test.
