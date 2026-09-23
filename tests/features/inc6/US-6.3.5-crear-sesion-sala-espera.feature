@US-6.3.5
Feature: Docente crea la sesión y abre la sala de espera (US-6.3.5)

  @happy-path
  Scenario: Entrada desde el detalle de la Comisión
    Given el detalle de una Comisión del Docente
    When el Docente pulsa "+ Nueva sesión en vivo"
    Then abre el formulario con el breadcrumb de esa Comisión y sin selector de Comisión

  @happy-path
  Scenario: Creación exitosa
    Given el formulario completo con cantidad de preguntas y tiempo límite
    When el Docente crea la sesión
    Then navega a la sala de espera con el estado EnEspera

  @error-case
  Scenario: Validación de cliente
    Given el formulario con tiempo límite 0
    When el Docente intenta crear
    Then ve el error y no se envía la request

  @error-case
  Scenario: Preguntas insuficientes
    Given un banco con menos preguntas que las pedidas
    When el Docente crea la sesión
    Then ve el mensaje del servidor y permanece en el formulario

  @happy-path
  Scenario: Los participantes aparecen en vivo
    Given la sala de espera abierta
    When un Estudiante se une
    Then su nombre aparece como chip sin recargar

  @happy-path
  Scenario: Iniciar la sesión
    Given la sala de espera con participantes
    When el Docente pulsa "Iniciar sesión"
    Then navega a la proyección de la primera pregunta

  @happy-path
  Scenario: Iniciar sin participantes
    Given la sala de espera sin participantes
    When el Docente inicia
    Then ve la advertencia y la sesión se inicia igual

  @happy-path
  Scenario: Recuperar una sesión activa
    Given una sesión EnCurso de la Comisión y el Docente que cerró la pestaña
    When abre el detalle de la Comisión
    Then ve la sesión con "Continuar" que lleva a la proyección

  @happy-path
  Scenario: Recargar la sala con la sesión ya iniciada
    Given una sesión que ya está EnCurso
    When el Docente recarga la sala de espera
    Then es redirigido a la proyección

  @happy-path
  Scenario: Reconexión de la sala
    Given la sala de espera y una caída del canal
    When se reconecta
    Then la lista de participantes se vuelve a cargar y desaparece el indicador
