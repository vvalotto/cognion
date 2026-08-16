# Reporte de Implementación: US-2.1.11

## Resumen Ejecutivo

- **Historia de Usuario:** US-2.1.11 - Docente carga una pregunta eligiendo su tipo
- **Puntos estimados:** 3
- **Tiempo real:** ~24 min (fases 0-7, ver `docs/plans/inc2/US-2.1.11-plan.md` §Métricas de Tiempo)
- **Estado:** ✅ COMPLETADO
- **Fecha completado:** 2026-08-16

---

## Alcance

Frontend puro, sin cambios de backend — consume `POST /preguntas/opcion-multiple` y
`POST /preguntas/verdadero-falso` tal como quedaron en `US-2.1.3`/`US-2.1.4`, y `GET /materias`
(`US-2.1.9`) para resolver `materiaId → bancoId`.

---

## Componentes Implementados

### Frontend
- ✅ **`NuevaPreguntaTipo.tsx`** (nuevo, `frontend/src/pages/NuevaPreguntaTipo.tsx`) — dos
  tarjetas clicables ("Opción múltiple" / "Verdadero/Falso"), navega al formulario
  correspondiente; aclara que el tipo no se puede cambiar después de creada la pregunta
- ✅ **`NuevaPreguntaOpcionMultiple.tsx`** (nuevo) — texto, opciones dinámicas (mínimo 2, radio
  de correcta, "+ Agregar opción", ✕ para quitar salvo que baje de 2), unidad temática y tema
  (texto libre — sin catálogo ni endpoint de origen, mismo criterio que `US-2.1.8`),
  dificultad/importancia (`<select>`); validación de cliente antes de enviar (INV-BP-02/03:
  mínimo 2 opciones, exactamente una correcta)
- ✅ **`NuevaPreguntaVerdaderoFalso.tsx`** (nuevo) — texto, selector Verdadero/Falso sin
  default, mismos metadatos que Opción Múltiple
- ✅ **`router.tsx`** — reemplaza los 3 placeholders de
  `/materias/:materiaId/banco/preguntas/nueva*` (dejados por `US-2.1.8`) por las pantallas
  reales; la ruta de "editar" sigue en placeholder, pendiente de `US-2.1.12`

---

## Métricas de Calidad

| Métrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| oxlint | 0 errores | 0 errores | ✅ |
| `tsc --noEmit` | 0 errores | 0 errores | ✅ |
| Coverage `NuevaPreguntaTipo.tsx` (statements/branches/functions) | 100% / 100% / 100% | ≥ 80% | ✅ |
| Coverage `NuevaPreguntaOpcionMultiple.tsx` | 83.33% / 75% / 77.41% | ≥ 80% (statements) | ✅ |
| Coverage `NuevaPreguntaVerdaderoFalso.tsx` | 90.47% / 75% / 81.25% | ≥ 80% (statements) | ✅ |

Fuente: `quality/reports/inc2/US-2.1.11-quality.json`.

**Estado General:** ✅ APROBADO

---

## Tests Implementados

### Frontend

**Unitarios (9 tests nuevos, Vitest)**
- `NuevaPreguntaTipo.test.tsx` — elegir Opción múltiple navega al formulario, elegir
  Verdadero/Falso navega al formulario, "Cancelar" vuelve al banco
- `NuevaPreguntaOpcionMultiple.test.tsx` — carga exitosa con 3 opciones y una correcta, rechazo
  de cliente sin ninguna opción marcada como correcta, quitar opción no permite bajar de 2
- `NuevaPreguntaVerdaderoFalso.test.tsx` — carga exitosa eligiendo Verdadero, rechazo de
  cliente sin elegir V/F, "Cancelar" vuelve al banco sin guardar

**Integración (3 tests nuevos + 1 test parametrizado ajustado, `router.test.tsx`)**
- Ruta de selección de tipo renderiza `NuevaPreguntaTipo` con sesión de docente
- Ruta de Opción Múltiple renderiza el formulario real con sesión de docente
- Ruta de Verdadero/Falso renderiza el formulario real con sesión de docente
- Test parametrizado de placeholders reducido a la única ruta que sigue pendiente
  (`.../editar`, `US-2.1.12`)

**BDD (4 escenarios frontend)**
- `tests/features/inc2/US-2.1.11-carga-pregunta-tipo.feature` — validados por mapeo directo a
  los tests de Vitest de arriba (sin step_defs/pytest-bdd, misma adaptación de `US-2.1.9`/
  `US-2.1.10`)

**Todos los tests pasando:** ✅ 89/89 frontend (suite completa)

---

## Archivos Creados/Modificados

### Código de producción — frontend
- `frontend/src/pages/NuevaPreguntaTipo.tsx` (nuevo)
- `frontend/src/pages/NuevaPreguntaOpcionMultiple.tsx` (nuevo)
- `frontend/src/pages/NuevaPreguntaVerdaderoFalso.tsx` (nuevo)
- `frontend/src/router.tsx` (modificado)

### Tests
- `tests/features/inc2/US-2.1.11-carga-pregunta-tipo.feature` (nuevo)
- `frontend/src/pages/NuevaPreguntaTipo.test.tsx` (nuevo)
- `frontend/src/pages/NuevaPreguntaOpcionMultiple.test.tsx` (nuevo)
- `frontend/src/pages/NuevaPreguntaVerdaderoFalso.test.tsx` (nuevo)
- `frontend/src/router.test.tsx` (modificado)

### Documentación
- `docs/specs/inc2/US-2.1.11.md` (ya existente, sin cambios de alcance)
- `docs/plans/inc2/US-2.1.11-context.md`
- `docs/plans/inc2/US-2.1.11-plan.md`
- `docs/reports/inc2/US-2.1.11-report.md` (este archivo)
- `quality/reports/inc2/US-2.1.11-quality.json`
- `CHANGELOG.md` (entrada nueva bajo `[Unreleased]`)

---

## Criterios de Aceptación

- [x] Elegir tipo Opción Múltiple — muestra el formulario con lista de opciones y radio de correcta
- [x] Carga exitosa de Opción Múltiple — crea la pregunta y vuelve al banco filtrado
- [x] Rechazo de cliente por opciones inválidas — bloquea el envío, no llama al backend
- [x] Carga exitosa de Verdadero/Falso — crea la pregunta y vuelve al banco filtrado

**Todos los criterios cumplidos:** ✅

---

## Próximos Pasos

- [ ] Implementar `US-2.1.12` (Docente edita una pregunta existente) — reemplaza el placeholder
  de "Editar" en `Banco.tsx` y la ruta `.../editar`
- [ ] Implementar `US-2.1.13` (Docente elimina una pregunta con confirmación previa) — habilita
  el botón "Eliminar", deshabilitado desde `US-2.1.10`

---

**Reporte generado automáticamente por Claude Code**
**Fecha:** 2026-08-16
