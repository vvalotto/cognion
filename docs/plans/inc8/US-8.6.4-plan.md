# Plan de Implementación — US-8.6.4

## Decisión de diseño a confirmar: dónde se publica la imagen
| | Opción | Lo bueno | Lo malo |
|---|---|---|---|
| A | **GHCR público** (`ghcr.io/vvalotto/cognion`) | Gratis, sin credenciales en la VM, nada nuevo en GCP, sin tope de 0,5 GB | El paquete queda público (el código ya lo es); la visibilidad pública se activa **una vez a mano** en GitHub |
| B | Artifact Registry | Todo en GCP | Habilita una API y un repositorio, hay que dar permisos a la VM (hoy solo tiene `devstorage.read_only`) y el tope gratuito es 0,5 GB |

**Recomendación: A.**

## Tareas
1. **`deploy/gcp/aprovisionar.sh`** (en la Mac, idempotente): valida `gcloud` y sesión; muestra el plan y pide confirmación (`--si` la omite); crea solo lo que falta — proyecto, vínculo de facturación, APIs, presupuesto de 5 USD, elimina `default-allow-rdp`, IP estática, regla `cognion-web` (solo 80/443), VM `e2-micro` con la IP asignada —; usa siempre `--project`, nunca cambia la configuración activa de `gcloud`.
2. **`deploy/gcp/preparar-vm.sh`** (se ejecuta en la VM por SSH, idempotente): swap de 1 GiB persistente, Docker desde el repositorio oficial **verificando la huella de la clave**, usuario en el grupo `docker`.
3. **`deploy/gcp/destruir.sh`**: borra VM, regla e IP por su nombre, con confirmación; el proyecto solo con `--proyecto` y escribiendo su ID.
4. **`deploy/gcp/cognion.sh`**: nuevos subcomandos `desplegar <imagen>` y `rollback`. Secuencia: guarda la imagen actual → baja la nueva (si falla, aborta sin tocar nada) → toma un respaldo si existe `respaldar.sh` (avisa si no) → **migra con la imagen nueva mientras la vieja sigue sirviendo** (si falla, aborta) → reemplaza la aplicación → espera `/api/health` → si no responde, **vuelve a la imagen anterior** y sale con error. El estado (`COGNION_IMAGE`, `COGNION_IMAGE_ANTERIOR`) se guarda en `.env` con permisos 600.
5. **`deploy/gcp/desplegar.sh`** (en la Mac): sincroniza `deploy/gcp/` a la VM sin tocar el `.env` y ejecuta `cognion.sh desplegar` por SSH.
6. **CI (`cd.yml`):** al crear una etiqueta `v*.*.*`, inicia sesión en GHCR con `GITHUB_TOKEN`, construye y publica `ghcr.io/vvalotto/cognion:<versión>` (más `sha-<commit>`); en `main` solo construye. Los pasos de Fly.io siguen comentados.
7. **Tests** (`tests/unit/inc8/test_us_8_6_4_*.py`) con `gcloud`/`docker`/`curl`/`ssh` simulados: idempotencia, confirmación obligatoria, solo 80/443, IP asignada, destrucción acotada, despliegue exitoso, rollback ante salud fallida, aborto ante pull o migración fallida, errores sin traza.
8. **Verificación real** (con tu confirmación en cada paso): idempotencia de `aprovisionar.sh` contra el proyecto existente; despliegue y rollback reales en la VM (un despliegue sano, y uno con una imagen que no responde, que debe volver sola); publicación real con una etiqueta temporal en CI, que se borra al terminar.

## Riesgos
- Los scripts crean y borran recursos que **cuestan dinero**: confirmación por defecto, `--si` explícito, y nunca borran el proyecto sin escribir su ID.
- Una migración incompatible no se deshace con el rollback (no hay `alembic downgrade` confiable, `US-8.3.4`): se documenta; se restaura el respaldo.
- La prueba de rollback real **interrumpe unos segundos** el sitio de prueba.
- La etiqueta temporal queda visible en el repositorio hasta que se borre, y publica una imagen pública en GHCR.
- La visibilidad pública del paquete la cambia Víctor en la interfaz de GitHub (no hay forma por API).
