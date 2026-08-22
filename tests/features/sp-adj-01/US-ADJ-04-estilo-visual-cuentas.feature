Feature: Alineación visual de Cuentas/Contraseñas con el prototipo aprobado (US-ADJ-04)

  Scenario: Listado de cuentas con tags de color y acción Ver
    Given un Administrador autenticado en "Cuentas"
    When la tabla de cuentas carga
    Then el Rol de cada cuenta se muestra con un tag de color
    And el Estado se muestra con un tag de color (verde activa, rojo bloqueada)
    And cada fila tiene un botón "Ver"

  Scenario: Detalle de cuenta con tarjeta de datos
    Given un Administrador autenticado viendo el detalle de una cuenta bloqueada
    When la pantalla carga
    Then el breadcrumb muestra "Administración › Cuentas › {nombre}"
    And los datos de la cuenta se muestran dentro de una tarjeta con sombra
    And el Rol y el Estado se muestran con tags de color

  Scenario: Confirmación de reseteo como pantalla de éxito
    Given un Administrador que acaba de resetear la contraseña de una cuenta
    When llega a la pantalla de confirmación
    Then ve un ícono de éxito (✓) y el mensaje dentro de una tarjeta centrada

  Scenario: Sin regresión funcional
    Given la suite de tests existente de Cuentas/Contraseñas
    When se ejecuta después de este ajuste
    Then todos los tests siguen pasando sin cambios en los criterios de aceptación de US-2.2.2 a US-2.2.9
