@US-ADJ-45
Feature: Docente consulta la evolución temporal de aciertos (US-ADJ-45)
  Como Docente
  Quiero ver cómo evolucionó el % de aciertos de un estudiante puntual, comparado contra el
  promedio de su comisión, actividad tras actividad
  Para detectar si un estudiante viene mejorando o empeorando, no solo su promedio
  acumulado (RF-21)

  @happy-path
  Scenario: Serie individual con 3 evaluaciones
    Given un estudiante con 3 Evaluacion finalizadas en distintas fechas y % de acierto
    When un Docente hace GET .../estudiantes/{id}/evolucion-temporal
    Then recibe 200 con 3 puntos ordenados cronológicamente, cada uno con el título de su actividad

  @happy-path
  Scenario: Serie de comisión con participación parcial
    Given una comisión de 3 estudiantes donde solo 2 finalizaron la actividad A
    When un Docente hace GET .../comisiones/{id}/evolucion-temporal
    Then el punto de la actividad A promedia solo esos 2 estudiantes, no los 3

  @edge-case
  Scenario: Estudiante sin evaluaciones finalizadas
    Given un estudiante sin ninguna Evaluacion finalizada en la materia
    When un Docente consulta su evolución
    Then recibe 200 con lista vacía

  @error-case
  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET /analytics/materias/X/comisiones/{esa comisión}/evolucion-temporal
    Then recibe 422

  @error-case
  Scenario: Sin autenticación
    Given una request sin JWT válido
    When hace GET .../evolucion-temporal
    Then recibe 401

  @error-case
  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET .../evolucion-temporal
    Then recibe 403
