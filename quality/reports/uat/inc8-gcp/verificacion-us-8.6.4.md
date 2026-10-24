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
*(pendiente de autorización de Víctor)*
