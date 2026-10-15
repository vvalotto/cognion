# Contexto de Ejecución — US-ADJ-59

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-59.md` (decisiones por defecto aceptadas por Víctor 2026-10-03), Issue [#474](https://github.com/vvalotto/cognion/issues/474)
- **Fuente Arquitectura:** `CLAUDE.md` §"Arquitectura interna", `docs/architecture/`, `docs/design/domain/BC-identidad-modelo.md`
- **Fuente UX:** `docs/design/ux/wireframes-cuentas-administracion.md` §2.9 + prototipo `identidad-cuentas-administracion.html` pantalla 8 (gate aprobado por Víctor 2026-10-03)

## Historia de Usuario
- **ID:** US-ADJ-59
- **Título:** Una cuenta deshabilitada no puede iniciar sesión
- **Tipo:** Corrección de bug (regla de negocio no hecha cumplir) con comportamiento nuevo — backend + frontend
- **Puntos:** 3 (estimado)
- **Prioridad:** Alta — hallazgo #11 🔴 de la UAT v1; primera US del Incremento 7-ADJ

## Decisiones de Ejecución
- **Perfil:** `clean-architecture-bc`
- **BDD:** Sí — los escenarios de la spec (7)
- **skip_bdd:** false
- **Fases a ejecutar:** 0 a 9
- **Dos partes en una sola US** (decisión de Víctor 2026-10-03: implementar por US): Parte A backend y Parte B frontend, con el gate UX ya aprobado.

## Perfil Activo
- **Perfil:** `clean-architecture-bc`
- **Patrón arquitectónico:** `clean-architecture` (entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad** (mismos que `US-ADJ-58`):
  - Backend: pylint ≥ 8.0, CC ≤ 10, MI ≥ 20, cobertura ≥ 95% del código nuevo; CodeGuard con `--analysis-type full`
  - Frontend: `npm run test:coverage` (umbral 80% branches), `tsc -b` y `oxlint` 0 errores
  - Pre-push: DesignReviewer 0 CRITICAL (vigilar CBO)

## Rutas de Artefactos
- Contexto: `docs/plans/inc7-adj/US-ADJ-59-context.md`
- BDD feature: `tests/features/inc7-adj/US-ADJ-59-cuenta-deshabilitada-no-inicia-sesion.feature`
- Step defs: `tests/step_defs/inc7-adj/test_us_adj_59_steps.py`
- Plan: `docs/plans/inc7-adj/US-ADJ-59-plan.md`
- Reporte: `docs/reports/inc7-adj/US-ADJ-59-report.md`
- Quality report: `quality/reports/inc7-adj/US-ADJ-59-quality.json`

## Regla local de ejecución de tests
Solo `tests/unit` y las suites de frontend corren en esta máquina. **`tests/integration` y BDD
vacían la base local compartida** (ya documentado desde la prueba de estabilización) — se
escriben y se verifican en CI, no localmente. Con `pytest tests/unit` y `vitest` alcanza para
las fases 4 y 7 localmente.

## Hallazgos de la Fase 0 (lectura de código)
- `IniciarSesionUseCase` (`src/identidad/use_cases/iniciar_sesion.py`) ya chequea `bloqueada`
  antes de verificar la contraseña: la guarda de `deshabilitada` va **antes** de esa, mismo patrón.
- `auth_router.py` mapea `CuentaBloqueadaError` → 403 con `detail` en texto plano y
  `CredencialesInvalidas` → 401. `ApiError.detail?: unknown` ya existe en el frontend
  (`api-client.ts`), así que el `detail` estructurado no requiere cambios de infraestructura.
- `Login.tsx` interpreta **cualquier** `403` como cuenta bloqueada (`setBloqueada(true)`): hay
  que discriminar por `err.detail.codigo` para no mostrar la alerta equivocada.
- Tests existentes del login: `tests/unit/inc1/test_iniciar_sesion_use_case.py`,
  `tests/unit/inc1/test_auth_controller.py` (más integración/BDD de `US-1.1.4`/`US-2.2.1`).
  No deben cambiar de comportamiento: la guarda nueva solo actúa con `deshabilitada = true`.
- `BC-identidad-modelo.md` no lista `deshabilitada` en la tabla de atributos de `Usuario`
  (deriva documental): se corrige en esta US junto con `INV-ID-18`.
- Sin dependencias nuevas en el use case → sin riesgo de CBO.
