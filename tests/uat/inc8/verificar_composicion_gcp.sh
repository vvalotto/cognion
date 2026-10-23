#!/usr/bin/env bash
# Verifica la composición de deploy/gcp/ YA LEVANTADA (US-8.6.2): la corre CI con dominio `localhost` y, más adelante,
# se puede repetir en la VM (ahí el reinicio se prueba reiniciando la máquina). Requiere docker y que `deploy/gcp/cognion.sh iniciar` haya terminado.
# Uso: tests/uat/inc8/verificar_composicion_gcp.sh
set -uo pipefail
cd "$(dirname "$0")/../../../deploy/gcp"

DOMINIO="$(grep -E '^COGNION_DOMINIO=' .env | cut -d= -f2-)"
ok() { echo "OK   $1"; }
fallo() { echo "FAIL $1"; FALLOS=$((FALLOS + 1)); }
FALLOS=0
contenedor() { docker compose ps -q "$1"; }

# 1. La aplicación responde por HTTPS a través del proxy (el proxy recién arrancó: se admite una espera corta)
RESPUESTA=""; ERROR_CURL=""
for _ in $(seq 1 20); do
  ERROR_CURL="$(curl -fsS -k --max-time 10 -o /tmp/salud.json "https://${DOMINIO}/api/health" 2>&1)" && { RESPUESTA="$(cat /tmp/salud.json)"; break; }
  sleep 2
done
[[ "$RESPUESTA" == *'"ok"'* ]] && ok "1. /api/health responde por HTTPS" || fallo "1. /api/health (${ERROR_CURL})"

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

# Espera a que la aplicación vuelva a responder por HTTPS (hasta ~2 min)
esperar_aplicacion() {
  for _ in $(seq 1 40); do
    curl -fsS -k --max-time 5 "https://${DOMINIO}/api/health" >/dev/null 2>&1 && return 0
    sleep 3
  done
  return 1
}

# 5a. Una caída real de la aplicación se recupera sola. `docker kill` NO sirve para probarlo: Docker lo trata como una
# detención manual y no aplica la política de reinicio. Tampoco alcanza con mandarle una señal al PID 1 desde dentro del
# contenedor (el núcleo la ignora). Se mata el proceso principal desde el host, como lo haría un fallo real.
PID_APP="$(docker inspect -f '{{.State.Pid}}' "$(contenedor app)")"
sudo kill -9 "$PID_APP"
if esperar_aplicacion; then
  REINICIOS="$(docker inspect -f '{{.RestartCount}}' "$(contenedor app)")"
  [ "$REINICIOS" -ge 1 ] 2>/dev/null && ok "5a. la aplicación volvió sola tras caer (reinicios: $REINICIOS)" || fallo "5a. volvió pero RestartCount=$REINICIOS"
else
  fallo "5a. la aplicación no volvió tras caer"
fi

# 5b. Equivale a reiniciar la máquina: se reinicia el demonio de Docker y los servicios deben volver solos.
# En CI se activa con VERIFICAR_REINICIO_DOCKER=1 (el runner permite sudo); en la VM se prueba reiniciándola de verdad.
if [ "${VERIFICAR_REINICIO_DOCKER:-0}" = "1" ]; then
  sudo systemctl restart docker
  sleep 5
  if esperar_aplicacion; then ok "5b. los servicios volvieron solos tras reiniciar Docker"; else fallo "5b. los servicios no volvieron tras reiniciar Docker"; fi
else
  echo "SKIP 5b. reinicio de Docker (definir VERIFICAR_REINICIO_DOCKER=1; en la VM se prueba reiniciándola)"
fi

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
