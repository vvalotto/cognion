@US-1.1.4
Feature: Autenticación con JWT por rol (US-1.1.4)
  Como Docente, Administrador o Estudiante con una cuenta ya creada
  Quiero autenticarme con mi email y contraseña
  Para recibir un JWT con mi rol y poder operar el resto del sistema según los permisos
  que me corresponden (RF-02)

  @autenticacion @happy-path
  Scenario: Login exitoso de un Docente
    Given un Usuario con perfil Docente y contraseña "Docente#2026"
    When ejecuta IniciarSesion(email, "Docente#2026")
    Then el sistema emite un JWT con claim rol "docente"
    And el JWT expira 60 minutos después de la emisión
    And se emite el evento SesionIniciada

  @autenticacion @happy-path
  Scenario: Login exitoso de un Administrador
    Given un Usuario con perfil Administrador y contraseña correcta
    When ejecuta IniciarSesion(email, password correcta)
    Then el sistema emite un JWT con claim rol "administrador"

  @autenticacion @happy-path
  Scenario: Login exitoso de un Estudiante
    Given un Usuario con perfil Estudiante y contraseña correcta
    When ejecuta IniciarSesion(email, password correcta)
    Then el sistema emite un JWT con claim rol "estudiante"

  @autenticacion @error
  Scenario: Rechazo por contraseña incorrecta
    Given un Usuario existente
    When ejecuta IniciarSesion(email, password incorrecta)
    Then el sistema rechaza la operación con CredencialesInvalidas
    And el mensaje no distingue si el email existe

  @autenticacion @error
  Scenario: Rechazo por email inexistente
    Given ningún Usuario registrado con ese email
    When ejecuta IniciarSesion(email inexistente, cualquier password)
    Then el sistema rechaza la operación con CredencialesInvalidas
    And el mensaje es idéntico al del caso de contraseña incorrecta
