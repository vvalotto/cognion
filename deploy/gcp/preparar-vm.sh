#!/usr/bin/env bash
# Prepara la VM de la prueba: swap de 1 GiB y Docker (US-8.6.4). Idempotente: lo que ya está no se toca.
# Se ejecuta EN la VM (aprovisionar.sh lo envía por SSH): bash -s < preparar-vm.sh
# Docker se instala desde su repositorio oficial de paquetes y se VERIFICA la huella de la clave antes de usarla;
# no se descarga ni ejecuta ningún script suelto.
set -euo pipefail

# Huella de la clave oficial de Docker (sin espacios). Si la clave descargada no coincide, se aborta.
HUELLA_DOCKER="9DC858229FC7DD38854AE2D88D81803C0EBFCD88"
USUARIO="${SUDO_USER:-${USER:-$(id -un)}}"

abortar() { echo "ERROR: $1" >&2; exit 1; }
[ "$(id -u)" -eq 0 ] || command -v sudo >/dev/null 2>&1 || abortar "Hace falta sudo."
S=""; [ "$(id -u)" -eq 0 ] || S="sudo"

# --- Swap de 1 GiB -------------------------------------------------------------------------------------
if $S swapon --show=NAME --noheadings | grep -qx "/swapfile"; then
  echo "• Swap: ya activo."
else
  echo "• Swap: creando 1 GiB en /swapfile"
  [ -f /swapfile ] || $S fallocate -l 1G /swapfile
  $S chmod 600 /swapfile
  $S mkswap /swapfile >/dev/null
  $S swapon /swapfile
fi
grep -q "^/swapfile " /etc/fstab || echo "/swapfile none swap sw 0 0" | $S tee -a /etc/fstab >/dev/null

# --- Docker --------------------------------------------------------------------------------------------
if command -v docker >/dev/null 2>&1 && $S docker compose version >/dev/null 2>&1; then
  echo "• Docker: ya instalado ($($S docker --version))."
else
  echo "• Docker: instalando desde el repositorio oficial"
  export DEBIAN_FRONTEND=noninteractive
  $S apt-get update -qq
  $S apt-get install -y -qq ca-certificates curl gnupg >/dev/null
  $S install -m 0755 -d /etc/apt/keyrings
  $S curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  HUELLA="$($S gpg --show-keys --with-colons /etc/apt/keyrings/docker.asc 2>/dev/null | awk -F: '/^fpr:/{print $10; exit}')"
  if [ "$HUELLA" != "$HUELLA_DOCKER" ]; then
    $S rm -f /etc/apt/keyrings/docker.asc
    abortar "La huella de la clave de Docker no coincide (recibida: ${HUELLA:-vacía}). No se instala nada."
  fi
  $S chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | $S tee /etc/apt/sources.list.d/docker.list >/dev/null
  $S apt-get update -qq
  $S apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin >/dev/null
fi
$S systemctl enable --now docker >/dev/null 2>&1 || true
id -nG "$USUARIO" | tr ' ' '\n' | grep -qx docker || $S usermod -aG docker "$USUARIO"

echo "• Listo. Swap:"; $S swapon --show
echo "• Docker: $($S docker --version); $($S docker compose version)"
