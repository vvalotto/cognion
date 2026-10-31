# US-8.6.8: Prueba de uso y cierre de la iteración

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `UAT + cierre`
**Bounded Context**: transversal
**Issue**: #552

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **usar el sistema en la VM con la gente que se decidió y dejar registrado qué pasó**,
para **saber si el despliegue sirve para el uso real y cerrar la iteración con evidencia**.

---

## Contexto

Es la prueba de uso que motivó la iteración. Su alcance (cuentas reales o de prueba, qué se avisa a los alumnos, qué
cuenta de Google) lo fijó `US-8.6.1`. Solo corresponde hacerla si `US-8.6.7` dio **go**. Depende de las decisiones de `US-8.6.1` (`ADR-025`); si alguna cambia el diseño, se actualiza esta spec antes de implementar.

## Especificacion del comportamiento

- Guion breve de la prueba en `quality/reports/uat/inc8-gcp/guion-prueba-de-uso.md`: preparación (un día antes y 30 minutos
  antes), flujo (registro, una actividad de período abierto y, si se decide, una sesión en vivo), qué observar y registrar
  (alumnos conectados a la vez, errores visibles, tiempos percibidos), plan B si falla la red o el servidor.
- Respaldo antes y después de la prueba.
- Registro de hallazgos en `quality/reports/uat/inc8-gcp/hallazgos.md`, clasificados 🔴/🟡/⚪ con el track que corresponde
  (`CLAUDE.md` §Clasificación de hallazgos).
- **Cierre de la iteración:** `DesignReviewer`, actualización de `CLAUDE.md` y de `inc8-candidatas.md` con el resultado,
  decisión sobre `US-8.2.x`/`8.3.1`/`8.4.x` (reemplazadas, desestimadas o vigentes), Issues cerrados con sus SHAs. El cierre
  de baseline del Incremento 8 sigue siendo `BL-013`.

## Escenarios

1. La prueba se realiza con el alcance de `ADR-025` y queda registrada con fecha y participantes.
2. Todo hallazgo tiene severidad y track; los bloqueantes quedan listados.
3. Hay un respaldo previo y otro posterior a la prueba.
4. `CLAUDE.md` e `inc8-candidatas.md` reflejan el resultado y la decisión sobre el resto del Incremento 8.
5. Si `US-8.6.7` dio no-go, esta US no se ejecuta y el cierre documenta el motivo.

## Fuera de alcance

Uso con datos institucionales oficiales; operación sostenida más allá de la prueba.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
