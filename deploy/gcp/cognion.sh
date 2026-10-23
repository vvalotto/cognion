#!/usr/bin/env bash
# Operación de la VM de la prueba de uso (US-8.6.2). Se ejecuta desde cualquier carpeta.
#
#   cognion.sh iniciar         levanta la base, aplica las migraciones y arranca la aplicación y el proxy
#   cognion.sh migrar          aplica las migraciones (paso explícito; la aplicación nunca migra al arrancar, US-8.1.4)
#   cognion.sh administrador   crea el primer Administrador (nombre y email por ADMIN_NOMBRE/ADMIN_EMAIL o se piden;
#                              la contraseña se pide por terminal sin eco, o ADMIN_PASSWORD en una corrida no interactiva)
#   cognion.sh estado          muestra los servicios y consulta /api/health
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
    curl -fsS -k "https://$(dominio)/api/health" && echo
    ;;
  logs)
    compose logs -f --tail=100 "${@:2}"
    ;;
  detener)
    compose down
    ;;
  *)
    sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
    exit 1
    ;;
esac
