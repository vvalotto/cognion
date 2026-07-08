# Escenarios de Calidad — Cognión (borrador para revisión)

> Para cada escenario: confirmá si representa bien la situación, ajustá lo que no cierre,
> descartá los que no aplican.

---

## Rendimiento

**Escenario R1 — Ranking en sesión en vivo**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Sesión en vivo activa con hasta 60 alumnos respondiendo simultáneamente |
| **Estímulo** | El docente cierra una pregunta |
| **Respuesta esperada** | El servidor calcula el ranking y hace broadcast a todos los clientes conectados |
| **Expectativa PO** | El ranking aparece en pantalla en menos de 1 segundo (percibido como instantáneo) |
| **Factibilidad arquitecto** | Procesamiento server-side ≤ 100ms (≤ 10% del tiempo percibido); la latencia de red es del entorno |
| **Medida acordada** | Procesamiento server-side ≤ 100ms |

---

## Disponibilidad

**Escenario D1 — Caída durante sesión en vivo**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Sesión en vivo activa durante clase |
| **Estímulo** | El sistema deja de responder inesperadamente |
| **Respuesta esperada** | El sistema intenta recuperarse según el mecanismo del proveedor de hosting |
| **Expectativa PO** | Si no levanta en 5 minutos, la sesión se cancela |
| **Factibilidad arquitecto** | Depende del SLA del proveedor (infraestructura pendiente de decisión) |
| **Medida acordada** | Ventana de tolerancia: 5 minutos. Healthcheck disponible como endpoint del sistema |

**Escenario D2 — Caída durante período abierto de parcial/final**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Sesión de período abierto activa con ventana de tiempo definida |
| **Estímulo** | El sistema no está disponible durante parte de la ventana |
| **Respuesta esperada** | Cuando el sistema vuelve, el docente extiende el plazo de cierre (RF-11b) |
| **Expectativa PO** | Contingencia operativa — el docente ajusta el período; no se requiere recuperación automática |
| **Factibilidad arquitecto** | RF-11b contempla modificar el período post-creación |
| **Medida acordada** | El sistema permite modificar la fecha/hora de cierre de una sesión activa |

---

## Confiabilidad

**Escenario C1 — Interrupción durante sesión de período abierto**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Alumno cursando un examen, con respuestas parciales confirmadas |
| **Estímulo** | El alumno pierde conexión, cierra el browser o el dispositivo se reinicia |
| **Respuesta esperada** | Las respuestas confirmadas quedan persistidas; al reconectarse retoma desde donde estaba con el mismo set de preguntas |
| **Expectativa PO** | Cero pérdida de respuestas confirmadas; el alumno no puede obtener un set nuevo por reconexión |
| **Factibilidad arquitecto** | Persistencia respuesta por respuesta en BD al momento de confirmación; set de preguntas cacheado e inmutable desde el inicio |
| **Medida acordada** | Cero pérdida de respuestas confirmadas ante reconexión; set de preguntas inmutable |

---

## Seguridad

**Escenario S1 — Control de acceso por rol**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Cualquier operación en el sistema |
| **Estímulo** | Un actor intenta acceder a funcionalidades fuera de su rol |
| **Respuesta esperada** | El sistema deniega el acceso |
| **Expectativa PO** | RBAC suficiente para el contexto académico; sin mecanismos adicionales |
| **Factibilidad arquitecto** | RBAC con JWT; validación de rol en cada endpoint del servidor |
| **Medida acordada** | Ningún actor puede acceder a recursos fuera de su rol (verificable por revisión de API) |

---

## Usabilidad

**Escenario U1 — Acceso desde dispositivos de alumnos**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Alumno participa en una sesión desde su dispositivo personal |
| **Estímulo** | Acceso desde PC, tablet o smartphone con cualquier browser vigente |
| **Respuesta esperada** | La interfaz se adapta y es completamente funcional |
| **Expectativa PO** | Compatible con todos los dispositivos y browsers vigentes (Chrome, Firefox, Safari, Edge) |
| **Factibilidad arquitecto** | Diseño responsive estándar |
| **Medida acordada** | Funcional sin degradación en browsers vigentes en cualquier tamaño de pantalla |

**Escenario U2 — Proyección en el aula (interfaz del docente)**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | El docente proyecta la pantalla durante una sesión en vivo |
| **Estímulo** | Los alumnos intentan leer el contenido desde sus asientos |
| **Respuesta esperada** | El texto y los elementos clave son legibles desde cualquier punto del aula |
| **Expectativa PO** | Legibilidad completa en toda el aula |
| **Factibilidad arquitecto** | A definir en diseño UX |
| **Medida acordada** | ⚠️ Ítem abierto — se especifica en etapa de diseño UX |

---

## Mantenibilidad

**Escenario M1 — Incorporación de nuevo tipo de pregunta**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Se decide incorporar un nuevo tipo de pregunta post v1 |
| **Estímulo** | El desarrollador inicia la implementación |
| **Respuesta esperada** | Se incorpora sin modificar la lógica central de sesiones, scoring ni analytics |
| **Expectativa PO** | ≤ 1 día de desarrollo |
| **Factibilidad arquitecto** | ⚠️ Depende del modelo de dominio (polimorfismo de tipos de pregunta) — a definir |
| **Medida acordada** | ⚠️ Ítem abierto — depende del modelo de dominio |

---

## Observabilidad

**Escenario O1 — Diagnóstico post-incidente**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Ocurrió un error o comportamiento inesperado durante una sesión |
| **Estímulo** | El desarrollador necesita reconstruir qué pasó |
| **Respuesta esperada** | Existen registros de eventos suficientes para el diagnóstico |
| **Expectativa PO** | Consulta diferida de logs de errores, conexiones y actividad de sesiones |
| **Factibilidad arquitecto** | Event sourcing — eventos del sistema alimentan read models para consulta |
| **Medida acordada** | El sistema registra: errores, conexiones (quién, duración) y actividad de sesiones. Healthcheck consultable sin autenticación |

---

## Administrabilidad

**Escenario A1 — Deployment de nueva versión**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | El desarrollador tiene cambios listos para producción |
| **Estímulo** | Push a la rama main del repositorio |
| **Respuesta esperada** | La nueva versión se despliega automáticamente |
| **Expectativa PO** | Sin intervención manual |
| **Factibilidad arquitecto** | CI/CD conectado al repositorio |
| **Medida acordada** | Push a main desencadena deployment automático |

**Escenario A2 — Backup y recuperación**

| Campo | Descripción |
|-------|-------------|
| **Contexto** | Se necesita restaurar datos ante pérdida o corrupción |
| **Estímulo** | El desarrollador detecta pérdida de datos |
| **Respuesta esperada** | Existe un backup reciente para restaurar |
| **Expectativa PO** | Backups mensuales, retención 12 meses; pérdida máxima aceptable: datos del mes en curso |
| **Factibilidad arquitecto** | Depende del proveedor de hosting elegido |
| **Medida acordada** | Backup automático mensual; 12 meses de retención |
