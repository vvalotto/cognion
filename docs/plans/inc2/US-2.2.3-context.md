# Contexto de Ejecución — US-2.2.3

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc2/US-2.2.3.md`
- **Fuente Arquitectura:** `CLAUDE.md` (raíz del repo) + `docs/rf/ARQ_v1.md`

## Historia de Usuario
- **ID:** US-2.2.3
- **Título:** Administrador ve el detalle de una cuenta
- **Tipo:** Nueva funcionalidad
- **Puntos:** 2
- **Prioridad:** Alta — RF-03, tercera US de la Iteración 2 del Incremento 2

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya incluye escenarios Gherkin completos en Criterios de aceptación
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc2/US-2.2.3-context.md
- BDD feature: tests/features/inc2/US-2.2.3-detalle-cuenta.feature
- Plan: docs/plans/inc2/US-2.2.3-plan.md
- Reporte: docs/reports/inc2/US-2.2.3-report.md
- Quality report: quality/reports/inc2/US-2.2.3-quality.json

## Notas de dominio (de la spec)
- BC: Identidad. Query de solo lectura, sin invariantes de dominio propias.
- `ObtenerCuenta(usuario_id)`: devuelve `id`, `nombre`, `email`, tipo de perfil, `bloqueada`,
  `creado_en`, y `comision_id` (solo si Estudiante, `null` si Docente/Administrador).
- Nuevo error `UsuarioNoExiste` si no hay `Usuario` con ese id.
- Suma un endpoint a `CuentasController`/`cuentas_router.py` ya existentes (`US-2.2.2`).

## Decisión previa a esta implementación (confirmada por Víctor)
`creado_en` no existe hoy en `Usuario`/`UsuarioModel`. Se agrega en esta US (migración con
backfill por timestamp único de la migración). Es un campo distinto y en un aggregate distinto
al `fecha_creacion` de `PreguntaPlantilla` que agregará `US-ADJ-03` (iteración de ajuste
diferida) — ambos comparten el mismo patrón (columna de auditoría + backfill con timestamp
único), pero no son el mismo cambio. Víctor eligió "agregar el campo ahora" en vez de excluirlo
del alcance de esta US.

## Nota sobre CBO (aprendizaje de US-2.2.2)
`CuentasController`/`cuentas_router.py` ya existen desde `US-2.2.2` con 1 método cada uno —
agregar un segundo método (`obtener_cuenta`) los deja en 2/2, lejos de cualquier umbral. No se
anticipa riesgo de CBO en esta US, pero verificar contra `develop` si el pre-push gate lo
marca de todos modos (ver `feedback_cbo_pre_push_no_fase7` en memoria).
