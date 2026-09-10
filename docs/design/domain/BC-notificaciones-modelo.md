# BC Notificaciones — Modelo de Dominio (Event Storming ligero)

> Estado documental: **borrador — pendiente de aprobación explícita de Víctor en el comentario
> de cierre del Issue [#304](https://github.com/vvalotto/cognion/issues/304) (US-5.0.1,
> Iteración 0, Incremento 5).**
> Alcance de este modelo: RF-14 (email de apertura y cierre de una Actividad Evaluativa de
> período abierto). Sin pantalla propia — el email es el único artefacto visible, no requiere
> wireframes.
>
> Fuente: `docs/rf/RF_v1.md` (RF-14), `docs/rf/ARQ_v1.md` (Notificaciones = Generic Subdomain,
> Event-driven; lenguaje ubicuo: Notificación, Canal, Evento de integración), `ADR-006`
> (integración directa Actividad Evaluativa → Notificaciones — decisión de mecanismo ya
> cerrada, este modelo la instancia como puerto+adapter in-process, consistente con
> `CLAUDE.md` "comunicación entre BCs solo por puertos"), `docs/design/domain/
> BC-actividad-evaluativa-modelo.md` (eventos `ActividadEvaluativaCreada`/
> `ActividadEvaluativaCerrada`, campo `comisiones_ids`).
> Decisiones de producto/alcance confirmadas con Víctor 2026-09-10 (§6).

---

## 1. Actores

| Actor | Rol en el BC |
|---|---|
| Sistema (BC Actividad Evaluativa) | Dispara la notificación al crear o cerrar manualmente una Actividad Evaluativa de período abierto — único disparador, sin acción humana directa sobre este BC |
| Estudiante | Destinatario del email — no interactúa con este BC de ninguna otra forma |

Sin actor Docente ni Administrador — este BC no tiene ninguna operación que un usuario invoque
directamente.

---

## 2. Concepto central — BC reactivo sin aggregate propio

Segundo BC del sistema sin aggregate ni invariante de negocio que proteger (el primero fue
Analytics, aunque por un motivo distinto: Analytics es de solo lectura, Notificaciones es
puramente de efecto de borde). No hay estado que mutar ni consulta que resolver — el trabajo de
este BC es **recibir un disparo desde Actividad Evaluativa, resolver destinatarios vía un
puerto propio hacia Identidad, y enviar un email por un canal configurable**.

**Sin persistencia propia** — no se modela una tabla ni aggregate `Notificacion` en base de
datos. El envío es un efecto de borde de una sola vez, sin necesidad de historial ni de
reintentos posteriores a la corrida (§6, decisión de manejo de fallos). Si más adelante se
necesita auditoría de envíos, se agrega como extensión — no se anticipa sin caso de uso real.

**Patrón de integración (`ADR-006` instanciado):** BC Actividad Evaluativa define y posee el
puerto de disparo (`NotificacionPort`, §5) — mismo criterio que otros puertos cruzados ya
existentes en el proyecto (`ComisionConsultaPort` de Banco de Preguntas hacia Identidad,
`EvaluacionConsultaPort` de Identidad hacia Actividad Evaluativa): cada BC consumidor posee su
propio puerto angosto, implementado por un adapter in-process en su propio `frameworks/`, que
en este caso invoca directamente los Use Case de `src/notificaciones/`. Notificaciones, a su
vez, define su **propio** `ComisionConsultaPort` hacia Identidad para resolver el roster y el
email de los estudiantes — no reutiliza el de ningún otro BC (mismo criterio ya aplicado entre
Analytics/Banco de Preguntas/Identidad: cada BC consumidor arma su propia copia del contrato
que necesita).

---

## 3. Eventos consumidos (disparo desde Actividad Evaluativa)

| Evento origen | Cuándo se dispara la notificación | Contenido que Actividad Evaluativa ya tiene en memoria al disparar |
|---|---|---|
| `ActividadEvaluativaCreada` | Al crear la actividad (`CrearActividadPeriodoAbiertoUseCase`) | `actividad_id`, `materia_id`, `titulo`, `fecha_apertura`, `fecha_cierre`, `comisiones_ids` |
| `ActividadEvaluativaCerrada` | Solo cierre manual (`CerrarActividadUseCase`, `US-3.3.2`) — **no** el vencimiento natural de `fecha_cierre` (§6, decisión 1) | `actividad_id`, `materia_id`, `titulo`, `comisiones_ids` — ya disponibles en el aggregate reconstruido por `CerrarActividadUseCase` antes de emitir el evento, sin necesidad de ampliar el schema de `ActividadEvaluativaCerrada` |

No hay notificación de `PeriodoDisponibilidadModificado` ni `TituloActividadModificado` — fuera
de alcance de RF-14, que solo menciona apertura y cierre.

---

## 4. Destinatarios

**Estudiantes de las Comisiones a las que la actividad está restringida** (§6, decisión 2) —
mismo criterio que ya usa el Estudiante para ver la actividad en su portal
(`ActividadEvaluativaPeriodoAbierto.comisiones_ids`, vacío = todas las Comisiones de la
Materia). Se resuelve en Notificaciones, no en Actividad Evaluativa: recibe `materia_id` +
`comisiones_ids` por el puerto de disparo, y arma el roster con su propio
`ComisionConsultaPort` (§5).

Mismo conjunto de destinatarios para apertura y cierre — no se filtra por si el estudiante ya
rindió, se dio de baja u otro estado individual (RF-14 es sobre el ciclo de la actividad, no
sobre el estado de una `Evaluacion` puntual).

---

## 5. Puertos nuevos

### `NotificacionPort` → dueño de BC Actividad Evaluativa

Puerto de **disparo** (no de consulta) — vive en
`src/actividad_evaluativa/entities/ports/notificacion_port.py`, implementado por
`NotificacionPortInProcess` en `src/actividad_evaluativa/frameworks/adapters/` (único punto de
Actividad Evaluativa que importa `src.notificaciones`).

| Método | Cuándo se llama |
|---|---|
| `notificar_apertura(actividad_id, materia_id, materia_nombre, titulo, fecha_apertura, fecha_cierre, comisiones_ids)` | Al final de `CrearActividadPeriodoAbiertoUseCase.execute()`, después de persistir `ActividadEvaluativaCreada` |
| `notificar_cierre(actividad_id, materia_id, materia_nombre, titulo, comisiones_ids)` | Al final de `CerrarActividadUseCase.execute()`, después de persistir `ActividadEvaluativaCerrada` |

`materia_nombre` viaja aparte de `materia_id` en ambos métodos porque Notificaciones no tiene
su propio `MateriaConsultaPort` — quien invoca (`CrearActividadPeriodoAbiertoUseCase`/
`CerrarActividadUseCase`, ambos ya con `MateriaConsultaPort` inyectado) lo resuelve y lo pasa
directo (`US-5.1.2`/`US-5.1.3`).

Ninguno de los dos métodos devuelve nada ni puede propagar una excepción hacia quien lo llama
(§6, decisión 4) — el manejo de fallos de envío se resuelve enteramente del lado de
Notificaciones.

### `ComisionConsultaPort` → dueño de BC Identidad (copia propia de Notificaciones)

Vive en `src/notificaciones/entities/ports/comision_consulta_port.py`, implementado por un
adapter in-process en `src/notificaciones/frameworks/adapters/`.

**Diferencia con la copia ya existente en Analytics/Banco de Preguntas:** ninguna expone el
email del estudiante (`EstudianteResumen` de Identidad y de Analytics solo traen `id`/`nombre`,
pensados para selectores de UI). Este puerto SÍ necesita `email` — puerto nuevo, no basta con
copiar la forma existente.

| Método | Devuelve |
|---|---|
| `listar_comisiones_por_materia(materia_id)` | `list[UUID]` de comisiones activas de la materia — usado solo cuando `comisiones_ids` llega vacío desde el disparo |
| `listar_destinatarios(comision_ids: list[UUID])` | `list[DestinatarioNotificacion]` (`estudiante_id`, `nombre`, `email`) — roster combinado de todas las comisiones indicadas, sin duplicados si un estudiante estuviera en más de una |

### `CanalEnvioPort` → propio de Notificaciones

Vive en `src/notificaciones/entities/ports/canal_envio_port.py` — la abstracción que RF-14
pide ("el canal de notificación debe ser extensible a otros medios en el futuro"). Un único
método:

| Método | Comportamiento |
|---|---|
| `enviar(destinatario_email, asunto, cuerpo) -> None` | Envía el mensaje por el canal concreto. Implementación: `SmtpCanalEnvio` (`frameworks/adapters/`), configurado por variables de entorno (`SMTP_HOST`/`SMTP_PORT`/`SMTP_USER`/`SMTP_PASSWORD`/`SMTP_FROM`, mismo criterio de configuración por entorno que el resto del proyecto, `ARQ_v1.md` "Configuración y secretos"). **Decidido en `US-5.1.1`:** `smtplib` estándar + `asyncio.to_thread` — no `aiosmtplib` (candidata original de este documento) — reutiliza el mismo patrón ya probado en `SmtpNotificador` de Identidad (`ADR-012`) sin sumar una dependencia nueva; los dos adaptadores quedan separados por BC. |

El manejo de fallos (§6, decisión 4) vive en el Use Case que llama a `CanalEnvioPort`, no en el
adapter: cada fallo de envío se captura, se loguea (`logging`, nivel `warning`, incluye
`estudiante_id`/`email`/tipo de notificación) y se continúa con el siguiente destinatario — un
email que falla no aborta el resto del roster ni la operación de dominio que disparó la
notificación.

---

## 6. Hot spots — resueltos con Víctor (2026-09-10)

1. **Qué cuenta como "cierre" para RF-14:** solo el cierre manual del Docente
   (`ActividadEvaluativaCerrada`, `US-3.3.2`). El vencimiento natural de `fecha_cierre` **no**
   dispara notificación de cierre — no requiere ningún cambio en
   `VerificarVencimientosUseCase` ni un evento nuevo a nivel de la Actividad.
2. **Destinatarios de la notificación de apertura (y cierre):** solo los estudiantes de las
   Comisiones a las que la actividad está restringida (`comisiones_ids`, vacío = todas las
   Comisiones de la Materia) — no todos los estudiantes de la Materia sin filtrar.
3. **Canal de envío en este entorno (datos de prueba/locales):** SMTP real de prueba
   (Mailtrap/Mailhog local) — no un adapter mudo que solo loguea, ni un proveedor real con
   destinatarios reales.
4. **Manejo de fallos de envío:** no bloquea — si el email falla, se loguea y la
   creación/cierre de la Actividad se confirma igual. Mismo criterio de "deuda técnica
   consciente" ya aceptado en `ADR-006` para el acoplamiento de la integración.

**Pendiente de definir en la spec de implementación (no bloquea la aprobación del modelo):**
- Contenido exacto del asunto/cuerpo del email (texto plano vs. HTML mínimo, qué datos de la
  actividad incluir) — a resolver en `US-5.1.2`/`US-5.1.3`.
- **Resuelto en `US-5.1.1`:** sin Mailhog/Mailtrap instalado en este entorno de desarrollo —
  la verificación automatizada (unit/integration/BDD) usa un servidor SMTP-stub embebido en
  los propios tests (`tests/integration/inc5/`, `tests/step_defs/inc5/`), sin depender de
  infraestructura externa. Instalar Mailhog real (vía Homebrew, mismo criterio que PostgreSQL)
  queda diferido para cuando haga falta un smoke test manual end-to-end de `US-5.1.2`/`5.1.3`.
- Si `CrearActividadPeriodoAbiertoUseCase`/`CerrarActividadUseCase` acumulan CBO al inyectar
  `NotificacionPort` (mismo patrón de CRITICAL de CBO ya visto repetidamente en el proyecto,
  `US-2.1.2`/`2.1.5`/`2.1.6`/`3.1.3`/`3.2.1`) — a resolver si el pre-push gate lo detecta,
  mismo criterio de separación por responsabilidad ya aplicado en esos casos.

---

## 7. Próximo paso

Modelo completo, sin hot spots de producto abiertos (§6) — pasa a aprobación explícita de
Víctor en el comentario de cierre del Issue #304 (DoD tipo `Modelado`,
`WORKFLOW-DESARROLLO.md` §2). Una vez aprobado, es el input directo de las specs US-IEDD de la
Iteración 1 (`docs/plans/inc5/inc5-candidatas.md`).
