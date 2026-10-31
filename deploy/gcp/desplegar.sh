#!/usr/bin/env bash
# Despliega una versión en la VM desde tu Mac (US-8.6.4): sincroniza deploy/gcp/ (sin tocar el .env de la VM) y
# ejecuta `cognion.sh desplegar` por SSH. Si la versión nueva no responde, la VM vuelve sola a la anterior.
#
#   PROYECTO=cognion-prueba-2410 ./desplegar.sh <versión | imagen>
#
# Una versión sola (v0.8.2) se completa a ghcr.io/vvalotto/cognion:v0.8.2; una imagen completa se usa tal cual.
# Variables opcionales: ZONA (us-central1-a), VM (cognion-vm), REPOSITORIO_IMAGEN (ghcr.io/vvalotto/cognion).
set -euo pipefail
cd "$(dirname "$0")"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }
case "${1:-}" in -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;; esac

PROYECTO="${PROYECTO:-}"; ZONA="${ZONA:-us-central1-a}"; VM="${VM:-cognion-vm}"
REPOSITORIO_IMAGEN="${REPOSITORIO_IMAGEN:-ghcr.io/vvalotto/cognion}"
ENTRADA="${1:-}"
command -v gcloud >/dev/null 2>&1 || abortar "Falta gcloud." "Instalá el SDK de Google Cloud."
[ -n "$PROYECTO" ] || abortar "Falta PROYECTO." "Ej.: PROYECTO=cognion-prueba-2410 $0 v0.8.2"
[ -n "$ENTRADA" ] || abortar "Indicá la versión o la imagen a desplegar." "Ej.: PROYECTO=cognion-prueba-2410 $0 v0.8.2"

case "$ENTRADA" in
  */*|*:*) IMAGEN="$ENTRADA" ;;
  *) IMAGEN="$REPOSITORIO_IMAGEN:$ENTRADA" ;;
esac

SSH=(gcloud compute ssh "$VM" --project="$PROYECTO" --zone="$ZONA" --quiet)
echo "• Sincronizando deploy/gcp/ con la VM (el .env de la VM no se toca)"
COPYFILE_DISABLE=1 tar czf - -C .. --exclude='gcp/.env' gcp | "${SSH[@]}" --command='mkdir -p ~/cognion/deploy && tar xzf - -C ~/cognion/deploy'
echo "• Desplegando $IMAGEN"
"${SSH[@]}" --command="cd ~/cognion/deploy/gcp && ./cognion.sh desplegar '$IMAGEN'"
