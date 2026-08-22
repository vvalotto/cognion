Feature: Alineación visual del Banco de Preguntas con el prototipo aprobado (US-ADJ-01)

  Scenario: Listado de materias con el estilo del prototipo
    Given un Docente autenticado en "Materias"
    When la pantalla carga
    Then cada materia se muestra en una tarjeta con sombra e ícono
    And la tarjeta "+ Nueva materia" se muestra punteada con el "+" centrado
    And el breadcrumb muestra "Banco de preguntas › Materias"

  Scenario: Banco de preguntas con tags de color
    Given un Docente autenticado viendo el banco de una materia
    When la tabla de preguntas carga
    Then el Tipo de cada pregunta se muestra con un tag de color (azul opción múltiple, violeta V/F)
    And la Dificultad y la Importancia se muestran con tags de color (rojo alto, ámbar medio, verde bajo)
    And el botón "Eliminar" de cada fila tiene fondo sólido destructivo

  Scenario: Sin regresión funcional
    Given la suite de tests existente de Banco de Preguntas
    When se ejecuta después de este ajuste
    Then todos los tests siguen pasando sin cambios en los criterios de aceptación de US-2.1.9 a US-2.1.13
