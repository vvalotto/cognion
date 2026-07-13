# ADR-NNN — <Título de la decisión>

**Estado:** Propuesto / Aceptado / Superseded
**Fecha:** AAAA-MM-DD

---

## Contexto

<Qué situación o tensión requirió tomar esta decisión. En 2–4 oraciones — qué driver
arquitectónico o qué restricción la origina.>

## Opciones Consideradas

<Alternativas evaluadas, con su trade-off principal cada una. Si solo hubo una opción
razonable, decirlo explícitamente en vez de omitir la sección.>

## Decisión

<Qué se decidió, en una oración directa.>

## Justificación

<Por qué esta opción y no las alternativas descartadas.>

## Impacto en Configuración

> **Obligatoria si el ADR decide stack, librería, driver o herramienta.** Omitir solo si la
> decisión es puramente de dominio y no tiene ningún artefacto de configuración asociado.

<Listar explícitamente qué archivos del proyecto deben actualizarse como consecuencia de
esta decisión — ej: `pyproject.toml`, `docker-compose.yml`, `.env.example`,
`[tool.designreviewer]` en `pyproject.toml`, `CLAUDE.md`. Un ADR de stack sin esta sección
está incompleto: la decisión queda documentada pero no necesariamente reflejada en el
código de configuración real hasta que alguien lo detecta a mitad de implementación.>

## Consecuencias

- ✅ <Beneficio>
- ⚠️ <Trade-off o limitación que se acepta>
