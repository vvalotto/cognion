# US-8.6.3: Plan de instalación y prueba manual del despliegue en GCP

**Estado**: `Especificada`
**Iteracion / Sprint**: `INC-8.6`
**Tipo**: `plan + prueba manual (spike de despliegue)`
**Bounded Context**: transversal (`docs/plans/`, `quality/reports/uat/inc8-gcp/`)
**Issue**: #547

---

## Descripcion (lenguaje de negocio)

Como **responsable de la prueba de uso**,
quiero **un plan de instalación escrito y revisado, y haberlo ejecutado a mano una vez con evidencia**,
para **descubrir los problemas del despliegue en GCP antes de automatizarlo y no escribir scripts de más**.

---

## Contexto

`US-8.6.2` dejó la composición de servicios verificada en CI, pero nunca se vio funcionar en una VM real. Quedan sin comprobar la
memoria total con el sistema operativo y Docker en 1 GB, el certificado real de DuckDNS, el puerto de PostgreSQL visto desde internet
y cómo llega la imagen a la VM (CI la construye pero no la publica; la VM no puede compilarla con 1 GB). La cuenta de facturación es
**paga y sin créditos** (`ADR-025`, revisión 2026-10-23), así que un descuido cuesta dinero real. Esta US **reemplaza** a la antigua
`US-8.6.3` (script de aprovisionamiento), que pasa a `US-8.6.4` y se escribe con lo aprendido acá.

## Especificacion del comportamiento

1. **Plan escrito:** `docs/plans/DESPLIEGUE-GCP.md`, con la convención de `DESPLIEGUE-LOCAL.md` (cada paso marcado probado / sin probar):
   - Prerrequisitos: `gcloud` con sesión vigente, cuenta de facturación, subdominio de DuckDNS.
   - Pasos numerados con comandos reales, **resultado esperado y criterio de éxito** por paso.
   - **Puerta de confirmación** antes de cada acción que cree recursos o genere costo; nada se ejecuta sin el visto bueno de Víctor.
   - Quién hace cada cosa (lo que ejecuta Claude, lo que hace Víctor, lo que se comprueba desde el celular).
   - Control de costos (límite de tiempo, qué mirar en Facturación) y **desmontaje** borrando el proyecto entero.
   - Lo que **no** cubre (alta disponibilidad, datos reales, acceso institucional).
2. **Revisión con Víctor** del plan antes de ejecutarlo; los cambios que pida se incorporan.
3. **Ejecución manual** del plan, con bitácora en `quality/reports/uat/inc8-gcp/bitacora-despliegue.md` (comando, resultado, hora, costo
   observado). Cubre: proyecto nuevo `cognion-prueba` vinculado a la cuenta de facturación; presupuesto propio y bajo; **evaluación
   de los límites de inversión** (alcance, qué pausan, si afectan a otros proyectos) antes de depender de ellos; VM `e2-micro` en
   `us-central1` con IP estática y firewall solo en 80/443; imagen construida con Cloud Build y publicada en un registro (se verifica
   que entre en los límites gratuitos de Artifact Registry; si no, se elige otro); Docker en la VM; `deploy/gcp/` con el `.env` real;
   DuckDNS apuntando a la IP; HTTPS real comprobado desde el celular.
4. **Mediciones tempranas** (informativas, la medición formal con criterios es `US-8.6.7`): memoria en reposo con sistema operativo y
   Docker, un login real, tiempos de arranque y el costo observado tras al menos un día.
5. **Corrección del `ADR-025`** por la facturación (primer commit de esta US).
6. **Qué se aprende:** la bitácora cierra con una lista de ajustes a `deploy/gcp/` y de lo que `US-8.6.4` debe automatizar.

## Escenarios

1. El plan de instalación existe, fue revisado por Víctor y cada paso tiene resultado esperado y criterio de éxito.
2. Ninguna acción que crea recursos o genera costo se ejecuta sin confirmación explícita previa.
3. Siguiendo el plan se llega de un proyecto vacío a la aplicación respondiendo por HTTPS real con un login exitoso desde el celular.
4. Desde internet el puerto de PostgreSQL no responde.
5. La bitácora registra la memoria en reposo con sistema operativo y Docker, y el costo observado.
6. Los límites de inversión quedan evaluados y la decisión de usarlos o no, registrada.
7. Al terminar queda decidido si el entorno se conserva para `US-8.6.7` o se desmonta.

## Fuera de alcance

Scripts de aprovisionamiento y despliegue (`US-8.6.4`); backup (`US-8.6.5`); runbook definitivo (`US-8.6.6`); mediciones con criterios de
go/no-go (`US-8.6.7`); prueba con usuarios (`US-8.6.8`).

## Fuente de verdad UX

No aplica — sin cambios en `frontend/`.
