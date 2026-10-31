#!/usr/bin/env bash
# Respalda la base local de Cognión (US-8.5.4, ADR-022 variante local): `pg_dump -Fc` verificado y con rotación.
#
# Uso: scripts/local/respaldar.sh
# Variables opcionales:
#   COGNION_RESPALDOS     carpeta destino            (default ~/CognionRespaldos; fuera de git)
#   COGNION_RESPALDOS_N   respaldos a conservar      (default 30)
#   COGNION_LOCAL_ENV     configuración de la base   (default .env.local)
set -euo pipefail
cd "$(dirname "$0")/../.."
. scripts/local/_conexion.sh

DESTINO="${COGNION_RESPALDOS:-$HOME/CognionRespaldos}"
CONSERVAR="${COGNION_RESPALDOS_N:-30}"
case "$CONSERVAR" in ''|*[!0-9]*|0) abortar "COGNION_RESPALDOS_N debe ser un entero positivo (recibí '$CONSERVAR')." ;; esac

[ -n "$(admin "SELECT 1 FROM pg_database WHERE datname='${BASE}'" 2>/dev/null || true)" ] \
  || abortar "La base '$BASE' no existe." "Ejecutá scripts/local/levantar.sh para crearla."

umask 077
mkdir -p "$DESTINO"
# El nombre lleva el de la base respaldada (con la base por defecto, `cognion_local-<fecha>.dump`): así los
# respaldos de dos bases en la misma Mac no se mezclan ni se rotan entre sí (hallazgo #10 de la UAT de v0.9.0).
ARCHIVO="$DESTINO/${BASE}-$(date +%Y%m%d-%H%M%S).dump"

if ! PGPASSWORD="$CLAVE" pg_dump -Fc -h "$HOST" -p "$PUERTO_PG" -U "$USUARIO" -f "$ARCHIVO" "$BASE" 2>"$ARCHIVO.err"; then
  cat "$ARCHIVO.err" >&2; rm -f "$ARCHIVO" "$ARCHIVO.err"
  abortar "pg_dump falló."
fi
rm -f "$ARCHIVO.err"

# Verificación: no vacío y legible por pg_restore.
if [ ! -s "$ARCHIVO" ] || ! pg_restore --list "$ARCHIVO" >/dev/null 2>&1; then
  rm -f "$ARCHIVO"
  abortar "El respaldo generado está vacío o no es legible; se descartó."
fi
( cd "$DESTINO" && shasum -a 256 "$(basename "$ARCHIVO")" > "$(basename "$ARCHIVO").sha256" )

# Rotación: se ordena por nombre (lleva la fecha y hora) y se conservan los últimos N.
SOBRAN="$(ls -1 "$DESTINO"/"${BASE}"-*.dump | sort | awk -v n="$CONSERVAR" '{a[NR]=$0} END{for(i=1;i<=NR-n;i++) print a[i]}')"
for viejo in $SOBRAN; do rm -f "$viejo" "$viejo.sha256"; done

echo "Respaldo listo: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"
echo "Conservados: $(ls -1 "$DESTINO"/"${BASE}"-*.dump | wc -l | tr -d ' ') (máximo $CONSERVAR)"
