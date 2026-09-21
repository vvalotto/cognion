# US-6.3.1: Nombres de los Estudiantes en la sala de espera y el ranking

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-6.3`
**Tipo**: `feature backend` (técnica — cambio aditivo de contrato)
**Agregado principal afectado**: — (presentación de datos de `ParticipacionEnVivo` y de los read models)
**Bounded Context**: Actividad Evaluativa (con un puerto hacia Identidad)

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **ver el nombre de cada Estudiante en la sala de espera y en el ranking**,
para **que la proyección en el aula muestre personas y no identificadores**.

---

## Contexto del dominio

### Problema

Los wireframes aprobados muestran "chips con nombre de cada estudiante" (§2.2) y el ranking con "nombre +
puntaje" (§2.6, §2.7, §3.5). Hoy **solo viaja `estudiante_id`**, por HTTP y por WebSocket. Es el ítem abierto
que dejó la Iteración 2 (`inc6-candidatas.md`, "Nombres de los estudiantes…"). **Decidido con Víctor
(2026-09-21):** el backend agrega el nombre — el frontend nunca resuelve ni muestra ids.

### Mensajes y respuestas que ganan `nombre` (cambio aditivo: no rompe ningún consumidor)

| Superficie | Hoy | Después |
|---|---|---|
| WS `participantes_actualizados` | `participantes[{estudiante_id, unido_en}]` | `+ nombre` en cada elemento |
| WS `pregunta_cerrada` | `ranking[{posicion, estudiante_id, puntaje_acumulado}]` | `+ nombre` en cada elemento |
| WS `sesion_finalizada` | `ranking[{posicion, estudiante_id, puntaje_acumulado}]` | `+ nombre` en cada elemento |
| `GET /sesiones-en-vivo/{id}/participantes` | `[{estudiante_id, unido_en}]` | `+ nombre` |
| `GET /sesiones-en-vivo/{id}/ranking` | `[{posicion, estudiante_id, puntaje_acumulado}]` | `+ nombre` |

### Modelo involucrado

| Elemento | Nombre | Responsabilidad |
|---|---|---|
| Puerto (ampliado) | `EstudianteConsultaPort` | `obtener_nombres(ids: list[UUID]) -> dict[UUID, str]` — una sola consulta por lote, no una por Estudiante |
| Adapter (ampliado) | `EstudianteConsultaPortInProcess` (Identidad) | Implementa el método nuevo leyendo `usuario.nombre` |
| Read models / DTOs | `ParticipanteResumen`, `ParticipanteEnRanking` | Ganan `nombre: str` (o se enriquecen en el use case — decisión de la Fase 2) |
| Use cases | Unirse, Cerrar pregunta, Finalizar, Listar participantes, Obtener ranking | Resuelven los nombres del lote antes de armar el mensaje o la respuesta |
| Schemas | `ParticipanteResponse`, `RankingItemResponse` | `+ nombre` |

### Reglas

- **Sin imports entre BCs**: la resolución pasa por el puerto (`CLAUDE.md`).
- **Un Estudiante sin cuenta resoluble** (dato inconsistente) no rompe el broadcast: `nombre = "Estudiante sin nombre"`.
- Lo que se publica sigue siendo **best-effort** (`US-6.1.3`): un fallo al resolver nombres no revierte la unión ni el cierre.
- **RNF ≤ 100 ms** de `CerrarPreguntaActual`: la resolución de nombres suma **una consulta por lote** al camino
  medido en `US-6.2.9`; se **re-mide** con `tests/uat/inc6/medir_rendimiento_cierre.py` y el p95 debe seguir ≤ 100 ms.
- **Privacidad:** los nombres de los compañeros se ven en la proyección del aula y en el resultado final (Top 3);
  el Estudiante no ve el ranking completo de nombres durante la sesión (`§17` punto 10 se mantiene).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.2.x` cerradas.

### Postcondicion

- Todas las superficies de la tabla traen `nombre`; ningún campo existente cambia de nombre ni de tipo.
- Sin escrituras nuevas, sin migración.

### Excepciones

Sin excepciones nuevas. Un id sin nombre resoluble usa el texto de reemplazo, no levanta error.

---

## Criterios de aceptacion

```gherkin
Feature: Nombres de los Estudiantes en la sesión en vivo (US-6.3.1)

  Scenario: La sala de espera trae los nombres
    Given tres Estudiantes con nombre unidos a una sesión
    When el Docente lista los participantes
    Then cada participante trae su nombre además de su identificador

  Scenario: El broadcast de participantes trae los nombres
    Given un Docente conectado por WebSocket
    When un Estudiante se une
    Then el mensaje participantes_actualizados incluye el nombre de cada participante

  Scenario: El cierre de pregunta trae los nombres en el ranking
    Given una sesión con respuestas registradas
    When el Docente cierra la pregunta
    Then el ranking del mensaje pregunta_cerrada incluye el nombre de cada Estudiante

  Scenario: El ranking final trae los nombres
    Given una sesión finalizada
    When se consulta el ranking o se recibe sesion_finalizada
    Then cada fila trae el nombre del Estudiante

  Scenario: Un Estudiante sin nombre resoluble no rompe el mensaje
    Given un participante cuya cuenta ya no existe
    When se publica el ranking
    Then esa fila trae "Estudiante sin nombre" y el resto sale normal

  Scenario: El rendimiento se mantiene
    Given 60 participantes que respondieron la pregunta actual
    When se mide el cierre de pregunta 30 veces
    Then el p95 del use case sigue siendo menor o igual a 100 ms
```

---

## Impacto arquitectonico

- [ ] No — extiende un puerto existente hacia Identidad, mismo patrón que `ComisionConsultaPort` (`US-6.1.1`).

**Capa(s) afectadas:**
- [x] Entities — método en `EstudianteConsultaPort`, `nombre` en los DTOs de lectura
- [x] Use Cases — resolución del lote en 5 use cases (**vigilar CBO**: `UnirseASesionEnVivoUseCase` ya tiene 5 dependencias — resolver por función de módulo o decorador del canal, no sumar una dependencia más a la clase; el CBO solo se mide en el pre-push)
- [x] Interface Adapters / Frameworks — schemas y adapter de Identidad
- [ ] Frontend — consume `US-6.3.5` en adelante

---

## Fuente de verdad UX

No aplica — backend. Los nombres que se muestran salen de `wireframes-actividad-evaluativa-en-vivo.md` §2.2, §2.6, §2.7, §3.5.

---

## Artefactos a modificar

| Artefacto | Cambio |
|---|---|
| `src/actividad_evaluativa/entities/ports/estudiante_consulta_port.py` | `obtener_nombres` |
| `src/actividad_evaluativa/frameworks/adapters/estudiante_consulta_port_in_process.py` | Implementación |
| `src/actividad_evaluativa/use_cases/` (unirse, cerrar, finalizar, listar participantes, obtener ranking) | Resolución de nombres |
| `src/actividad_evaluativa/frameworks/api/schemas.py`, `sesiones_en_vivo_router.py` | `nombre` en las respuestas |
| `tests/unit/inc6/_fakes.py`, `tests/unit/inc3/_fakes.py` | Actualizar los fakes del puerto **en el mismo commit** que el puerto |
| `tests/unit/inc6/`, `tests/integration/inc6/`, `tests/features/inc6/US-6.3.1*.feature` + step defs | Unitarios, HTTP + WebSocket, BDD |

---

## Referencias

- Ítem abierto de origen: `docs/plans/inc6/inc6-candidatas.md` §Iteración 2, "Ítems abiertos…"
- Precedente de puerto hacia Identidad: `US-6.1.1` (`ComisionConsultaPort`)
- Depende de: `US-6.2.5`, `US-6.2.7`, `US-6.2.8`, `US-6.2.9` (medición del RNF)
- Consumida por: `US-6.3.3`, `US-6.3.5` a `US-6.3.9`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
