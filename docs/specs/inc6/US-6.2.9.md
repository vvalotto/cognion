# US-6.2.9: Verificación de la sesión en vivo completa y del RNF de rendimiento

**Estado**: `Implementada` (2026-09-21) — revisión manual de Víctor pendiente
**Iteracion / Sprint**: `INC-6.2`
**Tipo**: `verificación` (UAT backend — sin código de producción)
**Agregado principal afectado**: — (recorre ambos aggregates de punta a punta)
**Bounded Context**: Actividad Evaluativa

---

## Descripcion (lenguaje de negocio)

Como **Docente**,
quiero **tener evidencia de que una sesión en vivo completa funciona de punta a punta y de que el
ranking aparece rápido con toda la clase conectada**,
para **confiar en usarla en el aula antes de que exista la pantalla**.

---

## Contexto del dominio

### Problema

Cierra la Iteración 2 y el **hito del incremento**: "el docente conduce una sesión en vivo
completa en el aula, con ranking actualizado en tiempo real dentro del umbral de ≤100 ms
server-side acordado en RNF" (`inc6-candidatas.md`). Es el **primer RNF de rendimiento duro** que el
proyecto verifica con datos reales en vez de solo documentarlo (`RNF_v1.md`, Rendimiento,
Escenario 1).

No agrega código de producción: agrega **evidencia** — un test de sesión completa, una medición
reproducible y una revisión manual. Si la medición supera el umbral, **es un hallazgo**: se
registra y la iteración no cierra hasta optimizar (US-ADJ) o decidir explícitamente con Víctor.

### Qué se mide

**Procesamiento server-side de `CerrarPreguntaActual`** con 60 participantes: desde que el Use Case
empieza hasta que terminó de publicar a las 60 conexiones (persistir el evento, leer ranking e
histograma, leer la respuesta correcta, armar y enviar el mensaje). **No** incluye la latencia de red
de cada cliente (el RNF la deja fuera: "es del entorno").

### Alcance de la medición (honestidad del método)

- Base de datos **PostgreSQL real**, con 60 participantes y respuestas ya registradas por la API.
- Broadcast con el `ConnectionManager` real y **60 conexiones simuladas** en memoria (medir el envío
  de 60 mensajes, no la red). Se complementa con un caso con **2 WebSockets reales** vía
  `TestClient` para verificar que el mensaje llega íntegro.
- Máquina de desarrollo local, no producción: los números son una **cota de referencia**, no una
  garantía del despliegue final (la infraestructura definitiva sigue pendiente, `CLAUDE.md`).

---

## Especificacion del comportamiento

### Precondicion

- `US-6.2.1` a `US-6.2.8` cerradas.

### Postcondicion

- Existe un test de integración que conduce una sesión completa por la API real.
- Existe una medición reproducible del RNF con su evidencia guardada.
- Víctor validó una revisión manual del flujo (por Swagger/HTTP + un cliente WebSocket), como en la
  Iteración 1 del Incremento 3, y por eso RF-08/09/10 pueden pasar a **Implementado**.

### Criterio de aceptación del RNF

`p95 ≤ 100 ms` de procesamiento server-side de `CerrarPreguntaActual` sobre **al menos 30
repeticiones** con 60 participantes (además de reportar mediana, máximo y desvío). Si `p95 > 100 ms`
→ hallazgo bloqueante de la iteración.

---

## Criterios de aceptacion

```gherkin
Feature: Verificación de la sesión en vivo completa (US-6.2.9)

  Scenario: Sesión completa de punta a punta
    Given una Comisión con 5 Estudiantes y un banco con preguntas suficientes
    When el Docente crea la sesión, los Estudiantes se unen, se inicia y se recorren 3 preguntas
      (mostrar opciones, responder, cerrar, avanzar) y se finaliza
    Then cada paso responde 200 y cada broadcast llega a todos los conectados
    And el ranking final coincide con la suma de los puntajes de cada respuesta
    And el Estudiante puede consultar el ranking solo después de finalizar

  Scenario: Cierre de pregunta con 60 participantes dentro del umbral
    Given una sesión con 60 participantes que ya respondieron la pregunta actual
    When el Docente cierra la pregunta, repetido 30 veces sobre preguntas distintas
    Then el p95 del procesamiento server-side es menor o igual a 100 ms
    And se guardan mediana, máximo y desvío como evidencia

  Scenario: Respuestas simultáneas de 60 Estudiantes
    Given una pregunta con las opciones mostradas y 60 participantes
    When los 60 responden a la vez
    Then las 60 respuestas se registran y el histograma suma exactamente 60
    And el ranking refleja los puntajes de todos

  Scenario: Reconexión durante la sesión
    Given un Estudiante que pierde la conexión con la pregunta abierta
    When se reconecta y consulta el estado
    Then recupera la pregunta actual, el tiempo restante y su avance, sin perder su participación

  Scenario: Las respuestas tardías se descartan
    Given una pregunta con el tiempo límite ya vencido
    When un Estudiante intenta responder
    Then el sistema rechaza con TiempoAgotado (422) y no altera el ranking
```

---

## Impacto arquitectonico

**¿Esta US requiere una decision arquitectonica?**
- [ ] No — verificación. Si la medición falla, la decisión de cómo optimizar se toma con Víctor
  (posible ADR o `US-ADJ`) y no se resuelve dentro de esta US.

**Capa(s) afectadas:**
- [ ] Entities / Use Cases / Interface Adapters / Frameworks — ninguna (sin código de producción)
- [ ] Frontend — no aplica

---

## Fuente de verdad UX

No aplica — verificación de backend, sin pantalla.

---

## Artefactos a crear

| Artefacto | Contenido |
|---|---|
| `tests/integration/inc6/test_sesion_en_vivo_completa.py` | Sesión completa por la API real, con WebSockets |
| `tests/uat/inc6/medir_rendimiento_cierre.py` | Medición reproducible del RNF (60 participantes, ≥30 repeticiones) |
| `tests/uat/inc6/guion_manual_iteracion2.sh` (o `.md`) | Guion de la revisión manual por Swagger/HTTP + cliente WebSocket |
| `quality/reports/uat/inc6/design-iteracion2.md`, `evidencia-iteracion2.md` | Diseño y evidencia de la UAT, con los números medidos |
| `docs/traceability/matrix.md` | RF-08/09/10 → Implementado, **solo** tras la validación de Víctor |

Convención de UAT: `docs/plans/PROCEDIMIENTO-UAT.md` (Capa 1 = suite completa, Capa 2 = recorrido
real, revisión manual).

---

## Referencias

- RNF: `docs/rf/RNF_v1.md` Rendimiento, Escenario 1 (≤100 ms server-side, <1 s percibido)
- Modelo: `docs/design/domain/BC-actividad-evaluativa-modelo.md` §15, §16
- Procedimiento: `docs/plans/PROCEDIMIENTO-UAT.md`
- Precedente: UAT de la Iteración 1 del Incremento 3 (`tests/uat/inc3/guion_manual_iteracion1.sh`)
- Depende de: `US-6.2.1` a `US-6.2.8`
- Candidatas: `docs/plans/inc6/inc6-candidatas.md`

---

*Basado en template IEDD v2.0 — adaptado a capas `entities/use_cases/interface_adapters/frameworks` (`CLAUDE.md`).*
