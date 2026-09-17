@US-ADJ-46
Feature: Docente consulta el ranking de preguntas más falladas (US-ADJ-46)
  Como Docente
  Quiero ver qué preguntas puntuales concentran más errores, ordenadas por tasa de error, para
  toda la materia o acotado a una comisión
  Para revisar el enunciado de la pregunta más problemática, no solo el tema al que pertenece
  (RF-22)

  @happy-path
  Scenario: Materia completa, sin filtrar por comisión
    Given una materia con respuestas vigentes de 5 preguntas distintas
    When un Docente hace GET /analytics/materias/X/ranking-preguntas-falladas
    Then recibe 200 con las 5 preguntas ordenadas por tasa de error descendente, con enunciado

  @happy-path
  Scenario: Acotado a una comisión
    Given la misma materia de arriba
    When un Docente hace GET .../ranking-preguntas-falladas?comision_id=C1
    Then recibe 200 con el ranking calculado solo sobre las respuestas de C1

  @happy-path
  Scenario: Tasa de error prevalece sobre conteo bruto
    Given una pregunta con 1 presentación y 1 fallo, y otra con 50 presentaciones y 10 fallos
    When se calcula el ranking
    Then la primera aparece antes que la segunda (100% > 20%)

  @edge-case
  Scenario: Materia sin ninguna pregunta presentada
    Given una materia sin ninguna Respuesta vigente
    When un Docente consulta el ranking
    Then recibe 200 con lista vacía

  @error-case
  Scenario: Comisión que no pertenece a la materia
    Given una comisión de otra materia
    When un Docente hace GET .../ranking-preguntas-falladas?comision_id={esa comisión}
    Then recibe 422

  @error-case
  Scenario: Rol distinto de Docente
    Given un Estudiante autenticado
    When hace GET /analytics/materias/X/ranking-preguntas-falladas
    Then recibe 403
