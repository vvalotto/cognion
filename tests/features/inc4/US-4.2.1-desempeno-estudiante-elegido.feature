@US-4.2.1
Feature: Docente consulta el desempeño de un estudiante elegido (US-4.2.1)
  Como Docente
  Quiero ver el desempeño de un estudiante que yo elijo — mismo detalle que ve el propio
  estudiante
  Para hacer seguimiento individual sin depender de que el estudiante comparta su propio
  resultado (RF-16)

  @happy-path
  Scenario: Estudiante con evaluaciones finalizadas
    Given un Docente autenticado y un Estudiante con 2 Evaluacion finalizadas en la materia X
    When el Docente hace GET /analytics/materias/X/estudiantes/{estudiante_id}/desempeno
    Then recibe 200 con 2 filas en "evaluaciones" y el "resumen" acumulado correcto

  @edge-case
  Scenario: Estudiante sin evaluaciones finalizadas
    Given un Docente autenticado y un Estudiante sin ninguna Evaluacion finalizada en la materia Y
    When el Docente hace GET /analytics/materias/Y/estudiantes/{estudiante_id}/desempeno
    Then recibe 200 con "evaluaciones": [] y "resumen" en cero, sin dividir por cero en porcentaje_acierto

  @error-case
  Scenario: Estudiante inexistente
    Given un Docente autenticado
    When hace GET /analytics/materias/X/estudiantes/{id-inexistente}/desempeno
    Then recibe 404

  @error-case
  Scenario: Sin autenticación
    Given una request sin JWT válido
    When hace GET /analytics/materias/X/estudiantes/{estudiante_id}/desempeno
    Then recibe 401

  @error-case
  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/estudiantes/{otro_estudiante_id}/desempeno
    Then recibe 403
