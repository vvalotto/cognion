# Incremento 8 — Despliegue y operación

**Estado: cerrado el 2026-10-31 como `BL-013` (`v0.9.0`, versión local).** El despliegue en la nube quedó diferido y sus 17 Issues están en el Milestone "Incremento 8 — Despliegue en la nube (diferido)" (`.cm/baselines/BL-013-incremento-8-despliegue-y-operacion.md`). Texto histórico a continuación — **en curso desde 2026-10-16.** Iteración 0 (spikes) resuelta: `ADR-021` (Fly.io), `ADR-022` (backup pg_dump → Drive), `ADR-023` (SMTP por materia), `ADR-024` (dominio fly.dev). Iteración 1 (artefacto desplegable) cerrada 2026-10-16: `US-8.1.1` a `US-8.1.7` (PR #535).
**Standby de nube desde 2026-10-17:** las Iteraciones 2 y 3 (CD, staging, rollback, backup en la nube) esperan la decisión sobre el convenio de la Universidad con Google. Mientras tanto se ejecutó la **Iteración 5 — Despliegue local** (cerrada 2026-10-18) y se propone la **Iteración 6 — Despliegue de prueba en GCP con VM gratuita** (ver más abajo).
**Milestone:** [Incremento 8 — Despliegue y operación](https://github.com/vvalotto/cognion/milestone/16)
**Política:** sin BC nuevo ni RF funcional nuevo — no abre con Iteración 0 de Modelado. Abre
con una iteración de **spikes de decisión** (infraestructura, backup, SMTP, dominio), porque
sin ellas el resto no se puede especificar.

## Origen

Los Incrementos 0 a 7 (+ ADJ) construyeron y validaron el producto, pero ninguno definió cómo se
**empaqueta, instala, configura y opera** en un entorno de uso final. Hoy:

- `cd.yml` solo construye la imagen Docker; migraciones, `flyctl deploy` y healthcheck
  post-deploy están comentados.
- `src/app.py` tiene CORS fijo a `http://localhost:5173`; el frontend usa
  `VITE_API_BASE_URL ?? "http://localhost:8000"` (HTTP y WebSocket).
- No hay procedimiento de bootstrap del primer Administrador, ni de backup/restore, ni runbook.
- `docs/plans/CHECKLIST-INSTALACION.md` cubre solo el entorno de **desarrollo**.
- El RNF de Administrabilidad (`RNF_v1.md` Escenario 2: backup mensual, retención 12 meses) y el
  checkpoint de staging del RNF de rendimiento con WSS real (`PROCEDIMIENTO-UAT.md` §4) siguen
  sin cubrir. La decisión de infraestructura de producción (`ARQ_v1.md`) sigue abierta.

Decisión de secuencia a confirmar por Víctor: este incremento va **antes o después de RF-07**
(importación PDF, Incremento 7 Iteración 2). Recomendación: antes de cualquier uso con datos
reales de estudiantes, RF-07 puede ir en paralelo o después.

## Alcance

| # | Iteración | Qué | Track |
|---|---|---|---|
| 0 | Decisiones (spikes) | Infraestructura destino, backup, SMTP real, dominio/TLS | Spike (`tipo:spike`), con Víctor presente |
| 1 | Artefacto desplegable | Configuración por entorno, fail-fast, migraciones, bootstrap de Administrador | Formal (`/implement-us`) |
| 2 | Despliegue automático | CD completo, staging, rollback, checkpoint RNF con WSS real | Formal / infraestructura |
| 3 | Operación | Backup y restore, observabilidad, `downgrade` de migraciones | Formal / infraestructura |
| 4 | Entrega e instalación | Guía de instalación, runbook, ensayo de instalación limpia, cierre | Documentación + UAT |
| 5 | Despliegue local | `ENTORNO=local`, email por consola, scripts de arranque y respaldo (cerrada 2026-10-18) | Formal (tooling) |
| 6 | Despliegue de prueba en GCP | VM gratuita `e2-micro` con aplicación y PostgreSQL juntos, para una prueba de uso (propuesta 2026-10-19) | Spike + formal (tooling e infraestructura) + UAT |

## Iteración 0 — Decisiones

| US | Título | Resuelve |
|---|---|---|
| US-8.0.1 | Spike: destino de despliegue de producción (Fly.io vs servidor FIUNER) | Ítem abierto "Infraestructura definitiva" |
| US-8.0.2 | Spike: estrategia de backup y restauración | RNF Escenario 2 (mensual, 12 meses) |
| US-8.0.3 | Spike: cuenta SMTP real por materia | Ítem abierto "Cuenta de envío SMTP" (RF-14) |
| US-8.0.4 | Spike: dominio, TLS y política de acceso | WSS real, CORS, URL del frontend |

Gate: las cuatro decisiones registradas (ADR donde corresponda) antes de especificar la
Iteración 1 en detalle.

## Iteración 1 — Artefacto desplegable

| US | Título |
|---|---|
| US-8.1.1 | CORS configurable por entorno (`allow_origins` desde settings) |
| US-8.1.2 | URL base de API y WebSocket del frontend resuelta en build (HTTP/HTTPS, WS/WSS) |
| US-8.1.3 | Validación fail-fast de settings de producción (`secret_key`, `database_url`, SMTP) |
| US-8.1.4 | Migraciones Alembic como paso explícito de release (no al arrancar la app) |
| US-8.1.5 | Bootstrap del primer Administrador (comando idempotente, sin contraseña en el repo) |
| US-8.1.6 | Servir el frontend compilado desde el mismo origen (o proxy) y verificarlo en la imagen |
| US-8.1.7 | Cuenta SMTP resuelta por materia con fallback global (`ADR-023`) |

## Iteración 2 — Despliegue automático (EN STANDBY)

> Bloqueada por la decisión de nube (`ADR-021` en revisión). Issues #520–#523 con label `blocked`.

| US | Título |
|---|---|
| US-8.2.1 | CD: migraciones + deploy + healthcheck post-deploy habilitados en `main`/tags |
| US-8.2.2 | Entorno de staging espejo del de producción |
| US-8.2.3 | Rollback: volver a la imagen/versión anterior y a su esquema |
| US-8.2.4 | Checkpoint de staging del RNF de rendimiento (≤100 ms, WSS real) — `PROCEDIMIENTO-UAT.md` §4 |

## Iteración 3 — Operación (parcialmente en standby)

> `US-8.3.1` (#524, backup automático en la nube) bloqueada; `US-8.3.2` a `US-8.3.4` no dependen de la nube. La variante local del backup se resuelve en `US-8.5.4`.

| US | Título |
|---|---|
| US-8.3.1 | Backup automático mensual con retención de 12 meses |
| US-8.3.2 | Restauración probada desde un backup real (ensayo documentado) |
| US-8.3.3 | Observabilidad mínima: logs estructurados y healthcheck de readiness (base de datos) |
| US-8.3.4 | `alembic downgrade base` funcional (FK sin nombre en `estudiante`) |

## Iteración 4 — Entrega e instalación

| US | Título |
|---|---|
| US-8.4.1 | Guía de instalación en el entorno final (reemplaza el alcance "solo desarrollo" del checklist) |
| US-8.4.2 | Runbook operativo: arranque, parada, rotación de secretos, restauración, incidentes |
| US-8.4.3 | Ensayo de instalación limpia desde cero + UAT de despliegue; cierre como `BL-013` |


## Iteración 5 — Despliegue local y prueba con alumnos (se ejecuta antes que la 2 y la 3)

Origen: mientras se decide la nube (convenio de la Universidad con Google), se quiere usar el sistema en
la máquina de Víctor, con alumnos conectándose por la **red local del aula**. Todo lo que se construye acá
sirve igual en cualquier nube (configuración, migraciones, bootstrap, arranque, backup, guía) y además
ensaya la instalación limpia de la `US-8.4.3`.

| US | Título | Issue |
|---|---|---|
| US-8.5.1 | Entorno local: `ENTORNO=local` con secreto fuerte para uso en red | #536 ✅ |
| US-8.5.2 | Canal de email por consola para uso sin SMTP | #537 ✅ |
| US-8.5.3 | Comando único para levantar y detener el despliegue local | #538 ✅ |
| US-8.5.4 | Backup y restauración local probada | #539 ✅ |
| US-8.5.5 | Verificación de la imagen Docker en CI (sin Docker local; no bloquea) | #540 ⛔ desestimada |
| US-8.5.6 | Guía de despliegue local y guion de la prueba con alumnos | #541 ⛔ desestimada (la guía se hizo aparte) |
| US-8.5.7 | Ensayo y prueba en red local con alumnos (UAT) | #542 ⛔ desestimada |

**Estado 2026-10-18:** `US-8.5.1` a `8.5.4` implementadas (PR #544); `US-8.5.5`, `8.5.6` y `8.5.7` **desestimadas por Víctor** (no corresponden ahora). La guía de instalación se escribió igual en `docs/plans/DESPLIEGUE-LOCAL.md`, sin el plan de la clase de prueba con alumnos.

Orden original: 8.5.1 → 8.5.2 → 8.5.3 → 8.5.4 → 8.5.6 → 8.5.7; la 8.5.5 depende de la 8.5.1 y la 8.5.2 y puede ir en paralelo. No se instala Docker Desktop por falta de espacio en la máquina de Víctor (2026-10-17): la imagen se verifica en GitHub Actions.

**Definition of Done de la iteración:** (1) un comando levanta el sistema desde cero en la máquina de Víctor y
queda accesible por IP desde otros dispositivos de la red; (2) existe un backup que se probó restaurar;
(3) ensayo previo con dispositivos reales sin hallazgos 🔴; (4) prueba con alumnos ejecutada y sus hallazgos
registrados en `quality/reports/uat/inc8-local/`.

**Riesgos conocidos:** la red del aula puede aislar clientes entre sí (hay que probar antes con hotspot o
router propio); si la máquina se duerme se cortan las sesiones en vivo; los datos de estudiantes quedan en el
equipo de Víctor (definir con la facultad si la prueba usa cuentas reales o de prueba).

## Definition of Done del incremento

1. Una instalación limpia en el entorno de producción elegido, siguiendo solo la guía, queda
   operativa (primer Administrador incluido) sin tocar código.
2. El deploy desde `main`/tag es automático, con healthcheck y rollback ensayado.
3. Backup mensual en ejecución y una restauración probada de punta a punta.
4. Checkpoint de staging del RNF de rendimiento con WSS real, medido.
5. Quality gates del cierre de baseline y UAT de despliegue sin hallazgos 🔴.

## Fuera de alcance

RF-07 (Iteración 2 del Incremento 7), RF-18 (KPIs históricos), multi-inscripción de
estudiantes, issues de deuda técnica #496–#498 y #500–#502 (se priorizan aparte).

## Iteración 6 — Despliegue de prueba en GCP con VM gratuita (propuesta 2026-10-19)

**Estado:** propuesta con 8 US, pendiente de aprobación de Víctor. Issues #545–#552 y specs en `docs/specs/inc8/US-8.6.1.md` a `US-8.6.8.md` creados el 2026-10-19; `US-8.6.2` a `8.6.8` con label `blocked` hasta cerrar `US-8.6.1`. Reemplaza en la práctica a las
Iteraciones 2 y 3 mientras dure el standby de Fly.io, que no se tocan.

### Origen

El 2026-10-19 Víctor pidió analizar GCP **con su cuenta personal** (`vvalotto@gmail.com`) y eligió la **opción A**: una VM
`e2-micro` de la capa gratuita con la aplicación y PostgreSQL juntos, para una **prueba de uso**. Esta iteración adecua el
despliegue a esa decisión y la valida con mediciones.

Análisis previo (precios y límites de las páginas oficiales al 2026-10-19):
- Capa gratuita: 1 VM `e2-micro` no preemptible por mes solo en `us-west1`, `us-central1` o `us-east1`; 30 GB de disco
  estándar; 1 GB de salida de red por mes; Cloud Storage 5 GB en regiones de EE.UU.
- **Facturación (revisada el 2026-10-23, ver `ADR-025`):** la cuenta de facturación de Víctor es **paga y sin créditos**: el `Free Trial`
  de 300 USD venció el 15 de octubre de 2021 sin usarse y no hay otro. La VM `e2-micro` sigue siendo gratuita por la capa permanente,
  pero todo lo que la supere se cobra desde el primer día; hay un presupuesto de alerta existente (monto 0 USD) y la consola ofrece
  límites de inversión que pausan servicios, a evaluar.
- Opción B descartada por ahora: Cloud Run con CPU siempre asignada y una sola instancia, más Cloud SQL. Unos 45–50 USD por
  mes de Cloud Run (estimación) más 8 a 26 USD de Cloud SQL, sin SLA en las instancias compartidas.

### Restricciones del sistema que condicionan el diseño

- **Una sola instancia y un solo proceso:** el canal WebSocket vive en memoria y el `VerificadorDeVencimientos` corre como
  tarea de fondo en el `lifespan`. No se escala horizontalmente.
- **El artefacto ya existe:** la imagen sirve interfaz y API desde un mismo origen (`US-8.1.6`) y se configura solo por
  variables de entorno (`US-8.1.1` a `8.1.7`). Las migraciones son un paso explícito (`US-8.1.4`).
- **Reutilizable de la Iteración 5:** `ENTORNO=local`, `EMAIL_MODO`, `respaldar.sh` y `restaurar.sh`.

### Riesgos que la iteración debe medir (no suponer)

1. **CPU compartida:** una `e2-micro` sostiene solo una fracción de vCPU. El hash bcrypt de 30 a 60 logins simultáneos al
   empezar una clase puede saturarla.
2. **1 GB de RAM** para la aplicación, PostgreSQL y el proxy; hace falta swap y ajustar PostgreSQL.
3. **Región solo en EE.UU.:** la latencia desde Argentina no está medida. El RNF de 100 ms es del servidor (p95 de 43,81 ms
   en la Mac de Víctor), no de la red.
4. **Datos de alumnos en una cuenta personal de Gmail:** decisión institucional, no técnica.
5. **Un solo punto de falla:** sin SLA; PostgreSQL lo operamos nosotros.

### US

Ocho US, en este orden. La primera es un spike con Víctor presente; el resto se especifica y se implementa después de su
gate. **Replanificada el 2026-10-23:** antes de automatizar nada se escribe un plan de instalación y se ejecuta a mano (`US-8.6.3`),
porque los scripts (`US-8.6.4`) deben nacer de comandos que ya funcionaron; el runbook (`US-8.6.6`) parte de ese plan. Se agruparon las piezas que solo se pueden probar juntas (respaldo con restauración, despliegue con rollback, runbook
con su ensayo) y se quitaron como US la observabilidad (basta la alerta de presupuesto y leer el log) y el cierre (es parte
de cerrar la iteración, no una historia). Versión inicial con 17 US reducida a 8 por pedido de Víctor el 2026-10-19.

| US | Título | Contenido |
|---|---|---|
| US-8.6.1 (#545) | Spike: decisiones del despliegue de prueba (produce `ADR-025`) | **Gate** de toda la iteración. Cuatro decisiones: (1) dominio y HTTPS sin dominio propio (subdominio gratuito de DuckDNS, `sslip.io`, túnel de Cloudflare o dominio propio); (2) modo de email y `ENTORNO` para una prueba expuesta a internet (`EMAIL_MODO=consola` deja tokens en el log y se rechaza en staging/producción: SMTP real con `ENTORNO=staging`, o `ENTORNO=local` aceptando el riesgo en una prueba acotada); (3) contenedores o procesos nativos en 1 GB de RAM (Docker agrega consumo fijo; nativo lo ahorra pero pierde la paridad con la imagen); (4) alcance de datos y cuenta de la prueba (¿cuentas reales o de prueba?, ¿qué se avisa a los alumnos?, ¿cuenta personal o institucional?, ¿cuándo pasar a cuenta paga?). `ADR-021` y `ADR-024` quedan anotados con su relación al nuevo ADR. Si llega antes la respuesta de la Universidad sobre el convenio con Google, se reevalúa acá |
| US-8.6.2 (#546) | Composición de servicios y configuración de la VM | Aplicación, PostgreSQL y proxy HTTPS; límites de memoria, ajuste de PostgreSQL, rotación de logs, reinicio automático; carga de secretos (archivo con permisos 600) y bootstrap del primer Administrador |
| US-8.6.3 (#547) | Plan de instalación y prueba manual del despliegue en GCP | Se escribe `docs/plans/DESPLIEGUE-GCP.md` (pasos con comandos, resultado esperado, puertas de confirmación antes de crear recursos o generar costo, quién hace cada cosa, control de costos y desmontaje) y se revisa con Víctor; después se **ejecuta a mano**, paso a paso, con bitácora y mediciones tempranas. Incluye: proyecto nuevo `cognion-prueba`, presupuesto propio y evaluación de los límites de inversión, VM `e2-micro`, imagen con Cloud Build, Docker en la VM, DuckDNS con HTTPS real. Verifica lo que `US-8.6.2` dejó pendiente (memoria total, certificado real, puerto de PostgreSQL desde internet) |
| US-8.6.4 (#548) | Scripts de aprovisionamiento, publicación y despliegue con rollback | Codifican lo que funcionó en la prueba manual: creación y destrucción de la VM con `gcloud` (firewall solo 80/443, IP siempre asignada, swap, presupuesto), publicación de la imagen desde CI o Cloud Build según lo aprendido, y despliegue en la VM con migraciones, `/api/health` y vuelta a la versión anterior si falla |
| US-8.6.5 (#549) | Backup a Cloud Storage con restauración ensayada | Reutiliza `respaldar.sh`; destino dentro de los 5 GB gratuitos; retención de 12 meses (`ADR-022`); respaldo antes y después de cada clase; restauración completa desde un respaldo real en la VM, documentada |
| US-8.6.6 (#550) | Runbook operativo y ensayo de instalación limpia | Parte del plan de `US-8.6.3`: arranque, parada, actualización, rotación de secretos, restauración e incidentes; se valida reconstruyendo desde cero con los scripts de `US-8.6.4` y siguiendo solo el runbook |
| US-8.6.7 (#551) | Mediciones en la VM con criterios de go/no-go | Ver criterios abajo |
| US-8.6.8 (#552) | Prueba de uso y cierre de la iteración | Prueba con alumnos según lo decidido en `US-8.6.1`, registro de hallazgos, `DesignReviewer`, actualización de `CLAUDE.md` y de este plan. El cierre de baseline del Incremento 8 sigue siendo `BL-013` |

### Criterios de go/no-go de `US-8.6.7` (propuestos, a confirmar con Víctor)

| Medición | Criterio |
|---|---|
| 60 logins simultáneos en un minuto | 0 errores y p95 < 3 s |
| Sesión en vivo con 60 participantes | p95 de `CerrarPreguntaActual` < 100 ms en el servidor (RNF) |
| Memoria | < 80 % de 1 GB sostenida; sin cierres por falta de memoria |
| Reinicio de la VM | el sistema vuelve solo en menos de 3 minutos |
| Latencia desde Argentina | se mide y se registra (informativo) |
| Respaldo y restauración | restauración completa exitosa en la VM |

Si algún criterio falla: se registra el resultado y se decide entre una VM paga más grande o la opción B (Cloud Run + Cloud
SQL) en un ADR nuevo. La imagen es la misma, así que el código no cambia.

### Relación con el resto del Incremento 8

- `US-8.2.1` a `8.2.4` y `8.3.1` (Fly.io, Issues #520–#524) **siguen en standby**. Si se adopta GCP de forma definitiva, se
  reemplazan o se marcan como desestimadas en el cierre.
- `US-8.4.1` a `8.4.3` (guía, runbook, ensayo de instalación limpia) se **solapan** con `US-8.6.6` y `US-8.6.7`; al cierre se
  decide cuáles se dan por cubiertas.
- Pendiente fuera de este plan: la respuesta de la Universidad sobre el convenio con Google.

### Ítems abiertos

- Confirmar los criterios de go/no-go.
- Tarifa de salida de red por encima del 1 GB gratuito: verificar antes de la prueba con alumnos.

## Iteración 7 — Versión de producción local (`v0.9.0`)

**Decisión de Víctor, 2026-10-24:** la Iteración 6 queda en pausa (el costo de la nube lo desaconseja por ahora). La primera versión de producción corre **en su Mac, sin nube**, con `scripts/local/`; después se usará temporalmente su GCP con los scripts de `US-8.6.4`. Número `v0.9.0` (no `v1.0.0`: faltan RF-07, RF-18 y la prueba en la red del aula). Cierre como `BL-013`. Las preguntas no se versionan: Víctor genera los archivos JSON.

| US | Título | Alcance |
|---|---|---|
| US-8.7.1 (#564) | Carga de datos iniciales (materias y preguntas) desde archivos JSON o Markdown | Comando idempotente que usa los casos de uso del Banco de Preguntas; lee también los 17 cuestionarios `.md` de Gestión de Proyectos (340 preguntas); formato en la spec |

**Gates antes de etiquetar:** instalación limpia en la Mac (base vacía, `levantar.sh`, carga, login), un ciclo de `respaldar.sh`/`restaurar.sh` con esos datos, `DESPLIEGUE-LOCAL.md` y `CHANGELOG` al día, y el procedimiento completo de cierre de baseline.

## Iteración 8 — Ajustes de la UAT de `v0.9.0`

**Origen:** UAT `US-8.7.2` (2026-10-25, `quality/reports/uat/inc8/`): 10 hallazgos y un plan de corrección **aprobado por Víctor**. **Decisiones de Víctor, 2026-10-26:** todo se resuelve **antes de etiquetar `v0.9.0`** (los 🔴 y los 🟡/⚪); el bootstrap que pide la contraseña dos veces se hace ahora (`US-ADJ-65`); en el hallazgo #6, los formularios de cargar y editar pregunta cambian igual que los filtros; los pasos van en el orden de abajo. Pocas US formales; lo que solo toca `frontend/`, scripts o documentación va por el track informal (sin spec ni `/implement-us`).

| Paso | Qué | Hallazgos | Track |
|---|---|---|---|
| 1 | **Fechas con zona horaria** en `NuevaActividad` y `ExtenderPlazo`: enviar la fecha con su zona; verificar con la hora real que un parcial de 14:00 a 16:00 queda de 14:00 a 16:00 | #7 🔴 | Informal (`frontend/`) |
| 2 | **`US-ADJ-64`** (#570): `configurar_logging()` al arrancar; los emails de consola salen en el log; `token=` enmascarado en el log de acceso | #2 🔴, #9 🟡 | Formal (`src/`) |
| 3 | **`US-ADJ-65`** (#571): `bootstrap_administrador` pide la contraseña dos veces (hasta 3 intentos) | #3 🟡 | Formal (`src/`) |
| 4 | **Prueba del iPhone con Norton Mobile Security pausado** (la hace Víctor). Si anda: línea en la guía, #8 pasa a 🟡 de entorno. Si no: `US-ADJ-66` (el servidor acepta la forma absoluta del pedido WebSocket) | #8 🔴→🟡 | Condicional |
| 5 | **Repetir los pasos afectados de la UAT**: C4, C7, D1 (emails y fechas), D5 con el iPhone si cambió algo | #2, #7, #8 | UAT |
| 6 | **Lote UX informal** — antes, actualizar los wireframes (gate UX) y que Víctor los apruebe: Unidad temática → Tema dependientes con "Todos" en los filtros del banco, en "Nueva actividad" y en cargar/editar pregunta; "repetir email" en el autoregistro; título de la pestaña "Cognión" | #6, #5, #1 | Informal (`frontend/`) |
| 7 | **Lote documentación y scripts**: advertencia del link de invitación en `DESPLIEGUE-LOCAL.md`, prefijo del respaldo con el nombre de la base, fila de `DESPLIEGUE-GCP.md` en los índices | #4, #10 | Informal |

**Gates antes de etiquetar `v0.9.0`:** los pasos 1 a 7 hechos o reclasificados con decisión de Víctor, la UAT repetida en lo afectado, `CHANGELOG` y `DESPLIEGUE-LOCAL.md` al día, y el procedimiento completo de cierre de `BL-013`.

