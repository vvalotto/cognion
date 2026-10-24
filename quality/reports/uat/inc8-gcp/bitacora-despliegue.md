# Bitácora del despliegue manual en GCP (US-8.6.3)

Plan: `docs/plans/DESPLIEGUE-GCP.md`. Decisiones: `docs/adr/ADR-025-despliegue-de-prueba-en-gcp.md`.
Cuenta: `vvalotto@gmail.com` · Facturación: paga y sin créditos · Dominio: `cognion-fiuner.duckdns.org`.
Aprobación del plan por Víctor: 2026-10-24, con aviso de presupuesto de 5 USD y SSH abierto con clave.

Convención: cada paso lleva el **comando real**, la **hora**, el **resultado**, el **costo observado** y cualquier desvío.

---

## Paso 0 — Prerrequisitos · 2026-10-24 09:42
- `gcloud auth list`: `vvalotto@gmail.com` activa (SDK 550.0.0). Sesión renovada con `gcloud auth login` el 2026-10-23.
- Subdominio de DuckDNS creado por Víctor: `cognion-fiuner.duckdns.org` (cuenta de GitHub). El token se regeneró el 2026-10-23 porque quedó expuesto en una captura; no se usa en el plan.
- Resultado: **OK**. Costo: 0.

## Paso 1 — Configuración de `gcloud` aparte · 2026-10-24 09:42
- Comandos: `gcloud config configurations create cognion --no-activate` y `CLOUDSDK_ACTIVE_CONFIG_NAME=cognion gcloud config set account vvalotto@gmail.com`.
- Resultado: la configuración `cognion` existe con la cuenta, **inactiva**; `default` sigue activa con `app-termostato-2025`. Se usa con la variable de entorno por comando, sin cambiar la configuración activa de la terminal.
- Desvío respecto del plan original: se evitó `config set project` y la activación para no tocar la configuración global.
- Resultado: **OK**. Costo: 0.

## Paso 2 🔒 — Proyecto y facturación · 2026-10-24 09:44 · confirmado por Víctor
- Comandos: `gcloud projects create cognion-prueba-2410 --name="Cognion prueba"`, `gcloud config set project cognion-prueba-2410` (solo en la configuración `cognion`), `gcloud billing projects link cognion-prueba-2410 --billing-account=019D68-E7FC7F-247D34`.
- Resultado: proyecto `ACTIVE`, número `888211184158`, `billingEnabled: true` con "Mi cuenta de facturación". Se habilitó automáticamente `cloudapis.googleapis.com` (sin costo).
- Aviso de `gcloud`: el proyecto activo no coincide con el *quota project* del archivo de credenciales de aplicación (ADC). No afecta a `gcloud`; **no se cambió** porque podría afectar a otras aplicaciones de Víctor que usen esas credenciales.
- `default` sigue con `app-termostato-2025`.
- Costo observado: 0 (proyecto sin recursos).

## Paso 3 (parte de lectura) — Evaluación de los límites de inversión · 2026-10-24 09:44
- Fuente: documentación oficial de Cloud Billing ("Manage spend cap budgets", notas de versión de octubre de 2026).
- Hallazgos: se aplican a **un proyecto y un servicio elegible**; **pausan el uso nuevo**, pero **no los recursos persistentes** (VM, disco), que siguen acumulando cargos; usan costos brutos estimados; disponibles de forma general solo para algunos servicios.
- **Decisión: no depender de ellos.** No protegen una VM. La protección es presupuesto con alertas, revisión de costos al día siguiente y borrar el proyecto.
- Costo: 0.

## Paso 3 🔒 (parte de acción) — Presupuesto propio · 2026-10-24 09:46 · confirmado por Víctor
- Comandos: `gcloud services enable billingbudgets.googleapis.com` y `gcloud billing budgets create --billing-account=019D68-E7FC7F-247D34 --display-name="cognion-prueba" --budget-amount=5USD --filter-projects="projects/888211184158" --threshold-rule=percent=0.5 --threshold-rule=percent=1.0`.
- Resultado: presupuesto `cognion-prueba` (id `4451187e-9499-4b6f-b063-e405b3d82131`), 5 USD mensuales, acotado al proyecto `888211184158`, con alertas al 50 % y 100 % sobre el gasto actual. El presupuesto existente "ALERTA PRINCIPAL" no se tocó.
- Las opciones de `gcloud billing budgets create` del plan coincidieron con la versión instalada (550.0.0): sin ajustes.
- Costo observado: 0 (los presupuestos solo avisan).

## Paso 4 🔒 — Compute Engine y revisión de la red · 2026-10-24 09:50 · confirmado por Víctor
- Comandos: `gcloud services enable compute.googleapis.com`, `gcloud compute networks list`, `gcloud compute firewall-rules list`, `gcloud compute instances list`, `gcloud compute addresses list`.
- Resultado: API habilitada. Existe la red `default` (modo automático). Reglas por defecto: `default-allow-icmp` (0.0.0.0/0), `default-allow-internal` (10.128.0.0/9), `default-allow-rdp` (0.0.0.0/0, tcp:3389) y `default-allow-ssh` (0.0.0.0/0, tcp:22). Sin VMs ni IPs.
- **Hallazgo de seguridad:** `default-allow-rdp` deja el 3389 abierto a internet y una VM Linux no lo usa. Se incorpora al paso 5 eliminarla.
- Costo observado: 0 (habilitar la API no cuesta).

## Paso 5 🔒 — IP estática, firewall y VM · 2026-10-24 09:53 · confirmado por Víctor
**Desde esta hora corre el reloj de los recursos facturables.**
- Comandos, en este orden: `gcloud compute firewall-rules delete default-allow-rdp --quiet`; `gcloud compute addresses create cognion-ip --region=us-central1`; `gcloud compute firewall-rules create cognion-web --network=default --direction=INGRESS --action=ALLOW --rules=tcp:80,tcp:443 --target-tags=cognion-web --source-ranges=0.0.0.0/0`; `gcloud compute instances create cognion-vm --zone=us-central1-a --machine-type=e2-micro --image-family=debian-12 --image-project=debian-cloud --boot-disk-size=30GB --boot-disk-type=pd-standard --address=cognion-ip --tags=cognion-web`.
- Resultado verificado:
  - VM `cognion-vm`: `e2-micro`, `us-central1-a`, estado `RUNNING`, `provisioningModel: STANDARD` (no preemptible), etiqueta `cognion-web`, IP interna 10.128.0.2.
  - IP `cognion-ip` = **34.30.252.89**, estado `IN_USE`, usada por `cognion-vm`.
  - Disco `cognion-vm`: `pd-standard`, 30 GB.
  - Firewall: `cognion-web` (tcp:80 y tcp:443, solo a la etiqueta `cognion-web`), más `default-allow-icmp`, `default-allow-internal` y `default-allow-ssh`. `default-allow-rdp` eliminada.
  - Inventario del proyecto: 1 VM, 1 IP, 1 disco.
- Avisos de `gcloud` (sin acción): disco menor a 200 GB puede tener E/S baja (esperado en la capa gratuita); el disco de 30 GB es mayor que la imagen de 10 GB y Debian 12 amplía la partición solo.
- Costo observado: aún sin datos de Facturación (los informes tardan hasta 24 h). Pendiente: verificar al día siguiente el SKU `External IP Charge`.
