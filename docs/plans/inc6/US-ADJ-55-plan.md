# Plan de Implementación: US-ADJ-55 - Espera máxima de Testing Library acorde a la suite completa

**Estado:** APROBADO por Víctor 2026-09-24 (valor 5000 ms).

## Mediciones (2026-09-24, `npm run test:coverage`, 2 corridas completas)

Envoltorio temporal de `asyncWrapper` que registra la duración de cada llamada, clasificada por su stack
(`espera` = `findBy*`/`waitFor`; `user` = `user-event`). `asyncUtilTimeout` en 10 s durante la medición.
Datos crudos: `quality/reports/inc6/US-ADJ-55-mediciones.txt`.

| Esperas (`findBy*`/`waitFor`) | Corrida 1 | Corrida 2 |
|---|---|---|
| Cantidad | 646 | 646 |
| p50 | 47 ms | 52 ms |
| p95 | 699 ms | 665 ms |
| p99 | 1865 ms | 1922 ms |
| Máximo | 3984 ms | 2400 ms |
| ≥ 1 s | 21 | 18 |

- La cola lenta varía de test entre corridas: es carga, no un test puntual.
- Los números están **inflados**: la medición agrega carga (escritura a disco y captura de stack por llamada) y el load
  llegó a 87-99, contra ~35 en una corrida normal. Sirven como cota del orden de magnitud.
- **Primera medición descartada:** sin clasificar, `user.type`/`user.click` (que también pasan por `asyncWrapper`)
  contaban como esperas.

## Decisión

- `configure({ asyncUtilTimeout: 5000 })` en `frontend/src/test/setup.ts`: cubre el máximo observado (4 s) con margen y
  queda lejos del `testTimeout` de 20 s (`US-ADJ-53`). Costo: un `findBy` sobre algo que nunca aparece falla a los 5 s en
  vez de 1 s (solo afecta a tests ya rotos).
- Mención en la sección Frontend de `.claude/skills/implement-us/phases/phase-7-quality-gates.md`.

## Tareas

- [ ] `frontend/src/test/setup.ts` — `asyncUtilTimeout: 5000` con comentario
- [ ] `phase-7-quality-gates.md` — mención
- [ ] Verificación: `npm run test:coverage` × 3 y `npm run test` × 3 seguidas, en verde; diff sin componentes ni tests
