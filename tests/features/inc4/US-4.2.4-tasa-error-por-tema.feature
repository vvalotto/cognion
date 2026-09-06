@US-4.2.4
Feature: Docente consulta la tasa de error por unidad/tema de una materia (US-4.2.4)
  Como Docente
  Quiero ver qué unidades/temas concentran más errores en una materia, para toda la materia
  o acotado a una comisión
  Para decidir dónde reforzar la enseñanza sin revisar evaluación por evaluación (RF-17)

  @happy-path
  Scenario: Materia completa, sin filtrar por comisión
    Given una materia con Evaluacion finalizadas de 2 comisiones distintas
    When un Docente hace GET /analytics/materias/X/tasa-error-por-tema
    Then recibe 200 con la tasa de error agregada de ambas comisiones, ordenada descendente

  @happy-path
  Scenario: Acotado a una comisión
    Given la misma materia de arriba
    When un Docente hace GET /analytics/materias/X/tasa-error-por-tema?comision_id=C1
    Then recibe 200 con la tasa de error calculada solo sobre los estudiantes de C1

  @edge-case
  Scenario: Materia sin evaluaciones finalizadas
    Given una materia sin ninguna Evaluacion finalizada
    When un Docente hace GET /analytics/materias/Y/tasa-error-por-tema
    Then recibe 200 con lista vacía

  @error-case
  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET /analytics/materias/X/tasa-error-por-tema?comision_id={esa comisión}
    Then recibe 422

  @error-case
  Scenario: Sin autenticación
    Given una request sin JWT válido
    When hace GET /analytics/materias/X/tasa-error-por-tema
    Then recibe 401

  @error-case
  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/tasa-error-por-tema
    Then recibe 403
