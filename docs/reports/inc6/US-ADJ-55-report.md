# Reporte de Implementación: US-ADJ-55

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-55 — Espera máxima de Testing Library acorde a la suite completa (Issue #437)
- **Puntos estimados:** 1
- **Tiempo real:** ver `.claude/tracking/US-ADJ-55-tracking.json`
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-09-24
- **Origen:** Fase 7 de `US-6.3.8` — `AutoregistroEstudiante` falló con `findByRole` bien escrito: se agotó el
  `asyncUtilTimeout` de 1 s bajo la carga de la propia suite.

## Cambio

`frontend/src/test/setup.ts`: `configure({ asyncUtilTimeout: 5000 })` con el motivo en un comentario. Mención en la
sección Frontend de `phase-7-quality-gates.md`. **Ningún componente ni test individual modificado.**

## Medición

Envoltorio temporal de `asyncWrapper` (no commiteado) que registró la duración de cada llamada en 2 corridas completas
de `npm run test:coverage`, clasificada por stack.

| Esperas (`findBy*`/`waitFor`) | Corrida 1 | Corrida 2 |
|---|---|---|
| Cantidad | 646 | 646 |
| p50 / p95 | 47 / 699 ms | 52 / 665 ms |
| p99 | 1865 ms | 1922 ms |
| Máximo | 3984 ms | 2400 ms |
| ≥ 1 s | 21 | 18 |

- **Primera medición descartada:** `user-event` también pasa por `asyncWrapper`; sin clasificar, cada `user.type`/
  `user.click` contaba como espera (llegó a mostrar 130 llamadas ≥ 1 s).
- Los números están inflados por la propia medición (load 87-99 vs. ~35 normal): cota de orden de magnitud.
- **5000 ms** cubre el máximo con margen y queda lejos del `testTimeout` de 20 s (`US-ADJ-53`).

Datos crudos: `quality/reports/inc6/US-ADJ-55-mediciones.txt`.

## Verificación

3 × `npm run test` (115 / 104 / 109 s) y 3 × `npm run test:coverage` (120 / 118 / 120 s) seguidas: 671/671 en las 6.
Cobertura 92,36% / 83,35%. `tsc -b` y `oxlint` 0 errores. Evidencia: `quality/reports/inc6/US-ADJ-55-verificacion.txt`.

## Criterios de Aceptación

✅ configuración única y documentada · ✅ valor fijado con medición registrada · ✅ 6 corridas seguidas en verde ·
✅ sin cambios de componentes ni tests.

## Lecciones Aprendidas

- Las tres causas de fallos aleatorios de la suite eran distintas y cada una necesitó su ajuste: timeout por test
  (`US-ADJ-53`), esperas incompletas en los tests (`US-ADJ-54`) y la espera máxima de Testing Library (esta US).
- Al instrumentar `asyncWrapper`, clasificar el origen: no todo lo que pasa por ahí es una espera.
