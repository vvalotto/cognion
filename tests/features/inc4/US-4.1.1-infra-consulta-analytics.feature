@US-4.1.1
Feature: Infraestructura de consulta del BC Analytics (US-4.1.1)
  Como Equipo de desarrollo
  Quiero el puerto de consulta y el adapter que le permiten a Analytics leer el event store
  de Actividad Evaluativa en modo solo-lectura
  Para que US-4.1.2 (y toda la Iteración 2) tengan de dónde leer el desempeño de un
  estudiante, sin que cada Use Case reimplemente su propia consulta sobre la tabla events
  ajena

  @happy-path
  Scenario: Estudiante con evaluaciones finalizadas en la materia
    Given un estudiante con 2 Evaluacion finalizadas en la materia X (una con 8 correctas y 2 incorrectas, otra con 5 correctas y 3 incorrectas)
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then el resultado tiene 2 filas con los conteos exactos de cada una

  @edge-case
  Scenario: Evaluación EnCurso, sin finalizar
    Given un estudiante con una Evaluacion EnCurso (sin EvaluacionFinalizada) en la materia X
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then esa Evaluacion no aparece en el resultado

  @edge-case
  Scenario: Respuesta con reintentos — cuenta solo la vigente
    Given una Evaluacion finalizada con 2 Respuesta para la misma pregunta_id (la primera incorrecta, la segunda mas reciente correcta)
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id de esa Evaluacion)
    Then esa pregunta cuenta como correcta, no como incorrecta

  @happy-path
  Scenario: Filtro por materia
    Given un estudiante con Evaluacion finalizadas en dos materias distintas
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then el resultado solo incluye las de la materia X

  @edge-case
  Scenario: Estudiante sin evaluaciones finalizadas
    Given un estudiante sin ninguna Evaluacion finalizada
    When se llama listar_evaluaciones_finalizadas(estudiante_id, materia_id=X)
    Then el resultado es una lista vacía
