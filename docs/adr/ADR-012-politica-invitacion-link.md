# ADR-012 — Política de invitación por link: expiración y canal de entrega (RF-01)

**Estado:** Aceptado
**Fecha:** 2026-07-16

---

## Contexto

`RF_v1.md` (RF-01) dejó explícitamente sin definir el comportamiento ante un link de
invitación vencido o inválido, y no especifica si el link se entrega manualmente o por email.
Esta decisión se tomó antes de arrancar la Iteración 0 — Modelado del Incremento 1 (BC
Identidad), porque condiciona el event storming de la entidad Invitación.

## Opciones Consideradas

- **Entrega manual del link** (el docente copia/pega y lo distribuye por el medio que
  prefiera) — descartada: el docente pidió envío automático por email para no depender de
  otro canal ad hoc.
- **Entrega por email vía puerto compartido en `shared/entities/`**, reutilizable luego por
  BC Notificaciones (Incremento 5, ADR-006) — descartada por ahora: adelanta una abstracción
  para un caso de uso (el envío de Notificaciones) que todavía no está modelado, con riesgo de
  diseñar el puerto equivocado antes de tiempo.
- **Entrega por email con adaptador SMTP propio de BC Identidad** — elegida.
- **Link sin expiración** (válido hasta revocación manual del docente) — descartada: el propio
  RF-01 anticipa un caso límite de "link vencido", que no aplicaría sin expiración por tiempo.
- **Link con expiración por tiempo** — elegida.
- **Reenvío automático ante link vencido** — descartada: agrega un flujo adicional (asociar el
  link a un email conocido para poder reenviarlo) no pedido para v1.

## Decisión

El link de invitación expira a los 7 días de generado. Ante un link vencido o inválido, el
sistema rechaza el registro y muestra un mensaje explicando el motivo — sin recuperación
automática; el estudiante debe pedirle al docente un nuevo link. El link se entrega por email,
enviado directamente por BC Identidad mediante su propio adaptador SMTP, independiente del
Servicio Email que usará BC Notificaciones en el Incremento 5 (ADR-006).

## Justificación

7 días cubre el ciclo típico de inscripción a una comisión sin quedar indefinidamente válido.
Un adaptador SMTP propio de Identidad evita bloquear el Incremento 1 con una abstracción
cross-BC que Notificaciones todavía no necesita modelar — se acepta la duplicación de
infraestructura de envío de email entre ambos BCs como trade-off consciente, a revisar cuando
se modele Notificaciones.

## Impacto en Configuración

- `.env.example` — variables SMTP propias de Identidad (host, puerto, credenciales, remitente).
- `src/identidad/entities/` — agregado Invitación con campo de expiración (7 días desde
  generación).
- `src/identidad/frameworks/` — adaptador de envío de email (SMTP) propio del BC.
- `src/identidad/interface_adapters/` — endpoint de registro valida expiración/validez del
  link antes de crear la cuenta.

## Consecuencias

- ✅ No bloquea el Incremento 1 con una integración cross-BC prematura.
- ✅ Resuelve el caso límite que `RF_v1.md` (RF-01) dejaba explícitamente abierto.
- ⚠️ Cuando se modele BC Notificaciones (Incremento 5, ADR-006) habrá dos adaptadores SMTP
  independientes en el sistema — evaluar en ese momento si conviene unificarlos.
