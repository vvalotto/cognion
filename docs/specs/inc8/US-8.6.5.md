# US-8.6.5: Backup a Cloud Storage con restauración ensayada

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `tooling operativo / infraestructura`
**Bounded Context**: transversal (`scripts/`, `deploy/gcp/`)
**Issue**: #549

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **respaldar la base fuera de la VM y haber restaurado un respaldo de verdad**,
para **no perder lo que hicieron los alumnos si la VM se borra o se rompe**.

---

## Contexto

`ADR-022` decidió `pg_dump` con retención de 12 meses; la variante local (`US-8.5.4`, `respaldar.sh`/`restaurar.sh`) ya
verifica el archivo con `sha256`, rota por cantidad y ensaya la restauración en una base temporal. La nube ofrece 5 GB
gratuitos de Cloud Storage en regiones de EE.UU. Un respaldo que nunca se restauró no es un respaldo. Depende de las decisiones de `US-8.6.1` (`ADR-025`); si alguna cambia el diseño, se actualiza esta spec antes de implementar.

## Especificacion del comportamiento

- Reutiliza `respaldar.sh`/`restaurar.sh`, adaptados a la base de la VM (en contenedor o nativa según `ADR-025`).
- Destino: un bucket de Cloud Storage en una región gratuita, con acceso mínimo para la cuenta de servicio de la VM, sin
  claves guardadas en archivos.
- **Retención de 12 meses** (`ADR-022`): se evalúa la regla de ciclo de vida del bucket en lugar de borrar por script; si no
  alcanza, se borra desde el script.
- **Cuándo:** respaldo programado, y respaldo manual antes y después de cada clase y antes de cada despliegue.
- **Restauración ensayada** en la VM sobre una base temporal, con comparación de conteos (usuarios, eventos, preguntas),
  documentada con fecha y resultado.
- El bucket no es público y el tamaño se vigila contra los 5 GB gratuitos.

## Escenarios

1. Ejecutar el respaldo genera un archivo verificado y lo sube; aparece en el bucket con su `sha256`.
2. Restaurar ese archivo en una base temporal de la VM da los mismos conteos que el origen y la temporal se elimina.
3. Un archivo corrupto en el bucket hace fallar la restauración con mensaje claro sin tocar la base de producción.
4. Un objeto con más de 12 meses deja de existir según la regla de retención.
5. El bucket no es accesible sin credenciales.

## Fuera de alcance

Subir respaldos a Drive (`ADR-022` original); respaldo continuo o recuperación a un punto en el tiempo.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
