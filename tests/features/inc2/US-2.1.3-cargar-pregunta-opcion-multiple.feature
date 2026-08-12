@US-2.1.3
Feature: Carga de pregunta de opción múltiple (US-2.1.3)
  Como Docente
  Quiero cargar una pregunta de opción múltiple con sus opciones y metadatos
  Para que quede disponible en el banco de su materia, lista para usarse en sesiones (RF-04, RF-05)

  Background:
    Given un Docente autenticado y un Banco existente para "Ingeniería de Software"

  @cargar-pregunta-opcion-multiple @happy-path
  Scenario: Carga exitosa
    When ejecuta CargarPreguntaOpcionMultiple con 3 opciones y una marcada como correcta
    Then el sistema persiste la PreguntaPlantillaOpcionMultiple con activa = true
    And se emite el evento PreguntaCargada

  @cargar-pregunta-opcion-multiple @error
  Scenario: Rechazo por ninguna opción correcta
    When ejecuta CargarPreguntaOpcionMultiple con 3 opciones y ninguna marcada como correcta
    Then el sistema rechaza la operación con OpcionesInvalidas
    And no se persiste ninguna pregunta nueva

  @cargar-pregunta-opcion-multiple @error
  Scenario: Rechazo por más de una opción correcta
    When ejecuta CargarPreguntaOpcionMultiple con 2 opciones marcadas como correctas
    Then el sistema rechaza la operación con OpcionesInvalidas
    And no se persiste ninguna pregunta nueva

  @cargar-pregunta-opcion-multiple @error
  Scenario: Rechazo por menos de 2 opciones
    When ejecuta CargarPreguntaOpcionMultiple con una única opción
    Then el sistema rechaza la operación con OpcionesInvalidas
    And no se persiste ninguna pregunta nueva
