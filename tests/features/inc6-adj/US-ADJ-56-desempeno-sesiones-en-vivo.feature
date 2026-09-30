Feature: El desempeño incluye las sesiones en vivo (US-ADJ-56)

  Como Estudiante quiero ver en "Mi desempeño" las sesiones en vivo en las que participé,
  con mi puntaje y mi posición, para tener mi historial completo de la materia.
  Como Docente quiero ver lo mismo para el estudiante que elijo en "Desempeño por alumno".

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

  Scenario: Sesiones canceladas no aparecen
    Given una sesión en vivo cancelada antes de iniciar
    When el Estudiante abre "Mi desempeño"
    Then esa sesión no figura

  Scenario: Se unió pero no respondió
    Given un Estudiante que se unió a una sesión y no respondió ninguna pregunta
    When abre "Mi desempeño"
    Then la sesión figura con 0 puntos, 0 correctas y su posición

  Scenario: Período abierto no se mezcla
    Given un Estudiante con evaluaciones de período abierto y sesiones en vivo
    When abre "Mi desempeño"
    Then el resumen de período abierto es el mismo de antes
    And las sesiones en vivo están en su propia sección

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
