# US-ADJ-56: El desempeño del Estudiante incluye las sesiones en vivo

**Estado**: `Especificada`
**Iteracion / Sprint**: sin asignar — se implementa **después** del cierre de `BL-011` (decisión de Víctor, 2026-09-25)
**Tipo**: `feat` backend + frontend
**Agregado principal afectado**: ninguno nuevo (lectura; Analytics no tiene aggregate propio, `BC-analytics-modelo.md` §2)
**Bounded Context**: Analytics (lee de Actividad Evaluativa por puerto, `ADR-006`)
**Origen**: pregunta de Víctor durante la validación manual de `US-6.3.10` (2026-09-25): "los resultados de la
actividad en vivo, ¿no se guardan como performance de los estudiantes?". No — hueco de alcance entre incrementos.

---

## Descripcion (lenguaje de negocio)

Como **Estudiante**,
quiero **ver en "Mi desempeño" las sesiones en vivo en las que participé, con mi puntaje y mi posición**,
para **tener mi historial completo de la materia, no solo las actividades de período abierto**.

Como **Docente**,
quiero **ver lo mismo para el estudiante que elijo en "Desempeño por alumno"**,
para **seguir la participación de cada alumno también en las dinámicas en clase**.

---

## Contexto del dominio

### Problema

`RF-15` pide explícitamente *"para sesiones en vivo, ve su puntaje y posición en el ranking"*, con el criterio
*"el historial refleja todas las sesiones en las que participó el estudiante"*. `RF-16` pide al Docente
*"respuestas correctas e incorrectas por sesión"*.

En el Incremento 4 el modelo de Analytics lo dejó fuera con una nota de alcance
(`BC-analytics-modelo.md`, "Nota de alcance RF-15": las sesiones en vivo no existían todavía, Incremento 6). El
Incremento 6 no lo retomó y `RF-15` quedó **Validado** en `BL-006` con ese alcance acotado. Hoy el adaptador de
Analytics (`evaluacion_desempeno_consulta_port_in_process.py`) solo lee agregados `Evaluacion` (período abierto).

### Los datos ya existen (no se guarda nada nuevo)

| Dato | Origen |
|---|---|
| Sesiones de la materia y su fecha | evento `SesionEnVivoCreada` (`materia_id`, `comision_id`, `ocurrido_en`) |
| Solo sesiones terminadas | evento `SesionEnVivoFinalizada` |
| En qué sesiones participó el Estudiante | evento `EstudianteUnido` (`sesion_id`, `estudiante_id`) |
| Correctas / incorrectas / puntaje por respuesta | evento `RespuestaEnVivoRegistrada` (`es_correcta`, `puntaje`) |
| Puntaje final y posición | read model `ranking_por_sesion` (`puntaje_acumulado`; la posición se deriva ordenando la sesión, mismo criterio que `ObtenerRankingDeSesion`) |

### Modelo involucrado (propuesta, se confirma en la Fase 2)

| Elemento | Responsabilidad |
|---|---|
| Puerto nuevo de Analytics hacia Actividad Evaluativa (in-process, `ADR-006`) | Listar las participaciones en vivo **finalizadas** de un estudiante, opcionalmente por materia, con fecha, puntaje, posición, total de participantes, correctas e incorrectas |
| Use case de lectura (o ampliación de `ObtenerDesempenoEstudianteUseCase`, `US-4.1.2`) | Sumar la sección "sesiones en vivo" a la respuesta, **sin mezclar** sus conteos con los de período abierto |
| Endpoint | Ampliar `GET /analytics/materias/{materia_id}/mi-desempeno` y su equivalente del Docente (`US-4.2.1`), o un endpoint hermano — se decide en la Fase 2 cuidando el CBO de los controllers |
| Frontend | Sección "Sesiones en vivo" en `MiDesempeno.tsx` y `DesempenoPorAlumno.tsx` (componente compartido `DesempenoResumenDetalle.tsx`, `US-4.2.5`) |

---

## Especificacion del comportamiento

### Precondicion

- `BL-011` cerrada (Incremento 6).
- **Gate UX:** ampliar `docs/design/ux/wireframes-analytics.md` (y su prototipo) con la sección "Sesiones en vivo"
  y aprobarla **antes** de tocar `frontend/`.

### Postcondicion

- "Mi desempeño" (Estudiante) y "Desempeño por alumno" (Docente) muestran, por materia, una fila por sesión en
  vivo **finalizada** en la que participó el estudiante: fecha, puntaje final, posición ("3° de 14"), correctas e
  incorrectas.
- El resumen acumulado de período abierto **no cambia** (las sesiones en vivo se muestran en su propia sección).
- Sin sesiones en vivo: la sección dice "Todavía no participaste en sesiones en vivo" (Estudiante) o el
  equivalente para el Docente.
- Sesiones en curso o en espera **no** aparecen.
- `docs/traceability/matrix.md` y `BC-analytics-modelo.md` reflejan que `RF-15`/`RF-16` cubren también el modo en vivo.

---

## Criterios de aceptacion

```gherkin
Feature: El desempeño incluye las sesiones en vivo (US-ADJ-56)

  Scenario: El Estudiante ve sus sesiones en vivo
    Given un Estudiante que participó en dos sesiones en vivo finalizadas de su materia
    When abre "Mi desempeño"
    Then ve una fila por sesión con fecha, puntaje, posición, correctas e incorrectas

  Scenario: La posición es la del ranking final
    Given una sesión en la que el Estudiante quedó 3° de 14
    When mira esa fila
    Then dice "3° de 14" y el mismo puntaje que vio en el resultado final de la sesión

  Scenario: Sesiones que no terminaron no aparecen
    Given una sesión en vivo todavía en curso
    When el Estudiante abre "Mi desempeño"
    Then esa sesión no figura

  Scenario: Se unió pero no respondió
    Given un Estudiante que se unió a una sesión y no respondió ninguna pregunta
    When abre "Mi desempeño"
    Then la sesión figura con 0 puntos, 0 correctas y su posición

  Scenario: Período abierto no se mezcla
    Given un Estudiante con evaluaciones de período abierto y sesiones en vivo
    When abre "Mi desempeño"
    Then el resumen de período abierto es el mismo de antes y las sesiones en vivo están en su propia sección

  Scenario: Sin sesiones en vivo
    Given un Estudiante que nunca participó en una sesión en vivo
    When abre "Mi desempeño"
    Then la sección dice "Todavía no participaste en sesiones en vivo"

  Scenario: El Docente ve lo mismo para un alumno
    Given el Docente en "Desempeño por alumno" con un estudiante elegido
    When mira su desempeño
    Then ve la misma sección de sesiones en vivo de ese estudiante

  Scenario: Otra materia no se mezcla
    Given un Estudiante con sesiones en vivo en dos materias
    When elige una materia
    Then solo ve las sesiones de esa materia
```

---

## Impacto arquitectonico

- [x] Sí — puerto nuevo de Analytics hacia Actividad Evaluativa (lectura in-process, `ADR-006`), mismo patrón que
  `EvaluacionDesempenoConsultaPort` (`US-4.1.1`). Sin eventos ni tablas nuevas.

**Capa(s) afectadas:** `src/analytics/` (entities/ports, use_cases, interface_adapters, frameworks) + `frontend/`.

---

## Decisiones abiertas (para la Fase 2, con Víctor)

1. **RF-17 y RF-20 a RF-23** (tasa de error por tema, desempeño por comisión, evolución, ranking de preguntas
   falladas, completitud): ¿incluyen también las respuestas en vivo? Esta US **no** los cubre; si se decide que sí,
   van en US aparte.
2. ¿Un acumulado general que sume período abierto + vivo, o siempre separados? Esta US los deja **separados**.
3. ¿El Estudiante puede ver el detalle pregunta por pregunta de una sesión en vivo? Esta US **no** lo incluye
   (la revisión por pregunta es de período abierto, RF-13).

---

## Fuente de verdad UX

- `docs/design/ux/wireframes-analytics.md` — **a ampliar** con la sección "Sesiones en vivo" (gate previo).
- Pantallas existentes: `MiDesempeno.tsx`, `DesempenoPorAlumno.tsx`, `DesempenoResumenDetalle.tsx`.

---

## Referencias

- `docs/rf/RF_v1.md` RF-15, RF-16
- `docs/design/domain/BC-analytics-modelo.md` (nota de alcance RF-15)
- Backend: `US-4.1.1`, `US-4.1.2`, `US-4.2.1` (Analytics); `US-6.1.3`, `US-6.2.3`, `US-6.2.4`, `US-6.2.7` (datos del modo en vivo)
- Origen: validación manual de `US-6.3.10`
