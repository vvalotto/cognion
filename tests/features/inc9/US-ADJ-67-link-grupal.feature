@US-ADJ-67
Feature: El Docente genera un link de invitación grupal con vencimiento corto (US-ADJ-67)
  Como Docente que da una clase
  Quiero generar un solo link que toda la comisión pueda usar durante un tiempo corto, y poder desactivarlo
  Para que mis estudiantes se registren sin que yo reparta un link por persona y sin dejar un link abierto para siempre

  @grupal @happy-path
  Scenario: Generar un link grupal con la duración por defecto
    Given una comisión con un Docente asignado
    When el Docente genera un link grupal sin indicar la duración
    Then el link se crea y vence en 1 hora

  @grupal @duracion
  Scenario Outline: Duraciones elegibles
    Given una comisión con un Docente asignado
    When el Docente genera un link grupal de <minutos> minutos
    Then el link se crea y vence en <minutos> minutos

    Examples:
      | minutos |
      | 15      |
      | 60      |
      | 1440    |

  @grupal @error
  Scenario: Una duración no elegible se rechaza
    Given una comisión con un Docente asignado
    When el Docente genera un link grupal de 90 minutos
    Then la respuesta es 422

  @grupal @autorizacion
  Scenario: Un Docente no asignado no genera ni desactiva links de la comisión
    Given una comisión con un Docente asignado
    And otro Docente que no está asignado a esa comisión
    When ese otro Docente intenta generar un link grupal
    And ese otro Docente intenta desactivar el link
    Then ambas respuestas son 403

  @grupal @happy-path
  Scenario: Varios estudiantes se registran con el mismo link
    Given un link grupal vigente
    When 3 estudiantes se registran con ese link
    Then los 3 registros se crean en la comisión
    And el link informa 3 registrados

  @grupal @concurrencia
  Scenario: Registros simultáneos no pierden ninguna cuenta ni ninguna cuenta del contador
    Given un link grupal vigente
    When 20 estudiantes se registran a la vez con ese link
    Then los 20 registros se crean
    And el link informa 20 registrados

  @grupal @vencimiento
  Scenario: Un link vencido ya no sirve
    Given un link grupal que ya venció
    When un estudiante consulta el link y se intenta registrar
    Then ambas respuestas informan invitacion_vencida

  @grupal @desactivar
  Scenario: Desactivar el link
    Given un link grupal vigente con 2 estudiantes ya registrados
    When el Docente desactiva el link
    And un estudiante consulta el link y se intenta registrar
    Then ambas respuestas informan invitacion_revocada
    And los 2 estudiantes registrados siguen en la comisión
    And desactivar el link por segunda vez no falla

  @grupal @un-solo-vigente
  Scenario: Generar un link nuevo desactiva el anterior
    Given un link grupal vigente
    When el Docente genera otro link grupal para la misma comisión
    Then el link anterior informa invitacion_revocada
    And el link nuevo permite registrarse

  @grupal @consulta
  Scenario: Consultar la última invitación grupal de la comisión
    Given una comisión con un Docente asignado
    When el Docente consulta la última invitación grupal y todavía no generó ninguna
    Then no hay ninguna invitación grupal
    When el Docente genera un link grupal y lo consulta
    Then la consulta informa estado vigente, el token, el vencimiento y 0 registrados
    When el Docente desactiva el link y lo consulta
    Then la consulta informa estado revocada y no devuelve el token

  @grupal @sin-regresion
  Scenario: El link individual no cambia
    Given una invitación individual vigente
    When un estudiante se registra con ella y un segundo estudiante la intenta usar
    Then el primero se registra y el segundo recibe invitacion_usada
    And la invitación individual vence a los 7 días

  @grupal @registro
  Scenario: Una contraseña inválida no cuenta como uso y no confunde el link
    Given un link grupal vigente
    When un estudiante se intenta registrar con una contraseña que no cumple la política
    Then la respuesta informa password_invalida
    And el link informa 0 registrados y sigue sirviendo

  @grupal @registro
  Scenario: Un email ya registrado no cuenta como uso
    Given un link grupal vigente con 1 estudiante ya registrado
    When otro estudiante se intenta registrar con el mismo email
    Then la respuesta es 409
    And el link sigue informando 1 registrado
