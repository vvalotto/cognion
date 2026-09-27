@US-ADJ-58
Feature: Cancelar una sesión en vivo, finalizarla en cualquier etapa y no iniciarla sin participantes (US-ADJ-58)
  Como Docente
  Quiero cancelar una sesión que no voy a dar y terminar una en curso en cualquier momento
  Para que no queden sesiones colgadas ni tenga que forzar el cierre de una pregunta que no voy a usar

  # --- Cancelar (INV-AEV-10) ---

  @backend @happy-path
  Scenario: Cancelar una sesión en espera
    Given una sesión en vivo EnEspera
    When el Docente cancela la sesión
    Then la sesión queda Cancelada
    And deja de figurar en el listado de sesiones EnEspera y EnCurso de la Comisión

  @backend @happy-path
  Scenario: Los estudiantes en la sala se enteran de la cancelación
    Given una sesión en vivo EnEspera con dos Estudiantes unidos
    When el Docente cancela la sesión
    Then todos los conectados reciben el mensaje sesion_cancelada

  @backend @error-case
  Scenario: No se cancela una sesión iniciada
    Given una sesión en vivo EnCurso
    When el Docente intenta cancelar la sesión
    Then el sistema rechaza con SesionYaIniciada (422)
    And la sesión sigue EnCurso

  @backend @error-case
  Scenario: No se cancela dos veces
    Given una sesión en vivo Cancelada
    When el Docente intenta cancelar la sesión
    Then el sistema rechaza con SesionYaCancelada (422) sin emitir otro evento

  @backend @error-case
  Scenario: Nadie se puede unir a una sesión cancelada
    Given una sesión en vivo Cancelada
    When un Estudiante intenta unirse
    Then el sistema rechaza con SesionYaCancelada (422)

  @backend @error-case
  Scenario: Cancelar una sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión
    When el Docente intenta cancelar la sesión
    Then el sistema rechaza con SesionNoExiste (404)

  @backend @error-case
  Scenario: Solo el Docente cancela
    Given un usuario autenticado con rol Estudiante
    When intenta cancelar la sesión
    Then el sistema responde 403

  # --- Iniciar con participantes (INV-AEV-11) ---

  @backend @error-case
  Scenario: No se inicia sin participantes
    Given una sesión en vivo EnEspera sin Estudiantes unidos
    When el Docente intenta iniciar la sesión
    Then el sistema rechaza con SinParticipantes (422)
    And la sesión sigue EnEspera

  @backend @happy-path
  Scenario: Con un participante se inicia
    Given una sesión en vivo EnEspera con un Estudiante unido
    When el Docente inicia la sesión
    Then la sesión pasa a EnCurso

  # --- Finalizar en cualquier etapa (INV-AEV-03 modificado) ---

  @backend @happy-path
  Scenario: Finalizar con la pregunta sin opciones mostradas
    Given una sesión EnCurso en la pregunta 1 de 4, sin opciones mostradas
    When el Docente finaliza la sesión
    Then la sesión queda Finalizada
    And todos los conectados reciben el ranking final

  @backend @happy-path
  Scenario: Finalizar con las opciones a la vista
    Given una sesión EnCurso con las opciones mostradas y dos respuestas registradas
    When el Docente finaliza la sesión
    Then la sesión queda Finalizada
    And el ranking final incluye el puntaje de esas dos respuestas
    And la pregunta actual no se cerró (no se emite PreguntaEnVivoCerrada)

  # --- Frontend (validados con Vitest y los circuitos E2E de frontend/e2e/, no con pytest-bdd) ---

  @frontend @happy-path
  Scenario: El Docente cancela desde la sala de espera
    Given el Docente en la sala de espera de una sesión
    When pulsa "Cancelar sesión" y confirma
    Then vuelve al detalle de la Comisión y la sesión ya no figura en "Sesiones en vivo activas"

  @frontend @happy-path
  Scenario: El Estudiante ve la cancelación
    Given un Estudiante en la sala de espera
    When el Docente cancela la sesión
    Then ve "El Docente canceló la sesión" y un botón para volver a sus actividades

  @frontend @happy-path
  Scenario: Finalizar con la pregunta abierta pide confirmación
    Given el Docente proyectando una pregunta abierta
    When pulsa "Finalizar sesión"
    Then ve la confirmación y, al confirmar, el podio final

  @frontend @happy-path
  Scenario: Finalizar desde el histograma no pide confirmación
    Given el Docente en el histograma de una pregunta cerrada
    When pulsa "Finalizar sesión"
    Then pasa directo al podio final
