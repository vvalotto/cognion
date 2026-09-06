import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { listarComisionesPorMateria, listarEstudiantesDeComision } from "@/lib/identidad-comisiones-api"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("identidad-comisiones-api", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe("listarComisionesPorMateria", () => {
    it("hace GET /materias/{materiaId}/comisiones", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [{ id: "c1", horario: "Lunes 18-20hs" }]),
      )

      const comisiones = await listarComisionesPorMateria("m1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/materias/m1/comisiones")
      expect(init?.method ?? "GET").toBe("GET")
      expect(comisiones).toEqual([{ id: "c1", horario: "Lunes 18-20hs" }])
    })

    it("mapea una lista vacía (materia sin comisiones)", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      const comisiones = await listarComisionesPorMateria("m1")

      expect(comisiones).toEqual([])
    })
  })

  describe("listarEstudiantesDeComision", () => {
    it("hace GET /comisiones/{comisionId}/estudiantes", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [{ id: "u1", nombre: "Ana Pérez" }]),
      )

      const estudiantes = await listarEstudiantesDeComision("c1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/comisiones/c1/estudiantes")
      expect(init?.method ?? "GET").toBe("GET")
      expect(estudiantes).toEqual([{ id: "u1", nombre: "Ana Pérez" }])
    })

    it("mapea una lista vacía (comisión sin estudiantes)", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      const estudiantes = await listarEstudiantesDeComision("c1")

      expect(estudiantes).toEqual([])
    })
  })
})
