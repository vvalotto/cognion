# Contexto de Ejecución — US-ADJ-26

## Fuentes
- **Fuente HU:** GitHub Issue [#271](https://github.com/vvalotto/cognion/issues/271) + spec `docs/specs/ajustes/US-ADJ-26.md`
- **Fuente Arquitectura:** `CLAUDE.md` (Clean Architecture BC-first, perfil `clean-architecture-bc`)

## Historia de Usuario
- **ID:** US-ADJ-26
- **Título:** Docente genera el link de invitación de una Comisión
- **Tipo:** Nueva funcionalidad (pantallas nuevas del lado Docente) + ampliación de un endpoint existente (token en la respuesta, email opcional)
- **Puntos:** 2
- **Prioridad:** Alta — última US de la cadena Comisiones/Invitación de la Iteración 1a

## Decisiones de Ejecución
- **BDD:** Sí — nueva funcionalidad con criterios de aceptación claros (Issue #271, spec §Criterios de aceptación)
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** Clean Architecture BC-first (entities/use_cases/interface_adapters/frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Gaps detectados en Fase 0 (decididos con Víctor antes de escribir la spec)

1. `InvitacionResponse` no exponía `token` — el endpoint `POST /comisiones/{id}/invitaciones`
   (`US-1.1.1`) fue diseñado para enviar el token por email, no para mostrarlo en pantalla.
   Decisión: agregar `token` a la respuesta y volver `email_destinatario` opcional en
   `GenerarInvitacionRequest` (si no se envía, el use case omite el envío de email). Sin
   invariante de dominio nueva — `Invitacion.crear()` ya generaba el token.
2. No existe `GET /docentes/{id}/comisiones`. Decisión: no agregarlo — el Docente llega a sus
   Comisiones navegando Materias → Comisiones de la materia, reutilizando
   `GET /materias/{id}/comisiones` (ya acepta rol `docente`, `US-4.2.2`) sin filtrar por
   asignación en el listado — la validación real de "está asignado" la sigue haciendo el
   backend al generar la invitación (`DocenteNoAsignadoAComision`, INV-ID-08).

Detalle completo de ambas decisiones en `docs/specs/ajustes/US-ADJ-26.md` §Contexto del
dominio.

## Rutas de Artefactos
- Contexto: `docs/plans/inc4-adj/US-ADJ-26-context.md`
- BDD feature: `tests/features/inc4-adj/US-ADJ-26-generar-invitacion.feature`
- Plan: `docs/plans/inc4-adj/US-ADJ-26-plan.md`
- Reporte: `docs/reports/inc4-adj/US-ADJ-26-report.md`
- Quality report: `quality/reports/inc4-adj/US-ADJ-26-quality.json`
