# Diseño de Pruebas UAT — Incremento 0 "Fundación Técnica"

| Campo | Valor |
|-------|-------|
| Incremento | 0 |
| Baseline | BL-001 |
| US cubiertas | Ninguna — incremento técnico sin US-IEDD (ver `HITO-3`) |
| Entorno | Propio |

---

## Capas aplicables

**Capa 1 (pytest de flujo de dominio vía `use_cases/`): no aplica.** El Incremento 0 no
introduce dominio — todos los BCs siguen siendo esqueletos vacíos. No hay flujo de
`use_cases/` que ejecutar.

**Capa 2 (HTTP, entorno propio): aplica.** Es la única capa relevante para este
incremento — verifica que el servicio arranca y responde.

**Checkpoint de staging (`PROCEDIMIENTO-UAT.md` §4):** nombrado explícitamente para el
cierre de este tipo de incremento, pero bloqueado — no hay entorno de staging desplegado
todavía (decisión de infraestructura pendiente, ítem abierto en `CLAUDE.md` /
`ARQ_v1.md`). Se difiere junto con esa decisión, no es un gap nuevo de este cierre.

---

## Criterio de aceptación

- `GET /health` contra la app corriendo localmente responde `200` con
  `{"status": "ok"}`.
- `alembic upgrade head` aplica sin errores contra PostgreSQL local.
- Sin hallazgos 🔴 Bloqueantes.

---

## Evidencia (Capa 2)

Ver `quality/reports/uat/inc0/evidencia.md`.
