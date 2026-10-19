# Incremento 8-ADJ — Despliegue de prueba en GCP (VM gratuita)

**Estado:** propuesto 2026-10-19, pendiente de aprobación de Víctor. Sin Milestone, Issues ni specs todavía.
**Milestone:** a crear al aprobar este plan.
**Política:** mismo criterio de nomenclatura que `Incremento 3-ADJ` a `7-ADJ` — ajuste insertado fuera de la
secuencia numérica de `docs/rf/PLAN_v1.md`, sin renumerar. Las US siguen la numeración corrida de los
ajustes (`US-ADJ-63` en adelante). Sin RF nuevo ni BC nuevo: no abre con Iteración 0 de Modelado, sino de **decisiones**.

## Origen

El Incremento 8 dejó en standby la nube (Iteraciones 2 y 3) mientras se esperaba el convenio de la Universidad con
Google (`ADR-021`/`ADR-024` en revisión). El 2026-10-19 Víctor pidió analizar GCP **con su cuenta personal**
(`vvalotto@gmail.com`) y eligió la **opción A**: una VM `e2-micro` de la capa gratuita con la aplicación y PostgreSQL
juntos, para una **prueba de uso**. Este incremento adecua el despliegue a esa decisión y la valida con mediciones.

Análisis previo (precios y límites de las páginas oficiales al 2026-10-19):
- Capa gratuita: 1 VM `e2-micro` no preemptible por mes solo en `us-west1`, `us-central1` o `us-east1`; 30 GB de disco
  estándar; 1 GB de salida de red por mes; Cloud Storage 5 GB en regiones de EE.UU.
- Prueba gratuita de 300 USD por 90 días con tarjeta. Si no se pasa a cuenta paga, al vencer se apagan los recursos y
  tras 30 días de gracia se borran. Para conservar la capa gratuita hay que pasar a cuenta paga.
- Alternativa descartada por ahora (opción B): Cloud Run con CPU siempre asignada y una sola instancia, más Cloud SQL.
  Unos 45–50 USD por mes de Cloud Run (estimación) más 8 a 26 USD de Cloud SQL, sin SLA en las instancias compartidas.

## Restricciones del sistema que condicionan el diseño

- **Una sola instancia y un solo proceso:** el canal WebSocket vive en memoria y el `VerificadorDeVencimientos`
  corre como tarea de fondo en el `lifespan`. No se escala horizontalmente.
- **El artefacto ya existe:** la imagen Docker sirve interfaz y API desde un mismo origen (`US-8.1.6`) y se configura
  solo por variables de entorno (`US-8.1.1` a `8.1.7`). Las migraciones son un paso explícito (`US-8.1.4`).
- **Reutilizable de la Iteración 5 del Incremento 8:** `ENTORNO=local`, `EMAIL_MODO`, `respaldar.sh`/`restaurar.sh`.

## Riesgos que el incremento debe medir (no suponer)

1. **CPU compartida:** una `e2-micro` sostiene solo una fracción de vCPU. El hash bcrypt de 30 a 60 logins
   simultáneos al empezar una clase puede saturarla.
2. **1 GB de RAM** para la aplicación, PostgreSQL y el proxy; hace falta swap y ajustar PostgreSQL.
3. **Región solo en EE.UU.:** la latencia desde Argentina no está medida. El RNF de 100 ms es del servidor
   (p95 de 43,81 ms en la Mac de Víctor), no de la red.
4. **Datos de alumnos en una cuenta personal de Gmail:** decisión institucional, no técnica (ver Iteración 0).
5. **Un solo punto de falla:** sin SLA; PostgreSQL lo operamos nosotros.

## Alcance

| # | Iteración | Qué | Track |
|---|---|---|---|
| 0 | Decisiones | Dominio/HTTPS, modo de email, contenedores vs. procesos, datos de la prueba | Spike con Víctor presente; cierra con `ADR-025` |
| 1 | Artefacto y VM | Composición de servicios, aprovisionamiento reproducible, imagen publicada, despliegue y rollback | Formal (tooling e infraestructura) |
| 2 | Operación | Backup a Cloud Storage con restauración ensayada, observabilidad mínima, runbook | Formal / documentación |
| 3 | Ensayo y cierre | Instalación limpia, mediciones con criterios de go/no-go, prueba de uso, baseline | UAT |

## Iteración 0 — Decisiones (spikes)

| US | Título | Resuelve |
|---|---|---|
| US-ADJ-63 | Spike: dominio y HTTPS sin dominio propio | `ADR-024` (hoy atado a `fly.dev`). Opciones: subdominio gratuito de DuckDNS, `sslip.io`, túnel de Cloudflare, dominio propio |
| US-ADJ-64 | Spike: modo de email y `ENTORNO` para una prueba expuesta a internet | `EMAIL_MODO=consola` deja tokens en el log y se rechaza en staging/producción. Opciones: SMTP real con `ENTORNO=staging`, o `ENTORNO=local` aceptando el riesgo en una prueba acotada |
| US-ADJ-65 | Spike: contenedores o procesos nativos en 1 GB de RAM | Docker agrega consumo fijo; procesos nativos lo ahorran pero pierden la paridad con la imagen |
| US-ADJ-66 | Spike: alcance de datos y cuenta de la prueba | ¿Cuentas reales o de prueba?, ¿qué se avisa a los alumnos?, ¿cuenta personal o institucional?, ¿cuándo pasar a cuenta paga? |

Gate: las cuatro decisiones registradas en `ADR-025` antes de especificar la Iteración 1. `ADR-021` y `ADR-024`
quedan anotados con la relación al nuevo ADR. Si la respuesta de la Universidad sobre el convenio llega antes,
se reevalúa en este punto.

## Iteración 1 — Artefacto y VM

| US | Título |
|---|---|
| US-ADJ-67 | Composición de servicios para la VM: aplicación, PostgreSQL y proxy HTTPS; límites de memoria, ajuste de PostgreSQL, rotación de logs, reinicio automático |
| US-ADJ-68 | Aprovisionamiento reproducible de la VM con `gcloud`: `e2-micro` en `us-central1`, disco, IP estática, reglas de firewall (solo 80/443; sin PostgreSQL expuesto), swap, alerta de presupuesto |
| US-ADJ-69 | Publicar la imagen en un registro desde CI al crear una etiqueta `v*.*.*`, reemplazando el `build` solitario de `cd.yml` (los pasos de Fly.io quedan comentados) |
| US-ADJ-70 | Despliegue y rollback en la VM: bajar la imagen, aplicar migraciones, reiniciar, verificar `/api/health`, y volver a la versión anterior si falla |
| US-ADJ-71 | Bootstrap del primer Administrador y carga de secretos en la VM (archivo con permisos 600) |

## Iteración 2 — Operación

| US | Título |
|---|---|
| US-ADJ-72 | Backup automático a Cloud Storage (dentro de los 5 GB gratuitos) reutilizando `respaldar.sh`, con retención de 12 meses (`ADR-022`) y respaldo antes y después de cada clase |
| US-ADJ-73 | Restauración ensayada desde un respaldo real en la VM, documentada |
| US-ADJ-74 | Observabilidad mínima: verificación externa de disponibilidad, alerta de disco/memoria y de presupuesto, logs consultables |
| US-ADJ-75 | Runbook operativo de la VM: arranque, parada, actualización, rotación de secretos, restauración e incidentes |

## Iteración 3 — Ensayo y cierre

| US | Título |
|---|---|
| US-ADJ-76 | Ensayo de instalación limpia desde cero siguiendo solo el runbook |
| US-ADJ-77 | Mediciones en la VM con criterios de go/no-go (ver abajo) |
| US-ADJ-78 | Prueba de uso con alumnos según lo decidido en `US-ADJ-66` y registro de hallazgos |
| US-ADJ-79 | Cierre: baseline, `DesignReviewer`, actualización de `CLAUDE.md`, matriz y `CHANGELOG.md` |

### Criterios de go/no-go de `US-ADJ-77` (propuestos, a confirmar con Víctor)

| Medición | Criterio |
|---|---|
| 60 logins simultáneos en un minuto | 0 errores y p95 < 3 s |
| Sesión en vivo con 60 participantes | p95 de `CerrarPreguntaActual` < 100 ms en el servidor (RNF) |
| Memoria | < 80 % de 1 GB sostenida; sin cierres por falta de memoria |
| Reinicio de la VM | el sistema vuelve solo en menos de 3 minutos |
| Latencia desde Argentina | se mide y se registra (informativo) |
| Respaldo y restauración | restauración completa exitosa en la VM |

Si algún criterio falla: se registra el resultado y se decide entre una VM paga más grande o la opción B (Cloud Run +
Cloud SQL) en un ADR nuevo. La imagen es la misma, así que el código no cambia.

## Relación con el Incremento 8

- `US-8.2.1` a `8.2.4` y `8.3.1` (Fly.io, Issues #520–#524) **siguen en standby**; este incremento no las toca.
  Si se adopta GCP de forma definitiva, se reemplazan o se marcan como desestimadas en el cierre.
- `US-8.4.1` a `8.4.3` (guía, runbook, ensayo de instalación limpia) se **solapan** con las Iteraciones 2 y 3 de este
  incremento; al cierre se decide cuáles se dan por cubiertas.
- Pendiente fuera de este plan: la respuesta de la Universidad sobre el convenio con Google.

## Ítems abiertos

- Confirmar el nombre del incremento (`8-ADJ`) o preferir otro.
- Confirmar los criterios de go/no-go.
- Tarifa de salida de red por encima de 1 GB gratuito: verificar antes de la prueba con alumnos.
