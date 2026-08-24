@US-2.2.6
Feature: Listado de cuentas en la UI (US-2.2.6)
  Como Administrador
  Quiero ver el listado de cuentas desde la aplicación, con filtros por rol, estado y
  búsqueda
  Para ubicar la cuenta que necesito gestionar sin depender de una consola o de la base de
  datos (RF-03)

  @frontend @happy-path
  Scenario: Filtrar por rol y estado
    Given un Administrador en el listado de cuentas
    When selecciona rol "Estudiante" y estado "Bloqueada"
    Then la tabla muestra solo Estudiantes con cuenta bloqueada

  @frontend @happy-path
  Scenario: Navegar al detalle
    Given un Administrador en el listado de cuentas
    When hace clic en una fila
    Then el sistema navega al detalle de esa cuenta
