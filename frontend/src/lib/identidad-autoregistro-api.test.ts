import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  autoregistrarDocente,
  autoregistrarEstudiante,
  listarComisionesAutoregistro,
  listarMateriasAutoregistro,
} from "@/lib/identidad-autoregistro-api"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("identidad-autoregistro-api", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("autoregistrarDocente hace POST a /identidad/autoregistro/docente sin token", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, { id: "u1", nombre: "Nico", email: "nico@fiuner.edu.ar", tipo_perfil: "docente" }),
    )

    const resultado = await autoregistrarDocente("Nico", "nico@fiuner.edu.ar", "Password#123x")

    expect(resultado).toEqual({ id: "u1", nombre: "Nico", email: "nico@fiuner.edu.ar" })
    const [url, options] = vi.mocked(fetch).mock.calls[0]
    expect(String(url)).toContain("/identidad/autoregistro/docente")
    expect(options?.method).toBe("POST")
    expect(new Headers(options?.headers).has("Authorization")).toBe(false)
  })

  it("autoregistrarEstudiante hace POST con comision_id en snake_case", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, { id: "u2", nombre: "Vale", email: "vale@fiuner.edu.ar", tipo_perfil: "estudiante" }),
    )

    await autoregistrarEstudiante("Vale", "vale@fiuner.edu.ar", "Password#123x", "com-1")

    const [, options] = vi.mocked(fetch).mock.calls[0]
    const body = JSON.parse(options?.body as string)
    expect(body).toEqual({
      nombre: "Vale",
      email: "vale@fiuner.edu.ar",
      password: "Password#123x",
      comision_id: "com-1",
    })
  })

  it("listarMateriasAutoregistro hace GET a /identidad/autoregistro/materias", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [{ id: "mat-1", nombre: "Ingeniería de Software" }]),
    )

    const materias = await listarMateriasAutoregistro()

    expect(materias).toEqual([{ id: "mat-1", nombre: "Ingeniería de Software" }])
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain("/identidad/autoregistro/materias")
  })

  it("listarComisionesAutoregistro hace GET a /identidad/autoregistro/materias/{id}/comisiones", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [{ id: "com-1", horario: "Lunes 18-21hs" }]),
    )

    const comisiones = await listarComisionesAutoregistro("mat-1")

    expect(comisiones).toEqual([{ id: "com-1", horario: "Lunes 18-21hs" }])
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain(
      "/identidad/autoregistro/materias/mat-1/comisiones",
    )
  })
})
