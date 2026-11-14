# 01 · Resumen ejecutivo

## Juicio global

Cognión `1.0.0` es un sistema bien construido en su núcleo y con una disciplina de ingeniería poco común para un equipo de una persona. La arquitectura declarada se cumple: las capas internas no tienen dependencias de frameworks, los contratos de `import-linter` pasan y están probados, y el modelo de dominio tiene agregados chicos con invariantes nombrados.

Las debilidades están en lo que las reglas no miden: **qué cruza cada frontera**. Entre capas viajan entidades sin traducir. Entre contextos viajan repositorios y entidades ajenas. Entre el agregado y el almacén viajan diccionarios sin tipo ni versión. Entre dos escrituras de un mismo caso de uso no hay transacción. En los cuatro casos la regla de dependencia se cumple y la separación que la regla busca queda a medias.

El riesgo principal no es que el sistema falle hoy. Es el costo de cambiarlo: 9 de los 11 hallazgos de severidad alta afectan la mantenibilidad.

## Los cinco hallazgos que más importan

1. **Las operaciones de dos escrituras no son atómicas** ([IM-03](05-implementacion-por-capa.md#im-03--la-transacción-vive-en-el-repositorio-no-en-el-caso-de-uso)). Cada repositorio confirma por su cuenta. Crear una materia y su banco son dos transacciones, aunque un invariante exige que vayan juntas. Es el único hallazgo de diseño que puede dejar datos inconsistentes.

2. **Ningún contexto publica una interfaz** ([AC-01](03-acoplamiento-entre-contextos.md#ac-01--ningún-contexto-publica-una-interfaz-el-consumidor-se-acopla-a-sus-internos)). La regla escrita dice "solo por puertos"; la regla verificada acepta cualquier import desde `frameworks/adapters/` (71 hoy). Los adaptadores usan repositorios SQL y entidades de otros contextos, e Identidad depende de los tres contextos que dependen de ella.

3. **Los eventos son diccionarios sin tipo ni versión** ([DM-01](04-dominio-y-event-sourcing.md#dm-01--el-evento-no-es-la-fuente-del-cambio-de-estado), [DM-02](04-dominio-y-event-sourcing.md#dm-02--los-eventos-no-tienen-versión-de-esquema)). El caso de uso arma el payload, el agregado lo interpreta al reconstruir y Analytics lo lee crudo. Tres lugares conocen un formato que no está declarado en ninguno, sobre un almacén que no se puede reescribir.

4. **La traducción de errores a HTTP está repetida 138 veces** ([IM-02](05-implementacion-por-capa.md#im-02--la-traducción-de-errores-a-http-está-repetida-a-mano)). No hay jerarquía de errores ni manejador central. Esto infla los routers, y empuja el acoplamiento que la métrica de CBO castiga, al punto de que hay código escrito para esquivar la métrica ([IQ-01](08-instrumentos-de-calidad.md#iq-01--el-umbral-de-cbo-está-moldeando-el-diseño)).

5. **Un tercio de las especificaciones son retrabajo detectado en UAT** ([PR-01](11-proceso-iedd.md#pr-01--un-tercio-del-trabajo-especificado-es-retrabajo-detectado-en-uat)). 62 de 176. Los gates automáticos miden estructura; los defectos que escapan son de comportamiento visible, y los encuentra una persona al final.

Fuera del diseño, hay un riesgo operativo que conviene cerrar primero: **el respaldo no se programa solo y queda en el mismo servidor** ([DO-02](10-despliegue-y-operacion.md#do-02--el-respaldo-depende-de-que-alguien-se-acuerde)).

## Lo que está bien y hay que conservar

- **La regla de dependencia custodiada por un test que prueba que falla.**
- **Agregados chicos con invariantes nombrados** y concurrencia optimista bien resuelta.
- **La estrategia de tests:** pirámide correcta, dobles escritos a mano, BDD trazado a cada historia.
- **La trazabilidad completa** de requerimiento a baseline.
- **Las vistas de arquitectura que declaran lo que no verificaron.**
- **El despliegue como un artefacto y un comando**, con versión única y composición probada en el CI.

## Resultado por vista

| Vista | Juicio | Hallazgos (alta / media / baja) |
|---|---|---|
| Conformidad arquitectónica | Se cumple y está custodiada | 0 / 2 / 1 |
| Acoplamiento entre contextos | Bien del lado consumidor, sin frontera del lado proveedor | 2 / 2 / 0 |
| Dominio y event sourcing | Buen modelo táctico; eventos a mitad de camino | 3 / 4 / 0 |
| Implementación por capa | Núcleo limpio; problemas en los bordes | 2 / 4 / 1 |
| Atributos de calidad | Autoevaluación honesta; mantenibilidad sin probar | 1 / 3 / 0 |
| Verificación | Muy buena estrategia; la cobertura promete de más | 0 / 4 / 1 |
| Instrumentos de calidad | Mucha medición, mal balanceada | 1 / 2 / 3 |
| Frontend | Disciplinado en lo local, artesanal en lo transversal | 0 / 4 / 2 |
| Despliegue y operación | Adecuado a la escala; respaldo pendiente | 1 / 4 / 1 |
| Proceso IEDD | Logra trazabilidad; detecta tarde | 1 / 3 / 2 |
| Documentación | Excelente en arquitectura; descuidada en la entrada | 0 / 3 / 3 |

## Por dónde empezar

El [capítulo 13](13-plan-priorizado.md) propone cuatro etapas. La primera son cierres de horas: programar el respaldo, proteger la base de desarrollo con una guarda en los tests, autorizar el canal en vivo y corregir `README.md` y `CLAUDE.md`. La segunda, de una iteración, resuelve transacciones y errores, que son los dos cambios con mejor relación entre esfuerzo y efecto.

## Límites de esta revisión

Se hizo leyendo y midiendo, sin ejecutar tests ni la aplicación. No cubre seguridad en profundidad, el modelo de datos, las migraciones ni el diseño de UX. Diez hallazgos están marcados como inferidos y necesitan confirmación. El detalle está en [No revisado](13-plan-priorizado.md#no-revisado).
