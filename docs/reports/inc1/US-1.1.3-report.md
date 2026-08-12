# Reporte de Implementación: US-1.1.3

## Resumen Ejecutivo

- **Historia de Usuario:** US-1.1.3 - Estudiante intenta registrarse con link vencido o inválido
- **Puntos estimados:** 3
- **Tiempo real:** ~13 min (fases 0-9, tracking de ejecución del agente, no comparable
  contra esfuerzo humano — nota PRIN-001 del skill `implement-us`)
- **Estado:** ✅ COMPLETADO (backend) — frontend diferido a la misma US-IEDD que ya diferían
  `US-1.1.2`
- **Fecha completado:** 2026-07-23

Cuarta US de la Iteración 1 (BC Identidad). Refina el camino de rechazo del mismo comando
`RegistrarEstudiante` que implementó `US-1.1.2`: el guard genérico `InvitacionNoValida` pasa
a tres excepciones específicas (`InvitacionInvalida`, `InvitacionVencida`, `InvitacionYaUsada`)
según el motivo del rechazo, sin cambiar el status HTTP ni el mensaje visible al Estudiante
(`ADR-012` — sin recuperación automática). Con esta US, RF-01 completa las tres US-IEDD que
requería y pasa a "Implementado" en `docs/traceability/matrix.md`.

---

## Componentes Implementados

### Entities (`src/identidad/entities/`)
- ✅ `errors.py` (editado) — `InvitacionNoValida` reemplazada por `InvitacionInvalida` (token
  inexistente), `InvitacionVencida` (`expira_en` pasado), `InvitacionYaUsada` (`usada_en` no
  null)
- ✅ `invitacion.py` (editado) — nuevo `verificar_vigente(ahora)`, distingue `InvitacionYaUsada`
  de `InvitacionVencida` (INV-ID-01, INV-ID-03); `aceptar()` lo reutiliza en vez de duplicar
  la lógica

### Use Cases (`src/identidad/use_cases/`)
- ✅ `registrar_estudiante.py` (editado) — `_buscar_invitacion_vigente` lanza
  `InvitacionInvalida` si el token no existe; delega en `invitacion.verificar_vigente()` para
  distinguir vencida/usada

### Interface Adapters
- ✅ `interface_adapters/controllers/registro_controller.py` — **sin cambios**, verificado

### Frameworks (`src/identidad/frameworks/`)
- ✅ `api/registro_router.py` (editado) — mapea `(InvitacionInvalida, InvitacionVencida,
  InvitacionYaUsada)` al mismo `HTTPException(422)` (mismo mensaje al Estudiante en los tres
  casos, ver wireframe §2.4)

### Sin cambios
- ✅ Sin cambios de DI (`frameworks/dependencies.py`) — mismos repos y hasher de `US-1.1.2`
- ✅ Sin endpoint nuevo — mismo `POST /identidad/registro`

---

## API Endpoints

| Método | Ruta | Descripción | Auth |
|--------|------|--------------|------|
| POST | `/identidad/registro` | Registrar Estudiante vía invitación | Público — sin JWT (sin cambios respecto a `US-1.1.2`) |

**Respuestas:** `201` (creado), `409` (`EmailYaRegistrado`), `422` (`InvitacionInvalida` /
`InvitacionVencida` / `InvitacionYaUsada` — mismo status y mensaje para los tres casos)

**OpenAPI Docs:** `/docs`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| Pylint | 9.91/10 | ≥ 8.0 | ✅ |
| Complejidad Ciclomática (máx/función) | 3 | ≤ 10 | ✅ |
| Índice de Mantenibilidad (mínimo) | 73.54 (grado A) | > 20 | ✅ |
| Cobertura de Tests | 100% | ≥ 95.0% | ✅ |

Fuente: `quality/reports/inc1/US-1.1.3-quality.json`. Coverage medido sobre los tres archivos
modificados (`entities/errors.py`, `entities/invitacion.py`, `use_cases/registrar_estudiante.py`
— 93/93 statements). Hallazgo R0903 (too-few-public-methods) en `RegistrarEstudianteUseCase` es
el mismo falso positivo esperado de Clean Architecture ya documentado en `US-1.1.0`–`US-1.1.2`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Tests Unitarios (7 tests nuevos/editados) — `tests/unit/inc1/`
- `test_invitacion.py` (editado) — `aceptar()` ahora espera `InvitacionVencida`/
  `InvitacionYaUsada`; 4 tests nuevos de `verificar_vigente()` (incluye prioridad ya-usada
  sobre vencida)
- `test_registrar_estudiante_use_case.py` (editado) — los tres rechazos esperan la excepción
  específica en vez de `InvitacionNoValida`

### Tests de Integración (1 test nuevo) — `tests/integration/inc1/`
- `test_registro_api_integration.py` (editado) — `test_registro_rechaza_invitacion_ya_usada`
  (los otros dos casos, token inexistente y vencida, ya estaban cubiertos desde `US-1.1.2`)

### Escenarios BDD (3 de 4 ejecutables) — `tests/features/inc1/US-1.1.3-*.feature` + `tests/step_defs/inc1/`
- Token inexistente → `InvitacionInvalida`
- Invitación vencida → `InvitacionVencida`
- Invitación ya usada → `InvitacionYaUsada`
- *(diferido)* Scenario Outline "La UI no distingue el motivo del rechazo" (tag `@ux`) —
  deseleccionado con `-m "not ux"`; no hay frontend contra el cual ejecutarlo todavía

**Todos los tests ejecutables pasando:** ✅ 85/85 (suite completa del proyecto, excluyendo el
escenario `@ux` diferido)

---

## Ajuste de Alcance — Frontend Diferido (mismo criterio de US-1.1.2)

Se verificó nuevamente `frontend/src`: sigue siendo el scaffold default de Vite, sin React
Router ni cliente HTTP. La pantalla `RegistroError.tsx` (`#registro-error`) que pide la spec
se implementa junto con `Registro.tsx`/`RegistroExito.tsx` en la misma US-IEDD de frontend ya
diferida desde `US-1.1.2`, una vez decidida la infraestructura base (routing, cliente API).

---

## Archivos Creados/Modificados

**Producción:** `src/identidad/entities/errors.py` (editado), `entities/invitacion.py`
(editado), `use_cases/registrar_estudiante.py` (editado), `frameworks/api/registro_router.py`
(editado) — ~40 líneas netas.

**Tests:** `tests/unit/inc1/test_invitacion.py` (editado), `test_registrar_estudiante_use_case.py`
(editado), `tests/integration/inc1/test_registro_api_integration.py` (editado),
`tests/features/inc1/US-1.1.3-registro-link-invalido.feature`,
`tests/step_defs/inc1/test_us_1_1_3_steps.py` — ~230 líneas.

**Documentación:** `docs/plans/inc1/US-1.1.3-{context,plan}.md`,
`docs/reports/inc1/US-1.1.3-report.md` (este archivo),
`quality/reports/inc1/US-1.1.3-quality.json`, `docs/traceability/matrix.md` (editado),
`CHANGELOG.md` (editado), `pyproject.toml` (editado — markers `registro-estudiante`,
`US-1.1.2`, `US-1.1.3`, `ux`).

---

## Criterios de Aceptación

- [x] Token inexistente → rechazo `InvitacionInvalida`
- [x] Invitación vencida (`expira_en` pasado) → rechazo `InvitacionVencida`
- [x] Invitación ya usada → rechazo `InvitacionYaUsada`
- [x] Ningún `Usuario` se crea en ninguno de los tres casos
- [x] Ningún evento de dominio se persiste (excepción de aplicación, no evento del Event Store)
- [ ] Frontend: pantalla de error (`#registro-error`) — **diferido**, ver nota de alcance
- [x] Tests unitarios de los tres caminos de rechazo

**Criterios de backend cumplidos:** ✅ — frontend diferido con acuerdo explícito (mismo
criterio que `US-1.1.2`)

---

## Próximos Pasos

- [ ] US-IEDD de infraestructura frontend (router + cliente API) + `Registro.tsx`/
  `RegistroExito.tsx`/`RegistroError.tsx`, diferida desde `US-1.1.2` y ahora también desde
  esta US
- [ ] `US-1.1.4` / `US-1.1.5` — siguientes US-IEDD de la Iteración 1 (Issues #9, #10)
- [x] RF-01 pasa a "Implementado" en `docs/traceability/matrix.md` — las tres US-IEDD que
  requería (`US-1.1.1`, `US-1.1.2`, `US-1.1.3`) están cerradas en backend

---

## Lecciones Aprendidas

- 💡 Cuando dos US comparten el mismo comando/use case (`US-1.1.2` y `US-1.1.3` comparten
  `RegistrarEstudianteUseCase`), diseñar el método de validación (`verificar_vigente`) para
  que lo reutilicen tanto el camino de aceptación como el de consulta evita duplicar la
  lógica de invariantes en dos lugares.
- 💡 Un escenario BDD que depende de una capa todavía no implementada (frontend, en este
  caso) se puede mantener documentado en el `.feature` con un tag propio (`@ux`) y excluir
  de la ejecución (`-m "not ux"`) en vez de fabricar un stub que simule cobertura inexistente.
- ✅ Verificar el blast radius de una excepción antes de eliminarla (`grep` de
  `InvitacionNoValida` en `src/` y `tests/`) confirmó que no quedaba ningún consumidor fuera
  del alcance de esta US.

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-07-23
