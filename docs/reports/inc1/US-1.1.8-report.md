# Reporte de Implementación: US-1.1.8

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.8 - Estudiante se registra desde la UI con un link de invitación
- **Puntos estimados:** 3
- **Tiempo real:** ~26 min (fases 0-9, tracking de ejecución del agente, no comparable contra
  esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-07-28

Tercera US de la Iteración 2 (frontend de Identidad). Consume la infraestructura de `US-1.1.6`
con el flujo con más estados del wireframe (registro: formulario + 2 pantallas de destino,
vs. login de una sola pantalla). Cierra `RF-01` en frontend. Incluye una ampliación de backend
acordada con Víctor durante la Fase 2 — el wireframe pedía mostrar el nombre de la comisión,
pero `RegistroResponse` solo exponía `comision_id` (UUID); ver adenda en
`docs/specs/inc1/US-1.1.8.md`.

---

## Componentes Implementados

### Backend — ampliación acordada (fuera del alcance original de la spec)
- ✅ `src/identidad/frameworks/api/schemas.py` (editado) — `RegistroResponse.materia: str`
- ✅ `src/identidad/use_cases/registrar_estudiante.py` (editado) —
  `RegistrarEstudianteUseCase` inyecta `ComisionRepositoryPort` (puerto ya existente) y
  resuelve `materia` vía `obtener_por_id`
- ✅ `src/identidad/interface_adapters/controllers/registro_controller.py` (editado) —
  propaga `materia` sin lógica adicional
- ✅ `src/identidad/frameworks/api/registro_router.py` (editado) — mapea `materia` a la
  respuesta
- ✅ `src/identidad/frameworks/dependencies.py` (editado) — inyecta
  `SQLAlchemyComisionRepository` en `get_registro_controller`

### Pantallas de Registro (`frontend/src/pages/`)
- ✅ `Registro.tsx` (nuevo) — formulario controlado (nombre/email/contraseña/confirmar
  contraseña), lee `token` de query param, valida contraseña en cliente (≥8 caracteres,
  coincidencia), consume `POST /identidad/registro`; 201 → `/registro/exito` (pasa `materia`
  por `location.state`); 422 → `/registro/error`; 409 → error inline en el formulario
- ✅ `RegistroError.tsx` (nuevo) — pantalla completa, mensaje genérico sin distinguir motivo
  del rechazo (§2.4 `wireframes-identidad.md`)
- ✅ `RegistroExito.tsx` (nuevo) — pantalla completa, confirmación con nombre de la comisión
  (con fallback genérico si se accede sin `location.state`); no autentica automáticamente

### Integración
- ✅ `frontend/src/pages/_placeholders.tsx` (editado) — quita `RegistroPlaceholder`
  (reemplazado por la pantalla real)
- ✅ `frontend/src/router.tsx` (editado) — `/registro` deja de ser placeholder; rutas nuevas
  `/registro/error`, `/registro/exito`

---

## Métricas de Calidad

Umbrales adaptados a stack mixto (backend Python + frontend TypeScript/React) — ver
`docs/plans/inc1/US-1.1.8-context.md`.

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| mypy (backend, `src/` completo) | 0 errores (79 archivos) | 0 errores | ✅ |
| CodeGuard (backend) | 0 errores, 1 advertencia (B101, patrón ya aceptado en el proyecto) | 0 errores | ✅ |
| black / isort / ruff (backend) | 0 errores | 0 errores | ✅ |
| pytest unitarios (backend) | 71/71 pasan (suite completa) | 100% pasan | ✅ |
| pytest integración (backend) | 38/38 pasan (suite completa) | 100% pasan | ✅ |
| ESLint/oxlint (frontend) | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` (frontend) | 0 errores | 0 errores | ✅ |
| Vitest (frontend) | 30/30 pasan (suite completa) | 100% pasan | ✅ |
| Cobertura pantallas de registro (statements) | 91.66% | ≥80% (referencia) | ✅ |
| Cobertura pantallas de registro (branches) | 88.88% | ≥80% (referencia) | ✅ |

**Estado General:** ✅ APROBADO (`quality/reports/inc1/US-1.1.8-quality.json`)

---

## Tests Implementados

### Tests Unitarios backend (reparados por cambio de firma, 7 tests)
- `test_registrar_estudiante_use_case.py` (6 tests, editado) — agrega `FakeComisionRepository`
  a cada caso, verifica `materia` en el resultado exitoso
- `test_registro_controller.py` (1 test, editado) — verifica que `materia` se propaga

### Tests de Integración backend (5 tests, editado)
- `test_registro_api_integration.py` — agrega aserción de `materia` en el registro exitoso
  contra Postgres real

### Tests frontend (9 tests nuevos + 1 editado)
- `Registro.test.tsx` (6 tests) — registro exitoso, token vencido/ya usado/inexistente
  (`it.each`), email ya registrado, contraseñas no coincidentes
- `RegistroError.test.tsx` (1 test) — mensaje genérico, sin formulario
- `RegistroExito.test.tsx` (2 tests) — nombre de comisión desde `location.state`, fallback
  genérico sin state
- `router.test.tsx` (editado) — `/registro` renderiza la pantalla real (antes verificaba el
  placeholder)

### Escenarios BDD (5 escenarios) — `tests/features/inc1/US-1.1.8-registro-ui.feature`
- Registro exitoso con invitación vigente
- Rechazado por token vencido
- Rechazado por token ya usado
- Rechazado por token inexistente
- Rechazado por email ya registrado

Sin runner Gherkin dedicado para TypeScript — los 5 escenarios están cubiertos 1:1 por
`Registro.test.tsx` (ver Fase 6).

**Todos los tests pasando:** ✅ 30/30 frontend, 71/71 unitarios backend, 38/38 integración backend

---

## Archivos Creados/Modificados

### Código de producción — backend
- `src/identidad/frameworks/api/schemas.py` (editado)
- `src/identidad/use_cases/registrar_estudiante.py` (editado)
- `src/identidad/interface_adapters/controllers/registro_controller.py` (editado)
- `src/identidad/frameworks/api/registro_router.py` (editado)
- `src/identidad/frameworks/dependencies.py` (editado)

### Código de producción — frontend
- `frontend/src/pages/Registro.tsx` (nuevo)
- `frontend/src/pages/RegistroError.tsx` (nuevo)
- `frontend/src/pages/RegistroExito.tsx` (nuevo)
- `frontend/src/pages/_placeholders.tsx` (editado)
- `frontend/src/router.tsx` (editado)

### Tests
- `tests/unit/inc1/test_registrar_estudiante_use_case.py` (editado)
- `tests/unit/inc1/test_registro_controller.py` (editado)
- `tests/integration/inc1/test_registro_api_integration.py` (editado)
- `frontend/src/pages/Registro.test.tsx` (nuevo)
- `frontend/src/pages/RegistroError.test.tsx` (nuevo)
- `frontend/src/pages/RegistroExito.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (editado)
- `tests/features/inc1/US-1.1.8-registro-ui.feature` (nuevo)

### Documentación
- `docs/specs/inc1/US-1.1.8.md` (editado — adenda de ampliación de backend)
- `docs/plans/inc1/US-1.1.8-context.md` (nuevo)
- `docs/plans/inc1/US-1.1.8-plan.md` (nuevo)
- `docs/reports/inc1/US-1.1.8-report.md` (este archivo)
- `quality/reports/inc1/US-1.1.8-quality.json` (nuevo)
- `CHANGELOG.md` (entrada `[US-1.1.8]`)
- `docs/traceability/matrix.md` (RF-01 → Implementado)
- `docs/plans/inc1/inc1-candidatas.md` (US-1.1.8 tachada como cerrada)

---

## Criterios de Aceptación

- [x] Registro exitoso con invitación vigente crea el Usuario, muestra la pantalla de éxito y
      no autentica automáticamente
- [x] Registro rechazado por token vencido muestra la pantalla de error, sin distinguir motivo
- [x] Registro rechazado por token ya usado muestra la misma pantalla de error
- [x] Registro rechazado por token inexistente muestra la misma pantalla de error
- [x] Registro rechazado por email ya registrado muestra el error en el propio formulario, sin
      navegar a la pantalla de error de token

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-1.1.9` (Administrador da de alta un Docente desde la UI) — última US-IEDD
      pendiente de la Iteración 2
- [ ] Abrir BL-002 una vez cerrada `US-1.1.9` (criterio de cierre de baseline,
      `docs/plans/PLAN-CM.md` §7)

---

## Lecciones Aprendidas

- 💡 El wireframe pedía mostrar el nombre de la comisión, pero el backend solo exponía
  `comision_id` (UUID) — el gap se detectó en Fase 2 (planificación), no en Fase 3
  (implementación), lo que evitó rehacer trabajo. Se consultó con Víctor antes de escribir
  código; decisión: ampliar el backend reutilizando un puerto ya existente
  (`ComisionRepositoryPort.obtener_por_id`), documentado como adenda en la spec.
- ✅ Cambiar la firma de `RegistrarEstudianteUseCase` rompió dos tests unitarios preexistentes
  de `US-1.1.2` — se repararon en la misma Fase 4, evitando arrastrar suite roja entre US.
- 💡 `it.each` en Vitest redujo duplicación para los tres escenarios de token inválido
  (vencido/ya usado/inexistente) que comparten exactamente el mismo tratamiento de UI.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-28
