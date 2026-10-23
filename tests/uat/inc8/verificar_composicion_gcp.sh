#!/usr/bin/env bash
# Verifica la composición de deploy/gcp/ YA LEVANTADA (US-8.6.2): la corre CI con dominio `localhost` y, más adelante,
# se puede repetir en la VM. Requiere docker y que `deploy/gcp/cognion.sh iniciar` haya terminado.
# Uso: tests/uat/inc8/verificar_composicion_gcp.sh
set -uo pipefail
cd "$(dirname "$0")/../../../deploy/gcp"

DOMINIO="$(grep -E '^COGNION_DOMINIO=' .env | cut -d= -f2-)"
ok() { echo "OK   $1"; }
fallo() { echo "FAIL $1"; FALLOS=$((FALLOS + 1)); }
FALLOS=0
contenedor() { docker compose ps -q "$1"; }

# 1. La aplicación responde por HTTPS a través del proxy
RESPUESTA="$(curl -fsS -k --max-time 10 "https://${DOMINIO}/api/health" 2>/dev/null || true)"
[[ "$RESPUESTA" == *'"ok"'* ]] && ok "1. /api/health responde por HTTPS" || fallo "1. /api/health ($RESPUESTA)"

# 2. Las migraciones están aplicadas
VERSIONES="$(docker compose exec -T db psql -U cognion -d cognion -Atc 'SELECT count(*) FROM alembic_version' 2>/dev/null || true)"
[ "$VERSIONES" = "1" ] && ok "2. migraciones aplicadas (alembic_version)" || fallo "2. alembic_version = '$VERSIONES'"

# 3. PostgreSQL y la aplicación no publican puertos en la VM
for srv in db app; do
  PUBLICADOS="$(docker inspect -f '{{json .HostConfig.PortBindings}}' "$(contenedor $srv)" 2>/dev/null)"
  [ "$PUBLICADOS" = "{}" ] || [ "$PUBLICADOS" = "null" ] && ok "3. $srv sin puertos publicados" || fallo "3. $srv publica $PUBLICADOS"
done
(exec 3<>/dev/tcp/127.0.0.1/5432) 2>/dev/null && fallo "3. el puerto 5432 responde desde fuera del contenedor" || ok "3. el puerto 5432 no responde desde fuera"

# 4. Límites de memoria y reinicio automático aplicados
for srv in db app caddy; do
  MEM="$(docker inspect -f '{{.HostConfig.Memory}}' "$(contenedor $srv)")"
  POL="$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$(contenedor $srv)")"
  [ "$MEM" -gt 0 ] 2>/dev/null && [ "$POL" = "unless-stopped" ] \
    && ok "4. $srv: límite $((MEM / 1048576)) MB y reinicio $POL" || fallo "4. $srv: memoria=$MEM reinicio=$POL"
done

# 5. Un contenedor caído se levanta solo
docker kill "$(contenedor app)" >/dev/null
RECUPERADA=0
for _ in $(seq 1 40); do
  if curl -fsS -k --max-time 5 "https://${DOMINIO}/api/health" >/dev/null 2>&1; then RECUPERADA=1; break; fi
  sleep 3
done
[ "$RECUPERADA" = "1" ] && ok "5. la aplicación volvió sola tras caer (reinicio automático)" || fallo "5. la aplicación no volvió"

# 6. Los secretos no aparecen en los logs
SECRETO="$(grep -E '^SECRET_KEY=' .env | cut -d= -f2-)"
PASSWORD_DB="$(grep -E '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)"
LOGS="$(docker compose logs --no-color 2>&1)"
if [ -n "$SECRETO" ] && [ -n "$PASSWORD_DB" ] && ! grep -qF -e "$SECRETO" -e "$PASSWORD_DB" <<<"$LOGS"; then
  ok "6. ningún secreto aparece en los logs"
else
  fallo "6. un secreto aparece en los logs"
fi

# 7. El primer Administrador se crea con el comando existente y puede iniciar sesión
ADMIN_EMAIL="verificacion@ejemplo.edu.ar"; ADMIN_PASSWORD="Verif#Prueba-2026"
if ADMIN_NOMBRE="Admin Verificacion" ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_PASSWORD="$ADMIN_PASSWORD" ./cognion.sh administrador >/dev/null 2>&1; then
  CODIGO="$(curl -s -k -o /dev/null -w '%{http_code}' -X POST "https://${DOMINIO}/api/identidad/login" \
    -H 'Content-Type: application/json' -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")"
  [ "$CODIGO" = "200" ] && ok "7. bootstrap del Administrador y login (HTTP 200)" || fallo "7. login del Administrador ($CODIGO)"
else
  fallo "7. cognion.sh administrador"
fi

# 8. Informativo: memoria en reposo por contenedor
echo "---- memoria en reposo (informativo) ----"
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}'

echo
if [ "$FALLOS" -eq 0 ]; then echo "Composición verificada."; else echo "$FALLOS verificación(es) fallaron."; exit 1; fi
