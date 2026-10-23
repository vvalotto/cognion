# US-8.6.4: Scripts de aprovisionamiento, publicación y despliegue con rollback

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `tooling operativo / infraestructura`
**Bounded Context**: transversal (`deploy/gcp/`, `.github/workflows/`)
**Issue**: #548

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **crear y destruir la VM, publicar una versión y desplegarla con un comando, pudiendo volver atrás si falla**,
para **repetir el despliegue sin depender de mi memoria y actualizar el sistema sin miedo antes de una clase**.

---

## Contexto

Esta US **codifica lo que funcionó en la prueba manual de `US-8.6.3`**; no se especifica a ciegas. Reúne lo que antes eran el script de
aprovisionamiento y la publicación con despliegue. Hoy `cd.yml` solo construye la imagen en cada push a `main`/etiqueta y no la publica;
la VM no puede compilar el frontend con 1 GB. `alembic downgrade base` no es confiable todavía (`US-8.3.4`). La cuenta de facturación es
paga y sin créditos: un recurso de más cuesta dinero. Depende de la bitácora de `US-8.6.3` y de `ADR-025`.

## Especificacion del comportamiento

**Aprovisionamiento (`deploy/gcp/`):**
- Script de creación con `gcloud`: proyecto, `e2-micro` en `us-central1`, disco estándar de 30 GB o menos, IP estática **siempre asignada a
  la VM** (una reservada sin asignar cuesta), swap, sistema base y Docker según lo probado.
- **Firewall:** solo 80 y 443 (y el acceso de administración que se decida); sin PostgreSQL expuesto.
- **Presupuesto propio y límite de inversión** según lo decidido en `US-8.6.3`.
- Script de destrucción que borra lo creado sin tocar nada más, e idempotencia razonable (ejecutarlo dos veces no duplica recursos).
- Prerrequisitos documentados: `gcloud`, facturación, sesión vigente.

**Publicación y despliegue:**
- **CI:** al crear una etiqueta `v*.*.*` se construye y publica la imagen en el registro que resultó viable en `US-8.6.3`, etiquetada con la
  versión; los pasos de Fly.io quedan comentados.
- **En la VM:** un comando baja la versión indicada, **aplica las migraciones**, reinicia el servicio y verifica `/api/health`.
- **Rollback:** si la verificación falla vuelve a la imagen anterior y lo informa. Es un rollback de **imagen**: las migraciones aplicadas no
  se deshacen (no hay `downgrade` confiable); las migraciones nuevas deben ser compatibles hacia atrás o, si no, se restaura el respaldo previo.
- Antes de desplegar se toma un respaldo (reutiliza `US-8.6.5` cuando exista).

## Escenarios

1. Sobre un proyecto limpio, el script deja una VM con IP estática y swap activo, accesible por SSH.
2. Un escaneo de puertos desde fuera muestra solo 80/443.
3. El script de destrucción deja el proyecto sin recursos facturables creados por esta iteración.
4. Crear la etiqueta `vX.Y.Z` deja la imagen publicada y verificable; desplegarla la deja respondiendo en `/api/health` con la versión nueva.
5. Desplegar una versión que no pasa el health check vuelve sola a la anterior y deja el sistema sirviendo.
6. Una migración que falla aborta el despliegue y la versión anterior sigue sirviendo.
7. Si falta `gcloud` o la facturación, o no hay conexión al registro, los scripts lo dicen y salen con código distinto de cero, sin traza.

## Fuera de alcance

CD automático al hacer merge (el despliegue es manual en esta iteración); `alembic downgrade` (`US-8.3.4`); Fly.io.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
