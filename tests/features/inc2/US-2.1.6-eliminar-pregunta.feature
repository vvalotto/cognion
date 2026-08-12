@US-2.1.6
Feature: Eliminación lógica de pregunta (US-2.1.6)
  Como Docente
  Quiero eliminar una pregunta que ya no quiero usar
  Para que deje de estar disponible en el banco y en nuevas sesiones, sin afectar sesiones
  pasadas que ya la usaron

  Background:
    Given un Docente autenticado

  @eliminar-pregunta @happy-path
  Scenario: Eliminación exitosa
    Given una PreguntaPlantilla activa
    When ejecuta EliminarPregunta sobre esa pregunta
    Then el sistema marca la pregunta como activa = false
    And la pregunta sigue existiendo en la base de datos
    And se emite el evento PreguntaEliminada

  @eliminar-pregunta @rechazo
  Scenario: Rechazo por pregunta inexistente
    Given un pregunta_id que no corresponde a ninguna PreguntaPlantilla
    When intenta ejecutar EliminarPregunta con ese id
    Then el sistema rechaza la operación con PreguntaNoExiste

  @eliminar-pregunta @rechazo
  Scenario: Rechazo por pregunta ya eliminada
    Given una PreguntaPlantilla con activa = false
    When ejecuta EliminarPregunta sobre ella
    Then el sistema rechaza la operación con PreguntaYaEliminada
