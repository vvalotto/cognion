#!/usr/bin/env bash
# Crea, de forma idempotente, la infraestructura de la prueba de uso en GCP (US-8.6.4, ADR-025).
# Solo crea lo que falta; ejecutarlo dos veces no duplica nada. Antes de crear muestra el plan y pide confirmación.
#
#   PROYECTO=cognion-prueba-2410 CUENTA_FACTURACION=XXXXXX-XXXXXX-XXXXXX ./aprovisionar.sh [--si]
#
# Variables opcionales: REGION (us-central1), ZONA (us-central1-a), VM (cognion-vm), IP_NOMBRE (cognion-ip),
# REGLA (cognion-web), PRESUPUESTO_NOMBRE (cognion-prueba), PRESUPUESTO_USD (5).
# --si omite la confirmación. NO cambia la configuración activa de gcloud: todo lleva --project.
# CUIDADO: crea recursos que pueden costar dinero (la IPv4 pública en uso se cobra, ~0,005 USD/hora).
set -euo pipefail
cd "$(dirname "$0")"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }

SI=0
for arg in "$@"; do
  case "$arg" in
    --si) SI=1 ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) abortar "Opción desconocida: $arg" "Usá --si o --help." ;;
  esac
done

PROYECTO="${PROYECTO:-}"
CUENTA_FACTURACION="${CUENTA_FACTURACION:-}"
REGION="${REGION:-us-central1}"
ZONA="${ZONA:-us-central1-a}"
VM="${VM:-cognion-vm}"
IP_NOMBRE="${IP_NOMBRE:-cognion-ip}"
REGLA="${REGLA:-cognion-web}"
PRESUPUESTO_NOMBRE="${PRESUPUESTO_NOMBRE:-cognion-prueba}"
PRESUPUESTO_USD="${PRESUPUESTO_USD:-5}"

command -v gcloud >/dev/null 2>&1 || abortar "Falta gcloud." "Instalá el SDK de Google Cloud: https://cloud.google.com/sdk/docs/install"
[ -n "$PROYECTO" ] || abortar "Falta PROYECTO." "Ej.: PROYECTO=cognion-prueba-2410 CUENTA_FACTURACION=XXXXXX-XXXXXX-XXXXXX $0"
[ -n "$CUENTA_FACTURACION" ] || abortar "Falta CUENTA_FACTURACION." "Ver tus cuentas: gcloud billing accounts list"
printf '%s' "$PROYECTO" | grep -Eq '^[a-z][a-z0-9-]{4,28}[a-z0-9]$' || abortar "PROYECTO inválido: '$PROYECTO'." "6 a 30 caracteres: minúsculas, números y guiones; empieza con letra."
[ -n "$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null)" ] \
  || abortar "No hay una sesión de gcloud activa." "Ejecutá: gcloud auth login"

# --- ¿Qué existe ya? -------------------------------------------------------------------------------------
existe_proyecto() { [ "$(gcloud projects describe "$PROYECTO" --format='value(lifecycleState)' 2>/dev/null)" = "ACTIVE" ]; }
facturacion_ok() { [ "$(gcloud billing projects describe "$PROYECTO" --format='value(billingEnabled)' 2>/dev/null)" = "True" ]; }
faltan_apis() {
  local habilitadas; habilitadas="$(gcloud services list --enabled --project="$PROYECTO" --format='value(config.name)' 2>/dev/null || true)"
  for api in compute.googleapis.com billingbudgets.googleapis.com; do grep -qx "$api" <<<"$habilitadas" || return 0; done
  return 1
}
existe_presupuesto() { gcloud billing budgets list --billing-account="$CUENTA_FACTURACION" --format='value(displayName)' 2>/dev/null | grep -qx "$PRESUPUESTO_NOMBRE"; }
existe_rdp() { gcloud compute firewall-rules describe default-allow-rdp --project="$PROYECTO" >/dev/null 2>&1; }
existe_ip() { gcloud compute addresses describe "$IP_NOMBRE" --region="$REGION" --project="$PROYECTO" >/dev/null 2>&1; }
existe_regla() { gcloud compute firewall-rules describe "$REGLA" --project="$PROYECTO" >/dev/null 2>&1; }
existe_vm() { gcloud compute instances describe "$VM" --zone="$ZONA" --project="$PROYECTO" >/dev/null 2>&1; }

HACER_PROYECTO=0; HACER_FACTURACION=0; HACER_APIS=0; HACER_PRESUPUESTO=0; HACER_RDP=0; HACER_IP=0; HACER_REGLA=0; HACER_VM=0
PLAN=()
existe_proyecto || { HACER_PROYECTO=1; PLAN+=("crear el proyecto $PROYECTO"); }
if [ $HACER_PROYECTO -eq 1 ] || ! facturacion_ok; then HACER_FACTURACION=1; PLAN+=("vincular la facturación $CUENTA_FACTURACION"); fi
if [ $HACER_PROYECTO -eq 1 ] || faltan_apis; then HACER_APIS=1; PLAN+=("habilitar Compute Engine y la API de presupuestos"); fi
existe_presupuesto || { HACER_PRESUPUESTO=1; PLAN+=("crear el presupuesto $PRESUPUESTO_NOMBRE de $PRESUPUESTO_USD USD (alertas al 50 % y 100 %)"); }
# En un proyecto nuevo la regla default-allow-rdp no existe todavía: la crea Google al habilitar Compute Engine, así que se
# decide si cerrarla DESPUÉS de habilitar las APIs (si no, la primera corrida la dejaría abierta a internet).
if [ $HACER_PROYECTO -eq 1 ] || existe_rdp; then HACER_RDP=1; PLAN+=("eliminar la regla default-allow-rdp si existe (RDP abierto a internet)"); fi
existe_ip || { HACER_IP=1; PLAN+=("reservar la IP estática $IP_NOMBRE en $REGION"); }
existe_regla || { HACER_REGLA=1; PLAN+=("crear la regla $REGLA (solo TCP 80 y 443)"); }
existe_vm || { HACER_VM=1; PLAN+=("crear la VM $VM (e2-micro, $ZONA, Debian 12, disco estándar de 30 GB) y prepararla (swap y Docker)"); }

if [ ${#PLAN[@]} -eq 0 ]; then
  echo "Nada que crear: la infraestructura de $PROYECTO ya está completa."
  exit 0
fi

echo "Proyecto: $PROYECTO · Facturación: $CUENTA_FACTURACION · Región: $REGION"
echo "Se va a hacer lo siguiente:"
for item in "${PLAN[@]}"; do echo "  - $item"; done
echo "AVISO: son recursos reales; la IPv4 pública en uso se cobra (~0,005 USD/hora) y el resto depende de la capa gratuita."
if [ $SI -ne 1 ]; then
  read -r -p "Escribí SI para continuar: " RESPUESTA || RESPUESTA=""
  [ "$RESPUESTA" = "SI" ] || abortar "Cancelado: no se creó nada." ""
fi

# --- Ejecución, en el orden que funcionó en la prueba manual ----------------------------------------------
[ $HACER_PROYECTO -eq 1 ] && { echo "• Creando el proyecto"; gcloud projects create "$PROYECTO" --name="Cognion prueba"; }
[ $HACER_FACTURACION -eq 1 ] && { echo "• Vinculando la facturación"; gcloud billing projects link "$PROYECTO" --billing-account="$CUENTA_FACTURACION"; }
[ $HACER_APIS -eq 1 ] && { echo "• Habilitando las APIs"; gcloud services enable compute.googleapis.com billingbudgets.googleapis.com --project="$PROYECTO"; }
if [ $HACER_PRESUPUESTO -eq 1 ]; then
  echo "• Creando el presupuesto"
  NUMERO="$(gcloud projects describe "$PROYECTO" --format='value(projectNumber)')"
  gcloud billing budgets create --billing-account="$CUENTA_FACTURACION" --display-name="$PRESUPUESTO_NOMBRE" \
    --budget-amount="${PRESUPUESTO_USD}USD" --filter-projects="projects/$NUMERO" \
    --threshold-rule=percent=0.5 --threshold-rule=percent=1.0
fi
if [ $HACER_RDP -eq 1 ] && existe_rdp; then echo "• Cerrando RDP"; gcloud compute firewall-rules delete default-allow-rdp --project="$PROYECTO" --quiet; fi
[ $HACER_IP -eq 1 ] && { echo "• Reservando la IP"; gcloud compute addresses create "$IP_NOMBRE" --region="$REGION" --project="$PROYECTO"; }
[ $HACER_REGLA -eq 1 ] && {
  echo "• Creando la regla de firewall"
  gcloud compute firewall-rules create "$REGLA" --project="$PROYECTO" --network=default --direction=INGRESS --action=ALLOW \
    --rules=tcp:80,tcp:443 --target-tags="$REGLA" --source-ranges=0.0.0.0/0
}
if [ $HACER_VM -eq 1 ]; then
  echo "• Creando la VM"
  gcloud compute instances create "$VM" --project="$PROYECTO" --zone="$ZONA" --machine-type=e2-micro \
    --image-family=debian-12 --image-project=debian-cloud --boot-disk-size=30GB --boot-disk-type=pd-standard \
    --address="$IP_NOMBRE" --tags="$REGLA"
  echo "• Esperando el acceso SSH (la primera vez gcloud crea una clave en ~/.ssh/google_compute_engine)"
  for intento in $(seq 1 18); do
    gcloud compute ssh "$VM" --project="$PROYECTO" --zone="$ZONA" --quiet --command=true >/dev/null 2>&1 && break
    [ "$intento" -lt 18 ] || abortar "La VM no aceptó SSH a tiempo." "Reintentá con: gcloud compute ssh $VM --project=$PROYECTO --zone=$ZONA"
    sleep 10
  done
  echo "• Preparando la VM (swap y Docker)"
  gcloud compute ssh "$VM" --project="$PROYECTO" --zone="$ZONA" --quiet --command='bash -s' < preparar-vm.sh
fi

IP_VALOR="$(gcloud compute addresses describe "$IP_NOMBRE" --region="$REGION" --project="$PROYECTO" --format='value(address)' 2>/dev/null || true)"
echo "Listo. IP de la VM: ${IP_VALOR:-desconocida}"
echo "Siguiente: apuntá tu subdominio de DuckDNS a esa IP y desplegá con deploy/gcp/desplegar.sh <versión>."
