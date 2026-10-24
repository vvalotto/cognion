# Verificación real de US-8.6.4 (scripts de aprovisionamiento, publicación y despliegue)

Fecha: 2026-10-24 11:40. VM de la prueba: `cognion-vm` (e2-micro, us-central1-a), proyecto `cognion-prueba-2410`.
Los tests automáticos usan `gcloud`, `docker` y `ssh` simulados (141 tests de `tests/unit/inc8`); acá se documenta lo que se
comprobó **de verdad**. Cada acción real fue confirmada por Víctor antes de ejecutarse.

## Verificación 1 — idempotencia de `aprovisionar.sh` contra el proyecto real
- Se corrió **sin `--si` y con la entrada vacía** (si hubiera querido crear algo, se cancelaba solo).
- **Primer intento: defecto encontrado.** El script propuso crear el presupuesto `cognion-prueba`, que ya existía. Con `--si`
  habría creado un duplicado.
- **Causa:** la API de presupuestos exige un *proyecto de cuota*; sin indicarlo toma el de la configuración activa de `gcloud`, que
  apuntaba al proyecto ya borrado (`app-termostato-2025`). La consulta fallaba y el script ocultaba el error (`2>/dev/null`),
  interpretándolo como "no existe".
- **Corrección:** `--billing-project="$PROYECTO"` en los comandos de presupuestos, y **falla cerrada** (si no puede consultar,
  aborta con el motivo). En una instalación limpia el chequeo se repite durante la ejecución, cuando el proyecto y la API ya existen.
  Los tests simulados ahora reproducen la exigencia de la API real y hay dos de regresión.
- **Segundo intento: "Nada que crear"**, código 0, con la configuración activa sin proyecto. Un único presupuesto `cognion-prueba`.
  Inventario del proyecto idéntico antes y después (1 VM, 1 IP `IN_USE`, regla `cognion-web` y reglas por defecto).
- Hallazgo adicional durante los tests (antes de la verificación real): en un proyecto nuevo la regla `default-allow-rdp` (3389
  abierto a internet) la crea Google **al habilitar Compute Engine**, durante la corrida; el script decidía cerrarla antes y la primera
  corrida la habría dejado abierta. Corregido: se decide después de habilitar las APIs (test de regresión).

## Verificación 2 — despliegue y rollback reales en la VM
Disponibilidad medida desde la Mac con una consulta a `/api/health` por HTTPS cada segundo (158 lecturas).

| Prueba | Resultado | Corte medido |
|---|---|---|
| **1. Despliegue sano** (`desplegar.sh cognion:prueba2`, alias local de la imagen cargada para forzar la recreación) | Sincronizó `deploy/gcp/`, migró con la imagen nueva, recreó la aplicación y esperó la salud. `.env`: actual `cognion:prueba2`, anterior `cognion:ci`, permisos **600** | **~10 s** |
| **2. Imagen rota** (derivada de la actual con `CMD sleep infinity`: migra bien, no arranca el servidor; espera de salud acortada a 40 s) | Detectó que no respondía, **volvió sola a `cognion:prueba2`**, salió con código 1. `.env` quedó **exactamente como antes** (el anterior no quedó apuntando a la versión rota) | **~63 s** |
| **3. Rollback manual** (`cognion.sh rollback`) | Volvió a `cognion:ci` e intercambió las versiones (es reversible) | **~6 s** |

- Todos los cortes fueron `502` de Caddy (la aplicación no estaba lista) y la última lectura fue `200`.
- El rollback automático **no es sin corte**: con una versión rota el sitio de prueba queda sin servicio unos 60 s (40 s de espera
  + la recreación de la anterior). Aceptable para esta prueba; con una espera de salud más corta se reduce.
- La migración se ejecutó con la imagen nueva y con la aplicación vieja aún sirviendo (la rota migró sin problemas, como se pretendía).
- No había `respaldar.sh` (es `US-8.6.5`): el script avisó y siguió. Cuando exista, se ejecuta antes de migrar.
- **Limpieza:** se borraron las etiquetas `cognion:prueba2` y `cognion:rota`, el directorio temporal y la línea
  `COGNION_IMAGE_ANTERIOR` del `.env` (permisos 600). La VM quedó con `cognion:ci`, sana.

## Verificación 3 — publicación real en CI con una etiqueta temporal
Autorizada por Víctor. Etiqueta temporal `v0.0.1-prueba.1` sobre el commit `8b46b99` (ya con los pasos de publicación en `cd.yml`).

- **CI (`CD`, corrida 40103840039): en verde.** Construyó la imagen, inició sesión en GHCR con `GITHUB_TOKEN` y publicó
  `ghcr.io/vvalotto/cognion:v0.0.1-prueba.1` y `ghcr.io/vvalotto/cognion:sha-8b46b995…`. Sin etiqueta `latest`.
- En paralelo corrió `Imagen y composición (smoke)` sobre la rama (corrida 40103789064): **en verde**, es decir que los cambios a `cognion.sh`
  no rompieron `iniciar` ni ninguna de las 12 verificaciones de composición.
- **Visibilidad:** el paquete se crea **privado**; Víctor lo hizo público a mano (Package settings, Danger Zone, Change visibility). No hay API
  para hacerlo. Es un paso manual **de una sola vez**: las etiquetas siguientes publican en el mismo paquete, que queda público.
- **Verificación sin credenciales desde internet** (Mac): token anónimo del registro, `tags/list` muestra `v0.0.1-prueba.1` y `sha-8b46b995…`, y el
  manifiesto responde HTTP 200 con 11 capas y **102,5 MB** comprimidos (coincide con los 100,7 MB del artefacto de CI).
- **Verificación en la VM, sin ninguna credencial de registro** (no existe `~/.docker/config.json`): `docker pull ghcr.io/vvalotto/cognion:v0.0.1-prueba.1`
  terminó en **8 s**. Etiquetas OCI presentes: `org.opencontainers.image.source = https://github.com/vvalotto/cognion` y
  `org.opencontainers.image.revision = 8b46b995…`. La imagen contiene `uvicorn` y `alembic` en `/app/.venv/bin/`.
- **Limpieza:** la etiqueta temporal se borró de git (local y remota); las etiquetas del repositorio quedan solo las de baseline
  (`v0.7.0` a `v0.8.1`). La imagen publicada **sigue disponible** sin la etiqueta de git.
- **Pendiente de limpieza manual (Víctor):** borrar las versiones de prueba del paquete en GitHub (Packages, `cognion`, Package versions); conviene
  borrar solo las versiones y conservar el paquete para que siga siendo público.

## Conclusión de las tres verificaciones
Los escenarios 4, 5, 6 y 7 de la spec quedaron verificados contra recursos reales; 1, 2 y 3 se verificaron con simulaciones y con la idempotencia contra
el proyecto real. **El escenario 1 con un proyecto limpio no se puede verificar sin crear otro proyecto: se hace en `US-8.6.6` (ensayo de
instalación limpia).**
