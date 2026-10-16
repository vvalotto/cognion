const API_DESARROLLO = "http://localhost:8000"

/**
 * Resuelve la URL base de la API (`US-8.1.2`): `VITE_API_BASE_URL` si está definida (absoluta o
 * relativa, como `/api` del proxy de desarrollo); si no, el mismo origen del frontend en producción
 * (`US-8.1.6`) o `localhost:8000` en desarrollo. Sin barra final.
 */
export function resolverApiBaseUrl(
  envUrl: string | undefined,
  esProduccion: boolean,
  origen: string,
): string {
  const configurada = envUrl?.trim()
  const base = configurada
    ? new URL(configurada, origen).toString()
    : esProduccion
      ? origen
      : API_DESARROLLO
  return base.replace(/\/+$/, "")
}

/** Convierte la base HTTP en la base WebSocket: `http` → `ws`, `https` → `wss`. */
export function aUrlWebSocket(baseHttp: string): string {
  return baseHttp.replace(/^http/, "ws")
}

export const API_BASE_URL = resolverApiBaseUrl(
  import.meta.env.VITE_API_BASE_URL,
  import.meta.env.PROD,
  window.location.origin,
)
export const WS_BASE_URL = aUrlWebSocket(API_BASE_URL)
