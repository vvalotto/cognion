#!/usr/bin/env bash
# Detiene el servidor que dejó en segundo plano `levantar.sh --fondo` (US-8.5.3).
set -euo pipefail
cd "$(dirname "$0")/../.."
LOGS="${COGNION_LOCAL_LOGS:-logs/local}"
PID_ARCHIVO="$LOGS/servidor.pid"

if [ ! -f "$PID_ARCHIVO" ]; then
  echo "No hay un servidor en segundo plano registrado ($PID_ARCHIVO)."
  exit 0
fi
PID="$(cat "$PID_ARCHIVO")"
if kill -0 "$PID" 2>/dev/null; then
  pkill -P "$PID" 2>/dev/null || true   # uvicorn, hijo de caffeinate
  kill "$PID" 2>/dev/null || true
  for _ in $(seq 1 40); do   # espera el cierre ordenado (hasta ~10 s) para que el puerto quede libre
    kill -0 "$PID" 2>/dev/null || break
    sleep 0.25
  done
  if kill -0 "$PID" 2>/dev/null; then
    pkill -9 -P "$PID" 2>/dev/null || true
    kill -9 "$PID" 2>/dev/null || true
  fi
  echo "Servidor detenido (PID $PID)."
else
  echo "El proceso $PID ya no estaba corriendo."
fi
rm -f "$PID_ARCHIVO"
