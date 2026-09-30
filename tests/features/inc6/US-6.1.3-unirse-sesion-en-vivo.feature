@US-6.1.3
Feature: Estudiante se une a una sesión en vivo (US-6.1.3)
  Como Estudiante
  Quiero unirme a una sesión en vivo desde mi portal, ya sea mientras espera que arranque o
  incluso después de que ya empezó
  Para participar de la dinámica en el momento, sin quedar afuera si llegué un poco tarde
  (RF-08)

  @backend @happy-path
  Scenario: Unión mientras la sesión está en espera
    Given una sesión en vivo en estado EnEspera
    When el Estudiante se une
    Then se crea su ParticipacionEnVivo y aparece en participantes_por_sesion
    And el Docente conectado al canal recibe la lista de participantes actualizada

  @backend @happy-path
  Scenario: Unión tardía, sesión ya en curso
    Given una sesión en vivo en estado EnCurso, en la tercera pregunta
    When un Estudiante que no se había unido antes se une ahora
    Then su ParticipacionEnVivo se crea igualmente, sin respuestas previas registradas

  @backend @idempotencia
  Scenario: Unión idempotente
    Given un Estudiante ya unido a una sesión
    When intenta unirse de nuevo
    Then el sistema responde 200 sin crear una segunda ParticipacionEnVivo

  @backend @error
  Scenario: Rechazo por sesión finalizada
    Given una sesión en vivo en estado Finalizada
    When un Estudiante intenta unirse
    Then el sistema rechaza la operación con SesionYaFinalizada (422)

  @backend @error
  Scenario: Sesión inexistente
    Given un sesion_id que no corresponde a ninguna sesión en vivo
    When un Estudiante intenta unirse
    Then el sistema rechaza la operación con SesionNoExiste (404)
