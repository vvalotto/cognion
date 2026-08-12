@US-2.1.4
Feature: Carga de pregunta Verdadero/Falso (US-2.1.4)
  Como Docente
  Quiero cargar una pregunta de Verdadero/Falso con su respuesta correcta y metadatos
  Para que quede disponible en el banco de su materia, lista para usarse en sesiones (RF-04, RF-05)

  Background:
    Given un Docente autenticado y un Banco existente para "Gestión de Proyectos"

  @cargar-pregunta-verdadero-falso @happy-path
  Scenario: Carga exitosa con respuesta Verdadero
    When ejecuta CargarPreguntaVerdaderoFalso con respuesta_correcta = true
    Then el sistema persiste la PreguntaPlantillaVerdaderoFalso con activa = true
    And se emite el evento PreguntaCargada

  @cargar-pregunta-verdadero-falso @happy-path
  Scenario: Carga exitosa con respuesta Falso
    When ejecuta CargarPreguntaVerdaderoFalso con respuesta_correcta = false
    Then el sistema persiste la PreguntaPlantillaVerdaderoFalso con activa = true
    And se emite el evento PreguntaCargada
