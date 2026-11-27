# Instalar Cognión

> Guía única de instalación. Es la que lleva el paquete `cognion-X.Y.Z-instalacion.tar.gz` de cada versión.
> Estado: operativo (`US-10.2.2`). El camino del servidor con Docker (A) lo prueba el CI contra Docker real en `localhost` (desde el 2026-11-18: levanta, respalda,
> ensaya la restauración, despliega y hace rollback), pero **todavía no se ensayó en un servidor con dominio, certificado y firewall** (Issue #624). Los caminos B (local) y C (GCP) sí se probaron en instalaciones reales.

## 1. Qué camino elegir

| Camino | Cuándo | Qué necesita | Detalle |
|---|---|---|---|
| **A. Servidor Linux con Docker** | Un servidor de la facultad o cualquier Linux, accesible por un dominio | Docker con `compose`, un dominio, puertos 80 y 443 | Sección 3 |
| **B. Local, sin Docker** | Una sola máquina (la tuya) para una clase, en la red del aula | Python (`uv`), Node 22, PostgreSQL 14+ | Sección 4 |
| **C. Google Cloud (VM de prueba)** | La prueba de uso que se hizo en GCP | Cuenta de GCP y `gcloud` | Sección 5 |

Elegí A para un uso estable con alumnos. B sirve para una clase puntual sin servidor. C es el camino que ya se probó en una VM `e2-micro`.

## 2. Qué trae el paquete y cómo se versiona

- Una versión tiene la forma `X.Y.Z` (por ejemplo `1.0.0`); su etiqueta en Git es `vX.Y.Z` y la imagen es `ghcr.io/vvalotto/cognion:vX.Y.Z`
  (pública: se baja sin credenciales). **No existe la etiqueta `latest`**: siempre se instala una versión concreta.
- El paquete contiene este documento, `VERSION`, `CHANGELOG.md` y `deploy/servidor/`. El código fuente completo (que necesita el camino B y
  el C) es el archivo "Source code" de la misma Release de GitHub.
- La versión que corre se consulta en `GET /api/health` (campo `version`).

## 3. Camino A — servidor Linux con Docker

### 3.1 Requisitos
- Linux **x86_64** (la imagen se publica solo para esa arquitectura), con **Docker Engine** y el plugin **Docker Compose v2** (`docker compose version`).
  Esta guía no instala Docker: cada servidor tiene su política.
- Memoria: 2 GB recomendados (una VM de 1 GB alcanzó para una clase de prueba, pero con poco margen).
- Un **dominio** (por ejemplo `cognion.facultad.edu.ar`) con un registro DNS que apunte al servidor, y los **puertos 80 y 443** abiertos hacia Internet
  o hacia la red de los alumnos: Caddy obtiene y renueva el certificado HTTPS solo, y necesita llegar a ellos.
- Salida a Internet para bajar la imagen (`ghcr.io`) y, si se configura, para enviar emails.

### 3.2 Instalación
```bash
tar xzf cognion-1.0.0-instalacion.tar.gz
cd cognion-1.0.0/deploy/servidor
./preparar-env.sh cognion.facultad.edu.ar     # crea .env con secretos aleatorios (permisos 600)
./cognion.sh iniciar                          # baja la base, migra, arranca la aplicación y el proxy
./cognion.sh administrador                    # crea el primer Administrador (la contraseña se pide sin eco)
./cognion.sh estado                           # muestra servicios, versión y la salud
```
Después entrá a `https://<tu-dominio>/` con el Administrador y creá las materias, comisiones y docentes desde la interfaz.

**Sin dominio** (solo HTTP, por IP o nombre dentro de la red): `./preparar-env.sh --sin-dominio 10.0.0.15`. Es una variante: no hay HTTPS, así que las
contraseñas viajan sin cifrar por esa red. Si el puerto 80 está ocupado, `COGNION_HTTP_PORT=8080 ./preparar-env.sh --sin-dominio 10.0.0.15`.

**Puertos y memoria:** si el servidor ya usa el 80 o el 443, o querés acotar la memoria, descomentá y editá `COGNION_HTTP_PORT`, `COGNION_HTTPS_PORT`,
`COGNION_MEM_DB` y `COGNION_MEM_APP` en `.env` (con puertos distintos, ajustá también `FRONTEND_URL` y `CORS_ALLOWED_ORIGINS`).

### 3.3 Correo
Sin configurar, los emails (recuperar contraseña) quedan en el log: `./cognion.sh logs app`. Para enviarlos de verdad con Gmail y una contraseña de
aplicación: `./cognion.sh email` (pide los datos sin eco y prueba la conexión) y `./cognion.sh email probar <destino>`. Volver al modo consola:
`./cognion.sh email consola`. Con `ENTORNO=produccion` la aplicación **exige** el correo configurado y no arranca en modo consola; el valor por
defecto, `local`, es el que se probó.

## 4. Camino B — local, sin Docker

1. Instalá `uv`, Node 22 y PostgreSQL 14+ (con `psql` y un rol con permiso para crear bases).
2. Bajá el "Source code" de la Release y descomprimilo; en esa carpeta: `uv sync`.
3. `cp .env.example .env` (el script solo toma de ahí el usuario y el host de PostgreSQL; si tu rol o contraseña no son los del ejemplo, editá
   `DATABASE_URL` en ese `.env`). Sin ese archivo `levantar.sh` se detiene con un aviso.
4. `scripts/local/levantar.sh --fondo` crea la base `cognion_local`, compila el frontend, migra, pide el primer Administrador y arranca el servidor; al final
   imprime la dirección que deben usar los alumnos. `scripts/local/detener.sh` lo detiene.
5. Respaldo y restauración: `scripts/local/respaldar.sh` (guarda en `~/CognionRespaldos`) y `scripts/local/restaurar.sh <archivo>` (ensayo; con
   `--sobre-local` reemplaza la base, pide escribir `RESTAURAR` y exige detener antes el servidor).
6. Actualizar: `scripts/local/detener.sh`, respaldar, descomprimir la versión nueva, `uv sync` y volver a ejecutar `levantar.sh --fondo` (reutiliza la
   base y su `.env.local`: copiá este último a la carpeta nueva; aplica las migraciones y no toca los datos).

El detalle (red del aula, emails, diagnóstico) está en `docs/plans/DESPLIEGUE-LOCAL.md` del código fuente.

## 5. Camino C — Google Cloud

La VM de prueba se crea y se opera con los scripts de `deploy/gcp/` (`aprovisionar.sh`, `desplegar.sh`, `destruir.sh`). Paso a paso, costos y
verificaciones: `docs/plans/DESPLIEGUE-GCP.md` y `ADR-025`, en el código fuente. Ese camino **no incluye** el respaldo del camino A.

## 6. Actualizar y volver atrás (camino A)

```bash
./cognion.sh desplegar ghcr.io/vvalotto/cognion:v1.0.1
```
Baja la imagen, **hace un respaldo**, aplica las migraciones con la imagen nueva (la vieja sigue sirviendo), reemplaza la aplicación y espera a que
`/api/health` responda. Si la versión nueva no responde, vuelve sola a la anterior. Si el respaldo falla, no se toca nada.

`./cognion.sh rollback` vuelve a la versión anterior **solo en la imagen**: las migraciones ya aplicadas no se deshacen. Si una migración nueva dañó
datos, hay que restaurar el respaldo hecho justo antes (sección 7).

## 7. Respaldo y restauración (camino A)

- `./cognion.sh respaldar` (o `./respaldar.sh`) guarda un `pg_dump` verificado, con su `sha256`, en `./respaldos/` y conserva los últimos 30
  (`COGNION_RESPALDOS_N`). Carpeta distinta: `COGNION_RESPALDOS`.
- **El respaldo diario queda programado solo.** `./cognion.sh iniciar` y `./cognion.sh desplegar` dejan una línea en el `cron` del usuario que lo
  ejecuta (a las 3:00 de cada día; otro horario: `COGNION_RESPALDO_HORARIO="15 2 * * *"`). Es idempotente: volver a correrlos no la duplica. Para
  programarlo a mano: `./cognion.sh programar-respaldo`. El resultado de cada corrida queda en `respaldos/respaldar.log`. Si el servidor no tiene
  `crontab`, el comando avisa y hay que programar `./respaldar.sh` con el planificador que haya.
- **`./cognion.sh estado` vigila los respaldos:** informa cuándo se hizo el último y avisa si tiene más de 36 horas (`COGNION_RESPALDO_MAX_HORAS`),
  si no hay ninguno o si el respaldo diario no está programado. Miralo después de un corte de luz o de un cambio de servidor.
- **Copiá `respaldos/` fuera del servidor** (otro equipo, otro disco): si el disco se rompe, se pierden la base y también las copias que estén en él.
  La copia no se hace sola, así que verificala una vez y repetí la verificación cada mes:
  1. Copiá: `rsync -av usuario@servidor:/opt/cognion/deploy/servidor/respaldos/ ~/CognionRespaldos/` (o `scp`, o el disco externo que uses).
  2. Comprobá la copia: `cd ~/CognionRespaldos && sha256sum -c cognion-<fecha>.dump.sha256` (en macOS: `shasum -a 256 -c …`). Tiene que decir `OK`.
  3. Ensayá restaurar esa copia (siguiente punto). Un respaldo que nunca se restauró no está comprobado.
- **Ensayo de restauración** (no toca la base real; recomendado una vez por mes): `./cognion.sh restaurar respaldos/cognion-<fecha>.dump`.
- **Restaurar de verdad:** `./cognion.sh restaurar respaldos/cognion-<fecha>.dump --reemplazar` (pide escribir `RESTAURAR`; detiene la aplicación,
  restaura en una sola transacción y la vuelve a levantar; se pierde lo cargado después de ese respaldo).

## 8. Abrir la aplicación por la dirección correcta

El link de invitación que el docente copia se arma con la dirección con la que **él** abrió la aplicación. Si entra por `localhost`, el link dirá
`localhost` y **no funcionará en los celulares de los alumnos**. El docente debe abrir Cognión por la dirección pública (el dominio, o la IP o el
nombre `.local` en el camino B) antes de generar el link.

## 9. Limitaciones conocidas de la versión 1.0

- **El camino A (servidor con Docker) no se ensayó en un servidor real.** El CI lo ejercita contra Docker real en `localhost` (con certificado interno):
  arranque, respaldo y ensayo de restauración contra PostgreSQL real, `desplegar` y `rollback`. Quedan por probar el certificado de Let's Encrypt con
  un dominio, el firewall y el comportamiento en un servidor de la facultad (Issue #624). Si ensayás este camino y algo falla, avisá: se corrige como `1.0.x`.
- **Importar preguntas desde PDF (`RF-07`)** y **los KPIs históricos (`RF-18`)** no están en la 1.0. La importación se planifica como importar desde JSON.
- **No hay respaldo automático a la nube** ni un runbook operativo completo; el respaldo del camino A es local al servidor y la copia externa es un paso manual (sección 7).
- **Los registros ocupan hasta 30 MB por servicio** (3 archivos de 10 MB, rotados). Con el uso previsto (una comisión de 60 alumnos) los de la aplicación alcanzan para unas 4 a 5 semanas; antes de ese plazo se pisan los más viejos. Si necesitás conservar más, copiá los de `docker compose logs` antes.
- **No hay despliegue automático:** el CD publica la imagen, pero el despliegue en el servidor lo ejecutás vos (`./cognion.sh desplegar`).
- **Solo x86_64** y una sola instancia de la aplicación (sin alta disponibilidad).
- **La aplicación corre con un solo proceso y no hay que cambiarlo.** No agregues `--workers` ni `WEB_CONCURRENCY` ni levantes una segunda réplica «para que ande más rápido»: el canal de la sesión en vivo guarda las conexiones en la memoria del proceso, así que con dos procesos parte de los alumnos deja de recibir los mensajes y no aparece ningún error. Un test del proyecto falla si el `Dockerfile` o un `docker-compose` piden más de un proceso. El verificador de vencimientos sí está protegido por un bloqueo de PostgreSQL: si dos procesos arrancan, solo uno corre cada vuelta.
- **UAT de la 1.0:** se verificó en una instalación local (camino B), con un navegador de escritorio y un viewport de celular emulado. No se probó en un
  celular real ni el canal en vivo con un JWT vencido.

## 10. Problemas frecuentes

| Síntoma | Qué mirar |
|---|---|
| `Falta el plugin 'docker compose'` | Instalá Docker Compose v2 (`docker-compose-plugin`). |
| Caddy no obtiene el certificado | El DNS del dominio debe apuntar al servidor y los puertos 80 y 443 deben llegar a él. `./cognion.sh logs caddy`. |
| El puerto 80 o el 443 ya está en uso | Cambiá `COGNION_HTTP_PORT`/`COGNION_HTTPS_PORT` en `.env` o liberá el puerto. |
| `/api/health/ready` responde 503 | La aplicación vive pero la base no responde: `./cognion.sh logs db`. |
| La aplicación no arranca con `ENTORNO=produccion` | Falta configurar el correo (`./cognion.sh email`), o hay valores de `localhost` en el `.env`. |
| El link de invitación dice `localhost` | Ver la sección 8. |
