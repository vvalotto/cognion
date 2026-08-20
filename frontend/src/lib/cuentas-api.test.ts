import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { listarCuentas, obtenerCuenta, resetearPassword } from "@/lib/cuentas-api"

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

  describe("obtenerCuenta", () => {
    it("hace GET /usuarios/{id} y mapea snake_case a camelCase", async () => {
      const cuentaApi = {
        id: "u1",
        nombre: "Ana",
        email: "ana@fiuner.edu.ar",
        perfil: "docente",
        bloqueada: false,
        creado_en: "2026-08-01T10:00:00Z",
        comision_id: null,
      }
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))

      const resultado = await obtenerCuenta("u1")

      const [url] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toMatch(/\/usuarios\/u1$/)
      expect(resultado).toEqual({
        id: "u1",
        nombre: "Ana",
        email: "ana@fiuner.edu.ar",
        perfil: "docente",
        bloqueada: false,
        creadoEn: "2026-08-01T10:00:00Z",
        comisionId: null,
      })
    })

    it("mapea comision_id cuando la cuenta es de un Estudiante", async () => {
      const cuentaApi = {
        id: "u2",
        nombre: "Luis",
        email: "luis@fiuner.edu.ar",
        perfil: "estudiante",
        bloqueada: true,
        creado_en: "2026-08-01T10:00:00Z",
        comision_id: "c1",
      }
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))

      const resultado = await obtenerCuenta("u2")

      expect(resultado.comisionId).toBe("c1")
    })
  })

  describe("resetearPassword", () => {
    it("hace POST /usuarios/{id}/resetear-password con la contraseña nueva", async () => {
      const cuentaApi = {
        id: "u1",
        nombre: "Ana",
        email: "ana@fiuner.edu.ar",
        perfil: "docente",
        bloqueada: false,
        creado_en: "2026-08-01T10:00:00Z",
        comision_id: null,
      }
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaApi))

      const resultado = await resetearPassword("u1", "nuevaPassword123")

      const [url, options] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toMatch(/\/usuarios\/u1\/resetear-password$/)
      expect(options?.method).toBe("POST")
      expect(JSON.parse(String(options?.body))).toEqual({ password_nueva: "nuevaPassword123" })
      expect(resultado.bloqueada).toBe(false)
    })
  })
})
