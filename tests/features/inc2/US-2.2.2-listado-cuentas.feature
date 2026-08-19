@US-2.2.2
Feature: Listado de cuentas con filtros (US-2.2.2)
  Como Administrador
  Quiero ver el listado de todas las cuentas de usuarios, filtrable por rol, estado y
  búsqueda por nombre/email
  Para encontrar rápido la cuenta que necesito gestionar cuando un docente o estudiante
  reporta un problema (RF-03)

  @listado-cuentas @happy-path
  Scenario: Listado sin filtros
    Given existen cuentas de distintos roles y estados
    When un Administrador ejecuta ListarCuentas() sin filtros
    Then el sistema devuelve todas las cuentas

  @listado-cuentas @happy-path
  Scenario: Filtro combinado por rol y estado
    Given existen Estudiantes activos y bloqueados, y Docentes activos
    When un Administrador ejecuta ListarCuentas(rol=estudiante, estado=bloqueada)
    Then el sistema devuelve solo los Estudiantes con bloqueada = true

  @listado-cuentas @happy-path
  Scenario: Búsqueda por email parcial
    Given existe una cuenta con email "mgonzalez@fiuner.edu.ar"
    When un Administrador ejecuta ListarCuentas(busqueda="mgonzalez")
    Then esa cuenta aparece en el resultado
