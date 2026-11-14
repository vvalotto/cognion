# 10 · Despliegue y operación

> Pregunta: ¿se puede instalar y operar el sistema con confianza?

## Qué se miró

- `Dockerfile`, `deploy/servidor/` y `deploy/gcp/` (listado y `docker-compose.yml` del servidor).
- `.github/workflows/cd.yml` e `imagen-smoke.yml`.
- `fly.toml`, `scripts/` y los endpoints de salud en `app.py`.

No se construyó la imagen ni se levantó la composición. Los scripts de respaldo y restauración no se leyeron en detalle.

## Fortalezas

- **Imagen en dos etapas** y un solo artefacto: la API sirve el frontend compilado.
- **Las migraciones no corren al arrancar**; son un paso explícito.
- **Composición cuidada.** Solo Caddy publica puertos, hay límites de memoria, `healthcheck` en la base y en la aplicación, y rotación de registros.
- **La versión es una sola.** El CD rechaza un tag que no coincida con el archivo `VERSION`, y `/api/health` la informa.
- **La composición se prueba en el CI** (`imagen-smoke.yml` construye la imagen y la levanta completa).
- **Publicación reproducible.** Cada tag publica imagen, notas y paquete de instalación.

## Hallazgos

### DO-01 · La imagen no está endurecida

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** en el `Dockerfile`:
  - No hay instrucción `USER`: la aplicación corre como `root`.
  - `pip install uv` sin versión fija.
  - Las imágenes base usan etiquetas móviles (`python:3.12-slim`, `node:22-alpine`, y en la composición `postgres:16` y `caddy:2`).
  - `--forwarded-allow-ips "*"` acepta cabeceras de reenvío de cualquier origen.
- **Por qué importa:** son las cuatro prácticas básicas de una imagen de producción. El último punto es inocuo mientras solo Caddy alcance a la aplicación, y eso depende de que nadie publique el puerto 8000.
- **Recomendación:** agregar un usuario sin privilegios, fijar la versión de `uv`, y limitar `--forwarded-allow-ips` a la red interna de la composición.

### DO-02 · El respaldo depende de que alguien se acuerde

- **Vara:** Conformidad · **Severidad:** Alta · **Confianza:** Verificado (por la vista 70 y `BL-017`) · **Esfuerzo:** S
- **Evidencia:** `respaldar.sh` hace el volcado, lo verifica y rota 30 copias, pero "el operador lo programa y lo copia fuera del servidor" (vista 70). La base y los respaldos quedan en el mismo servidor.
- **Por qué importa:** el sistema guarda evaluaciones con valor académico. Un respaldo que no se programa solo no existe el día que hace falta, y un respaldo en el mismo disco no protege de la falla más probable.
- **Recomendación:** que `cognion.sh` instale un temporizador de `systemd` al desplegar, y que `cognion.sh salud` avise si el último respaldo tiene más de N días. Dejar la copia externa como paso obligatorio de la guía, con verificación.

### DO-03 · Dos juegos de scripts casi iguales y se prueba el que no se usa

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado (la duplicación de nombres), Inferido (el grado de divergencia) · **Esfuerzo:** M
- **Evidencia:**
  - `deploy/gcp/` y `deploy/servidor/` tienen cada uno su `cognion.sh`, `docker-compose.yml`, `Caddyfile`, `preparar-env.sh` y `salud.sh`.
  - `imagen-smoke.yml` levanta `deploy/gcp/cognion.sh`. La variante vigente es `deploy/servidor/`.
  - `CLAUDE.md` declara "no verificado: el camino del servidor con Docker real (Issue #624)".
- **Por qué importa:** la variante que se entrega en el paquete de la `1.0.0` es la que no tiene prueba automática. Dos copias de los mismos scripts divergen sin que nadie lo note.
- **Recomendación:** una composición base con un archivo de ajustes por variante, y que el CI pruebe `deploy/servidor/`. Si GCP sigue en pausa, archivar `deploy/gcp/`.

### DO-04 · El diagnóstico posterior a un incidente depende de 30 MB de registros

- **Vara:** Conformidad (escenario de observabilidad) · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** la composición rota los registros a 3 archivos de 10 MB por servicio. No hay métricas, alertas ni destino externo. El `healthcheck` del contenedor consulta `/api/health` (el proceso vive) y no `/api/health/ready` (la base responde).
- **Por qué importa:** el escenario pide poder reconstruir qué pasó. Con registros en formato JSON y actividad normal, 30 MB pueden ser horas o días; no se midió. Si la base deja de responder, el contenedor sigue figurando sano.
- **Recomendación:** medir cuánto duran 30 MB con una sesión en vivo real y ajustar. Usar `/api/health/ready` en el `healthcheck`. Que `cognion.sh` tenga un comando para empaquetar registros y estado ante un incidente.

### DO-05 · Quedan restos de despliegues anteriores

- **Vara:** Conformidad · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:**
  - `fly.toml` sigue en la raíz, marcado "HISTÓRICO", porque hay tests que leen su contenido ([VT-04](07-verificacion-y-testeabilidad.md#vt-04--los-tests-están-organizados-por-incremento-no-por-lo-que-prueban)).
  - El `Dockerfile` explica las migraciones con una referencia a `fly.toml`.
  - El job del CD se llama `build-and-deploy` y no despliega.
- **Por qué importa:** quien llega al repositorio encuentra tres destinos de despliegue y tiene que leer la documentación para saber cuál vale.
- **Recomendación:** borrar `fly.toml` y sus tests, corregir el comentario y renombrar el job.

### DO-06 · El despliegue automático que pide el requerimiento no existe

- **Vara:** Conformidad · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** decisión
- **Evidencia:** `cd.yml` construye y publica; instalar es `cognion.sh desplegar`, a mano. La vista 70 lo declara.
- **Por qué importa:** con un servidor y un operador, el despliegue manual con un comando es razonable. El problema es que el requerimiento escrito dice otra cosa.
- **Recomendación:** renegociar el escenario ([AQ-02](06-atributos-de-calidad.md#aq-02--dos-escenarios-llevan-incumplidos-desde-que-se-escribieron)), no automatizar.

## Juicio

Para un sistema de un docente y un servidor, el despliegue está bien pensado: un artefacto, un comando, versión única y composición probada. Lo urgente es el respaldo (DO-02), porque es el único hallazgo de este capítulo cuyo costo, si se materializa, es irreversible. Lo demás es endurecimiento y limpieza.
