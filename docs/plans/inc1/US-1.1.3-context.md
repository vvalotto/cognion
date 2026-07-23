# Contexto de Ejecución — US-1.1.3

## Fuentes
- **Fuente HU:** `docs/specs/inc1/US-1.1.3.md` (Issue GitHub #8)
- **Fuente Arquitectura:** `docs/rf/ARQ_v1.md` + `CLAUDE.md` (Clean Architecture BC-first)

## Historia de Usuario
- **ID:** US-1.1.3
- **Título:** Estudiante intenta registrarse con link vencido o inválido
- **Tipo:** Mejora de comportamiento existente — refina el camino de rechazo ya implementado
  en `US-1.1.2` (`InvitacionNoValida` genérica → `InvitacionInvalida` / `InvitacionVencida` /
  `InvitacionYaUsada`)
- **Puntos:** 3
- **Prioridad:** Alta — cierra RF-01 junto con `US-1.1.2`

## Decisión de alcance — reutilización de código existente

`US-1.1.2` ya implementó `RegistrarEstudianteUseCase`, `RegistroController` y el router
`POST /identidad/registro`, con una excepción genérica `InvitacionNoValida` (`src/identidad/entities/errors.py:47`)
lanzada desde `Invitacion.aceptar()` y `RegistrarEstudianteUseCase._buscar_invitacion_vigente()`.
Esta US no crea un nuevo endpoint ni un nuevo use case: refina esa excepción en tres específicas
y ajusta el mapeo HTTP en `registro_router.py`. El código de `US-1.1.2` es la base a modificar,
no un ejemplo a replicar.

## Decisión de alcance — frontend

Igual que en `US-1.1.2`: `frontend/src` sigue siendo el scaffold default de Vite (sin React
Router, sin cliente HTTP, sin páginas propias — verificado en esta sesión). La pantalla
`RegistroError.tsx` (`#registro-error`) que pide la spec requeriría decidir routing y cliente
API ahora, fuera de alcance de esta US.

**Decisión (aplicando el mismo criterio ya confirmado por Víctor en `US-1.1.2`):** esta US se
cierra con backend completo (las tres excepciones específicas + mapeo 4xx). El frontend de
error de registro se implementa junto con `Registro.tsx`/`RegistroExito.tsx` en la misma
US-IEDD de frontend diferida, una vez decidida la infraestructura base. Si Víctor prefiere
tratarlo distinto, avisar antes de Fase 2.

## Decisiones de Ejecución
- **BDD:** Sí — comportamiento nuevo (tres rechazos específicos) con criterios Gherkin ya
  definidos en la spec
- **skip_bdd:** false
- **Fases a ejecutar:** 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

## Perfil Activo
- **Perfil:** clean-architecture-bc
- **Patrón arquitectónico:** clean-architecture (entities → use_cases → interface_adapters → frameworks, BC-first)
- **Umbrales de calidad:**
  - pylint ≥ 8.0
  - CC ≤ 10
  - MI ≥ 20
  - cobertura ≥ 95%

## Rutas de Artefactos
- Contexto: docs/plans/inc1/US-1.1.3-context.md
- BDD feature: tests/features/inc1/US-1.1.3-registro-link-invalido.feature
- Plan: docs/plans/inc1/US-1.1.3-plan.md
- Reporte: docs/reports/inc1/US-1.1.3-report.md
- Quality report: quality/reports/inc1/US-1.1.3-quality.json
