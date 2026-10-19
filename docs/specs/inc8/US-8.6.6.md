# US-8.6.6: Runbook operativo y ensayo de instalación limpia

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `documentación + UAT`
**Bounded Context**: transversal
**Issue**: #550

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **un procedimiento escrito que alguien pueda seguir desde cero y haberlo seguido de verdad**,
para **poder rehacer el entorno si la VM se pierde y no depender de mi memoria**.

---

## Contexto

`docs/plans/DESPLIEGUE-LOCAL.md` cubre la máquina de Víctor. Falta lo equivalente para la VM, y la regla del proyecto es no
documentar lo no probado (`US-8.5.6` original). Esta US se solapa con `US-8.4.1` a `8.4.3`; al cierre de la iteración se
decide cuáles se dan por cubiertas. Depende de las decisiones de `US-8.6.1` (`ADR-025`); si alguna cambia el diseño, se actualiza esta spec antes de implementar.

## Especificacion del comportamiento

`docs/plans/DESPLIEGUE-GCP.md` con: prerrequisitos y cuenta; crear la VM; instalar y configurar; primer Administrador;
publicar y desplegar una versión; respaldar y restaurar; parar y arrancar; actualizar; rotar secretos; qué hacer ante los
incidentes previsibles (VM sin memoria, disco lleno, certificado vencido, presupuesto agotado, fin de los 90 días de prueba);
lo que **no** cubre (alta disponibilidad, acceso institucional, datos oficiales). Cada paso lleva su marca de estado
(probado / sin probar) como `DESPLIEGUE-LOCAL.md`.

**Ensayo:** destruir la VM y reconstruir el entorno siguiendo **solo** el runbook, midiendo cuánto tarda y anotando cada
vacío. Los vacíos se corrigen en el documento.

## Escenarios

1. Siguiendo solo el runbook se llega de un proyecto vacío a un sistema respondiendo por HTTPS.
2. Se recupera un respaldo en la VM nueva y los datos reaparecen.
3. El documento enumera explícitamente lo no cubierto.
4. Los vacíos hallados en el ensayo quedan corregidos y registrados.
5. El tiempo de reconstrucción queda medido y anotado.

## Fuera de alcance

Automatizar la reconstrucción completa en un solo comando.

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
