# Contexto de Ejecución — US-ADJ-08

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-08.md` (Issue GitHub #448)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (§"Arquitectura interna — reglas no negociables")

## Historia de Usuario
- **ID:** US-ADJ-08
- **Título:** Estudiante ve la materia/comisión de la invitación antes de registrarse
- **Tipo:** Mejora de comportamiento existente
- **Puntos:** 2
- **Prioridad:** Media (deuda de UX relevada en UAT 2026-08-23, sin bloquear ningún RF)

## Decisiones de Ejecución
- **BDD:** Sí — nuevo endpoint público + cambio de comportamiento visible en `Registro.tsx`
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (BC-first: entities → use_cases → interface_adapters → frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95.0%

## Rutas de Artefactos
- Contexto: docs/plans/inc6-adj/US-ADJ-08-context.md
- BDD feature: tests/features/incN/US-ADJ-08-invitacion-preview.feature (ubicación real a confirmar contra la convención de features de Identidad)
- Plan: docs/plans/inc6-adj/US-ADJ-08-plan.md
- Reporte: docs/reports/inc6-adj/US-ADJ-08-report.md
- Quality report: quality/reports/inc6-adj/US-ADJ-08-quality.json

## Notas de alcance (de la spec)
- Endpoint nuevo `GET /identidad/invitaciones/{token}` (público, sin auth) — solo lectura, no consume ni valida datos de registro. 404/422 si el token no existe o venció (mismo criterio sin distinguir causa que `US-1.1.8`).
- No debe filtrar información sensible: sin `docente_id`, sin email destinatario.
- Reutiliza el mismo puerto cross-BC (`MateriaPort`) que ya usa `RegistrarEstudianteUseCase`.
- Frontend: `Registro.tsx` hace fetch al montar con el `token` de la URL; chip `.comision-tag` del prototipo; maneja estado de carga/error si el token ya es inválido antes de completar el formulario.
- Decisión de diseño pendiente de Fase 2: qué mostrar en lugar de "Comisión A" (letra que no existe en el dominio) — candidatos: `horario` de la Comisión, o solo el nombre de la Materia.
