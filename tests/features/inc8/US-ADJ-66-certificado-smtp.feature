@US-ADJ-66
Feature: El envío de email valida el certificado del servidor SMTP (US-ADJ-66)
  Como responsable de operar Cognión con emails reales
  Quiero que la aplicación compruebe que el servidor de correo es el que dice ser antes de enviarle usuario, contraseña y mensajes
  Para que nadie que controle la red pueda leer las credenciales SMTP ni los links de recuperación e invitación

  @certificado @happy-path
  Scenario: Certificado válido
    Given un servidor SMTP con un certificado firmado por una autoridad de confianza y el nombre correcto
    When la aplicación envía un email con una cuenta autenticada
    Then el email sale

  @certificado @error
  Scenario: Certificado autofirmado o de otra autoridad
    Given un servidor SMTP con un certificado que no firma una autoridad de confianza
    When la aplicación envía un email con una cuenta autenticada
    Then el envío falla por certificado no verificable
    And el servidor no recibe usuario ni contraseña
    And el servidor no recibe el mensaje

  @certificado @error
  Scenario: El nombre del certificado no coincide con el servidor
    Given un servidor SMTP con un certificado válido emitido para otro nombre
    When la aplicación envía un email con una cuenta autenticada
    Then el envío falla por certificado no verificable
    And el servidor no recibe usuario ni contraseña

  @certificado @cuenta-por-materia
  Scenario: Una materia con certificado inválido no afecta a las demás
    Given una materia con cuenta propia cuyo servidor tiene un certificado inválido
    And otra materia que usa la cuenta global con un certificado válido
    When la aplicación envía un email de cada materia
    Then el email de la primera materia falla por certificado no verificable
    And el email de la segunda materia sale

  @sin-regresion
  Scenario: Servidor local de pruebas sin autenticación
    Given un servidor SMTP local sin usuario configurado
    When la aplicación envía un email
    Then el email sale sin negociar TLS

  @sin-regresion
  Scenario: Modo consola
    Given el modo de envío consola
    When la aplicación envía un email
    Then no se abre ninguna conexión

  @certificado @observabilidad
  Scenario: El error es visible y no expone secretos
    Given un servidor SMTP con un certificado que no firma una autoridad de confianza
    When la aplicación envía un email con una cuenta autenticada
    Then el log indica que el certificado no se pudo verificar
    And el log no contiene la contraseña ni el cuerpo del email
