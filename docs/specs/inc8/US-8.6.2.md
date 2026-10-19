# US-8.6.2: Composición de servicios y configuración de la VM

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `tooling operativo / infraestructura`
**Bounded Context**: transversal (`deploy/gcp/`)
**Issue**: #546

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **que la aplicación, la base y el acceso seguro arranquen juntos en una VM con poca memoria y se reinicien solos**,
para **no depender de levantarlos a mano ni de que algo se caiga en silencio**.

---

## Contexto

La VM `e2-micro` tiene 1 GB de RAM y CPU compartida. Sirve la interfaz y la API desde un solo proceso (`US-8.1.6`) y se
configura por variables de entorno (`US-8.1.1` a `8.1.7`). Depende de las decisiones de `US-8.6.1` (`ADR-025`); si alguna cambia el diseño, se actualiza esta spec antes de implementar.

## Especificacion del comportamiento

- Definición de servicios (aplicación, PostgreSQL, proxy HTTPS) con **límites de memoria**, reinicio automático, logs con
  rotación y la red interna sin exponer PostgreSQL al exterior. Si `ADR-025` elige procesos nativos, el equivalente son
  unidades de servicio con los mismos límites.
- PostgreSQL ajustado para 1 GB (memoria compartida y conexiones acotadas) y pool de conexiones de la aplicación acorde.
- Variables y secretos en un archivo con permisos 600 fuera del repositorio; `ENTORNO`, `EMAIL_MODO` y URLs según `ADR-025`.
  Plantilla sin valores reales versionada (`.env.example` ampliado o equivalente).
- Bootstrap del primer Administrador con el comando existente (`US-8.1.5`), contraseña por terminal sin eco.
- Las migraciones siguen siendo un paso explícito de despliegue (`US-8.1.4`), no ocurren al arrancar.

## Escenarios

1. Con la VM recién aprovisionada, un comando levanta todos los servicios y `/api/health` responde por HTTPS.
2. Tras reiniciar la VM, los servicios vuelven solos.
3. Desde fuera de la VM, el puerto de PostgreSQL no responde.
4. Ningún secreto aparece en el repositorio ni en el log de arranque.
5. Con la configuración aplicada, la memoria en reposo queda por debajo de lo que fije `ADR-025` (referencia: < 60 % de 1 GB).

## Fuera de alcance

Crear la VM (`US-8.6.3`); publicar la imagen (`US-8.6.4`); backup (`US-8.6.5`).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
