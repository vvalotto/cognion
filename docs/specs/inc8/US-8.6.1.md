# US-8.6.1: Spike: decisiones del despliegue de prueba (ADR-025)

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `spike (decisión, sin código de producción)`
**Bounded Context**: transversal
**Issue**: #545

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso en GCP**,
quiero **decidir de una vez, con la evidencia a la vista, las cuatro cuestiones que condicionan el resto del despliegue**,
para **que el resto de la iteración se especifique sin ambigüedades y quede registrado el porqué**.

---

## Contexto

La opción A (VM `e2-micro` gratuita con la aplicación y PostgreSQL juntos, cuenta personal) está elegida; ver
`docs/plans/inc8/inc8-candidatas.md` §Iteración 6. Las cuatro decisiones de abajo bloquean `US-8.6.2` a `US-8.6.8`.
Se resuelven **con Víctor presente**. `ADR-021` y `ADR-024` (Fly.io) están en revisión y no se reemplazan acá: se anotan.

## Especificacion del comportamiento

El resultado es `docs/adr/ADR-025-despliegue-de-prueba-en-gcp.md` (estado `Aceptado`) con estas decisiones y su razón:

1. **Dominio y HTTPS sin dominio propio.** Opciones a evaluar: subdominio gratuito de DuckDNS con certificado automático,
   `sslip.io`, túnel de Cloudflare, dominio propio. Criterios: costo cero, estabilidad de la URL, certificado válido
   para WSS, y que no dependa de abrir puertos más que 80/443. Se verifican límites vigentes de cada una antes de decidir.
2. **Modo de email y `ENTORNO`.** `EMAIL_MODO=consola` deja tokens de recuperación en el log y se rechaza en
   `staging`/`produccion`. Opciones: SMTP real con `ENTORNO=staging`, o `ENTORNO=local` aceptando el riesgo en una prueba
   acotada. Decide también qué cuenta SMTP se usa (`ADR-023`) si se elige SMTP real.
3. **Contenedores o procesos nativos en 1 GB de RAM.** Medir o estimar el consumo fijo de Docker frente a la paridad con
   la imagen que ya se construye en CI. Decide cómo se arranca la aplicación en la VM.
4. **Alcance de datos y cuenta.** ¿Cuentas reales o de prueba? ¿Qué se avisa a los alumnos? ¿Cuenta personal o
   institucional? ¿Cuándo pasar a cuenta paga para conservar la capa gratuita tras los 90 días de prueba?

Además registra los **criterios de go/no-go** de `US-8.6.7` confirmados por Víctor y la **tarifa de salida de red** por
encima del 1 GB mensual gratuito, hoy sin verificar.

## Escenarios

1. Las cuatro decisiones figuran en `ADR-025` con la opción elegida, las descartadas y la razón.
2. `ADR-021` y `ADR-024` quedan anotados con su relación al nuevo ADR (siguen en revisión, no se borran).
3. Los criterios de go/no-go quedan confirmados o corregidos por Víctor.
4. Las Issues #546 a #552 se actualizan quitando `blocked` y, si hace falta, ajustando su spec.

## Fuera de alcance

Implementar nada de lo decidido; elegir entre GCP y otro proveedor (ya decidido: GCP, opción A).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
