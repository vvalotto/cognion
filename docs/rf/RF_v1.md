# Requerimientos Funcionales — Cognion

> Versión: RF_v1  
> Fecha: 2026-06-24  
> Estado: borrador verificado
> Revisión 2026-07-16: el BC "Sesiones" se renombró a "Actividad Evaluativa" (`ADR-015`) —
> este documento no se reescribe, "sesión/sesiones" en el texto original se lee con ese
> significado.

## Descripción del sistema

Plataforma web de evaluación universitaria basada en cuestionarios que permite al docente gestionar un banco de preguntas, ejecutar sesiones de evaluación en dos modalidades distintas, y hacer seguimiento histórico del desempeño individual y grupal de los estudiantes.

## Actores

| Actor | Rol en el sistema |
|-------|-------------------|
| Administrador | Gestiona problemas de cuentas de usuarios |
| Docente | Arma y mantiene el banco de preguntas, crea y conduce sesiones, accede a analytics y KPIs |
| Estudiante | Se registra vía invitación, participa en sesiones, consulta su propio desempeño |

## Requerimientos por área de dominio

### Gestión de cuentas y acceso

**RF-01 — Registro de estudiante por invitación**  
El docente genera un link de invitación por comisión. El estudiante se registra usando ese link y queda automáticamente asignado a la comisión correspondiente, sin requerir aprobación del docente.  
- **Criterios de aceptación:** Al completar el registro con un link válido, el estudiante aparece asignado a la comisión en el sistema.  
- **Casos límite:** Comportamiento ante link vencido o inválido — a definir.

**RF-02 — Roles de usuario**  
El sistema distingue tres roles: administrador, docente y estudiante. Cada rol accede únicamente a las funcionalidades que le corresponden.  
- **Criterios de aceptación:** Un estudiante no puede acceder a la gestión del banco de preguntas ni a los analytics globales. Un docente no puede acceder a las herramientas de administración de cuentas.

**RF-03 — Gestión de cuentas por administrador**  
El administrador puede intervenir en cuentas de usuarios para resolver problemas (bloqueos, recuperación, etc.).  
- **Criterios de aceptación:** El administrador puede ver, modificar el estado y gestionar las cuentas sin necesidad de intervención del docente.

### Banco de preguntas

**RF-04 — Carga de preguntas**  
El docente puede cargar preguntas al banco. Cada pregunta tiene: texto de la pregunta, opciones de respuesta, respuesta correcta, y metadatos de clasificación.  
- **Criterios de aceptación:** Una pregunta guardada aparece disponible para ser usada en sesiones de la materia correspondiente.

**RF-05 — Tipos de pregunta**  
El sistema soporta dos tipos de pregunta: opción múltiple (una única respuesta correcta) y verdadero/falso. El diseño debe permitir incorporar nuevos tipos en el futuro.  
- **Criterios de aceptación:** Ambos tipos se pueden crear, editar y usar en cualquier modalidad de sesión.

**RF-06 — Metadatos de pregunta**  
Cada pregunta se clasifica con los siguientes atributos: materia, unidad temática, tema, nivel de dificultad (Alto / Medio / Bajo), nivel de importancia conceptual (Alto / Medio / Bajo).  
- **Criterios de aceptación:** Es posible filtrar el banco por cualquier combinación de estos atributos.

**RF-07 — Migración desde PDFs existentes**  
El sistema debe permitir importar las preguntas existentes del docente, actualmente en formato PDF.  
- **Criterios de aceptación:** Las preguntas importadas quedan disponibles en el banco con todos sus metadatos correctamente asignados.  
- **Casos límite:** Mecanismo de importación a definir (parseo automático vs. asistido).

### Sesiones — Modo en vivo (Kahoot!-style)

**RF-08 — Creación de sesión en vivo**  
El docente crea una sesión en vivo seleccionando materia, unidad temática o tema, y la cantidad de preguntas. Todos los estudiantes reciben el mismo set de preguntas.  
- **Criterios de aceptación:** El docente puede iniciar la sesión y los estudiantes de la comisión pueden unirse seleccionándola desde su portal.

**RF-09 — Dinámica en tiempo real**  
Durante la sesión en vivo, las preguntas se presentan de forma sincronizada para todos los participantes. Al cerrar cada pregunta, se muestra la respuesta correcta y se actualiza el ranking en tiempo real.  
- **Criterios de aceptación:** Todos los estudiantes conectados ven la misma pregunta al mismo tiempo. El ranking se actualiza tras cada pregunta.

**RF-10 — Puntaje en sesión en vivo**  
El puntaje de cada respuesta se calcula en función del tiempo de respuesta, la corrección de la respuesta, el nivel de dificultad y el nivel de importancia conceptual de la pregunta.  
- **Criterios de aceptación:** El algoritmo exacto está pendiente de definición (ver Ítems que requieren decisión).  
- **Casos límite:** Una respuesta incorrecta puede dar puntaje negativo, neutro o cero — a definir en el algoritmo.

### Sesiones — Modo período abierto

**RF-11 — Creación de sesión de período abierto**  
El docente crea una sesión definiendo: materia, período de disponibilidad (fecha/hora de apertura y cierre), cantidad de preguntas, y cantidad de intentos permitidos (por defecto: 1).  
- **Criterios de aceptación:** La sesión solo es accesible para los estudiantes dentro del período definido.

**RF-11b — Modificación del período de disponibilidad**  
El docente puede modificar la fecha/hora de cierre de una sesión de período abierto ya creada, incluso mientras está activa. Esto permite extender el plazo en caso de contingencias (caída del sistema, problemas técnicos, etc.).  
- **Criterios de aceptación:** El cambio de fecha/hora de cierre tiene efecto inmediato. Los estudiantes que ya iniciaron la sesión pueden seguir respondiendo hasta el nuevo límite.  
- **Casos límite:** No se puede acortar el período si hay estudiantes con sesiones activas en ese momento.

**RF-12 — Set aleatorio por estudiante**  
Al ingresar a la sesión, el sistema genera un set aleatorio de preguntas del banco, filtrado por materia, de la cantidad definida por el docente. Cada estudiante recibe un set diferente.  
- **Criterios de aceptación:** Dos estudiantes que inician la misma sesión reciben preguntas distintas (salvo colisión aleatoria aceptable).

**RF-13 — Revisión al finalizar**  
Al terminar la sesión, el estudiante ve el detalle de cada pregunta: su respuesta, si fue correcta o incorrecta, y la respuesta correcta en caso de error.  
- **Criterios de aceptación:** El detalle completo es visible inmediatamente al finalizar, no antes.

### Notificaciones

**RF-14 — Notificación de apertura y cierre de sesión**  
El sistema envía notificaciones por email al estudiante cuando se abre y cuando se cierra una sesión de período abierto que le corresponde.  
- **Criterios de aceptación:** El email se envía automáticamente al momento de apertura y cierre. El estudiante recibe la notificación en el correo registrado.  
- **Casos límite:** El canal de notificación debe ser extensible a otros medios en el futuro.

### Portal del estudiante

**RF-15 — Vista de desempeño individual**  
El estudiante accede a un portal donde puede consultar su historial de participación en sesiones. Para sesiones de período abierto, ve cantidad de respuestas correctas e incorrectas con el detalle por pregunta. Para sesiones en vivo, ve su puntaje y posición en el ranking.  
- **Criterios de aceptación:** El historial refleja todas las sesiones en las que participó el estudiante.

### Analytics del docente

**RF-16 — Seguimiento por alumno**  
El docente puede ver el desempeño individual de cada estudiante: respuestas correctas e incorrectas por sesión y acumuladas a lo largo de la cursada.  
- **Criterios de aceptación:** El docente puede seleccionar un estudiante y ver su historial completo.

**RF-17 — Seguimiento por curso y tema**  
El docente puede ver el desempeño agregado por comisión e identificar qué temas concentran más errores.  
- **Criterios de aceptación:** El sistema muestra qué temas/unidades tienen mayor tasa de error a nivel grupal.

**RF-18 — KPIs históricos**  
El sistema mantiene un historial de KPIs por sesión y por cursada que el docente puede consultar a lo largo del tiempo.  
- **Criterios de aceptación:** Los datos de sesiones anteriores son accesibles y comparables. Los KPIs específicos a mostrar serán definidos por el docente (ver Diferidos).

---

## Decisiones de alcance

### En alcance
- Dos modalidades de sesión: en vivo (Kahoot!-style) y período abierto
- Banco de preguntas con metadatos de clasificación temática y dificultad
- Tipos de pregunta: opción múltiple (una correcta) y verdadero/falso
- Registro de estudiantes por invitación por comisión
- Portal del estudiante con historial y desempeño propio
- Analytics del docente: por alumno, por curso, por tema
- Notificaciones por email en apertura y cierre de sesiones abiertas
- Migración inicial desde PDFs

### Fuera de alcance
- Múltiples docentes — *Razón:* el sistema es de uso personal del docente por ahora; se extiende después.
- Reportes exportables — *Razón:* se evalúa en una etapa posterior.

### Diferidos
- Algoritmo de selección de preguntas no aleatorio — *Razón del diferimiento:* requiere definir criterios de personalización (historial, desempeño previo, etc.).
- Notificaciones por canales distintos al email — *Razón del diferimiento:* la arquitectura debe preverlo pero la implementación queda para después.
- Definición detallada de KPIs a mostrar en el dashboard del docente — *Razón del diferimiento:* el docente los irá definiendo a medida que use el sistema.

---

## Ítems que requieren decisión

- **Algoritmo de puntaje en modo en vivo**: debe combinar tiempo de respuesta, corrección, dificultad e importancia conceptual. Requiere una sesión de diseño con opciones concretas y ejemplos numéricos antes de implementar.
- **Mecanismo de importación desde PDF**: definir si el parseo es automático, asistido, o manual con plantilla estructurada.
- **Comportamiento ante link de invitación vencido o inválido**: ¿se muestra error, se redirige, se permite solicitar uno nuevo?
- **Puntaje negativo en modo en vivo**: definir si una respuesta incorrecta resta puntos, da cero, o tiene otro tratamiento.
