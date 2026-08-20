import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { listarCuentas } from "@/lib/cuentas-api"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("cuentas-api", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe("listarCuentas", () => {
    it("hace GET /usuarios sin query string cuando no hay filtros", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      await listarCuentas()

      const [url] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toMatch(/\/usuarios$/)
    })

    it("arma el query string solo con los filtros presentes", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      await listarCuentas({ rol: "docente", estado: "bloqueada", busqueda: "ana" })

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.searchParams.get("rol")).toBe("docente")
      expect(parsed.searchParams.get("estado")).toBe("bloqueada")
      expect(parsed.searchParams.get("busqueda")).toBe("ana")
    })

    it("omite del query string los filtros no provistos", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      await listarCuentas({ rol: "estudiante" })

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.searchParams.get("rol")).toBe("estudiante")
      expect(parsed.searchParams.has("estado")).toBe(false)
      expect(parsed.searchParams.has("busqueda")).toBe(false)
    })

    it("devuelve la lista de cuentas tal como la envía el backend", async () => {
      const cuentas = [
        { id: "u1", nombre: "Ana", email: "ana@fiuner.edu.ar", perfil: "docente", bloqueada: false },
        { id: "u2", nombre: "Luis", email: "luis@fiuner.edu.ar", perfil: "estudiante", bloqueada: true },
      ]
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentas))

      const resultado = await listarCuentas()

      expect(resultado).toEqual(cuentas)
    })
  })
})
