#!/usr/bin/env bash
# Respalda la base de Cognión (US-10.2.2): `pg_dump -Fc` desde el contenedor, verificado, con sha256 y rotación.
#
#   ./respaldar.sh            (o ./cognion.sh respaldar)
#
# Variables opcionales:
#   COGNION_RESPALDOS     carpeta destino          (por defecto ./respaldos, junto a este script)
#   COGNION_RESPALDOS_N   respaldos a conservar    (por defecto 30)
#
# Si algo falla no queda ningún archivo a medias. `./cognion.sh desplegar` lo ejecuta antes de migrar y se aborta si falla.
# Copiá los respaldos FUERA del servidor: un disco roto se lleva la base y también las copias que estén en él.
set -euo pipefail
cd "$(dirname "$0")"

abortar() { echo "ERROR: $1" >&2; [ -n "${2:-}" ] && echo "  → $2" >&2; exit 1; }
hash_sha256() { if command -v sha256sum >/dev/null 2>&1; then sha256sum "$@"; else shasum -a 256 "$@"; fi; }

command -v docker >/dev/null 2>&1 || abortar "Falta docker."
[ -f .env ] || abortar "No existe deploy/servidor/.env." "Ejecutá ./preparar-env.sh primero."
DESTINO="${COGNION_RESPALDOS:-./respaldos}"
CONSERVAR="${COGNION_RESPALDOS_N:-30}"
case "$CONSERVAR" in ''|*[!0-9]*|0) abortar "COGNION_RESPALDOS_N debe ser un entero positivo (recibí '$CONSERVAR')." ;; esac

umask 077
mkdir -p "$DESTINO"
ARCHIVO="$DESTINO/cognion-$(date +%Y%m%d-%H%M%S).dump"
PARCIAL="$ARCHIVO.parcial"
trap 'rm -f "$PARCIAL" "$PARCIAL.err"' EXIT

if ! docker compose exec -T db pg_dump -Fc -U cognion cognion > "$PARCIAL" 2> "$PARCIAL.err"; then
  cat "$PARCIAL.err" >&2
  abortar "pg_dump falló." "¿Está la base arriba? Probá: ./cognion.sh iniciar"
fi
# Verificación: no vacío y legible por pg_restore.
if [ ! -s "$PARCIAL" ] || ! docker compose exec -T db pg_restore --list < "$PARCIAL" >/dev/null 2>&1; then
  abortar "El respaldo generado está vacío o no es legible; se descartó."
fi
mv "$PARCIAL" "$ARCHIVO"
( cd "$DESTINO" && hash_sha256 "$(basename "$ARCHIVO")" > "$(basename "$ARCHIVO").sha256" )

# Rotación: el nombre lleva fecha y hora, así que ordenar por nombre es ordenar por antigüedad.
SOBRAN="$(ls -1 "$DESTINO"/cognion-*.dump | sort | awk -v n="$CONSERVAR" '{a[NR]=$0} END{for(i=1;i<=NR-n;i++) print a[i]}')"
for viejo in $SOBRAN; do rm -f "$viejo" "$viejo.sha256"; done

echo "Respaldo listo: $ARCHIVO ($(du -h "$ARCHIVO" | cut -f1))"
echo "Conservados: $(ls -1 "$DESTINO"/cognion-*.dump | wc -l | tr -d ' ') (máximo $CONSERVAR)"
