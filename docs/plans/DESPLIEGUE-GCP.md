# Despliegue en GCP — plan de instalación y prueba manual

> Estado documental: **borrador para revisión de Víctor** — ningún paso se probó todavía
> Alcance: instalar y probar Cognión en una VM `e2-micro` de GCP con la cuenta personal `vvalotto@gmail.com`
> Origen: `US-8.6.3` (Incremento 8, Iteración 6) · decisiones en `docs/adr/ADR-025-despliegue-de-prueba-en-gcp.md`
> Composición de servicios: `deploy/gcp/` (`US-8.6.2`) · Última actualización: 2026-10-23

---

## 1. Qué es y qué no cubre

Una VM `e2-micro` de la capa gratuita corre tres contenedores (aplicación, PostgreSQL y Caddy) con HTTPS real sobre un subdominio de DuckDNS.
Se instala **a mano, una vez**, con bitácora. Lo que funcione se convierte después en scripts (`US-8.6.4`) y en el runbook (`US-8.6.6`).

**No cubre:** alta disponibilidad, datos reales de alumnos (solo cuentas de prueba, `ADR-025`), emails reales (`EMAIL_MODO=consola`), acceso institucional,
backup (`US-8.6.5`) ni mediciones con criterios de go/no-go (`US-8.6.7`; acá solo se toman mediciones tempranas, informativas).

---

## 2. Reglas de la prueba

1. **Puerta de confirmación.** Cada paso marcado 🔒 crea un recurso o puede generar costo. No se ejecuta sin que Víctor diga "sí" a ese paso puntual. Un "sí" no se extiende a los siguientes.
2. **La cuenta de facturación es paga y sin créditos** (`ADR-025`, revisión 2026-10-23). Un recurso de más cuesta dinero real desde el primer día.
3. **Proyecto aparte.** Todo va en `cognion-prueba-<sufijo>`, nunca en `app-termostato-2025` (otra aplicación). Al terminar se puede borrar el proyecto entero.
4. **Tiempo acotado:** unas 2 horas efectivas para la instalación y las mediciones, más una revisión de costos al día siguiente.
5. **Cuándo detenerse y avisar** (sin parchear en silencio): un recurso aparece con costo inesperado; la memoria en reposo supera el 70 % de 1 GB o el sistema usa swap de forma sostenida; un paso falla dos veces; algo exige exponer más de los puertos 80 y 443.
6. **Nada se instala descargando y ejecutando scripts sueltos.** Docker se instala desde su repositorio oficial de paquetes.

---

## 3. Quién hace qué

| Quién | Qué |
|---|---|
| **Claude** | Ejecuta los comandos `gcloud` y los de la VM, **solo tras la confirmación** de cada paso 🔒; lee los resultados; escribe la bitácora |
| **Víctor** | Crea el subdominio en DuckDNS; escribe la contraseña del Administrador (por terminal, sin eco); prueba desde el celular; mira la consola de Facturación; decide ante cada puerta |
| **Los dos** | Revisan el costo observado y deciden si el entorno se conserva para `US-8.6.7` o se desmonta |

---

## 4. Variables del plan

| Variable | Valor | Nota |
|---|---|---|
| `PROYECTO` | `cognion-prueba-<sufijo>` | El identificador de un proyecto es global: se agrega un sufijo numérico de 4 dígitos |
| `REGION` / `ZONA` | `us-central1` / `us-central1-a` | La capa gratuita solo cubre `us-west1`, `us-central1` y `us-east1`. Si la zona no tiene capacidad, se prueba `-b` o `-c` |
| `CUENTA_FACTURACION` | `019D68-E7FC7F-247D34` | "Mi cuenta de facturación", abierta, en USD |
| `VM` / `IP` / `REGLA` | `cognion-vm` / `cognion-ip` / `cognion-web` | |
| `DOMINIO` | `cognion-fiuner.duckdns.org` | Creado por Víctor el 2026-10-23 en DuckDNS (cuenta de GitHub). Sin esquema ni barras |

---

## 5. Pasos

Cada paso indica el comando, el **resultado esperado**, el **criterio de éxito** y el estado (`sin probar` hasta ejecutarlo).
Los comandos de `gcloud` se verifican con `--help` antes de ejecutarlos si algún nombre de opción no coincide con la versión instalada (550.0.0).

### Paso 0 — Prerrequisitos (sin probar)
- `gcloud` con sesión vigente: `gcloud auth list` muestra `vvalotto@gmail.com` activa. *(Verificado el 2026-10-23.)*
- Subdominio de DuckDNS creado por Víctor: `cognion-fiuner.duckdns.org` *(hecho el 2026-10-23)*. DuckDNS le asignó por defecto la IP pública de la casa de Víctor; se cambia por la de la VM en el paso 9. **El token de DuckDNS es una credencial: no se comparte ni se guarda en el repositorio** (este plan no lo necesita).
- **Éxito:** los dos puntos anteriores cumplidos y `DOMINIO` definido.

### Paso 1 — Configuración de `gcloud` aparte, para no tocar la tuya (sin probar)
Una configuración con nombre evita cambiar el proyecto por defecto (`app-termostato-2025`).
```bash
gcloud config configurations create cognion
gcloud config set account vvalotto@gmail.com
```
- **Éxito:** `gcloud config configurations list` muestra `cognion` activa y `default` intacta. Para volver: `gcloud config configurations activate default`.

### Paso 2 🔒 — Crear el proyecto y vincular la facturación (sin probar)
```bash
gcloud projects create cognion-prueba-<sufijo> --name="Cognion prueba"
gcloud config set project cognion-prueba-<sufijo>
gcloud billing projects link cognion-prueba-<sufijo> --billing-account=019D68-E7FC7F-247D34
```
- **Resultado esperado:** proyecto creado y con facturación habilitada.
- **Éxito:** `gcloud billing projects describe cognion-prueba-<sufijo>` muestra `billingEnabled: true`.
- **Costo:** ninguno por sí mismo.

### Paso 3 🔒 — Presupuesto propio y límite de inversión (sin probar)
1. Habilitar la API de presupuestos y crear un presupuesto acotado para este proyecto. El monto de aviso lo propone Claude (referencia: 5 USD) y lo confirma Víctor:
```bash
gcloud services enable billingbudgets.googleapis.com
gcloud billing budgets create --billing-account=019D68-E7FC7F-247D34 \
  --display-name="cognion-prueba" --budget-amount=5USD \
  --filter-projects="projects/<NUMERO_DEL_PROYECTO>" \
  --threshold-rule=percent=0.5 --threshold-rule=percent=1.0
```
   El número del proyecto sale de `gcloud projects describe cognion-prueba-<sufijo> --format="value(projectNumber)"`.
2. **Evaluar los límites de inversión** (*spend caps*): la consola de Facturación → Budgets & caps muestra una función que **pausa servicios** al superar un tope. **Antes de depender de ella** se lee la documentación oficial para entender: qué servicios pausa, si aplica a un proyecto o a toda la cuenta de facturación, y si afectaría a `app-termostato-2025`. El resultado (usarla o no, y por qué) se anota en la bitácora.
- **Éxito:** el presupuesto existe y alcanza a este proyecto; la decisión sobre los límites queda registrada.

### Paso 4 🔒 — Habilitar Compute Engine y revisar la red (sin probar)
```bash
gcloud services enable compute.googleapis.com
gcloud compute networks list
gcloud compute firewall-rules list
```
- **Resultado esperado:** existe la red `default` con sus reglas por defecto (incluida la de SSH).
- **Si no existe `default`:** se detiene y se decide si crearla (red automática) y qué regla de SSH poner.
- **Éxito:** la red y las reglas están a la vista.
- **Costo:** habilitar la API no cuesta.

### Paso 5 🔒 — IP estática, regla de firewall y VM (sin probar)
```bash
gcloud compute addresses create cognion-ip --region=us-central1
gcloud compute firewall-rules create cognion-web --network=default --direction=INGRESS \
  --action=ALLOW --rules=tcp:80,tcp:443 --target-tags=cognion-web --source-ranges=0.0.0.0/0
gcloud compute instances create cognion-vm --zone=us-central1-a --machine-type=e2-micro \
  --image-family=debian-12 --image-project=debian-cloud \
  --boot-disk-size=30GB --boot-disk-type=pd-standard \
  --address=cognion-ip --tags=cognion-web
```
- **Resultado esperado:** una VM `e2-micro` en `us-central1-a`, con disco estándar de 30 GB y la IP reservada **asignada** a ella.
- **Éxito:** `gcloud compute instances describe cognion-vm --zone=us-central1-a --format="yaml(machineType,status,networkInterfaces[0].accessConfigs[0].natIP)"` muestra `e2-micro`, `RUNNING` y la IP reservada; `gcloud compute addresses list` la muestra como `IN_USE`.
- **Costos a tener presentes:**
  - Una IP reservada **sin asignar** se cobra. Esta queda asignada; si la VM se borra, la IP se libera también (paso de desmontaje).
  - **La IPv4 pública en uso se cobra** (≈0,005 USD/hora, unos 3,65 USD por mes según el precio vigente que encontré). Las fuentes no coinciden en si la capa gratuita lo cubre; **se verifica en el primer día** en Facturación → Informes, agrupando por SKU, buscando "External IP Charge". Si se cobra, el costo mensual real de la prueba es esa cifra, y no cero.
  - La capa gratuita cubre una `e2-micro` en `us-central1` con 30 GB de disco estándar y 1 GB de salida de red por mes; el exceso de salida se cobra (tarifa sin confirmar).
- **SSH:** la regla por defecto permite SSH desde cualquier origen, con autenticación por clave (la que genera `gcloud compute ssh`). Para la prueba se deja así; si se prefiere, se restringe a la IP de Víctor.

### Paso 6 — Preparar la VM: acceso, swap y Docker (sin probar)
Primero el acceso:
```bash
gcloud compute ssh cognion-vm --zone=us-central1-a
```
Dentro de la VM, **swap de 1 GB** (la memoria es el riesgo principal):
```bash
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -m
```
**Docker desde el repositorio oficial de paquetes** (los comandos se contrastan con la documentación vigente de Docker para Debian antes de ejecutarlos):
```bash
sudo apt-get update && sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker "$USER"
```
- **Éxito:** `docker --version` y `docker compose version` responden (tras volver a entrar a la sesión); `free -m` muestra el swap activo.
- **Medición temprana #1:** memoria libre con el sistema operativo y Docker en reposo, **antes** de levantar Cognión. Se anota en la bitácora.

### Paso 7 — Llevar la configuración y la verificación a la VM (sin probar)
Desde la Mac, conservando la estructura de carpetas que espera el script de verificación:
```bash
tar czf /tmp/cognion-deploy.tgz deploy/gcp tests/uat/inc8/verificar_composicion_gcp.sh
gcloud compute scp /tmp/cognion-deploy.tgz cognion-vm:~ --zone=us-central1-a
```
En la VM: `mkdir -p ~/cognion && tar xzf ~/cognion-deploy.tgz -C ~/cognion`.
- **Éxito:** existen `~/cognion/deploy/gcp/docker-compose.yml` y `~/cognion/tests/uat/inc8/verificar_composicion_gcp.sh`.

### Paso 8 — Llevar la imagen a la VM (sin probar)
La VM no puede compilar el frontend con 1 GB, y todavía no hay registro. Para esta prueba la imagen viaja como **artefacto de CI** (vence a las 24 h):
1. El workflow `imagen-smoke.yml` exporta la imagen como artefacto (cambio incluido en esta US). Se toma el de la última corrida de la rama.
2. `gh run download <id> -n cognion-imagen -D /tmp/cognion-imagen` (en la Mac).
3. `gcloud compute scp /tmp/cognion-imagen/cognion-imagen.tar.gz cognion-vm:~ --zone=us-central1-a`
4. En la VM: `gunzip -c ~/cognion-imagen.tar.gz | docker load`
- **Resultado esperado:** `docker images` muestra `cognion:ci`.
- **Medición temprana #2:** tamaño comprimido del archivo y de la imagen. Alimenta la elección del registro de `US-8.6.4` (límite gratuito de Artifact Registry: 0,5 GB).
- **Éxito:** la imagen está cargada y su tamaño anotado.

### Paso 9 — DuckDNS apunta a la IP (hace Víctor) (sin probar)
Caddy pide el certificado al arrancar, así que el nombre tiene que resolver a la VM **antes** del paso 10.
- Víctor reemplaza la IP del subdominio por la IP reservada (`gcloud compute addresses describe cognion-ip --region=us-central1 --format="value(address)"`): en el sitio de DuckDNS, escribe la IP en el campo *current ip* y aprieta *update ip*.
- **Éxito:** `dig +short <DOMINIO>` (o `nslookup`) devuelve esa IP.

### Paso 10 — Configuración y arranque (sin probar)
En la VM, desde `~/cognion/deploy/gcp`:
```bash
./preparar-env.sh <DOMINIO>
sed -i 's|^COGNION_IMAGE=.*|COGNION_IMAGE=cognion:ci|' .env
./cognion.sh iniciar
```
- **Resultado esperado:** la base arriba, las migraciones aplicadas como paso explícito, y la aplicación y Caddy arriba.
- **Éxito:** `./cognion.sh estado` muestra los tres servicios arriba y la salud respondiendo.

### Paso 11 — Primer Administrador y verificación de HTTPS real (sin probar)
```bash
./cognion.sh administrador      # nombre, email y contraseña por terminal, sin eco (la escribe Víctor)
curl -fsS https://<DOMINIO>/api/health
```
- **Éxito:** el certificado es válido (sin `-k`), `/api/health` responde por HTTPS y el login del Administrador funciona **desde el celular** de Víctor.
- Se confirma además que `Copiar link` de invitación funciona (necesita contexto seguro, `ADR-025`).

### Paso 12 — Verificación de la composición y reinicio real (sin probar)
En la VM:
```bash
VERIFICAR_REINICIO_DOCKER=1 ~/cognion/tests/uat/inc8/verificar_composicion_gcp.sh
```
Después, un **reinicio real de la máquina** (esto cubre el escenario 2 de `US-8.6.2`):
```bash
sudo reboot
```
- **Éxito:** el script termina con "Composición verificada"; tras el reinicio los servicios vuelven solos y `/api/health` responde sin intervención.
- Desde la Mac: `nc -vz <IP> 5432` **no** debe conectar (PostgreSQL no se ve desde internet).

### Paso 13 — Mediciones tempranas (informativas) (sin probar)
- Memoria con todo corriendo: `free -m` y `docker stats --no-stream` en reposo.
- Un login real con tiempo medido desde la Mac: `curl -s -o /dev/null -w '%{time_total}\n' ...` (da una idea de la latencia desde Argentina a `us-central1`).
- Uso de CPU y de swap durante un login.
- **Éxito:** los números quedan en la bitácora. La medición formal con criterios es `US-8.6.7`.

---

## 6. Control de costos

| Cuándo | Qué se mira |
|---|---|
| Al terminar la instalación | `gcloud compute instances list`, `gcloud compute addresses list`, `gcloud compute disks list`: solo lo esperado (1 VM, 1 IP `IN_USE`, 1 disco de 30 GB) |
| **Al día siguiente** | Facturación → Informes, filtrado por este proyecto y agrupado por SKU: `External IP Charge`, disco, salida de red. Se anota el gasto real |
| Una semana después, si el entorno se conserva | Mismo informe; se compara con la estimación (la IPv4 pública, ~3,65 USD/mes, si se cobra) |

---

## 7. Desmontaje

```bash
gcloud projects delete cognion-prueba-<sufijo>
```
Borra el proyecto y sus recursos (VM, IP, disco). Queda en estado de eliminación pendiente por un tiempo y se puede recuperar mientras dure. Confirmar en la consola que no quedan recursos facturables. El subdominio de DuckDNS no se borra (no tiene costo).
Para volver a la configuración normal: `gcloud config configurations activate default`.

---

## 8. Si algo sale mal

| Síntoma | Qué hacer |
|---|---|
| Falla la creación de la VM por falta de capacidad | Probar otra zona de `us-central1` (`-b`, `-c`); si ninguna, detenerse y avisar |
| `gcloud` rechaza una opción | Revisar `gcloud <comando> --help` y ajustar; anotar el comando correcto en la bitácora |
| El certificado no se emite | Verificar que el subdominio resuelva a la IP (`dig`), que 80 y 443 estén abiertos y que no haya otro servicio en esos puertos; revisar el log de Caddy |
| Poca memoria o swap sostenido | Detenerse y avisar: se mide qué consume cada servicio; la salida es un ADR (VM más grande o la opción B), no un parche |
| Un costo inesperado en Facturación | Detenerse, identificar el SKU y decidir si se desmonta |
| La imagen no carga o es muy grande | Anotar el tamaño; evaluar Cloud Build + Artifact Registry o GHCR para `US-8.6.4` |

---

## 9. Bitácora

`quality/reports/uat/inc8-gcp/bitacora-despliegue.md`: por cada paso, el **comando real**, la **hora**, el **resultado**, el **costo observado** y cualquier desvío. Al cerrar, una lista de **ajustes a `deploy/gcp/`** y de **qué debe automatizar `US-8.6.4`**.

---

## 10. Lo que este plan no comprueba

- Disponibilidad sostenida y comportamiento bajo una clase real (`US-8.6.7` y `US-8.6.8`).
- Backup y restauración (`US-8.6.5`).
- Más de una VM, otra región o acceso institucional.
- La tarifa de salida de red por encima de 1 GB mensual (sin confirmar).

Al ejecutar cada paso, su marca pasa de *sin probar* a *probado* y se actualizan los comandos que hayan necesitado ajustes.
