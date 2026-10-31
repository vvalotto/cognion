#!/usr/bin/env bash
# Operación de la VM de la prueba de uso (US-8.6.2). Se ejecuta desde cualquier carpeta.
#
#   cognion.sh iniciar         levanta la base, aplica las migraciones y arranca la aplicación y el proxy
#   cognion.sh migrar          aplica las migraciones (paso explícito; la aplicación nunca migra al arrancar, US-8.1.4)
#   cognion.sh administrador   crea el primer Administrador (nombre y email por ADMIN_NOMBRE/ADMIN_EMAIL o se piden;
#                              la contraseña se pide por terminal sin eco, o ADMIN_PASSWORD en una corrida no interactiva)
#   cognion.sh estado          muestra los servicios, las versiones y consulta /api/health
#   cognion.sh desplegar <imagen>  baja la imagen, respalda si puede, migra con la imagen nueva (la vieja sigue sirviendo),
#                              la reemplaza y espera la salud; si no responde vuelve sola a la anterior (US-8.6.4)
#   cognion.sh rollback        vuelve a la versión anterior (solo de imagen: las migraciones no se deshacen)
#   cognion.sh logs [servicio] sigue el log
#   cognion.sh detener         baja los servicios (los datos quedan en el volumen)
set -euo pipefail
cd "$(dirname "$0")"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }
command -v docker >/dev/null 2>&1 || abortar "Falta docker." "Instalá Docker Engine y el plugin compose."
[ -f .env ] || abortar "No existe deploy/gcp/.env." "Ejecutá deploy/gcp/preparar-env.sh <dominio> primero."
compose() { docker compose "$@"; }
# Con terminal interactiva `run` reserva un tty; sin ella (CI) hay que pasarle -T.
correr() { if [ -t 0 ]; then compose run --rm "$@"; else compose run --rm -T "$@"; fi; }
dominio() { grep -E '^COGNION_DOMINIO=' .env | cut -d= -f2-; }
leer_env() { grep -E "^$1=" .env | head -n 1 | cut -d= -f2- || true; }
# Reemplaza o agrega una clave de .env de forma atómica y conservando los permisos 600.
escribir_env() {
  local tmp; tmp="$(mktemp ./.env.XXXXXX)"; chmod 600 "$tmp"
  { grep -v -E "^$1=" .env || true; } > "$tmp"
  printf '%s=%s\n' "$1" "$2" >> "$tmp"
  mv "$tmp" .env
}
# Levanta la aplicación con la imagen que dice .env y espera a que su healthcheck (/api/health) responda.
levantar_app() { compose up -d --wait --wait-timeout "${COGNION_ESPERA_SALUD:-90}" app; }

case "${1:-}" in
  iniciar)
    compose up -d --wait db
    correr app alembic upgrade head
    compose up -d --wait app
    compose up -d caddy
    echo "Servicios arriba. Probá: https://$(dominio)/api/health"
    ;;
  migrar)
    compose up -d --wait db
    correr app alembic upgrade head
    ;;
  administrador)
    compose up -d --wait db
    if [ -z "${ADMIN_NOMBRE:-}" ]; then read -r -p "Nombre y apellido del Administrador: " ADMIN_NOMBRE; fi
    if [ -z "${ADMIN_EMAIL:-}" ]; then read -r -p "Email del Administrador: " ADMIN_EMAIL; fi
    export ADMIN_NOMBRE ADMIN_EMAIL
    correr -e ADMIN_NOMBRE -e ADMIN_EMAIL ${ADMIN_PASSWORD:+-e ADMIN_PASSWORD} app \
      python -m src.identidad.frameworks.cli.bootstrap_administrador
    ;;
  estado)
    compose ps
    echo "Versión actual:   $(leer_env COGNION_IMAGE)"
    echo "Versión anterior: $(leer_env COGNION_IMAGE_ANTERIOR)"
    curl -fsS -k "https://$(dominio)/api/health" && echo
    ;;
  desplegar)
    imagen="${2:-}"
    [ -n "$imagen" ] || abortar "Indicá la imagen a desplegar." "Ej.: $0 desplegar ghcr.io/vvalotto/cognion:v0.8.2"
    actual="$(leer_env COGNION_IMAGE)"
    anterior_previo="$(leer_env COGNION_IMAGE_ANTERIOR)"
    [ -n "$actual" ] || abortar "No encuentro COGNION_IMAGE en .env." "Revisá deploy/gcp/.env."
    echo "• Desplegando $imagen (versión actual: $actual)"

    # 1. Bajar la imagen. Si falla no se toca nada. Una imagen cargada a mano (docker load) no se baja.
    if ! docker image inspect "$imagen" >/dev/null 2>&1; then
      docker pull "$imagen" || abortar "No pude bajar la imagen $imagen." "No se modificó nada: la versión actual sigue sirviendo."
    fi

    # 2. Respaldo previo, si ya existe el script (US-8.6.5).
    if [ -x ./respaldar.sh ]; then
      ./respaldar.sh || abortar "El respaldo previo falló." "Se abortó el despliegue: la versión actual sigue sirviendo."
    else
      echo "AVISO: no hay respaldar.sh todavía (US-8.6.5): se despliega sin respaldo previo." >&2
    fi

    # 3. Migraciones con la imagen NUEVA, mientras la aplicación vieja sigue sirviendo. Si fallan, se aborta.
    compose up -d --wait db
    if ! COGNION_IMAGE="$imagen" correr app alembic upgrade head; then
      abortar "La migración falló: el despliegue se abortó." "La versión anterior ($actual) sigue sirviendo."
    fi

    # 4. Reemplazar la aplicación y esperar la salud.
    escribir_env COGNION_IMAGE_ANTERIOR "$actual"
    escribir_env COGNION_IMAGE "$imagen"
    if levantar_app; then
      echo "Desplegado: $imagen. Versión anterior guardada para rollback: $actual"
      exit 0
    fi

    # 5. La versión nueva no pasó la verificación: volver a la anterior.
    echo "ERROR: la versión nueva no respondió en /api/health. Volviendo a $actual" >&2
    escribir_env COGNION_IMAGE "$actual"
    if [ -n "$anterior_previo" ]; then escribir_env COGNION_IMAGE_ANTERIOR "$anterior_previo"; else escribir_env COGNION_IMAGE_ANTERIOR ""; fi
    if levantar_app; then
      echo "Rollback hecho: sirve $actual otra vez." >&2
    else
      echo "ATENCIÓN: tampoco la versión anterior respondió. Revisá: $0 logs app" >&2
    fi
    exit 1
    ;;
  rollback)
    anterior="$(leer_env COGNION_IMAGE_ANTERIOR)"
    actual="$(leer_env COGNION_IMAGE)"
    [ -n "$anterior" ] || abortar "No hay una versión anterior guardada." "Se guarda al desplegar con: $0 desplegar <imagen>"
    echo "• Volviendo de $actual a $anterior (solo la imagen: las migraciones aplicadas no se deshacen)"
    escribir_env COGNION_IMAGE "$anterior"
    escribir_env COGNION_IMAGE_ANTERIOR "$actual"
    levantar_app || abortar "La versión $anterior no respondió en /api/health." "Revisá: $0 logs app"
    echo "Rollback hecho: sirve $anterior."
    ;;
  logs)
    compose logs -f --tail=100 "${@:2}"
    ;;
  detener)
    compose down
    ;;
  *)
    sed -n '2,16p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
