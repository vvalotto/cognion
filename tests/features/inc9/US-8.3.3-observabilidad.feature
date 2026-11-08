@US-8.3.3
Feature: Observabilidad mínima: logs estructurados y healthcheck de readiness (US-8.3.3)
  Como responsable de operar Cognión
  Quiero saber si la aplicación está viva y si realmente puede atender pedidos, y poder leer sus logs con una herramienta
  Para distinguir "el proceso está en pie" de "la base de datos no responde" y diagnosticar un incidente sin leer texto suelto a ojo

  @salud @sin-regresion
  Scenario: El healthcheck de vida no depende de la base
    Given la aplicación con la base de datos caída
    When se consulta /health
    Then responde 200 con status ok

  @salud @happy-path
  Scenario: Readiness con la base disponible
    Given la aplicación con la base de datos disponible
    When se consulta /health/ready
    Then responde 200 con status ok y base_de_datos ok

  @salud @error
  Scenario: Readiness con la base caída
    Given la aplicación con la base de datos caída
    When se consulta /health/ready
    Then responde 503 con status error y base_de_datos no disponible
    And el cuerpo no incluye el motivo, la dirección ni la contraseña de la base
    And el error queda en el log sin la contraseña

  @salud @autenticacion
  Scenario: Readiness no pide credenciales
    Given la aplicación con la base de datos disponible
    When se consulta /health/ready sin Authorization
    Then responde 200

  @logs @sin-regresion
  Scenario: Formato texto por defecto
    Given la aplicación arrancada sin LOG_FORMAT
    When la aplicación escribe un mensaje de log
    Then la línea tiene el formato de texto de siempre

  @logs @json
  Scenario: Formato json
    Given la aplicación arrancada con LOG_FORMAT=json
    When la aplicación y uvicorn escriben mensajes de log
    Then cada línea es un JSON válido con ts, nivel, logger y mensaje

  @logs @json
  Scenario: Una excepción sigue siendo una sola línea
    Given la aplicación arrancada con LOG_FORMAT=json
    When se registra un error con su excepción
    Then sale una sola línea JSON con el campo excepcion

  @logs @seguridad
  Scenario: Los tokens siguen enmascarados en json
    Given la aplicación arrancada con LOG_FORMAT=json
    When llega un pedido con un token en la query y otro a la ruta de una invitación
    Then ninguna línea del log contiene el token y aparece ***

  @logs @error
  Scenario: Un formato inválido impide arrancar
    Given una configuración con LOG_FORMAT=xml
    When se intenta arrancar la aplicación
    Then el arranque falla y el mensaje nombra LOG_FORMAT y los valores texto y json

  @operacion
  Scenario: cognion.sh estado muestra los dos healthchecks
    Given la salida de los dos healthchecks de una aplicación con la base caída
    When cognion.sh estado arma el resumen
    Then muestra la respuesta de /api/health y la de /api/health/ready indicando el 503
