import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  CambiarPasswordError,
  cambiarPassword,
  listarCuentas,
  obtenerCuenta,
  resetearPassword,
} from "@/lib/cuentas-api"

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
    it("hace GET /usuarios sin filtros pero con pagina/tamanio_pagina por defecto", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { cuentas: [], total: 0 }))

      await listarCuentas()

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.pathname).toMatch(/\/usuarios$/)
      expect(parsed.searchParams.get("pagina")).toBe("1")
      expect(parsed.searchParams.get("tamanio_pagina")).toBe("20")
    })

    it("arma el query string solo con los filtros presentes", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { cuentas: [], total: 0 }))

      await listarCuentas({ rol: "docente", estado: "bloqueada", busqueda: "ana" })

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.searchParams.get("rol")).toBe("docente")
      expect(parsed.searchParams.get("estado")).toBe("bloqueada")
      expect(parsed.searchParams.get("busqueda")).toBe("ana")
    })

    it("omite del query string los filtros no provistos", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { cuentas: [], total: 0 }))

      await listarCuentas({ rol: "estudiante" })

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.searchParams.get("rol")).toBe("estudiante")
      expect(parsed.searchParams.has("estado")).toBe(false)
      expect(parsed.searchParams.has("busqueda")).toBe(false)
    })

    it("[US-ADJ-05] incluye pagina y tamanio_pagina en el query string cuando se proveen", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { cuentas: [], total: 0 }))

      await listarCuentas({}, { pagina: 2, tamanioPagina: 20 })

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.searchParams.get("pagina")).toBe("2")
      expect(parsed.searchParams.get("tamanio_pagina")).toBe("20")
    })

    it("devuelve las cuentas y el total tal como los envía el backend", async () => {
      const cuentas = [
        { id: "u1", nombre: "Ana", email: "ana@fiuner.edu.ar", perfil: "docente", bloqueada: false },
        { id: "u2", nombre: "Luis", email: "luis@fiuner.edu.ar", perfil: "estudiante", bloqueada: true },
      ]
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { cuentas, total: 2 }))

      const resultado = await listarCuentas()

      expect(resultado.cuentas).toEqual(cuentas)
      expect(resultado.total).toBe(2)
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

  describe("cambiarPassword", () => {
    it("hace PUT /usuarios/me/password con las contraseñas", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 204 }))

      await cambiarPassword("actual123", "nuevaClave123")

      const [url, options] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toMatch(/\/usuarios\/me\/password$/)
      expect(options?.method).toBe("PUT")
      expect(JSON.parse(String(options?.body))).toEqual({
        password_actual: "actual123",
        password_nueva: "nuevaClave123",
      })
    })

    it("no navega a /login ante un 401 (no es una sesión inválida)", async () => {
      const { router } = await import("@/router")
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(401, { detail: { mensaje: "Incorrecta", intentos_restantes: 2 } }),
      )

      await expect(cambiarPassword("mala", "nuevaClave123")).rejects.toThrow()

      expect(router.navigate).not.toHaveBeenCalled()
    })

    it("lanza CambiarPasswordError con intentosRestantes cuando la contraseña actual es incorrecta", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(401, {
          detail: { mensaje: "La contraseña actual es incorrecta.", intentos_restantes: 2 },
        }),
      )

      const error = await cambiarPassword("mala", "nuevaClave123").catch((e: unknown) => e)

      expect(error).toBeInstanceOf(CambiarPasswordError)
      const cambiarPasswordError = error as CambiarPasswordError
      expect(cambiarPasswordError.intentosRestantes).toBe(2)
      expect(cambiarPasswordError.bloqueada).toBe(false)
    })

    it("lanza CambiarPasswordError con bloqueada=true al tercer fallo consecutivo", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(401, {
          detail: { mensaje: "La contraseña actual es incorrecta.", bloqueada: true },
        }),
      )

      const error = await cambiarPassword("mala", "nuevaClave123").catch((e: unknown) => e)

      expect(error).toBeInstanceOf(CambiarPasswordError)
      expect((error as CambiarPasswordError).bloqueada).toBe(true)
    })

    it("lanza CambiarPasswordError con bloqueada=true cuando la cuenta ya estaba bloqueada", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(403, { detail: { mensaje: "La cuenta está bloqueada.", bloqueada: true } }),
      )

      const error = await cambiarPassword("cualquiera", "nuevaClave123").catch((e: unknown) => e)

      expect(error).toBeInstanceOf(CambiarPasswordError)
      expect((error as CambiarPasswordError).bloqueada).toBe(true)
    })
  })
})
