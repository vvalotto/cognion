# 06 · Atributos de calidad

> Pregunta: ¿qué escenarios de `RNF_v1.md` se sostienen, y con qué evidencia?

## Qué se miró

La vista [`70-trazabilidad-rnf-vistas.md`](../architecture/70-trazabilidad-rnf-vistas.md) ya evalúa los 11 escenarios y es honesta: declara 4 cumplidos, 4 parciales, 1 no verificado y 2 no cumplidos. Este capítulo no la repite. Agrega lo que esta revisión encontró en el código sobre cada escenario.

## Lectura independiente de los escenarios

| Escenario | Vista 70 | Esta revisión | Motivo de la diferencia |
|---|---|---|---|
| Rendimiento: ranking ≤ 100 ms con 60 alumnos | Cumple (en desarrollo) | **Cumple con reserva** | Medido en una Mac con conexiones simuladas. `NullPool` abre una conexión por operación ([IM-06](05-implementacion-por-capa.md#im-06--nullpool-en-producción-por-una-necesidad-de-los-tests)); falta medir en el servidor |
| Disponibilidad 1: caída durante sesión en vivo | Parcial | Parcial | Coincide. Se agrega que el estado de conexiones está en memoria ([IM-05](05-implementacion-por-capa.md#im-05--dos-supuestos-de-proceso-único-sin-protección)): tras un reinicio todos deben reconectar |
| Disponibilidad 2: extender el plazo | Cumple | Cumple | — |
| Confiabilidad: cero pérdida de respuestas | Cumple | **Cumple en Actividad Evaluativa; no en el resto** | Las respuestas son eventos confirmados uno a uno. Pero Identidad y Banco tienen operaciones de dos escrituras no atómicas ([IM-03](05-implementacion-por-capa.md#im-03--la-transacción-vive-en-el-repositorio-no-en-el-caso-de-uso)) |
| Seguridad: control de acceso por rol | Cumple | **Cumple con una excepción** | El canal WebSocket no verifica pertenencia ([IM-04](05-implementacion-por-capa.md#im-04--el-canal-en-vivo-autentica-pero-no-autoriza)) |
| Usabilidad 1: dispositivos y navegadores | Parcial | Parcial | Coincide |
| Usabilidad 2: legibilidad en proyección | Parcial | Parcial | Coincide |
| Mantenibilidad: tipo de pregunta nuevo en un día | No verificado | **Probablemente no cumple** | El tipo se resuelve con `isinstance` y claves de diccionario en tres contextos ([DM-05](04-dominio-y-event-sourcing.md#dm-05--el-tipo-de-pregunta-se-resuelve-con-primitivos-y-isinstance)) |
| Observabilidad: diagnóstico posterior a un incidente | Parcial | Parcial | Coincide. Se agrega que los registros rotan a 30 MB por servicio ([DO-04](10-despliegue-y-operacion.md#do-04--el-diagnóstico-posterior-a-un-incidente-depende-de-30-mb-de-registros)) |
| Administrabilidad 1: despliegue automático | No cumple | No cumple | Coincide |
| Administrabilidad 2: respaldo mensual, 12 meses | No cumple | No cumple | Coincide |

## Hallazgos

### AQ-01 · El escenario de mantenibilidad nunca se probó

- **Vara:** Conformidad · **Severidad:** Alta · **Confianza:** Inferido · **Esfuerzo:** S (la prueba)
- **Evidencia:** la vista 70 lo marca "No verificado" y anticipa que "un tipo nuevo probablemente lo toque". El análisis de [DM-05](04-dominio-y-event-sourcing.md#dm-05--el-tipo-de-pregunta-se-resuelve-con-primitivos-y-isinstance) lo confirma por lectura.
- **Por qué importa:** es el único escenario de `RNF_v1.md` que habla del diseño interno, y es el que justifica separar Banco de Preguntas de Actividad Evaluativa. Sin probarlo, no se sabe si esa separación rinde.
- **Recomendación:** una prueba acotada: agregar un tercer tipo (por ejemplo, respuesta numérica) en una rama descartable, contar archivos tocados por contexto y horas. El resultado decide la prioridad de DM-05.

### AQ-02 · Dos escenarios llevan incumplidos desde que se escribieron

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S (decidir), M (implementar)
- **Evidencia:** despliegue automático y respaldo mensual con retención de 12 meses figuran como "No cumple como está escrito" en la vista 70, en `BL-017` y en `CLAUDE.md`. `RNF_v1.md` no se modifica por política.
- **Por qué importa:** un requerimiento que se sabe incumplido y no se renegocia deja de funcionar como requerimiento. La política de no modificar los documentos de definición protege la historia, pero aquí impide cerrar la distancia por el lado correcto.
- **Recomendación:** emitir `RNF_v2.md` (o un ADR que lo enmiende) con lo que de verdad se necesita para un docente y un servidor: "actualizar es un comando y tarda menos de N minutos" y "respaldo automático diario con copia fuera del servidor". El segundo se puede cumplir con poco trabajo ([DO-02](10-despliegue-y-operacion.md#do-02--el-respaldo-depende-de-que-alguien-se-acuerde)).

### AQ-03 · Falta un escenario para el crecimiento de los datos

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado (la ausencia) · **Esfuerzo:** S
- **Evidencia:** `RNF_v1.md` fija rendimiento para la sesión en vivo, no para Analytics ni para el historial. Analytics recorre todos los eventos de evaluación en cada consulta ([AC-03](03-acoplamiento-entre-contextos.md#ac-03--analytics-lee-los-eventos-crudos-de-actividad-evaluativa-y-los-recorre-completos)) y los agregados se reconstruyen leyendo su stream completo, sin instantáneas.
- **Por qué importa:** el sistema guarda eventos para siempre y nada dice cuánto historial debe soportar. Sin escenario no hay medida, y el problema aparece cuando ya hay datos reales.
- **Recomendación:** un escenario del tipo "con 3 años de historial (N evaluaciones), el reporte de una comisión responde en menos de 2 segundos", y una prueba con datos sembrados.

### AQ-04 · La sesión de usuario puede vencer en mitad de una clase

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Inferido (falta probarlo en ejecución) · **Esfuerzo:** S
- **Evidencia:** `access_token_expire_minutes = 60` en `settings.py`, sin renovación (`ADR-013`). El cliente, ante un 401, borra la sesión y navega a `/login` ([`api-client.ts`](../../frontend/src/lib/api-client.ts)).
- **Por qué importa:** una clase dura más de 60 minutos. Un docente que inició sesión al llegar y conduce una sesión en vivo una hora después recibiría un 401 al avanzar de pregunta, frente al aula. El escenario de disponibilidad en vivo no contempla este caso.
- **Recomendación:** verificarlo en navegador con un vencimiento corto. Si se confirma, subir la duración a la de una jornada (8 horas) es suficiente a esta escala; la renovación automática es la solución completa.

## Juicio

La evaluación propia del proyecto es correcta en lo que mide. Esta revisión baja tres "cumple" a "cumple con reserva" por evidencia de código que la vista no consideró, y señala que el escenario más ligado al diseño (mantenibilidad) sigue sin prueba. La acción más útil no es técnica: renegociar los dos escenarios que nunca se van a cumplir como están escritos.
