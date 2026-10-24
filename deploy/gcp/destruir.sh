#!/usr/bin/env bash
# Borra lo que creó aprovisionar.sh, por nombre y nada más (US-8.6.4): la VM, la regla de firewall y la IP.
# Pide confirmación. El PROYECTO solo se borra con --proyecto y escribiendo su ID. No toca presupuestos ni otras reglas.
#
#   PROYECTO=cognion-prueba-2410 ./destruir.sh [--si] [--proyecto]
#
# Variables opcionales: REGION, ZONA, VM, IP_NOMBRE, REGLA (mismos valores por defecto que aprovisionar.sh).
# CUIDADO: borrar el proyecto elimina TODO lo que contiene; queda 30 días en espera y se puede recuperar con
# `gcloud projects undelete`, pero después es definitivo.
set -euo pipefail
cd "$(dirname "$0")"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }

SI=0; BORRAR_PROYECTO=0
for arg in "$@"; do
  case "$arg" in
    --si) SI=1 ;;
    --proyecto) BORRAR_PROYECTO=1 ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) abortar "Opción desconocida: $arg" "Usá --si, --proyecto o --help." ;;
  esac
done

PROYECTO="${PROYECTO:-}"
REGION="${REGION:-us-central1}"; ZONA="${ZONA:-us-central1-a}"
VM="${VM:-cognion-vm}"; IP_NOMBRE="${IP_NOMBRE:-cognion-ip}"; REGLA="${REGLA:-cognion-web}"

command -v gcloud >/dev/null 2>&1 || abortar "Falta gcloud." "Instalá el SDK de Google Cloud."
[ -n "$PROYECTO" ] || abortar "Falta PROYECTO." "Ej.: PROYECTO=cognion-prueba-2410 $0"
[ -n "$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null)" ] \
  || abortar "No hay una sesión de gcloud activa." "Ejecutá: gcloud auth login"

existe_vm() { gcloud compute instances describe "$VM" --zone="$ZONA" --project="$PROYECTO" >/dev/null 2>&1; }
existe_regla() { gcloud compute firewall-rules describe "$REGLA" --project="$PROYECTO" >/dev/null 2>&1; }
existe_ip() { gcloud compute addresses describe "$IP_NOMBRE" --region="$REGION" --project="$PROYECTO" >/dev/null 2>&1; }

PLAN=()
existe_vm && PLAN+=("borrar la VM $VM (y su disco)")
existe_regla && PLAN+=("borrar la regla de firewall $REGLA")
existe_ip && PLAN+=("liberar la IP $IP_NOMBRE")
[ $BORRAR_PROYECTO -eq 1 ] && PLAN+=("BORRAR EL PROYECTO $PROYECTO completo (30 días para recuperarlo)")

if [ ${#PLAN[@]} -eq 0 ]; then
  echo "Nada que borrar: la VM, la regla y la IP de $PROYECTO ya no existen."
  exit 0
fi
echo "Proyecto: $PROYECTO. Se va a hacer lo siguiente:"
for item in "${PLAN[@]}"; do echo "  - $item"; done
if [ $SI -ne 1 ]; then
  read -r -p "Escribí SI para continuar: " RESPUESTA || RESPUESTA=""
  [ "$RESPUESTA" = "SI" ] || abortar "Cancelado: no se borró nada." ""
fi
if [ $BORRAR_PROYECTO -eq 1 ]; then
  read -r -p "Para borrar el proyecto escribí su ID exacto ($PROYECTO): " CONFIRMA || CONFIRMA=""
  [ "$CONFIRMA" = "$PROYECTO" ] || abortar "El ID no coincide: no se borró nada." ""
fi

# La VM primero: mientras la usa, la IP no se puede liberar.
existe_vm && { echo "• Borrando la VM"; gcloud compute instances delete "$VM" --zone="$ZONA" --project="$PROYECTO" --quiet; }
existe_regla && { echo "• Borrando la regla de firewall"; gcloud compute firewall-rules delete "$REGLA" --project="$PROYECTO" --quiet; }
existe_ip && { echo "• Liberando la IP"; gcloud compute addresses delete "$IP_NOMBRE" --region="$REGION" --project="$PROYECTO" --quiet; }
if [ $BORRAR_PROYECTO -eq 1 ]; then
  echo "• Borrando el proyecto"
  gcloud projects delete "$PROYECTO" --quiet
  echo "El proyecto queda en espera de eliminación 30 días: gcloud projects undelete $PROYECTO"
fi
echo "Listo."
