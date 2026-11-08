# Contexto de Ejecución — US-ADJ-67

## Fuentes
- **Fuente HU:** `docs/specs/ajustes/US-ADJ-67.md`, Issue [#590](https://github.com/vvalotto/cognion/issues/590)
- **Fuente UX:** `docs/design/ux/wireframes-portal-entrada.md` §3.4 y §4; `docs/design/ux/wireframes-identidad.md` §2.3 y §2.4; prototipos `portal-entrada.html` (pantalla 7) e `identidad-registro-login.html` (`#registro-error`, `#registro-requisitos`). Aprobados el 2026-11-08
- **Origen:** prueba real con estudiantes sobre la VM de GCP (2026-11-06)
- **Decisiones de producto:** #593, 2026-11-08 (duraciones 15 min / 1 h / 1 día, sin cupo, el grupal reemplaza al individual en la UI, un solo link vigente por comisión)
- **Código existente:** `src/identidad/entities/invitacion.py` (`EXPIRACION_DIAS = 7`, `usada_en`), `use_cases/generar_invitacion.py`, `registrar_estudiante.py`, `obtener_invitacion.py`, `frameworks/api/invitaciones_router.py` (`POST /comisiones/{id}/invitaciones`), `registro_router.py` (`GET /invitaciones/{token}`, `POST /registro`), `entities/ports/invitacion_repository_port.py`, `frameworks/db/models.py` (`InvitacionModel`). Frontend: `ComisionDetalleDocente.tsx`, `Registro.tsx`, `RegistroError.tsx`, `lib/identidad-comisiones-api.ts`

## Historia de Usuario
- **ID:** US-ADJ-67 — El Docente genera un link de invitación grupal con vencimiento corto
- **Tipo:** ajuste de producto, backend + frontend (Identidad)
- **Puntos:** 8 · **Patrón activo:** `clean-architecture-bc`
- **Iteración:** Incremento 9, Iteración 2 (rama `feature/inc-9-iter-2-link-grupal`, un commit por US y un solo PR al cierre)

## Decisiones de Ejecución
- **Un mismo agregado `Invitacion`** con `grupal`, `usos` y `revocada_en`; el comportamiento individual no cambia (un uso, 7 días). Los estados salen de métodos del agregado, no del router.
- **Endpoints nuevos, el individual intacto:** generar, consultar la última invitación grupal y desactivar bajo `/comisiones/{id}/invitaciones-grupales`. El `POST /comisiones/{id}/invitaciones` actual queda para compatibilidad.
- **Contador atómico:** `usos` se incrementa con una sola sentencia SQL en el repositorio; probado con registros simultáneos contra una base real.
- **Un solo link vigente:** el caso de uso revoca el anterior de la comisión y guarda el nuevo en la misma unidad de trabajo.
- **Errores con código:** `detail = {"codigo", "mensaje"}` en preview y registro; los status HTTP no cambian. La contraseña inválida del registro lleva `password_invalida`.
- **Migración con nombres explícitos y `downgrade`** que cumple la guarda de `US-8.3.4`; `verificar_migraciones.sh` debe seguir en verde.
- **Tests:** unitarios del agregado y los casos de uso (sin base); integración por HTTP con base descartable inline (incluye registros simultáneos); BDD de los escenarios de backend; Vitest para las pantallas. La verificación visual en navegador real queda para el cierre de la iteración.
- **Documentación en Fase 8:** `ADR-027` (nuevo), nota en `ADR-012`, `BC-identidad-modelo.md`, docstring de `Invitacion`.
- **Fases:** todas, con BDD.

## Rutas
- Plan: docs/plans/inc9/US-ADJ-67-plan.md · Reporte: docs/reports/inc9/US-ADJ-67-report.md · Quality: quality/reports/inc9/US-ADJ-67-quality.json
- Feature: tests/features/inc9/US-ADJ-67-link-grupal.feature
