# US-8.6.4: Publicar la imagen y desplegar con rollback

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `tooling operativo / CI`
**Bounded Context**: transversal (`.github/workflows/`, `deploy/gcp/`)
**Issue**: #548

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **publicar una versión con una etiqueta y desplegarla en la VM con un comando, pudiendo volver atrás si falla**,
para **actualizar el sistema sin miedo antes de una clase**.

---

## Contexto

Hoy `cd.yml` solo construye la imagen en cada push a `main`/etiqueta; no la publica ni despliega, y los pasos de Fly.io
están comentados. La VM no puede compilar el frontend con 1 GB de RAM, así que la imagen llega ya construida.
`alembic downgrade base` no es confiable todavía (`US-8.3.4`). Depende de las decisiones de `US-8.6.1` (`ADR-025`); si alguna cambia el diseño, se actualiza esta spec antes de implementar.

## Especificacion del comportamiento

- **CI:** al crear una etiqueta `v*.*.*` se construye y publica la imagen en el registro que decida `ADR-025` (respetando
  los límites gratuitos del registro), etiquetada con la versión. Los pasos de Fly.io se dejan comentados.
- **Despliegue en la VM:** un comando baja la versión indicada, **aplica las migraciones**, reinicia el servicio y verifica
  `/api/health`.
- **Rollback:** si la verificación falla, vuelve a la imagen anterior automáticamente y lo informa. El rollback es de
  **imagen**; las migraciones aplicadas no se deshacen (no hay `downgrade` confiable): las migraciones nuevas deben ser
  compatibles hacia atrás o, si no lo son, se restaura desde el respaldo previo (`US-8.6.5`).
- Antes de desplegar se toma un respaldo (reutiliza `US-8.6.5` cuando exista).

## Escenarios

1. Crear la etiqueta `vX.Y.Z` deja la imagen publicada y verificable en el registro.
2. Desplegar esa versión en la VM la deja respondiendo en `/api/health` con la versión nueva.
3. Desplegar una versión que no pasa el health check vuelve sola a la anterior y deja el sistema sirviendo.
4. Desplegar una versión con migración pendiente la aplica antes de reiniciar; si la migración falla, el despliegue se aborta
   y la versión anterior sigue sirviendo.
5. Desplegar sin conexión al registro falla con un mensaje claro y no deja el servicio caído.

## Fuera de alcance

CD automático al hacer merge (el despliegue es manual en esta iteración); `alembic downgrade` (`US-8.3.4`); Fly.io.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
