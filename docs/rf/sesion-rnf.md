# Sesión de elicitación — Atributos de Calidad (Cognión)

> Fecha: 2026-07-08  
> Estado: en curso

---

## Atributos en consideración

### Propuestos inicialmente

- **Rendimiento** — La sesión en vivo requiere que el ranking se actualice de forma sincronizada para todos los alumnos. ¿Cuánto tiempo puede pasar entre que el docente cierra una pregunta y el ranking aparece en pantalla antes de que la dinámica se rompa?

- **Disponibilidad** — ¿Qué tan grave es que el sistema no esté disponible durante una sesión en vivo o un período abierto de parcial? ¿Hay momentos del calendario académico donde una caída sería especialmente costosa?

- **Confiabilidad** — En el modo período abierto, si un alumno pierde conexión a mitad del examen, ¿sus respuestas ya enviadas deben quedar guardadas? ¿Puede explotar una reconexión para obtener un set de preguntas nuevo?

- **Seguridad** — Los alumnos no deben poder ver las respuestas correctas antes de que el sistema las revele. ¿Qué tan crítico es esto? ¿Hay otros aspectos de seguridad que te preocupen (suplantación de identidad, acceso entre alumnos)?

- **Usabilidad** — Los alumnos responden desde sus dispositivos en clase. ¿La interfaz tiene que ser mobile-first? ¿El docente proyecta la pantalla en el aula?

- **Mantenibilidad** — El sistema tiene partes explícitamente diferidas (algoritmo de puntaje, KPIs del docente, nuevos tipos de pregunta). ¿Qué tan fácil tiene que ser incorporarlas después? ¿Lo mantenés vos solo?

- **Costo operativo** — ¿Hay un presupuesto acotado para infraestructura? ¿Es un proyecto personal o tiene financiamiento institucional?

### Agregados por Victor

- **Observabilidad** — ¿Qué necesitás poder ver del sistema en producción? ¿Logs de errores, métricas de uso, trazabilidad de sesiones? ¿O algo más específico, como saber qué pasó durante una sesión que falló?

- **Configurabilidad** — ¿Qué aspectos del sistema necesitás poder cambiar sin tocar código? ¿Parámetros de sesión, reglas de puntaje, umbrales? ¿Quién configura — solo vos como admin, o también el docente desde la interfaz?

- **Administrabilidad** — ¿Qué operaciones administrativas tenés que poder hacer sobre el sistema en producción? ¿Gestión de usuarios, corrección de datos, limpieza de sesiones? ¿O pensás en la administración del sistema en sí (deployments, backups, mantenimiento)?

---

## Respuestas y notas de la sesión

### Administrabilidad
- **Deployment**: CI/CD conectado al repositorio — push a main despliega automáticamente
- **Backups**: automáticos, frecuencia mensual, retención de 12 meses
- **Limpieza de sesiones**: descartada — no aplica

### Configurabilidad
- No aplica como atributo de calidad separado — la configuración de roles/usuarios (administrador) y la creación de actividades (docente) ya están cubiertas en los RF funcionales. No hay parámetros de sistema que requieran cambio sin deployment.

### Observabilidad
- **Healthcheck**: el sistema expone un endpoint de healthcheck que permite monitoreo y alerta ante caída, sin esperar que lo reporten los alumnos
- **Eventos a registrar**: errores del sistema, conexiones de usuarios (quién, cuánto tiempo), métricas de uso de sesiones
- **Enfoque arquitectónico (decisión tomada)**: event sourcing — se generan registros de eventos que luego alimentan read models para consulta diferida (no en tiempo real)

### Costo operativo
- **⚠️ Ítem abierto**: depende de la decisión de infraestructura (nube vs. servidor institucional), todavía sin definir

### Mantenibilidad
- **Target**: agregar un nuevo tipo de pregunta en ≤ 1 día de desarrollo
- **⚠️ Ítem abierto**: la factibilidad del target depende del modelo de dominio (polimorfismo de tipos de pregunta) — se resolverá cuando se defina el modelo de dominio

### Usabilidad
- **Alumnos**: interfaz responsive compatible con PCs, tablets y smartphones usando elementos estándar de renderización en todos los browsers vigentes
- **Docente (proyección en aula)**: el texto de la pantalla proyectada debe ser legible desde cualquier punto del aula — criterio mínimo a respetar; el detalle se define en la etapa de diseño UX

### Seguridad
- Control de roles es suficiente (administrador / docente / estudiante)
- Las respuestas correctas se manejan sin mecanismos especiales de ocultamiento — el contexto académico no lo justifica
- PWA descartado simplifica el modelo de seguridad: todo online, el servidor controla el flujo de información

### Confiabilidad
- **Persistencia**: cada respuesta se confirma inmediatamente al enviarla (no al finalizar la sesión), tanto en cliente como en servidor
- **Set de preguntas**: inmutable desde el inicio de la sesión — se cachea al asignarse; una reconexión no genera un set nuevo
- **PWA**: descartado — la complejidad no se justifica. El sistema es exclusivamente online. Las sesiones en vivo son gamificadas y requieren conexión activa; las sesiones de período abierto también son online.

### Disponibilidad
- **Sesión en vivo**: si el sistema no levanta en 5 minutos, la sesión se cancela
- **Período abierto (parcial/final)**: ante caída, el docente extiende el plazo de cierre cuando el sistema vuelve — el sistema debe permitir modificar los atributos de la sesión (→ agregado como RF-11b en el RF)
- **Infraestructura**: pendiente de decisión (nube vs. servidor institucional); para pruebas: Fly.io o similar — la responsabilidad de uptime recae en el proveedor de hosting

### Rendimiento
- **Expectativa PO**: el usuario percibe el ranking como instantáneo — < 1 segundo desde el cierre de la pregunta
- **Factibilidad arquitecto**: procesamiento server-side ≤ 100ms; la latencia de red es del entorno y no es garantizable por el sistema
- **Principio acordado**: el servidor debe consumir como máximo el 10% del tiempo de respuesta percibido por el usuario

