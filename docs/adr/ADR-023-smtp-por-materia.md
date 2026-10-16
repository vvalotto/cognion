# ADR-023 — Cuenta SMTP de envío por materia

**Estado:** Aceptado
**Fecha:** 2026-10-16
**Origen:** `US-8.0.3` (Issue #512), Incremento 8. Cierra el ítem abierto "Cuenta de envío SMTP
real para Notificaciones" (RF-14).

---

## Contexto

`SmtpCanalEnvio` usa hoy una sola cuenta global (`SMTP_HOST/PORT/USER/PASSWORD/FROM`), apuntando a
`localhost:25`. Existen cuentas institucionales por materia (ej.
`gestiondeproyectos@ingenieria.uner.edu.ar`). Enviar "de parte de" un Docente sin ser su cuenta
real es spoofing y lo rechazan SPF/DKIM.

## Decisión

El remitente se resuelve **por materia**: cada materia con cuenta propia tiene sus credenciales
SMTP en variables de entorno (una por materia), nunca en el dominio ni en la base. Las materias sin
cuenta configurada caen en una **cuenta global por defecto**. Los emails que no pertenecen a una
materia (recuperación de contraseña) usan la cuenta global.

## Consecuencias

- ✅ El email sale de una identidad real y legítima de cada materia.
- ⚠️ Requiere código nuevo: resolver la cuenta según la materia de la actividad. Se agrega como
  `US-8.1.7` en la Iteración 1.
- ⚠️ A escala actual (2-3 materias) alcanza con variables de entorno; si crece, migrar a un
  almacén de secretos.
- ⚠️ Las credenciales reales de cada cuenta institucional las debe proveer Víctor; quedan fuera
  del repo.
