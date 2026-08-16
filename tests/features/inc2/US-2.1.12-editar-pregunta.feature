@US-2.1.12
Feature: Edición de pregunta desde la UI (US-2.1.12)
  Como Docente
  Quiero editar una pregunta existente desde la UI
  Para corregir errores o ajustar su clasificación sin recrearla (RF-05)

  @frontend @happy-path
  Scenario: Edición exitosa
    Given un Docente en la pantalla de edición de una PreguntaPlantillaOpcionMultiple
    When modifica el texto y guarda
    Then el sistema persiste los cambios
    And vuelve al banco filtrado, mostrando el texto actualizado

  @frontend @edge-case
  Scenario: Rechazo de cliente por opciones inválidas
    Given un Docente editando una pregunta de Opción Múltiple
    When deja más de una opción marcada como correcta e intenta guardar
    Then el formulario bloquea el envío con un mensaje de validación
    And no se llama al backend
