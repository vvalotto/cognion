Feature: Paginación del listado de cuentas (US-ADJ-05)

  Scenario: Listado con más de una página de resultados
    Given más de 20 cuentas registradas que matchean los filtros activos
    When un Administrador abre el listado de cuentas
    Then ve las primeras 20 cuentas, ordenadas por fecha de creación
    And los controles de paginación muestran la cantidad de páginas correspondiente

  Scenario: Cambiar de página
    Given un Administrador viendo la página 1 de un listado con más de una página
    When hace clic en "Siguiente" (o en el número de página 2)
    Then ve las cuentas 21 a 40
    And el botón "Anterior" queda habilitado

  Scenario: Cambiar un filtro reinicia la paginación
    Given un Administrador viendo la página 2 filtrado por rol "Estudiante"
    When cambia el filtro de Estado
    Then vuelve a la página 1 con el nuevo filtro combinado aplicado

  Scenario: Listado con una sola página
    Given menos de 20 cuentas que matchean los filtros
    When un Administrador lo abre
    Then ve todas las cuentas sin controles de paginación (o con "Anterior"/"Siguiente" deshabilitados)
