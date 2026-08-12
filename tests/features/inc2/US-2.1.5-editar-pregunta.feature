@US-2.1.5
Feature: Edición de pregunta (US-2.1.5)
  Como Docente
  Quiero editar una pregunta ya cargada (texto, opciones o respuesta, metadatos)
  Para corregir errores o ajustar su clasificación sin eliminarla y recrearla (RF-05)

  Background:
    Given un Docente autenticado

  @editar-pregunta @happy-path
  Scenario: Edición exitosa de opción múltiple
    Given una PreguntaPlantillaOpcionMultiple activa con 3 opciones
    When ejecuta EditarPregunta cambiando el texto y una opción
    Then el sistema persiste los cambios
    And se emite el evento PreguntaEditada

  @editar-pregunta @rechazo
  Scenario: Rechazo por dejar la pregunta sin opción correcta
    Given una PreguntaPlantillaOpcionMultiple activa
    When ejecuta EditarPregunta desmarcando la única opción correcta sin marcar otra
    Then el sistema rechaza la operación con OpcionesInvalidas

  @editar-pregunta @rechazo
  Scenario: Rechazo por editar una pregunta eliminada
    Given una PreguntaPlantilla con activa = false
    When ejecuta EditarPregunta sobre ella
    Then el sistema rechaza la operación con PreguntaInactiva
