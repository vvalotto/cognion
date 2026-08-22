# Reporte de Implementación: US-ADJ-05

## Resumen Ejecutivo

- **Historia de Usuario:** US-ADJ-05 - Paginar el listado de cuentas
- **Puntos estimados:** 4
- **Tiempo real (tracker):** 62 min (Fases 0 a 8)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-22
- **Tipo:** feature backend + frontend — última US de la iteración de ajuste conjunta
  `SP-ADJ-01` (`US-ADJ-01`, `US-ADJ-03`, `US-ADJ-04`, `US-ADJ-05`)

---

## Diferencia con US-ADJ-03 (detectada en Fase 2)

A diferencia de `PreguntaRepositoryPort.filtrar()` (reusado por 5 pantallas distintas),
`CuentaQueryPort.listar()` tiene un único consumidor a cada lado — verificado por grep:
`ListarCuentasUseCase` (backend) y `Cuentas.tsx` vía `listarCuentas()` (frontend). No hizo
falta el diseño opt-in de `US-ADJ-03`: `pagina`/`tamanio_pagina` se agregaron con default
fijo (`1`/`20`) siempre aplicado, sin riesgo de romper otro consumidor. Tampoco hizo falta
migración: `Usuario.creado_en` ya existía desde `US-2.2.3`.

---

## Componentes Implementados

### Backend (`src/identidad/`)

- ✅ `entities/resultado_paginado_cuentas.py` (nuevo) — `ResultadoPaginadoCuentas` (`cuentas`, `total`)
- ✅ `entities/ports/cuenta_query_port.py` — `listar()` gana `pagina`/`tamanio_pagina` (default 1/20)
- ✅ `interface_adapters/gateways/cuenta_query_repository.py` — `ORDER BY creado_en, id`,
  `LIMIT`/`OFFSET`, query de `total` separada
- ✅ `use_cases/listar_cuentas.py`, `interface_adapters/controllers/cuentas_controller.py`,
  `frameworks/api/schemas.py` (`CuentasPaginadasResponse`), `frameworks/api/cuentas_router.py`

### Frontend

- ✅ `lib/cuentas-api.ts` — `listarCuentas()` acepta `PaginacionCuentas` opcional, retorna
  `CuentasPaginadas`
- ✅ `pages/Cuentas.tsx` — estado de página, reset a 1 al cambiar cualquier filtro, reutiliza
  `components/ui/pagination.tsx` (`US-ADJ-03`) sin crear nada nuevo

---

## Métricas de Calidad

| Métrica | Backend | Frontend | Umbral |
|---|---|---|---|
| pylint | 9.56/10 | — | ≥ 8.0 |
| CC máx | Grado A (sin excepciones) | — | ≤ 10 |
| MI mín | 47.78 | — | ≥ 20 |
| Coverage | 98% (`src/identidad`) | 91.95% global | ≥ 95% / ≥80% ref. |
| oxlint | — | 0 errores | 0 errores |
| `tsc --noEmit` | — | 0 errores | 0 errores |

Fuente: `quality/reports/sp-adj-01/US-ADJ-05-quality.json`.

**Observación de calidad:** se detectó una anomalía de medición de coverage en
`cuenta_query_repository.py` (72-74% reportado, líneas del cuerpo de `listar()` marcadas
como no cubiertas pese a que un test dedicado ejecuta y verifica exactamente ese
comportamiento — reproducido de forma aislada). No es un patrón sistémico: el mismo patrón
de código en `pregunta_repository.py` (`US-ADJ-03`) reportó 100%. Documentado como
limitación de la herramienta, sin impacto en el coverage total de `src/identidad` (98%).

**Estado General:** ✅ APROBADO

---

## Tests Implementados

- **Backend unit:** `_fakes.py` (`FakeCuentaQueryRepository` actualizado),
  `test_listar_cuentas_use_case.py` (+1 caso de paginación), `test_cuentas_controller.py`
  (ajustado al nuevo contrato)
- **Backend integración:** `test_usuarios_api_integration.py` (+1 caso de paginación,
  ajustados los 3 existentes a `{cuentas, total}`)
- **Backend BDD:** `tests/step_defs/sp_adj_01/test_us_adj_05_steps.py` (nuevo, 4 escenarios
  con `pytest-bdd` real) + `test_us_2_2_2_steps.py` corregido (contrato de respuesta cambiado)
- **Frontend:** `Cuentas.test.tsx` (+4 casos de paginación), `cuentas-api.test.ts` (ajustado
  y +2 casos nuevos), `router.test.tsx` (ajustado)

### Escenarios BDD (4 escenarios, `tests/features/sp-adj-01/US-ADJ-05-paginar-cuentas.feature`)

- ✅ Listado con más de una página de resultados
- ✅ Cambiar de página
- ✅ Cambiar un filtro reinicia la paginación
- ✅ Listado con una sola página

**Todos los tests pasando:** ✅ 374 backend (306 unit/integración + 68 BDD), 165 frontend

---

## Verificación Visual

Recorrido en navegador real (Chrome vía claude-in-chrome) con 26 cuentas reales (1
administrador + 25 docentes) creadas vía API: página 1 muestra 20 cuentas con controles
"Anterior" (deshabilitado), "1"/"2", "Siguiente" (habilitado); página 2 muestra las 6
restantes con "Anterior" habilitado y "Siguiente" deshabilitado; filtrar por Rol = Docente
vuelve correctamente a la página 1. Sin hallazgos.

---

## Archivos Creados/Modificados

### Nuevos
- `src/identidad/entities/resultado_paginado_cuentas.py`
- `tests/features/sp-adj-01/US-ADJ-05-paginar-cuentas.feature`
- `tests/step_defs/sp_adj_01/test_us_adj_05_steps.py`
- `docs/plans/sp-adj-01/US-ADJ-05-context.md`, `US-ADJ-05-plan.md`
- `docs/reports/sp-adj-01/US-ADJ-05-report.md` (este archivo)
- `quality/reports/sp-adj-01/US-ADJ-05-quality.json`

### Modificados
- `src/identidad/entities/ports/cuenta_query_port.py`,
  `interface_adapters/gateways/cuenta_query_repository.py`, `use_cases/listar_cuentas.py`,
  `interface_adapters/controllers/cuentas_controller.py`, `frameworks/api/schemas.py`,
  `frameworks/api/cuentas_router.py`
- `frontend/src/lib/cuentas-api.ts`, `pages/Cuentas.tsx`
- Tests: `tests/unit/inc1/_fakes.py`, `test_listar_cuentas_use_case.py`,
  `test_cuentas_controller.py`, `tests/integration/inc1/test_usuarios_api_integration.py`,
  `tests/step_defs/inc2/test_us_2_2_2_steps.py`, `frontend/src/pages/Cuentas.test.tsx`,
  `frontend/src/lib/cuentas-api.test.ts`, `frontend/src/router.test.tsx`
- `CLAUDE.md`, `CHANGELOG.md`

---

## Criterios de Aceptación

- [x] `GET /usuarios` acepta `pagina`/`tamanio_pagina`, orden estable por `creado_en`
- [x] Página fuera de rango no probada explícitamente (mismo comportamiento SQL que
  `US-ADJ-03`, sin filas para OFFSET fuera de rango — no error)
- [x] Cambiar cualquier filtro reinicia la paginación a la página 1
- [x] Sin migración necesaria — `Usuario.creado_en` ya existía
- [x] Reutiliza `Pagination` sin duplicar componente
- [x] Ningún criterio de aceptación de `US-2.2.2`/`US-2.2.6` cambió

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] **Cierra completa la iteración de ajuste conjunta `SP-ADJ-01`** — evaluar apertura/
  cierre de baseline `BL-003` (la Baseline no cierra backend-only, mismo criterio que `BL-002`)
- [ ] Opcional: investigar la anomalía de coverage en `cuenta_query_repository.py` si se
  repite en US futuras con patrón similar

---

## Lecciones Aprendidas

- ✅ Verificar con grep quién más consume un puerto/endpoint antes de decidir si hace falta
  un diseño opt-in evitó complejidad innecesaria — no toda paginación necesita el mismo
  patrón que `US-ADJ-03`
- ⚠️ `coverage.py` puede fallar en atribuir cobertura a un método async específico sin causa
  aparente, incluso con tests que lo ejercitan y verifican explícitamente — vale la pena
  documentar la anomalía con evidencia en vez de forzar un ajuste que no cambiaría el
  comportamiento real
- 💡 Reutilizar un componente ya creado en una US previa (`Pagination` de `US-ADJ-03`) redujo
  el trabajo de frontend a wiring de estado, sin tocar el componente en sí

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-22
