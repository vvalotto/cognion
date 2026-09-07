import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  crearComision,
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
} from "@/lib/identidad-comisiones-api"
import { setSession } from "@/lib/session"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

/** Arma un JWT con el payload dado — sin firma real, alcanza para testear el decode del cliente. */
function jwtFalso(payload: Record<string, unknown>): string {
  const base64url = (obj: unknown) =>
    btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
  return `${base64url({ alg: "HS256" })}.${base64url(payload)}.firma`
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

  describe("crearComision", () => {
    it("hace POST /comisiones con administrador_id resuelto del JWT de sesión", async () => {
      const adminId = "22222222-2222-2222-2222-222222222222"
      setSession({ token: jwtFalso({ sub: adminId, rol: "administrador" }), rol: "administrador" })
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(201, { id: "c1" }))

      const comision = await crearComision("m1", "Lunes y Miércoles 18-20hs")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/comisiones")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({
        materia_id: "m1",
        horario: "Lunes y Miércoles 18-20hs",
        administrador_id: adminId,
      })
      expect(comision).toEqual({ id: "c1" })
    })
  })
})
