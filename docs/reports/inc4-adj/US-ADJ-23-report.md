# Reporte de Implementación: US-ADJ-23 - Administrador ve el listado de Comisiones de una Materia

## Información General

| Campo | Valor |
|-------|-------|
| **Historia de Usuario** | US-ADJ-23 |
| **Título** | Administrador ve el listado de Comisiones de una Materia |
| **Producto** | cognion |
| **Prioridad** | Alta — precondición de `US-ADJ-24`/`25`/`26` |
| **Puntos estimados** | 3 |
| **Fecha inicio** | 2026-09-07 |
| **Fecha fin** | 2026-09-07 |
| **Tiempo real** | ~27 min (1596s de tracking, Fases 0-9) |
| **Estado** | ✅ COMPLETADO |

---

## Resumen Ejecutivo

Primera US de la Iteración 1a del Incremento 4-ADJ: cierra la mitad del gap de `RF-01`
detectado en `HITO-9` — el Administrador ahora puede ver el listado de Comisiones de una
Materia (horario, Docentes asignados, cantidad de Estudiantes), precondición para crear
Comisiones y generar invitaciones reales desde la UI. Amplía el guard de rol de 3 endpoints
de consulta que hoy exigían `docente` únicamente, y corrige un gateway que hardcodeaba
`docentes_asignados=[]`. Verificado end-to-end en navegador real contra backend real.

---

## Componentes Implementados

### Código Fuente (Backend)

- ✅ `src/identidad/interface_adapters/gateways/comision_query_repository.py` — carga real de
  `docentes_asignados` vía `selectinload`, en vez de `[]` hardcodeado
- ✅ `src/identidad/frameworks/dependencies.py` — `require_docente_o_administrador` nuevo
- ✅ `src/identidad/frameworks/api/materias_comisiones_router.py` — guard ampliado
- ✅ `src/identidad/frameworks/api/comisiones_router.py` — guard ampliado
- ✅ `src/identidad/frameworks/api/schemas.py` — `ComisionResumenResponse.docentes_asignados`
- ✅ `src/banco_preguntas/frameworks/dependencies.py` — `require_docente_o_administrador`
  propio del BC (gap adicional, ver "Cambios no Previstos")
- ✅ `src/banco_preguntas/frameworks/api/materias_router.py` — guard de `GET /materias`
  ampliado

### Código Fuente (Frontend)

- ✅ `frontend/src/lib/identidad-comisiones-api.ts` (ya existía desde `US-4.2.5`, extendido con `docentesAsignados`) — `listarComisionesPorMateria`,
  `listarEstudiantesDeComision`
- ✅ `frontend/src/pages/identidad/Comisiones.tsx` (nuevo) — pantalla del listado
- ✅ `frontend/src/pages/_placeholders.tsx` — `ComisionPlaceholder` (hasta `US-ADJ-24`/`25`/`26`)
- ✅ `frontend/src/router.tsx` — rutas `/comisiones`, `/comisiones/nueva`, `/comisiones/:id`
- ✅ `frontend/src/components/ui/badge.tsx` — variantes `docente-asignado`/`docente-sin-asignar`

**Total archivos:** 12 (7 backend, 5 frontend)

---

### Tests

#### Tests de Integración
- ✅ `tests/integration/inc4/test_comision_query_repository.py` — 2 tests nuevos
- ✅ `tests/integration/inc4/test_comisiones_query_router.py` — 4 tests nuevos
- ✅ `tests/integration/inc2/test_materias_api_integration.py` — 1 test nuevo, 1 modificado
  (`test_rechazo_con_rol_insuficiente` ya no aplica a Administrador, ahora prueba Estudiante)

**Total tests nuevos:** 7 · **Estado:** 859/859 backend pasando (regresión completa incluida)

#### Escenarios BDD
- ✅ `tests/features/inc4-adj/US-ADJ-23-listado-comisiones.feature` — 8 escenarios
- ✅ `tests/step_defs/inc4-adj/test_us_adj_23_steps.py`

**Estado:** 8/8 pasando

---

## Métricas de Calidad

| Métrica | Valor | Objetivo | Estado |
|---------|-------|----------|--------|
| **Pylint** (archivos tocados) | 10.00/10 | ≥ 8.0 | ✅ |
| **Complejidad Ciclomática** (máx por función) | 3 | ≤ 10 | ✅ |
| **Índice Mantenibilidad** (mín) | 55.67 | > 20 | ✅ |
| **Coverage** (`src/identidad` + `src/banco_preguntas`) | 99.1% | ≥ 95% | ✅ |
| **mypy** (`src/` completo) | 0 errores | 0 errores | ✅ |
| **CodeGuard** (7 archivos modificados) | 5 errors\*, 123 warnings | 0 CRITICAL | ✅ |

\* Los 5 "errors" son timeouts del check Pylint/UnusedImports dentro de CodeGuard
(`software_limpio#70`, ya documentado en `CLAUDE.md`) — pylint directo dio 10.00/10 y mypy 0
errores sobre el mismo código, fuente de verdad local del proyecto.

### Detalle de CodeGuard

| Check | Errors | Warnings | Infos |
|-------|--------|----------|-------|
| Security | 0 | 0 | 7 |
| PEP8 | 0 | 0 | 7 |
| Complexity | 0 | 0 | 7 |
| DeadCode | 0 | 101 | 3 |
| Maintainability | 0 | 0 | 7 |
| Pylint | 3 | 0 | 4 |
| Spelling | 0 | 22 | 1 |
| Types | 0 | 0 | 7 |
| UnusedImports | 2 | 0 | 5 |

Los 101 warnings de `DeadCode` son falsos positivos de análisis por-archivo: marcan como "no
usado" funciones/variables (`require_docente`, `get_materias_controller`, etc.) que sí se
consumen desde otros archivos del mismo módulo (routers, composition root) — CodeGuard no
resuelve imports cross-file en este modo. Fuente:
`quality/reports/inc4-adj/US-ADJ-23-codeguard.json`,
`quality/reports/inc4-adj/US-ADJ-23-quality.json`.

---

## Criterios de Aceptación

- [x] El Administrador puede elegir una Materia y ver sus Comisiones
- [x] La tabla muestra horario, Docentes asignados (o "Sin docente asignado") y cantidad de
      Estudiantes inscriptos
- [x] Botón "+ Nueva Comisión" navega al alta (placeholder hasta `US-ADJ-24`)
- [x] Estado vacío si la Materia no tiene ninguna Comisión
- [x] Docente sigue teniendo acceso a ambos endpoints (regresión verificada)
- [x] Estudiante sigue sin acceso (403, regresión verificada)

**Estado:** 6/6 cumplidos

---

## Arquitectura Implementada

### Patrón Aplicado

Clean Architecture BC-first, sin componentes nuevos de dominio — el cambio vive en
`interface_adapters/gateways` (corrección de una consulta que descartaba un dato ya modelado
en la entidad) y `frameworks` (guard de rol, schema, router). El frontend sigue el mismo
patrón ya establecido (`Materias.tsx`/`Cuentas.tsx`): cliente API tipado + pantalla que lo
consume.

### Flujo de Datos

```
Administrador (browser)
  → GET /materias (banco_preguntas, guard ampliado)
  → GET /materias/{id}/comisiones (identidad, guard ampliado)
      → ComisionesQueryController → SQLAlchemyComisionQueryRepository (selectinload docentes)
  → GET /comisiones/{id}/estudiantes ×N (identidad, guard ampliado)
  → GET /usuarios?rol=docente (identidad, US-2.2.2, sin cambios) — resuelve nombres
```

---

## Cambios no Previstos

- **Gap adicional detectado en Fase 3** (verificación manual en navegador real contra backend
  real): `GET /materias` (Banco de Preguntas) también exigía rol `docente` únicamente y
  bloqueaba el propio selector de Materia de esta pantalla — no estaba cubierto en el plan
  original porque no se había verificado ese endpoint específico al planificar. Corregido con
  el mismo patrón (`require_docente_o_administrador` propio del BC Banco de Preguntas, ya que
  cada BC arma su propio composition root — no se comparte la dependency entre BCs).
- **Error propio detectado y corregido antes del PR**: `frontend/src/lib/identidad-comisiones-api.ts`
  ya existía (creado en `US-4.2.5`, consumido por `DesempenoPorAlumno.tsx`/`DesempenoPorTema.tsx`)
  — se sobreescribió sin detectarlo, renombrando `ComisionResumenResponse`/
  `EstudianteResumenResponse` a nombres nuevos. `tsc --noEmit` (sin `-b`) no lo detectó porque
  el `tsconfig.json` raíz tiene `files: []` con `references` a `tsconfig.app.json`/
  `tsconfig.node.json` — no chequea nada por sí solo sin `-b`. El comando real del proyecto es
  `tsc -b` (`package.json` → `"build": "tsc -b && vite build"`), que sí lo detectó (`TS2305`)
  al re-verificar antes de abrir el PR. Corregido manteniendo los nombres originales y
  agregando `docentesAsignados` como campo nuevo (no un archivo nuevo) — 261/261 tests
  frontend y 867/867 backend confirmados después del fix.

---

## Testing Manual Realizado

### Caso 1: Flujo completo end-to-end en navegador real

- **Pasos:** login como Administrador real (backend + Postgres local) → navegar a
  `/comisiones` → seleccionar Materia sembrada con una Comisión con Docente asignado
- **Resultado esperado:** tabla con horario, badge verde del Docente, conteo de Estudiantes
- **Resultado real:** exactamente eso — verificado por screenshot, sin errores en consola
  (el único 403 en el log de consola correspondía al intento previo al fix de `GET /materias`)
- **Estado:** ✅ PASS

Datos de prueba limpiados de Postgres al finalizar (mismo criterio que `smoke.sh`).

---

## Deuda Técnica

- Ninguna introducida por esta US. El backlog de `DesignReviewer`/`ArchitectAnalyst` a nivel
  de incremento se evalúa al cierre de `BL-007` (Incremento 4-ADJ), no por US.

---

## Próximos Pasos

### Historias Relacionadas

- [ ] `US-ADJ-24` — Administrador crea una Comisión
- [ ] `US-ADJ-25` — Administrador asigna un Docente a una Comisión
- [ ] `US-ADJ-26` — Docente genera el link de invitación de una Comisión

---

## Tiempo Invertido

| Fase | Tiempo Real |
|------|-------------|
| Validación de Contexto | 61s |
| Generación BDD | 42s |
| Plan | 42s |
| Implementación | 425s |
| Tests Unitarios | 4s (sin componentes nuevos de dominio) |
| Tests de Integración | 342s |
| Validación BDD | 47s |
| Quality Gates | 480s |
| Documentación | 32s |
| **TOTAL** | **1596s (~27 min)** |

Sin estimación previa por fase — `US-ADJ` no sigue el desglose de estimación humana de
`PRIN-001` (`WORKFLOW-DESARROLLO.md`).

---

## Lecciones Aprendidas

### Lo que Funcionó Bien

1. Reutilizar `listarMaterias()`/`listarCuentas({rol:"docente"})` ya existentes evitó
   duplicar clientes API — el único archivo de frontend genuinamente nuevo fue el propio de
   Comisiones.
2. Verificar en navegador real contra backend real (en vez de confiar solo en tests
   automatizados) detectó el gap de `GET /materias` que ningún test ni el plan original había
   anticipado.

### Recomendaciones para Próximas Historias

1. Al planificar una US que agrega un rol nuevo a un endpoint existente, revisar **todos** los
   endpoints que esa misma pantalla necesita consumir (no solo los explícitamente mencionados
   en la spec) — el gap de `GET /materias` estaba a un `grep` de distancia si se hubiera
   verificado en Fase 2.
2. Antes de crear un cliente API de frontend nuevo, `grep -rn` el nombre de archivo propuesto
   (y los nombres de función que va a exportar) contra `frontend/src/lib/` — este proyecto ya
   tenía `identidad-comisiones-api.ts` con las mismas dos funciones desde `US-4.2.5`, y el
   plan de Fase 2 lo marcó como "nuevo" sin verificarlo primero.
3. `tsc --noEmit` sin `-p`/`-b` explícito no es una verificación confiable en este proyecto —
   el `tsconfig.json` raíz no tiene archivos propios (`files: []`, solo `references`). Usar
   siempre `tsc -b` (el comando real de `npm run build`) para el chequeo de tipos de cierre de
   una US.

---

## Aprobación

Aprobado por Víctor — Fase 8 (documentación) confirmada 2026-09-07.
