# Contexto de Ejecución — US-ADJ-40

## Fuentes
- **Fuente HU:** Documento local — `docs/specs/ajustes/US-ADJ-40.md`
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (reglas de capas), sin capas de dominio aplicables (frontend puro)

## Historia de Usuario
- **ID:** US-ADJ-40
- **Título:** Pantallas "Olvidé mi contraseña" y "Definir nueva contraseña"
- **Tipo:** Nueva funcionalidad (pantallas nuevas que consumen endpoints ya existentes)
- **Puntos:** 3
- **Prioridad:** Última US de la Iteración 2 del Incremento 5-ADJ — la cierra completa. Depende
  de `US-ADJ-38`/`US-ADJ-39` (ya cerradas, endpoints funcionando).

## Decisiones de Ejecución
- **BDD:** No — frontend puro, sin lógica de dominio backend. Los criterios Gherkin ya
  redactados en la spec son la guía de comportamiento, pero se verifican con Vitest +
  Testing Library, no con pytest-bdd (el proyecto no tiene infraestructura BDD para
  frontend). Mismo criterio ya aplicado en `US-ADJ-35`/`36`/`37`.
- **skip_bdd:** true
- **Fases a ejecutar:** 0, 2, 3, 4, 5, 7, 8, 9 (se omiten 1 y 6)

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (no aplica a esta US — frontend puro, sin capas
  entities/use_cases/interface_adapters/frameworks)
- **Umbrales de calidad:**
  - pylint ≥ 8.0 (N/A — sin código Python en esta US)
  - CC ≤ 10 (N/A)
  - MI ≥ 20 (N/A)
  - cobertura ≥ 95% (aplica a `frontend/`, vía Vitest — umbral de branches del proyecto: 80%
    global, ver `CLAUDE.md`/`US-ADJ-16`)

## Rutas de Artefactos
- Contexto: docs/plans/inc5-adj/US-ADJ-40-context.md
- BDD feature: N/A (skip_bdd)
- Plan: docs/plans/inc5-adj/US-ADJ-40-plan.md
- Reporte: docs/reports/inc5-adj/US-ADJ-40-report.md
- Quality report: quality/reports/inc5-adj/US-ADJ-40-quality.json

## Notas específicas de esta US
- Backend ya existe completo (`US-ADJ-38`/`39`): `POST /identidad/recuperar-password/solicitar`
  (202, siempre mensaje genérico) y `POST /identidad/recuperar-password/confirmar` (200 éxito,
  422 con `detail` como **string plano** — no objeto estructurado — en caso de error).
- **Gap de diseño detectado en Fase 0, a resolver en el plan:** el 422 de `confirmar` no trae un
  código de error propio para distinguir "token inválido/vencido/ya usado" (→ pantalla de error)
  de "password fuera de política" (→ error inline) — a diferencia de `CambiarPasswordError`
  (`cuentas-api.ts`), que sí recibe un objeto estructurado. Las 5 excepciones de dominio
  (`src/identidad/entities/errors.py`) tienen mensajes distinguibles por texto: los de política
  de contraseña empiezan con `"La contraseña debe..."`, los de token mencionan
  `"El token de recuperación '...'"`. Se resuelve en el cliente API distinguiendo por ese
  patrón de texto (no por código), documentado explícitamente en el plan para que quede
  trazable — mismo criterio de "gap detectado antes de codear" ya aplicado en USs previas.
- Cliente API: se agrega a `frontend/src/lib/cuentas-api.ts` (ya concentra las operaciones de
  contraseña de Identidad — `resetearPassword`, `cambiarPassword` — es el "equivalente" que
  menciona la spec a `identidad-api.ts`, que no existe como archivo separado en este proyecto).
- Reutiliza `PasswordInput` (`US-ADJ-35`/`36`, con indicador de fortaleza) para los dos campos
  de contraseña nueva de `RecuperarPasswordNueva.tsx`.
- 3 rutas públicas nuevas en `router.tsx`, sin `RequireRole` (igual que `/login`, `/registro`).
- Issue: [#341](https://github.com/vvalotto/cognion/issues/341)
