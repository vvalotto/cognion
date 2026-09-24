# language: es
@US-ADJ-53
Feature: Suite frontend con cobertura estable (US-ADJ-53)

  Scenario: Un solo comando documentado
    Given el frontend con sus dependencias instaladas
    When se corre "npm run test:coverage"
    Then corre la suite completa con cobertura y aplica los umbrales de 80%, sin flags adicionales

  Scenario: Estable en corridas repetidas
    Given la máquina local sin otras cargas pesadas
    When se corre "npm run test:coverage" 3 veces seguidas
    Then las 3 corridas pasan completas

  Scenario: Sin saturar la máquina
    Given una corrida de "npm run test:coverage"
    When se mide el load average durante la corrida
    Then queda por debajo del valor medido hoy (116 con 8 núcleos), registrado en el reporte

  Scenario: El CI no empeora
    Given el workflow de CI
    When corre "npm run test"
    Then sigue pasando y su duración no crece sin justificación en el reporte
