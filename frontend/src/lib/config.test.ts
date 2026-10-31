import { describe, expect, it } from "vitest"

import { aUrlWebSocket, resolverApiBaseUrl } from "@/lib/config"

describe("resolverApiBaseUrl", () => {
  it("usa la variable de entorno y quita la barra final", () => {
    expect(resolverApiBaseUrl("https://api.x.fly.dev/", true, "https://app.fly.dev")).toBe(
      "https://api.x.fly.dev",
    )
  })

  it("en producción sin variable usa el mismo origen", () => {
    expect(resolverApiBaseUrl(undefined, true, "https://app.fly.dev")).toBe("https://app.fly.dev")
  })

  it("una variable vacía o con espacios se trata como no definida", () => {
    expect(resolverApiBaseUrl("  ", true, "https://app.fly.dev")).toBe("https://app.fly.dev")
  })

  it("en desarrollo sin variable usa localhost:8000", () => {
    expect(resolverApiBaseUrl(undefined, false, "http://localhost:5173")).toBe(
      "http://localhost:8000",
    )
  })

  it("resuelve una base relativa contra el origen", () => {
    expect(resolverApiBaseUrl("/api", false, "http://10.0.0.5:5173")).toBe(
      "http://10.0.0.5:5173/api",
    )
  })
})

describe("aUrlWebSocket", () => {
  it("http → ws", () => {
    expect(aUrlWebSocket("http://localhost:8000")).toBe("ws://localhost:8000")
  })

  it("https → wss", () => {
    expect(aUrlWebSocket("https://api.x.fly.dev")).toBe("wss://api.x.fly.dev")
  })

  it("conserva el prefijo de ruta", () => {
    expect(aUrlWebSocket("http://10.0.0.5:5173/api")).toBe("ws://10.0.0.5:5173/api")
  })
})
