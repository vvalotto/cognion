#!/usr/bin/env bash
# Genera deploy/servidor/.env con secretos aleatorios y permisos 600 (US-10.2.2). Idempotente: si ya existe, no lo toca.
#
#   ./preparar-env.sh cognion.facultad.edu.ar          con dominio: HTTPS automático (Caddy)
#   ./preparar-env.sh --sin-dominio 10.0.0.15          sin dominio: solo HTTP, por IP o nombre
#
# La imagen es ghcr.io/vvalotto/cognion:v<VERSION>, con la versión del paquete (archivo VERSION de la raíz del paquete).
# Variables opcionales: REPOSITORIO_IMAGEN (otra imagen) y, solo con --sin-dominio, COGNION_HTTP_PORT (si no es el 80).
set -euo pipefail
cd "$(dirname "$0")"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }
if [ -f .env ]; then
  echo ".env ya existe: no se modifica."
  exit 0
fi
command -v openssl >/dev/null 2>&1 || abortar "Falta openssl."

SIN_DOMINIO=0
if [ "${1:-}" = "--sin-dominio" ]; then SIN_DOMINIO=1; shift; fi
ENTRADA="${1:-}"
if [ -z "$ENTRADA" ]; then
  if [ "$SIN_DOMINIO" = "1" ]; then read -r -p "IP o nombre del servidor (ej. 10.0.0.15): " ENTRADA
  else read -r -p "Dominio (ej. cognion.facultad.edu.ar): " ENTRADA; fi
fi
printf '%s' "$ENTRADA" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$' \
  || abortar "Dirección inválida (sin esquema, puerto ni barras): '$ENTRADA'."

[ -f ../../VERSION ] || abortar "No encuentro ../../VERSION." "Este script se ejecuta desde el paquete de instalación (o el repositorio)."
VERSION="$(tr -d '[:space:]' < ../../VERSION)"
IMAGEN="${REPOSITORIO_IMAGEN:-ghcr.io/vvalotto/cognion}:v${VERSION}"

PUERTO_LINEA=""
if [ "$SIN_DOMINIO" = "1" ]; then
  DOMINIO=":80"
  PUERTO="${COGNION_HTTP_PORT:-80}"
  case "$PUERTO" in ''|*[!0-9]*) abortar "COGNION_HTTP_PORT debe ser un número (recibí '$PUERTO')." ;; esac
  if [ "$PUERTO" = "80" ]; then URL="http://${ENTRADA}"; else URL="http://${ENTRADA}:${PUERTO}"; PUERTO_LINEA="COGNION_HTTP_PORT=${PUERTO}"; fi
else
  DOMINIO="$ENTRADA"
  URL="https://${ENTRADA}"
fi

SECRETO="$(openssl rand -hex 32)"
PASSWORD_DB="$(openssl rand -hex 24)"
umask 077
sed -e "s|__DOMINIO__|${DOMINIO}|g" -e "s|__IMAGEN__|${IMAGEN}|g" -e "s|__URL__|${URL}|g" \
    -e "s|__SECRETO__|${SECRETO}|g" -e "s|__PASSWORD_DB__|${PASSWORD_DB}|g" .env.example > .env
[ -z "$PUERTO_LINEA" ] || printf '%s\n' "$PUERTO_LINEA" >> .env
chmod 600 .env
echo ".env creado en $(pwd)/.env (permisos 600). Los secretos no se muestran."
echo "Imagen: $IMAGEN · Acceso: $URL"
