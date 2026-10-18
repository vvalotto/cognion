# US-8.5.6: Guía de despliegue local y guion de la prueba con alumnos

**Estado**: `Desestimada` (decisión de Víctor, 2026-10-18; no se implementa en este incremento)
**Iteracion / Sprint**: `INC-8.5`
**Tipo**: `documentación` (sin código de producción)
**Bounded Context**: transversal
**Issue**: #541

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba con alumnos**,
quiero **una guía para instalar y operar el sistema en mi máquina y un guion de la clase de prueba**,
para **que la prueba sea repetible y no dependa de mi memoria**.

---

## Especificacion del comportamiento

1. `docs/plans/DESPLIEGUE-LOCAL.md` (reemplaza para este caso el alcance "solo desarrollo" de `CHECKLIST-INSTALACION.md`):
   - Prerrequisitos y cómo instalarlos; arranque y parada con `scripts/local/`.
   - **Red del aula**: cómo elegir la red (hotspot del celular o router propio frente al wifi institucional), cómo
     detectar el **aislamiento de clientes** (los dispositivos no se ven entre sí), el aviso del firewall de macOS
     al aceptar conexiones entrantes, IP que cambia (usar el nombre `.local` o reservar la IP).
   - Qué pasa si se cae el servidor o la máquina se duerme, y cómo retomar sin perder datos (respaldo antes y después).
   - **Datos y privacidad**: qué datos quedan en el equipo, si la prueba usa cuentas reales o de prueba, qué avisar a los
     alumnos. La decisión final es institucional, no técnica.
   - Diagnóstico rápido: cómo revisar el log, probar `/api/health` desde otro dispositivo, listar conexiones.
2. `quality/reports/uat/inc8-local/plan-de-prueba-con-alumnos.md`: preparación (un día antes, 30 minutos antes), flujo
   con alumnos (autoregistro o invitación → rendir una actividad de período abierto → una sesión en vivo con todos),
   qué observar y registrar (cuántos alumnos conectados a la vez, errores visibles, tiempos de respuesta percibidos),
   formulario breve de comentarios, criterios de éxito, y plan B si la red o el servidor fallan.
3. Cada paso de la guía se ejecuta al menos una vez antes de darlo por escrito (no se documenta lo no probado).

## Escenarios (BDD)

1. Seguir la guía desde cero en la máquina de Víctor deja el sistema accesible desde otro dispositivo.
2. El plan de prueba incluye criterios de éxito medibles y un plan B.
3. La guía enumera explícitamente lo que **no** está cubierto (TLS, alta disponibilidad, acceso desde fuera de la red).

## Fuente de verdad UX

No aplica — documentación.
