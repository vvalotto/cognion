# US-8.6.7: Mediciones en la VM con criterios de go/no-go

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `UAT / medición`
**Bounded Context**: transversal (`tests/uat/inc8/`)
**Issue**: #551

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **medir en la VM real si aguanta una clase con 60 alumnos**,
para **decidir con números si la opción A alcanza o hay que pasar a una máquina más grande**.

---

## Contexto

Los riesgos de la opción A son CPU compartida (el hash bcrypt de muchos logins juntos), 1 GB de RAM y una región solo en
EE.UU. El RNF de 100 ms es del servidor y ya se midió en la Mac de Víctor (`US-6.2.9`, p95 de 43,81 ms con 60
participantes); falta medirlo en esta VM. Depende de las decisiones de `US-8.6.1` (`ADR-025`); si alguna cambia el diseño, se actualiza esta spec antes de implementar.

## Especificacion del comportamiento

Mediciones repetibles, con scripts versionados en `tests/uat/inc8/`, ejecutadas contra la VM desplegada (`US-8.6.4`):

| Medición | Criterio (a confirmar en `US-8.6.1`) |
|---|---|
| 60 logins simultáneos en un minuto | 0 errores y p95 < 3 s |
| Sesión en vivo con 60 participantes (reutiliza el método de `US-6.2.9`) | p95 de `CerrarPreguntaActual` < 100 ms en el servidor |
| Memoria durante ambas cargas | < 80 % de 1 GB sostenida; sin cierres por falta de memoria |
| Reinicio de la VM | el sistema vuelve solo en menos de 3 minutos |
| Latencia desde Argentina | se mide y se registra (informativo) |
| Respaldo y restauración | restauración completa exitosa (`US-8.6.5`) |

Resultado: `quality/reports/uat/inc8-gcp/mediciones.md` con datos crudos, veredicto por criterio y una conclusión
**go / no-go**. Si algún criterio falla se registra y se propone el siguiente paso (VM paga más grande u opción B: Cloud
Run + Cloud SQL), decidido en un ADR nuevo. La imagen es la misma, así que el código no cambia.

## Escenarios

1. Cada medición produce un resultado con sus datos crudos y el método usado.
2. Una carga que supera la capacidad queda registrada como falla, no se oculta.
3. El veredicto go/no-go es consecuencia directa de los criterios confirmados.
4. Las mediciones se pueden repetir con los mismos scripts.

## Fuera de alcance

Pruebas de carga mayores a 60 participantes; optimizar el código para que pase (sería una US aparte).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
