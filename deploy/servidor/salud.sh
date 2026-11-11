#!/usr/bin/env bash
# Lectura del estado de salud de la aplicación (US-8.3.3). Se carga con `source` desde cognion.sh.
#
#   mostrar_salud https://mi-subdominio.duckdns.org
#
# Muestra la respuesta de /api/health (el proceso está vivo) y de /api/health/ready (además la base de
# datos responde). Si la segunda no es 200 lo dice, sin ocultar la primera: "viva pero sin base" es un
# estado distinto de "caída".

mostrar_salud() {
  local base="$1" ruta salida codigo cuerpo codigo_ready="000"
  for ruta in health health/ready; do
    if salida="$(curl -sS -k -m 10 -w $'\n%{http_code}' "${base}/api/${ruta}" 2>&1)"; then
      codigo="${salida##*$'\n'}"
      cuerpo="${salida%$'\n'*}"
    else
      codigo="000"
      cuerpo="sin respuesta"
    fi
    printf '%-18s %s  %s\n' "/api/${ruta}" "$codigo" "$cuerpo"
    [ "$ruta" = "health/ready" ] && codigo_ready="$codigo"
  done
  if [ "$codigo_ready" != "200" ]; then
    echo "AVISO: la aplicación no está lista para atender pedidos (/api/health/ready respondió ${codigo_ready}). Revisá la base de datos: ./cognion.sh logs app o ./cognion.sh estado."
  fi
}
