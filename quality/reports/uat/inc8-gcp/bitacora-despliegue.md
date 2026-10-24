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

## Paso 6 — Acceso, swap y Docker · 2026-10-24 09:59 · confirmado por Víctor (incluida la clave SSH)
- **Acceso:** `gcloud compute ssh cognion-vm --zone=us-central1-a --quiet`. La primera conexión actualizó los metadatos SSH del proyecto y creó en la Mac `~/.ssh/google_compute_engine` (sin passphrase) y su `.pub`. Tardó en propagar la clave (unos segundos).
- **Sistema:** Debian GNU/Linux 12 (bookworm), x86_64, 2 vCPU visibles, disco de 30 GB con 2,1 GB usados.
- **Memoria base (Debian + agentes de Google, sin swap ni Docker):** total 969 MiB, usada 350, libre 440, disponible 619.
- **Swap:** `fallocate -l 1G /swapfile`, `chmod 600`, `mkswap`, `swapon`, entrada en `/etc/fstab`. Resultado: 1 GiB activo y persistente. En PATH de un SSH no interactivo `swapon` no está sin `sudo` (está en `/usr/sbin`).
- **Docker:** repositorio oficial de paquetes (clave en `/etc/apt/keyrings/docker.asc`, huella `9DC8 5822 9FC7 DD38 854A E2D8 8D81 803C 0EBF CD88`, que coincide con la clave oficial de Docker). Versiones: Docker 29.9.2, Compose v5.6.1; `docker` activo y habilitado al arrancar. El usuario quedó en el grupo `docker` (efectivo en la sesión siguiente).
- Los avisos de `debconf` por falta de terminal son inocuos.
- **Medición temprana #1 (sistema + Docker en reposo, antes de Cognión):** total 969 MiB, usada **419**, libre 82, buff/cache 610, **disponible 550**, swap usado 8 MiB; carga 0,41. Procesos de mayor tamaño: `dockerd` 85 MB, `containerd` 42 MB, `google_osconfig` 40 MB, `unattended-upgr` 20 MB, `google_guest_agent` 18 MB. Docker sumó unos 65 MiB usados.
- **Proyección:** con los ~115 MiB medidos en CI para los tres contenedores, la memoria usada quedaría cerca de 535 MiB de 969 (≈55 %), por debajo del 70 % de la regla de parada. Es una proyección: se confirma con el paso 13.
- **Idea para más margen (no aplicada):** el agente `google_osconfig` ocupa unos 40 MB y no se necesita.
- Costo observado: 0 (instalar paquetes y crear swap no se factura).

## Paso 7 — Configuración y verificación a la VM · 2026-10-24 10:00
- Comandos: `tar czf /tmp/cognion-deploy.tgz deploy/gcp tests/uat/inc8/verificar_composicion_gcp.sh` (5.971 bytes, sin ningún `.env` real, solo `.env.example`), `gcloud compute scp ... cognion-vm:~`, y en la VM `mkdir -p ~/cognion && tar xzf ...`.
- Resultado: `~/cognion/deploy/gcp/` con `docker-compose.yml`, `Caddyfile`, `.env.example`, `cognion.sh`, `preparar-env.sh`, y `~/cognion/tests/uat/inc8/verificar_composicion_gcp.sh`, los tres scripts con permiso de ejecución. `docker compose config` lee la composición y solo avisa de las variables sin definir (esperado antes del `.env`).
- **Desvío:** el `tar` de macOS agregó archivos basura `._*` (metadatos AppleDouble) y avisos `LIBARCHIVE.xattr`. Se borraron en la VM. Corrección en el plan: usar `COPYFILE_DISABLE=1 tar ...`.
- Costo: 0.

## Paso 8 — Imagen a la VM · 2026-10-24 10:05 · descarga autorizada por Víctor
- Comandos: `gh run download 39976321310 -n cognion-imagen -D /tmp/cognion-imagen` (artefacto de nuestro CI, vigente hasta 2026-10-24T15:13Z), `gzip -t`, `gcloud compute scp ... cognion-vm:~`, y en la VM `gunzip -c ~/cognion-imagen.tar.gz | docker load`.
- Integridad: `gzip -t` OK; el `sha256` (`fbcf22d1…c26942`) coincide entre la Mac y la VM.
- **Medición temprana #2 (tamaño de la imagen):** archivo comprimido **100,7 MB**; imagen cargada `cognion:ci` de **569 MB** descomprimida. La subida a la VM tardó **26 s**. Disco de la VM tras cargar: 4,3 GB usados de 30.
- **Para `US-8.6.4` (registro):** 100 MB comprimidos entran en los 0,5 GB gratuitos de Artifact Registry, pero con varias versiones acumuladas se acercarían al límite; GHCR (sin ese tope) queda como alternativa. Decisión pendiente.
- Se borraron el archivo en la VM y la copia local.
- Costo: 0 (la entrada de datos a GCP no se factura).

## Paso 9 — DuckDNS apunta a la VM (lo hizo Víctor) · 2026-10-24 10:08
- Víctor reemplazó la IP de `cognion-fiuner` por `34.30.252.89` con *update ip*.
- Verificación: `dig +short cognion-fiuner.duckdns.org` desde la Mac y contra `8.8.8.8` y `1.1.1.1` devuelven `34.30.252.89`. Los puertos 80 y 443 de la VM están cerrados, como corresponde antes de arrancar los servicios.
- Resultado: **OK**. Costo: 0.

## Paso 10 — Configuración y arranque · 2026-10-24 10:11
- Comandos (en la VM, `~/cognion/deploy/gcp`): `./preparar-env.sh cognion-fiuner.duckdns.org`; `sed -i 's|^COGNION_IMAGE=.*|COGNION_IMAGE=cognion:ci|' .env`; `./cognion.sh iniciar`.
- `.env`: permisos 600, secretos aleatorios generados en la VM y no mostrados; `ENTORNO=local`, `EMAIL_MODO=consola`.
- **Arranque:** 73 s en total, incluida la descarga de `postgres:16` y `caddy:2` desde Docker Hub. Orden correcto: base sana → migraciones como paso explícito → aplicación sana → Caddy.
- **HTTPS real:** `curl https://cognion-fiuner.duckdns.org/api/health` desde la Mac, **sin `-k`**: `{"status":"ok"}`, HTTP 200, `ssl_verify=0`. Certificado emitido por **Let's Encrypt (CN=YE2)** para el dominio, **válido del 2026-10-24 al 2027-01-22**. `http://` redirige con 308 a `https://`. Caddy creó la cuenta ACME sin email y obtuvo el certificado al primer intento (sin reintentos ni límites).
- Servicios: `app` y `db` `healthy`, `caddy` `Up`.
- **Memoria con Cognión corriendo (justo después de arrancar, en reposo):**
  - Contenedores: `app` 95,9 MiB, `db` 44,2 MiB, `caddy` 16,4 MiB (**156 MiB en total**; en CI se habían medido 115). CPU en reposo: 2,1 % la aplicación.
  - Sistema: total 969 MiB, **usada 640 (66 %)**, buff/cache 411, **disponible 329**, swap usado **53 MiB**.
  - Comparación con la proyección: se había proyectado ~535 MiB usados (55 %); la medición real es **~105 MiB mayor**. Sigue por debajo del 70 % de la regla de parada, pero con poco margen y con swap ya en uso **antes** de cualquier carga.
  - Interpretación: parte del swap puede venir del arranque (descarga y descompresión de imágenes). Hay que remedir tras unos minutos de reposo y bajo carga (paso 13).
- Costo observado: 0 en recursos nuevos (las imágenes de Docker Hub no se facturan).
