# language: es
@US-ADJ-55
Feature: Espera máxima de Testing Library acorde a la suite (US-ADJ-55)

  Scenario: Configuración única
    Given el setup de tests del frontend
    When se revisa cómo se configura la espera de findBy y waitFor
    Then está fijada una sola vez en src/test/setup.ts, con el motivo documentado

  Scenario: Valor fijado con datos
    Given la suite completa con cobertura
    When se miden las esperas más lentas
    Then el valor elegido deja margen sobre lo medido y el reporte registra la medición

  Scenario: Estable en corridas repetidas
    Given la máquina en reposo
    When se corre "npm run test:coverage" 3 veces seguidas y "npm run test" 3 veces seguidas
    Then las 6 corridas pasan completas

  Scenario: Sin cambios de comportamiento
    Given el diff de la US
    When se revisan los archivos modificados
    Then no cambia ningún componente ni ningún test individual
