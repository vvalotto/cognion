# US-8.6.3: Aprovisionamiento reproducible de la VM con gcloud

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `tooling operativo / infraestructura`
**Bounded Context**: transversal (`deploy/gcp/`)
**Issue**: #547

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **crear y destruir la VM de la prueba con un script y no con clics en una consola**,
para **poder repetirlo desde cero y no quedar atado a una configuración que nadie recuerda**.

---

## Contexto

La capa gratuita incluye una `e2-micro` no preemptible por mes solo en `us-west1`, `us-central1` o `us-east1`, 30 GB de
disco estándar y 1 GB de salida de red. La cuenta es personal (`vvalotto@gmail.com`). Depende de las decisiones de `US-8.6.1` (`ADR-025`); si alguna cambia el diseño, se actualiza esta spec antes de implementar.

## Especificacion del comportamiento

- Script de creación con `gcloud`: proyecto, `e2-micro` en `us-central1`, disco estándar de 30 GB o menos, IP estática,
  swap configurado, sistema base y herramientas necesarias según `ADR-025`.
- **Firewall:** solo 80 y 443 (y el acceso de administración que se decida); nada más. Sin PostgreSQL expuesto.
- **Presupuesto:** alerta de presupuesto con umbral bajo configurado desde el primer día.
- Script de destrucción que borra la VM, la IP y las reglas creadas, sin tocar lo que no creó.
- Idempotencia razonable: ejecutarlo dos veces no duplica recursos ni falla sin explicación.
- Prerrequisitos documentados: `gcloud` instalado, facturación habilitada, cómo pasar de la prueba gratuita a cuenta paga
  sin perder la capa gratuita.

## Escenarios

1. Sobre un proyecto limpio, el script deja una VM accesible por SSH con IP estática y swap activo.
2. Un escaneo de puertos desde fuera muestra solo 80/443.
3. La alerta de presupuesto existe y tiene destinatario.
4. El script de destrucción deja el proyecto sin recursos facturables creados por esta iteración.
5. Si falta `gcloud` o la facturación, el script lo dice y sale con código distinto de cero, sin traza.

## Fuera de alcance

Instalar la aplicación (`US-8.6.2`); la elección de la región fuera de EE.UU. (la capa gratuita no la admite).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
