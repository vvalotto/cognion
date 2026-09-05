import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import { obtenerMiDesempeno } from "@/lib/analytics-api"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("analytics-api", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe("obtenerMiDesempeno", () => {
    it("hace GET /analytics/materias/{materiaId}/mi-desempeno y mapea a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          evaluaciones: [
            {
              evaluacion_id: "e1",
              actividad_id: "a1",
              finalizada_en: "2026-08-30T10:00:00Z",
              cantidad_correctas: 8,
              cantidad_incorrectas: 2,
            },
          ],
          resumen: {
            total_correctas: 8,
            total_incorrectas: 2,
            porcentaje_acierto: 80,
            cantidad_evaluaciones: 1,
          },
        }),
      )

      const desempeno = await obtenerMiDesempeno("m1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/analytics/materias/m1/mi-desempeno")
      expect(init?.method ?? "GET").toBe("GET")
      expect(desempeno).toEqual({
        evaluaciones: [
          {
            evaluacionId: "e1",
            actividadId: "a1",
            finalizadaEn: "2026-08-30T10:00:00Z",
            cantidadCorrectas: 8,
            cantidadIncorrectas: 2,
          },
        ],
        resumen: {
          totalCorrectas: 8,
          totalIncorrectas: 2,
          porcentajeAcierto: 80,
          cantidadEvaluaciones: 1,
        },
      })
    })

    it("mapea una lista vacía de evaluaciones", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          evaluaciones: [],
          resumen: {
            total_correctas: 0,
            total_incorrectas: 0,
            porcentaje_acierto: 0,
            cantidad_evaluaciones: 0,
          },
        }),
      )

      const desempeno = await obtenerMiDesempeno("m1")

      expect(desempeno.evaluaciones).toEqual([])
      expect(desempeno.resumen.cantidadEvaluaciones).toBe(0)
    })
  })
})
