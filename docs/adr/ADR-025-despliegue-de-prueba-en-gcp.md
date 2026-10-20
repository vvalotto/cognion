# ADR-025 — Despliegue de prueba en GCP: VM gratuita con la aplicación y PostgreSQL juntos

**Estado:** Aceptado (2026-10-20) — las cuatro decisiones de `US-8.6.1` (Issue #545) están tomadas; los criterios de go/no-go siguen pendientes de confirmación (ver abajo)
**Fecha:** 2026-10-20
**Origen:** `US-8.6.1`, Iteración 6 del Incremento 8. Relacionado con `ADR-021` y `ADR-024` (Fly.io, en revisión), `ADR-022` (backup) y `ADR-023` (SMTP).

---

## Contexto

Víctor eligió el 2026-10-19 desplegar una **prueba de uso** en una VM `e2-micro` de la capa gratuita de GCP, con su cuenta
personal, con la aplicación y PostgreSQL juntos (opción A de `docs/plans/inc8/inc8-candidatas.md` §Iteración 6). Cuatro
cuestiones condicionan el resto de la iteración y se resuelven una por una, con Víctor presente.

## Decisión 1 — Dominio y HTTPS: subdominio gratuito de DuckDNS (2026-10-20)

**Opciones consideradas:**
- **`sslip.io`** (el nombre contiene la IP): descartada. Los certificados de Let's Encrypt comparten el límite entre todos
  los usuarios de ese dominio y hay reportes de bloqueos.
- **Túnel de Cloudflare**: descartada. Sin dominio propio la URL cambia en cada reinicio; con URL estable exige un dominio, y
  suma otro proceso en 1 GB de RAM. No se verificó el paso de WebSockets.
- **Dominio propio**: viable y la más estable, pero Víctor no tiene uno ni quiere pagarlo para una prueba.
- **Subdominio gratuito de DuckDNS**: elegida.

**Decisión:** la prueba se publica bajo un subdominio de DuckDNS, con certificado automático de Let's Encrypt gestionado por
el proxy HTTPS de la VM.

**Justificación:** costo cero, nombre estable y fácil de dictar a los alumnos, y la VM tiene IP pública estática, así que la
validación por HTTP funciona con los puertos 80/443 abiertos. El riesgo de depender de un servicio gratuito de terceros es
aceptable en una prueba acotada.

**Notas y límites:**
- Sin HTTPS no se usa con alumnos reales: contraseñas y tokens viajarían sin cifrar y el botón "Copiar link" de invitación
  (`navigator.clipboard`, solo en contexto seguro) probablemente fallaría. Con `http://<IP>` se puede probar para uso propio.
- No se verificó si `duckdns.org` comparte el límite de certificados que sí afectó a `sslip.io`; con un solo certificado es
  poco probable que moleste. Si se migra a un dominio propio, el cambio es de configuración, no de código.
- La URL de la prueba alimenta `FRONTEND_URL` y `CORS_ALLOWED_ORIGINS` (mismo origen, `US-8.1.6`).

## Decisión 2 — Modo de email y `ENTORNO`: emails en el log, `ENTORNO=local` (2026-10-20)

**Opciones consideradas:**
- **Emails reales con SMTP y `ENTORNO=staging`**: descartada para esta primera prueba. Exige una cuenta SMTP y verificar que
  la VM pueda enviar: según el conocimiento general (no verificado en esta sesión) GCP bloquea por defecto el puerto 25
  saliente, el código solo implementa STARTTLS en el puerto 587 con usuario y clave (no SSL directo en el 465), y no se sabe
  si el servidor institucional de `ADR-023` acepta conexiones desde una IP de Google.
- **Emails en el log con `EMAIL_MODO=consola` y `ENTORNO=local`**: elegida.

**Decisión:** la VM corre con `ENTORNO=local` y `EMAIL_MODO=consola`. Ningún email sale; su contenido (con los links de token)
queda en el log INFO de la aplicación.

**Justificación:** no depende de una cuenta SMTP ni del bloqueo de puertos, y la configuración ya está probada en la máquina
de Víctor (`US-8.5.1`/`8.5.2`). La primera prueba se hace con cuentas de prueba o un grupo chico.

**Consecuencias asumidas:**
- Los alumnos **no pueden recuperar su contraseña por su cuenta**: Víctor lee el link en el log por SSH y se lo pasa.
- **No llegan los avisos de actividad** nueva o cerrada (RF-14); solo quedan en el log.
- Las **invitaciones** siguen funcionando: la pantalla muestra el link y, con HTTPS (decisión 1), el botón "Copiar link" anda.
- Los **tokens quedan en el log**: solo los lee quien entra a la VM. Por eso esta configuración no se usa con una cuenta
  abierta a terceros ni se comparte el log.
- `ENTORNO=local` valida solo el secreto (≥32 caracteres, distinto del ejemplo), no las URLs ni CORS. La base de datos puede
  estar en `localhost`, lo que deja abierta la decisión 3 (PostgreSQL nativo o en contenedor).
- Pasar a emails reales (`ENTORNO=staging` + SMTP) queda como mejora para una segunda prueba; es cambio de configuración, no
  de código, salvo que el servidor institucional exija SSL directo.

## Decisión 3 — Contenedores o procesos nativos en 1 GB de RAM: contenedores (2026-10-20)

**Opciones consideradas:**
- **Procesos nativos** (PostgreSQL de apt, `uv sync`, Caddy como servicio): descartada. Ahorra memoria, pero pierde la paridad
  con la imagen que ya construye CI, obliga a compilar el frontend afuera y copiarlo, y convierte el rollback en un proceso a
  medida. Cambiaría el diseño de `US-8.6.2` y `US-8.6.4`.
- **Contenedores** (imagen de CI + PostgreSQL + Caddy): elegida.

**Decisión:** la aplicación, PostgreSQL y el proxy HTTPS corren como contenedores en la VM, con la imagen que publica CI.

**Justificación:** todo el plan de la iteración (`US-8.6.2` a `8.6.6`) está pensado alrededor de la imagen; el despliegue y el
rollback son por versión de imagen y las migraciones corren dentro del contenedor.

**Consecuencias asumidas:**
- Docker suma un consumo fijo de memoria. Estimación de orden de magnitud, **no medida**: sistema ~200 MB, PostgreSQL ~150 MB,
  aplicación ~150 MB, Caddy ~30 MB y Docker ~100–150 MB, o sea ~680 MB de 1 GB (~66 %). `US-8.6.7` lo mide contra el
  criterio de menos del 80 %. **Plan de respaldo:** si no entra, pasar a procesos nativos en un ADR nuevo.
- **Riesgo conocido:** la imagen nunca se ejecutó en un entorno real (solo se construye en CI; su verificación, `US-8.5.5`,
  fue desestimada). El `Dockerfile` arranca con `uv run uvicorn …` y `uv run` puede intentar sincronizar dependencias,
  incluidas las de desarrollo, al arrancar (hipótesis sin verificar). Si ocurre, el contenedor tardaría o fallaría sin red y
  se corrige cambiando el comando de arranque.
- **Condición:** `US-8.6.2` incluye, antes de aprovisionar la VM, una prueba de arranque de la imagen contra una base
  descartable. Docker no está instalado en la máquina de Víctor; la prueba corre en CI o en la propia VM.
- El registro de imágenes (`US-8.6.4`) debe respetar los límites gratuitos (Artifact Registry: 0,5 GB).

## Decisión 4 — Alcance de datos y cuenta de la prueba: cuentas de prueba, cuenta personal (2026-10-20)

**Opciones consideradas (alcance):**
- **Alumnos reales voluntarios** en la cuenta personal de Víctor: descartada para esta primera prueba. Pondría nombres y emails
  reales en una cuenta personal de Gmail sin acuerdo con la facultad; es una decisión institucional, no técnica
  (`ADR-021` ya pedía revisar la residencia del dato).
- **Esperar** a una cuenta institucional o a la respuesta de la Universidad: descartada, frena la prueba sin fecha.
- **Prueba cerrada con cuentas de prueba** (Víctor, colegas o alumnos con nombres y emails ficticios): elegida.

**Decisión:** la primera prueba usa **solo cuentas de prueba, con datos ficticios**, en la **cuenta personal** de Google Cloud
de Víctor (`vvalotto@gmail.com`).

**Justificación:** mide la carga técnica sin tocar datos personales y sin depender de la facultad. Mantiene la regla vigente
desde el 2026-08-24 de no usar datos reales de estudiantes hasta una decisión institucional.

**Consecuencias asumidas:**
- Como no hay datos personales, no hace falta aviso de privacidad ni consentimiento. Si más adelante se quieren alumnos
  reales, cambia el alcance y se decide con la institución, no el código.
- Mide la carga técnica (logins, sesión en vivo, memoria, latencia), no cómo se comportan los alumnos reales.
- La cuenta puede migrarse a una institucional más adelante: la imagen y los scripts son los mismos, solo cambia el proyecto.
- **Vencimiento:** con los 300 USD de crédito por 90 días no se paga nada. Si no se pasa a cuenta paga antes del día 90, los
  recursos se apagan y a los 30 días de gracia se borran. **Recordatorio al día 75** (2027-01-03 si se aprovisiona el
  2026-10-20): si la prueba salió bien se pasa a cuenta paga, y se sigue en la capa gratuita mientras se use solo una
  `e2-micro`; si no, se hace un respaldo y se deja apagar.
- **Costos accidentales:** las alertas de presupuesto avisan pero no cortan el gasto. Una IP estática reservada sin asignar
  cuesta; el script de aprovisionamiento (`US-8.6.3`) debe dejarla siempre asignada a la VM.
- **Tarifa de salida de red:** sigue sin confirmarse para este caso. El único dato hallado es 0,12 USD/GiB para el primer TiB
  de Norteamérica a Europa (anuncio de VPC, 2024); se toma como orden de magnitud. Con 1 GiB mensual gratuito y una prueba
  chica no debería ser relevante, pero se verifica en la página oficial de tarifas antes de que haya tráfico real.

## Criterios de go/no-go de `US-8.6.7` (propuestos, pendientes de confirmación de Víctor)

| Medición | Criterio |
|---|---|
| 60 logins simultáneos en un minuto | 0 errores y p95 < 3 s |
| Sesión en vivo con 60 participantes | p95 de `CerrarPreguntaActual` < 100 ms en el servidor (RNF) |
| Memoria durante ambas cargas | < 80 % de 1 GB sostenida; sin cierres por falta de memoria |
| Reinicio de la VM | el sistema vuelve solo en menos de 3 minutos |
| Latencia desde Argentina | se mide y se registra (informativo) |
| Respaldo y restauración | restauración completa exitosa |

Si algún criterio falla se registra y se decide entre una VM paga más grande o la opción B (Cloud Run + Cloud SQL) en un ADR
nuevo; la imagen es la misma.

## Impacto en Configuración

- `deploy/gcp/` (nuevo, `US-8.6.2`): composición de servicios con aplicación, PostgreSQL y proxy HTTPS (decisión 3); variables
  `ENTORNO=local`, `EMAIL_MODO=consola`, `FRONTEND_URL` y `CORS_ALLOWED_ORIGINS` con la URL de DuckDNS (decisiones 1 y 2).
- `.env.example`: plantilla para la VM, sin valores reales.
- `.github/workflows/cd.yml` (`US-8.6.4`): publicar la imagen al crear una etiqueta `v*.*.*`; los pasos de Fly.io quedan
  comentados.
- `Dockerfile` (`US-8.6.2`): revisar el comando de arranque (`uv run`) tras la prueba de arranque de la imagen.
- `docs/adr/ADR-021` y `ADR-024`: anotados con su relación a este ADR (siguen en revisión).
- `CLAUDE.md` e `inc8-candidatas.md`: reflejar las decisiones al cerrar la iteración.

## Consecuencias

- ✅ Costo cero, sin depender de la facultad ni de una cuenta SMTP, y con una URL estable con HTTPS.
- ✅ La imagen y los scripts siguen siendo portables a otra nube o a una cuenta institucional.
- ⚠️ Sin recuperación de contraseña por cuenta propia ni avisos por email: Víctor hace de mesa de ayuda.
- ⚠️ Dependencia de un servicio gratuito de terceros (DuckDNS) y de una cuenta personal sujeta al vencimiento de los 90 días.
- ⚠️ 1 GB de RAM con contenedores es un margen a medir, no a suponer (`US-8.6.7`).
