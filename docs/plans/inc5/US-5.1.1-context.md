# Contexto de Ejecución — US-5.1.1

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/inc5/US-5.1.1.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` (ADR-006 integración entre BCs) + `CLAUDE.md` §"Arquitectura interna" — ya conocida, no requiere reconsulta al usuario (`feedback_contexto`).

## Historia de Usuario
- **ID:** US-5.1.1
- **Título:** Infraestructura del BC Notificaciones
- **Tipo:** Nueva funcionalidad (técnica — infraestructura sin UI)
- **Puntos:** 5 (no consignados explícitamente en la spec ni en `inc5-candidatas.md`; valor nominal para tracking, no afecta el criterio de cierre)
- **Prioridad:** Alta — desbloquea `US-5.1.2`/`US-5.1.3`, único orden posible dentro de la iteración

## Decisiones de Ejecución
- **BDD:** Sí — la spec ya trae 5 escenarios Gherkin completos en `docs/specs/inc5/US-5.1.1.md` §Criterios de aceptación; se traducen a `.feature` sin reformular contenido.
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
- Contexto: `docs/plans/inc5/US-5.1.1-context.md`
- BDD feature: `tests/features/inc5/US-5.1.1-infraestructura-notificaciones.feature`
- Plan: `docs/plans/inc5/US-5.1.1-plan.md`
- Reporte: `docs/reports/inc5/US-5.1.1-report.md`
- Quality report: `quality/reports/inc5/US-5.1.1-quality.json`

## Notas específicas de esta US
- Sin aggregate ni endpoint HTTP propio — BC Notificaciones puramente reactivo (`BC-notificaciones-modelo.md` §2). No hay `Controller`/`Router` en esta US.
- Toca 3 BCs: Notificaciones (nuevo), Identidad (método nuevo en puerto existente), Actividad Evaluativa (contrato de puerto sin cablear).
- `aiosmtplib` no está instalado todavía — se agrega en Fase 3 (`pyproject.toml` + `uv sync`).
- No hay Mailhog/servidor SMTP local corriendo en este entorno — el escenario "Envío real contra SMTP local" (BDD) se implementa contra un servidor SMTP de test embebido (`aiosmtplib` trae soporte de test vía `smtpd`/mock local, a definir en Fase 2) para no depender de infraestructura externa en CI; el smoke manual contra Mailhog real queda documentado en `docs/plans/CHECKLIST-INSTALACION.md` pero no bloquea el cierre automatizado de esta US.
