#!/usr/bin/env bash
# Verifica la composición de deploy/servidor/ YA LEVANTADA, contra Docker real (DO-03, Issue #665; relacionado con #624).
# La corre el CI (imagen-smoke.yml) con dominio `localhost`. Parte de la verificación de deploy/gcp/ y suma lo propio del
# paquete que se entrega: respaldo, ensayo de restauración, despliegue, rollback, estado y confianza en el proxy.
# Requiere docker y que `deploy/servidor/cognion.sh iniciar` haya terminado.
# Uso: tests/uat/inc12/verificar_servidor.sh
set -uo pipefail
cd "$(dirname "$0")/../../../deploy/servidor"

DOMINIO="$(grep -E '^COGNION_DOMINIO=' .env | cut -d= -f2-)"
IMAGEN="$(grep -E '^COGNION_IMAGE=' .env | cut -d= -f2-)"
ok() { echo "OK   $1"; }
fallo() { echo "FAIL $1"; FALLOS=$((FALLOS + 1)); }
FALLOS=0
contenedor() { docker compose ps -q "$1"; }
esperar_aplicacion() {
  for _ in $(seq 1 40); do
    curl -fsS -k --max-time 5 "https://${DOMINIO}/api/health" >/dev/null 2>&1 && return 0
    sleep 3
  done
  return 1
}

# 1. La aplicación responde por HTTPS a través del proxy
RESPUESTA=""; ERROR_CURL=""
for _ in $(seq 1 20); do
  ERROR_CURL="$(curl -fsS -k --max-time 10 -o /tmp/salud.json "https://${DOMINIO}/api/health" 2>&1)" && { RESPUESTA="$(cat /tmp/salud.json)"; break; }
  sleep 2
done
[[ "$RESPUESTA" == *'"ok"'* ]] && ok "1. /api/health responde por HTTPS" || fallo "1. /api/health (${ERROR_CURL})"

# 1b. Con la base lista (es lo que mira el healthcheck del compose desde DO-04)
CODIGO="$(curl -s -k -o /dev/null -w '%{http_code}' --max-time 10 "https://${DOMINIO}/api/health/ready")"
[ "$CODIGO" = "200" ] && ok "1b. /api/health/ready responde 200" || fallo "1b. /api/health/ready ($CODIGO)"

# 2. Las migraciones están aplicadas
VERSIONES="$(docker compose exec -T db psql -U cognion -d cognion -Atc 'SELECT count(*) FROM alembic_version' 2>/dev/null || true)"
[ "$VERSIONES" = "1" ] && ok "2. migraciones aplicadas (alembic_version)" || fallo "2. alembic_version = '$VERSIONES'"

# 3. PostgreSQL y la aplicación no publican puertos
for srv in db app; do
  PUBLICADOS="$(docker inspect -f '{{json .HostConfig.PortBindings}}' "$(contenedor $srv)" 2>/dev/null)"
  [ "$PUBLICADOS" = "{}" ] || [ "$PUBLICADOS" = "null" ] && ok "3. $srv sin puertos publicados" || fallo "3. $srv publica $PUBLICADOS"
done
(exec 3<>/dev/tcp/127.0.0.1/5432) 2>/dev/null && fallo "3. el puerto 5432 responde desde fuera del contenedor" || ok "3. el puerto 5432 no responde desde fuera"

# 4. Límites de memoria y reinicio automático
for srv in db app caddy; do
  MEM="$(docker inspect -f '{{.HostConfig.Memory}}' "$(contenedor $srv)")"
  POL="$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$(contenedor $srv)")"
  [ "$MEM" -gt 0 ] 2>/dev/null && [ "$POL" = "unless-stopped" ] \
    && ok "4. $srv: límite $((MEM / 1048576)) MB y reinicio $POL" || fallo "4. $srv: memoria=$MEM reinicio=$POL"
done

# 5. La aplicación no corre como root (DO-01) y confía solo en el proxy de su red (DO-01)
USUARIO="$(docker compose exec -T app id -u 2>/dev/null | tr -d '[:space:]')"
[ -n "$USUARIO" ] && [ "$USUARIO" != "0" ] && ok "5. la aplicación corre con UID $USUARIO (no root)" || fallo "5. la aplicación corre como UID '$USUARIO'"
# Una ruta sin la barra final responde con una redirección: su Location conserva https solo si la aplicación confía en el proxy.
UBICACION="$(curl -s -k -o /dev/null -w '%{redirect_url}' --max-time 10 "https://${DOMINIO}/api/health/")"
[[ "$UBICACION" == https://* ]] && ok "5b. la redirección conserva https (confía en el proxy): $UBICACION" || fallo "5b. la redirección no conserva https: '$UBICACION'"

# 6. Una caída real de la aplicación se recupera sola (se mata el proceso desde el host: `docker kill` no aplica la política de reinicio)
PID_APP="$(docker inspect -f '{{.State.Pid}}' "$(contenedor app)")"
sudo kill -9 "$PID_APP"
if esperar_aplicacion; then
  REINICIOS="$(docker inspect -f '{{.RestartCount}}' "$(contenedor app)")"
  [ "$REINICIOS" -ge 1 ] 2>/dev/null && ok "6. la aplicación volvió sola tras caer (reinicios: $REINICIOS)" || fallo "6. volvió pero RestartCount=$REINICIOS"
else
  fallo "6. la aplicación no volvió tras caer"
fi

# 7. Los secretos no aparecen en los logs
SECRETO="$(grep -E '^SECRET_KEY=' .env | cut -d= -f2-)"
PASSWORD_DB="$(grep -E '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)"
LOGS="$(docker compose logs --no-color 2>&1)"
if [ -n "$SECRETO" ] && [ -n "$PASSWORD_DB" ] && ! grep -qF -e "$SECRETO" -e "$PASSWORD_DB" <<<"$LOGS"; then
  ok "7. ningún secreto aparece en los logs"
else
  fallo "7. un secreto aparece en los logs"
fi

# 8. Respaldo: pg_dump verificado con su sha256, y el estado lo informa (DO-02)
if ./respaldar.sh >/tmp/respaldo.txt 2>&1; then
  DUMP="$(ls -1 respaldos/cognion-*.dump 2>/dev/null | sort | tail -n 1)"
  if [ -n "$DUMP" ] && [ -s "$DUMP" ] && [ -f "$DUMP.sha256" ]; then ok "8. respaldo creado con su sha256: $(basename "$DUMP")"; else fallo "8. el respaldo no dejó el archivo o su sha256"; fi
else
  cat /tmp/respaldo.txt; fallo "8. ./respaldar.sh falló"
  DUMP=""
fi
ESTADO="$(./cognion.sh estado 2>&1 || true)"
[[ "$ESTADO" == *"Último respaldo:"* ]] && ok "8b. estado informa el último respaldo" || { echo "$ESTADO"; fallo "8b. estado no informa el último respaldo"; }

# 9. Ensayo de restauración: no toca la base real
if [ -n "$DUMP" ]; then
  ./restaurar.sh "$DUMP" >/tmp/restauracion.txt 2>&1 && ok "9. ensayo de restauración" || { cat /tmp/restauracion.txt; fallo "9. el ensayo de restauración falló"; }
else
  fallo "9. no hay respaldo para ensayar la restauración"
fi

# 10. El respaldo diario queda programado (solo si el runner tiene cron)
if command -v crontab >/dev/null 2>&1; then
  ./cognion.sh programar-respaldo >/dev/null 2>&1
  crontab -l 2>/dev/null | grep -q "cognion-respaldo" && ok "10. respaldo programado en el cron" || fallo "10. el cron no quedó con el respaldo"
else
  echo "SKIP 10. este runner no tiene crontab"
fi

# 11. Despliegue completo con la imagen actual: respaldo previo, migración, reemplazo y salud; y después el rollback
if ./cognion.sh desplegar "$IMAGEN" >/tmp/desplegar.txt 2>&1; then
  ok "11. desplegar $IMAGEN"
  esperar_aplicacion && ok "11b. la aplicación responde después de desplegar" || fallo "11b. la aplicación no responde después de desplegar"
else
  cat /tmp/desplegar.txt; fallo "11. ./cognion.sh desplegar falló"
fi
if ./cognion.sh rollback >/tmp/rollback.txt 2>&1; then ok "12. rollback"; else cat /tmp/rollback.txt; fallo "12. ./cognion.sh rollback falló"; fi

# 13. El primer Administrador se crea con el comando existente y puede iniciar sesión
ADMIN_EMAIL="verificacion@ejemplo.edu.ar"; ADMIN_PASSWORD="Verif#Prueba-2026"
if ADMIN_NOMBRE="Admin Verificacion" ADMIN_EMAIL="$ADMIN_EMAIL" ADMIN_PASSWORD="$ADMIN_PASSWORD" ./cognion.sh administrador >/dev/null 2>&1; then
  CODIGO="$(curl -s -k -o /dev/null -w '%{http_code}' -X POST "https://${DOMINIO}/api/identidad/login" \
    -H 'Content-Type: application/json' -d "{\"email\":\"${ADMIN_EMAIL}\",\"password\":\"${ADMIN_PASSWORD}\"}")"
  [ "$CODIGO" = "200" ] && ok "13. bootstrap del Administrador y login (HTTP 200)" || fallo "13. login del Administrador ($CODIGO)"
else
  fallo "13. cognion.sh administrador"
fi

echo "---- memoria en reposo (informativo) ----"
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}'

echo
if [ "$FALLOS" -eq 0 ]; then echo "Composición del servidor verificada."; else echo "$FALLOS verificación(es) fallaron."; exit 1; fi
