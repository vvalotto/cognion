@US-4.1.2
Feature: Estudiante consulta su propio desempeño en una materia (US-4.1.2)
  Como Estudiante
  Quiero ver mi desempeño en una materia — detalle por evaluación finalizada y un resumen
  acumulado
  Para saber cómo me está yendo en la cursada, sin tener que sumar a mano el resultado de
  cada evaluación (RF-15)

  @happy-path
  Scenario: Desempeño con evaluaciones finalizadas
    Given un Estudiante autenticado con 2 Evaluacion finalizadas en la materia X
    When hace GET /analytics/materias/X/mi-desempeno
    Then recibe 200 con 2 filas en "evaluaciones" ordenadas por finalizada_en descendente
    And recibe el "resumen" acumulado correcto (total_correctas, total_incorrectas, porcentaje_acierto, cantidad_evaluaciones)

  @edge-case
  Scenario: Materia sin evaluaciones finalizadas
    Given un Estudiante autenticado sin ninguna Evaluacion finalizada en la materia Y
    When hace GET /analytics/materias/Y/mi-desempeno
    Then recibe 200 con "evaluaciones": []
    And recibe "resumen" en cero, sin dividir por cero en porcentaje_acierto

  @error-case
  Scenario: Sin autenticación
    Given una request sin JWT válido
    When hace GET /analytics/materias/X/mi-desempeno
    Then recibe 401

  @error-case
  Scenario: Rol distinto de Estudiante
    Given un Docente autenticado
    When hace GET /analytics/materias/X/mi-desempeno
    Then recibe 403

  @edge-case
  Scenario: estudiante_id siempre sale del token, nunca de la URL
    Given un Estudiante A autenticado y un Estudiante B con evaluaciones finalizadas en la materia X
    When el Estudiante A hace GET /analytics/materias/X/mi-desempeno
    Then recibe únicamente su propio desempeño, nunca el del Estudiante B
