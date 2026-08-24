Feature: Paginación del banco de preguntas (US-ADJ-03)

  Scenario: Banco con más de una página de resultados
    Given un banco con 71 preguntas activas y tamaño de página 20
    When un Docente abre el banco de esa materia
    Then ve las primeras 20 preguntas, ordenadas por fecha de creación
    And los controles de paginación muestran 4 páginas y el botón "Siguiente" habilitado

  Scenario: Cambiar de página
    Given un Docente viendo la página 1 de un banco con 4 páginas
    When hace clic en "Siguiente" (o en el número de página 2)
    Then ve las preguntas 21 a 40
    And el botón "Anterior" queda habilitado

  Scenario: Cambiar un filtro reinicia la paginación
    Given un Docente viendo la página 3 de un banco filtrado por "Unidad 2"
    When cambia el filtro de Dificultad
    Then vuelve a la página 1 con el nuevo filtro combinado aplicado

  Scenario: Banco con una sola página
    Given un banco con 5 preguntas activas
    When un Docente lo abre
    Then ve las 5 preguntas sin controles de paginación (o con "Anterior"/"Siguiente" deshabilitados)
