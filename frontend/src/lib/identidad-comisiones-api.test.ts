import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  asignarDocente,
  crearComision,
  generarInvitacion,
  listarComisionesPorMateria,
  listarEstudiantesDeComision,
  obtenerComision,
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

  describe("obtenerComision", () => {
    it("hace GET /comisiones/{id} y mapea docentes_asignados a docentesAsignados", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          id: "c1",
          materia_id: "m1",
          horario: "Lunes 18-20hs",
          administrador_id: "a1",
          docentes_asignados: ["d1"],
        }),
      )

      const comision = await obtenerComision("c1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/comisiones/c1")
      expect(init?.method ?? "GET").toBe("GET")
      expect(comision).toEqual({ id: "c1", horario: "Lunes 18-20hs", docentesAsignados: ["d1"] })
    })

    it("mapea docentes_asignados vacío", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          id: "c1",
          materia_id: "m1",
          horario: "Lunes 18-20hs",
          administrador_id: "a1",
          docentes_asignados: [],
        }),
      )

      const comision = await obtenerComision("c1")

      expect(comision.docentesAsignados).toEqual([])
    })
  })

  describe("asignarDocente", () => {
    it("hace POST /comisiones/{id}/docentes con docente_id", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          id: "c1",
          materia_id: "m1",
          horario: "Lunes 18-20hs",
          administrador_id: "a1",
          docentes_asignados: ["d1"],
        }),
      )

      const comision = await asignarDocente("c1", "d1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/comisiones/c1/docentes")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({ docente_id: "d1" })
      expect(comision.docentesAsignados).toEqual(["d1"])
    })
  })

  describe("generarInvitacion", () => {
    it("hace POST /comisiones/{id}/invitaciones con docente_id, sin email_destinatario, y mapea el token", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(201, {
          id: "i1",
          comision_id: "c1",
          docente_id: "d1",
          expira_en: "2026-09-14T00:00:00Z",
          token: "tok-123",
        }),
      )

      const invitacion = await generarInvitacion("c1", "d1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/comisiones/c1/invitaciones")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({ docente_id: "d1" })
      expect(invitacion).toEqual({
        id: "i1",
        comisionId: "c1",
        docenteId: "d1",
        expiraEn: "2026-09-14T00:00:00Z",
        token: "tok-123",
      })
    })
  })
})
