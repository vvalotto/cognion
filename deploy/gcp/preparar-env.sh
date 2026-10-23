#!/usr/bin/env bash
# Genera deploy/gcp/.env con secretos aleatorios y permisos 600 (US-8.6.2). Idempotente: si ya existe, no lo toca.
# Uso: deploy/gcp/preparar-env.sh [dominio]      (ej. cognion.duckdns.org; si falta, lo pide)
set -euo pipefail
cd "$(dirname "$0")"

if [ -f .env ]; then
  echo ".env ya existe: no se modifica."
  exit 0
fi
command -v openssl >/dev/null 2>&1 || { echo "ERROR: falta openssl." >&2; exit 1; }

DOMINIO="${1:-}"
[ -n "$DOMINIO" ] || read -r -p "Dominio de la prueba (ej. cognion.duckdns.org): " DOMINIO
if ! printf '%s' "$DOMINIO" | grep -Eq '^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$'; then
  echo "ERROR: dominio inválido (sin esquema ni barras): '$DOMINIO'." >&2
  exit 1
fi

SECRETO="$(openssl rand -hex 32)"
PASSWORD_DB="$(openssl rand -hex 24)"
umask 077
sed -e "s|__DOMINIO__|${DOMINIO}|g" -e "s|__SECRETO__|${SECRETO}|g" -e "s|__PASSWORD_DB__|${PASSWORD_DB}|g" .env.example > .env
chmod 600 .env
echo ".env creado en $(pwd)/.env (permisos 600). Los secretos no se muestran."
