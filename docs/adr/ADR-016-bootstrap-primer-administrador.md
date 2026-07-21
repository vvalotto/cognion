# ADR-016 — Bootstrap del primer Administrador vía script standalone (vs. seed en migración, vs. endpoint público)

**Estado:** Aceptado
**Fecha:** 2026-07-21

---

## Contexto

`US-1.1.0` establece que el alta de `Usuario` (incluyendo `Administrador`) se resuelve dentro
del producto — ejecutada por un Administrador ya autenticado. Pero el primer Administrador no
tiene, por definición, a nadie que lo dé de alta: es un problema huevo-y-gallina análogo al
`createsuperuser` de Django. Sin resolverlo, no hay forma de operar el sistema tras un deploy
limpio.

## Opciones Consideradas

- **Endpoint público de alta sin autenticación** — descartada: abriría una vía de escalación de
  privilegios permanente en producción, no solo en el primer arranque.
- **Seed embebido en una migración de Alembic** — descartada: hardcodea (o parametriza de forma
  incómoda) credenciales dentro de una migración versionada, mezclando esquema de datos con
  datos operativos; además una migración corre una sola vez por definición, lo cual es
  demasiado rígido si se necesita re-ejecutar el bootstrap en un entorno nuevo.
- **Script standalone (`scripts/seed_admin.py`)** — elegida.

## Decisión

El primer Administrador se crea con un script standalone (`scripts/seed_admin.py`) ejecutado
manualmente después del deploy, leyendo credenciales de variables de entorno
(`ADMIN_NOMBRE`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`). Reutiliza `CrearUsuarioUseCase` — no
duplica lógica de negocio, solo evita el requisito de autenticación previa.

## Justificación

Mantiene la regla operativa de `US-1.1.0` ("toda alta adicional se resuelve dentro del
producto") para todos los casos excepto el primero, documentado como la única excepción. Es
idempotente en la práctica (falla con `EmailYaRegistrado` si ya se ejecutó) y no introduce
superficie de ataque nueva en el API — no hay endpoint público que exponer.

## Impacto en Configuración

- `scripts/seed_admin.py` — nuevo, ejecuta el bootstrap.
- `docs/plans/CHECKLIST-INSTALACION.md` — debería referenciar este script como paso posterior
  al primer deploy (pendiente de actualizar en una futura sesión de mantenimiento documental).

## Consecuencias

- ✅ No hay endpoint de alta sin autenticación expuesto en ningún momento.
- ✅ Reutiliza el use case existente — sin lógica de negocio duplicada.
- ⚠️ Requiere acceso a shell/entorno de despliegue para ejecutarlo — aceptable para un equipo
  unipersonal, sería fricción en un equipo con despliegues delegados a terceros.
