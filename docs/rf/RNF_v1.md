# Atributos de Calidad — Cognión

> Versión: RNF_v1  
> Fecha: 2026-07-08  
> Estado: borrador verificado

---

## Atributos priorizados

| # | Atributo | Prioridad | Descripción breve |
|---|----------|-----------|-------------------|
| 1 | Rendimiento | Alta | El ranking en vivo debe percibirse como instantáneo para todos los participantes simultáneos. |
| 2 | Disponibilidad | Alta | El sistema no puede fallar durante sesiones en vivo ni en ventanas de parcial/final sin plan de contingencia. |
| 3 | Confiabilidad | Alta | Las respuestas de un examen deben persistirse ante cualquier interrupción; el set de preguntas es inmutable. |
| 4 | Seguridad | Media | Control de roles suficiente para el contexto académico; sin mecanismos adicionales de ocultamiento. |
| 5 | Usabilidad | Media | Interfaz responsive en todos los dispositivos y browsers; texto legible en proyección de aula. |
| 6 | Mantenibilidad | Media | El sistema debe poder extenderse (nuevos tipos de pregunta) sin modificar la lógica central. |
| 7 | Observabilidad | Media | Event sourcing como mecanismo de registro; healthcheck para monitoreo proactivo. |
| 8 | Administrabilidad | Media | Deployment automático vía CI/CD; backups mensuales con retención de 12 meses. |

---

## Escenarios de calidad

### Rendimiento

**Escenario 1 — Actualización del ranking en sesión en vivo**
- **Contexto:** Sesión en vivo activa con hasta 60 alumnos respondiendo simultáneamente.
- **Estímulo:** El docente cierra una pregunta; todos los clientes conectados esperan el ranking actualizado.
- **Respuesta esperada:** El servidor calcula el ranking y hace broadcast a todos los clientes conectados.
- **Expectativa PO:** El ranking aparece en pantalla en un tiempo percibido como instantáneo por un usuario promedio — menos de 1 segundo desde el cierre de la pregunta.
- **Factibilidad arquitecto:** El procesamiento server-side (cálculo + broadcast) debe consumir como máximo el 10% del tiempo de respuesta percibido por el usuario — es decir, ≤ 100ms. La latencia de red de cada cliente es del entorno y no es garantizable por el sistema.
- **Medida acordada:** Procesamiento server-side ≤ 100ms; tiempo percibido por el usuario < 1 segundo (el delta lo absorbe la red y el rendering del cliente).

---

### Disponibilidad

**Escenario 1 — Caída durante sesión en vivo**
- **Contexto:** Sesión en vivo activa con alumnos conectados durante clase.
- **Estímulo:** El sistema deja de responder inesperadamente.
- **Respuesta esperada:** El sistema intenta recuperarse automáticamente (según el mecanismo del proveedor de hosting). El docente espera.
- **Expectativa PO:** Si el sistema no levanta en 5 minutos, la sesión se cancela y el docente continúa la clase con otro recurso.
- **Factibilidad arquitecto:** Depende del SLA del proveedor de hosting (decisión de infraestructura pendiente). El sistema debe exponer un healthcheck para que el docente pueda verificar el estado sin depender de reportes de alumnos.
- **Medida acordada:** Ventana de tolerancia de 5 minutos antes de cancelar la sesión en vivo. Healthcheck disponible como endpoint del sistema.

**Escenario 2 — Caída durante período abierto de parcial/final**
- **Contexto:** Sesión de período abierto activa con ventana de tiempo definida (ej. 2 horas de parcial).
- **Estímulo:** El sistema no está disponible durante parte de la ventana.
- **Respuesta esperada:** Cuando el sistema vuelve, el docente extiende el plazo de cierre de la sesión para compensar el tiempo perdido (RF-11b).
- **Expectativa PO:** La contingencia se maneja operativamente — no se requiere recuperación automática del estado. El sistema debe permitir modificar el período de disponibilidad de una sesión activa.
- **Factibilidad arquitecto:** RF-11b ya contempla la modificación del período de disponibilidad post-creación. La responsabilidad de la caída recae en el proveedor de hosting.
- **Medida acordada:** El sistema permite modificar la fecha/hora de cierre de una sesión activa (RF-11b). La disponibilidad del servicio depende del SLA del proveedor.

---

### Confiabilidad

**Escenario — Interrupción durante sesión de período abierto**
- **Contexto:** Un alumno está cursando un examen en modalidad período abierto, habiendo confirmado respuestas parciales.
- **Estímulo:** El alumno pierde conexión, cierra el browser accidentalmente, o el dispositivo se reinicia.
- **Respuesta esperada:** Las respuestas ya confirmadas quedan persistidas en el servidor. Al reconectarse dentro del período de disponibilidad, el alumno retoma desde donde estaba. El set de preguntas es el mismo que recibió al iniciar.
- **Expectativa PO:** Ninguna respuesta confirmada puede perderse. El alumno no puede explotar la desconexión para obtener un nuevo set de preguntas.
- **Factibilidad arquitecto:** Persistencia respuesta por respuesta en base de datos al momento de confirmación. El set de preguntas se cachea al inicio de la sesión y es inmutable. Sin PWA — el sistema es exclusivamente online; la reconexión presupone disponibilidad del servidor.
- **Medida acordada:** Cero pérdida de respuestas confirmadas ante reconexión. El set de preguntas es fijo desde el inicio de la sesión (invariante de negocio).

---

### Seguridad

**Escenario — Control de acceso por rol**
- **Contexto:** Cualquier operación en el sistema.
- **Estímulo:** Un actor intenta acceder a funcionalidades fuera de su rol (ej. un alumno intenta ver el banco de preguntas o los analytics del docente).
- **Respuesta esperada:** El sistema deniega el acceso y retorna un error apropiado.
- **Expectativa PO:** El control de roles es suficiente para el contexto académico — no se requieren mecanismos adicionales de seguridad.
- **Factibilidad arquitecto:** RBAC estándar con tres roles (administrador, docente, estudiante). Autenticación con JWT. Validación de rol en cada endpoint del servidor.
- **Medida acordada:** Ningún actor puede acceder a recursos fuera de su rol. Verificable por revisión de la API.

---

### Usabilidad

**Escenario 1 — Acceso desde dispositivos de alumnos**
- **Contexto:** Alumno participa en una sesión desde su dispositivo personal durante clase.
- **Estímulo:** El alumno accede a la plataforma desde cualquier dispositivo (PC, tablet, smartphone) con cualquier browser vigente.
- **Respuesta esperada:** La interfaz se adapta al dispositivo y es completamente funcional.
- **Expectativa PO:** Compatible con PCs, tablets y smartphones usando elementos estándar de renderización en todos los browsers vigentes.
- **Factibilidad arquitecto:** Diseño responsive estándar con HTML/CSS/JS sin dependencias de tecnologías propietarias.
- **Medida acordada:** La interfaz es funcional sin degradación en los browsers vigentes (Chrome, Firefox, Safari, Edge) en dispositivos de cualquier tamaño.

**Escenario 2 — Proyección en el aula (interfaz del docente)**
- **Contexto:** El docente proyecta la pantalla de la plataforma en el aula durante una sesión en vivo.
- **Estímulo:** Los alumnos intentan leer el contenido proyectado desde sus asientos.
- **Respuesta esperada:** El texto y los elementos clave son legibles desde cualquier punto del aula.
- **Expectativa PO:** Legibilidad completa en toda el aula — criterio mínimo no negociable.
- **Factibilidad arquitecto:** A definir en la etapa de diseño UX (tamaño de fuente mínimo, contraste, layout de pantalla proyectada).
- **Medida acordada:** ⚠️ Ítem abierto: el criterio de legibilidad se especifica en la etapa de diseño UX.

---

### Mantenibilidad

**Escenario — Incorporación de un nuevo tipo de pregunta**
- **Contexto:** El docente decide incorporar un nuevo tipo de pregunta después de la versión inicial.
- **Estímulo:** El desarrollador inicia la implementación del nuevo tipo.
- **Respuesta esperada:** El sistema permite incorporar el nuevo tipo sin modificar la lógica central de sesiones, scoring ni analytics.
- **Expectativa PO:** El cambio no debería tomar más de una jornada de desarrollo (≤ 1 día) una vez definida la lógica del nuevo tipo.
- **Factibilidad arquitecto:** ⚠️ Ítem abierto: depende de que el tipo de pregunta esté modelado de forma polimórfica en el dominio. Esto emergirá del modelo de dominio durante el diseño.
- **Medida acordada:** ⚠️ Ítem abierto: requiere decisión de diseño sobre el modelo de tipos de pregunta antes de que pueda validarse esta medida.

---

### Observabilidad

**Escenario — Diagnóstico post-incidente**
- **Contexto:** Ocurrió un error o comportamiento inesperado durante una sesión.
- **Estímulo:** El desarrollador necesita entender qué pasó (quién se conectó, cuándo, qué falló).
- **Respuesta esperada:** El sistema tiene registros de eventos suficientes para reconstruir la secuencia de hechos.
- **Expectativa PO:** Poder consultar logs de errores, historial de conexiones y métricas de uso de sesiones de forma diferida (no en tiempo real).
- **Factibilidad arquitecto:** Event sourcing como mecanismo de registro — se generan eventos del sistema que alimentan read models para consulta. Healthcheck expuesto como endpoint para monitoreo proactivo.
- **Medida acordada:** El sistema registra mediante eventos: errores del sistema, conexiones de usuarios (quién, duración) y actividad de sesiones. El healthcheck es consultable sin autenticación.

---

### Administrabilidad

**Escenario 1 — Deployment de nueva versión**
- **Contexto:** El desarrollador tiene cambios listos para producción.
- **Estímulo:** Se hace push a la rama main del repositorio.
- **Respuesta esperada:** El sistema despliega automáticamente la nueva versión.
- **Expectativa PO:** El proceso de deployment no requiere intervención manual.
- **Factibilidad arquitecto:** CI/CD conectado al repositorio (GitHub Actions u equivalente según el proveedor de hosting elegido).
- **Medida acordada:** Push a main desencadena deployment automático sin intervención manual.

**Escenario 2 — Backup y recuperación de datos**
- **Contexto:** Se necesita restaurar datos ante pérdida o corrupción.
- **Estímulo:** El desarrollador detecta pérdida de datos y necesita restaurar desde backup.
- **Respuesta esperada:** Existe un backup reciente que permite restaurar el estado del sistema.
- **Expectativa PO:** Backups automáticos mensuales con retención de 12 meses. Pérdida máxima aceptable: datos del mes en curso.
- **Factibilidad arquitecto:** Depende del mecanismo de backup disponible en el proveedor de hosting elegido.
- **Medida acordada:** Backup automático mensual; retención de 12 meses (12 backups disponibles en todo momento).

---

## Restricciones técnicas o de entorno

- **Sistema exclusivamente online** — *Razón:* PWA descartado por complejidad no justificada en el contexto de uso. Las sesiones en vivo son gamificadas y requieren conexión activa; las sesiones de período abierto también son online.
- **Infraestructura: pendiente de decisión** — *Razón:* la elección entre hosting en la nube (ej. Fly.io) o servidor institucional no está definida. Para la fase de pruebas se usará hosting en la nube; la responsabilidad de uptime recae en el proveedor.
- **Autenticación: JWT estándar** — *Razón:* el sistema distingue tres roles; la autenticación debe ser stateless. No se requieren mecanismos avanzados en v1.
- **CI/CD obligatorio** — *Razón:* el sistema lo mantiene un único desarrollador; el deployment manual no es sostenible.
- **Event sourcing como mecanismo de registro (decisión tomada)** — *Razón:* permite generar múltiples read models (logs, métricas, historial) desde un único stream de eventos sin duplicar lógica de persistencia.

---

## Compromisos documentados

- **Confiabilidad vs. Complejidad (PWA)** — *Decisión:* se descarta PWA. La confiabilidad ante pérdida de conexión se garantiza mediante persistencia server-side respuesta por respuesta, no mediante capacidad offline del cliente. El sistema asume conexión activa en todo momento.

- **Disponibilidad vs. Automatización** — *Decisión:* ante caída en período abierto, la contingencia es operativa (el docente extiende el plazo vía RF-11b), no automática. La complejidad de recuperación automática de estado no se justifica para el contexto académico.

---

## Ítems sin definir

- **Costo operativo**: depende de la decisión de infraestructura (nube vs. servidor institucional) — pendiente.
- **Mantenibilidad — modelo de tipos de pregunta**: la medida de "≤ 1 día de desarrollo" depende de que el tipo de pregunta esté modelado de forma polimórfica. Esta decisión emerge del modelo de dominio durante el diseño arquitectónico.
- **Usabilidad — criterios de legibilidad en proyección**: tamaño de fuente mínimo, contraste y layout de la pantalla proyectada se especifican en la etapa de diseño UX.
- **Administrabilidad — mecanismo de backup**: depende del proveedor de hosting elegido; se define cuando se toma la decisión de infraestructura.
