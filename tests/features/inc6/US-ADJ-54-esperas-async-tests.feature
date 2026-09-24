# language: es
@US-ADJ-54
Feature: Esperas asincrónicas correctas en tests (US-ADJ-54)

  Scenario: Los casos confirmados esperan el dato
    Given los tests de EditarCuenta, MateriasActividades y EditarMateria
    When se revisa cómo verifican los valores que llegan después del primer render
    Then esperan el dato con reintento, no solo el elemento

  Scenario: Barrido documentado
    Given todos los tests del frontend
    When se busca el patrón de espera incompleta
    Then el reporte lista cada caso encontrado con su corrección o su descarte

  Scenario: Sin fallos aleatorios en corridas repetidas
    Given la suite completa
    When se corre "npm run test" 3 veces seguidas y "npm run test:coverage" 3 veces seguidas
    Then las 6 corridas pasan completas

  Scenario: Sin cambios de comportamiento
    Given los componentes de los tests corregidos
    When se compara el diff
    Then solo cambian archivos de test
