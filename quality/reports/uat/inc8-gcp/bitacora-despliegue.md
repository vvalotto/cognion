# Bitácora del despliegue manual en GCP (US-8.6.3)

Plan: `docs/plans/DESPLIEGUE-GCP.md`. Decisiones: `docs/adr/ADR-025-despliegue-de-prueba-en-gcp.md`.
Cuenta: `vvalotto@gmail.com` · Facturación: paga y sin créditos · Dominio: `cognion-fiuner.duckdns.org`.
Aprobación del plan por Víctor: 2026-10-24, con aviso de presupuesto de 5 USD y SSH abierto con clave.

Convención: cada paso lleva el **comando real**, la **hora**, el **resultado**, el **costo observado** y cualquier desvío.

---

## Paso 0 — Prerrequisitos · 2026-10-24 09:42
- `gcloud auth list`: `vvalotto@gmail.com` activa (SDK 550.0.0). Sesión renovada con `gcloud auth login` el 2026-10-23.
- Subdominio de DuckDNS creado por Víctor: `cognion-fiuner.duckdns.org` (cuenta de GitHub). El token se regeneró el 2026-10-23 porque quedó expuesto en una captura; no se usa en el plan.
- Resultado: **OK**. Costo: 0.

## Paso 1 — Configuración de `gcloud` aparte · 2026-10-24 09:42
- Comandos: `gcloud config configurations create cognion --no-activate` y `CLOUDSDK_ACTIVE_CONFIG_NAME=cognion gcloud config set account vvalotto@gmail.com`.
- Resultado: la configuración `cognion` existe con la cuenta, **inactiva**; `default` sigue activa con `app-termostato-2025`. Se usa con la variable de entorno por comando, sin cambiar la configuración activa de la terminal.
- Desvío respecto del plan original: se evitó `config set project` y la activación para no tocar la configuración global.
- Resultado: **OK**. Costo: 0.
