import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  obtenerDesempenoDeEstudiante,
  obtenerDesempenoPorComision,
  obtenerEvolucionTemporalComision,
  obtenerEvolucionTemporalEstudiante,
  obtenerMiDesempeno,
  obtenerTasaErrorPorTema,
} from "@/lib/analytics-api"

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

  describe("obtenerDesempenoDeEstudiante", () => {
    it("hace GET /analytics/materias/{materiaId}/estudiantes/{estudianteId}/desempeno y mapea a camelCase", async () => {
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

      const desempeno = await obtenerDesempenoDeEstudiante("m1", "u1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/analytics/materias/m1/estudiantes/u1/desempeno")
      expect(init?.method ?? "GET").toBe("GET")
      expect(desempeno.resumen.totalCorrectas).toBe(8)
    })

    it("mapea una lista vacía de evaluaciones (estudiante sin evaluaciones finalizadas)", async () => {
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

      const desempeno = await obtenerDesempenoDeEstudiante("m1", "u2")

      expect(desempeno.evaluaciones).toEqual([])
    })
  })

  describe("obtenerTasaErrorPorTema", () => {
    it("hace GET /analytics/materias/{materiaId}/tasa-error-por-tema sin comision_id y mapea a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          {
            unidad_tematica: "Unidad 3 — Principios SOLID",
            tema: "Inversión de dependencias",
            cantidad_respuestas: 42,
            cantidad_incorrectas: 24,
            tasa_error: 0.5714285714285714,
          },
        ]),
      )

      const tasas = await obtenerTasaErrorPorTema("m1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toBe(
        "http://localhost:8000/analytics/materias/m1/tasa-error-por-tema",
      )
      expect(init?.method ?? "GET").toBe("GET")
      expect(tasas).toEqual([
        {
          unidadTematica: "Unidad 3 — Principios SOLID",
          tema: "Inversión de dependencias",
          cantidadRespuestas: 42,
          cantidadIncorrectas: 24,
          tasaError: 0.5714285714285714,
        },
      ])
    })

    it("agrega comision_id a la query cuando se pasa", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      await obtenerTasaErrorPorTema("m1", "c1")

      const [url] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toBe(
        "http://localhost:8000/analytics/materias/m1/tasa-error-por-tema?comision_id=c1",
      )
    })

    it("mapea una lista vacía (materia sin evaluaciones finalizadas)", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      const tasas = await obtenerTasaErrorPorTema("m1")

      expect(tasas).toEqual([])
    })
  })

  describe("obtenerDesempenoPorComision", () => {
    it("hace GET /analytics/materias/{materiaId}/comisiones/{comisionId}/desempeno y mapea a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          {
            estudiante_id: "u1",
            nombre: "Ana Pérez",
            porcentaje_aciertos_acumulado: 82,
            actividades_pendientes: 1,
          },
          {
            estudiante_id: "u2",
            nombre: "Juan Gómez",
            porcentaje_aciertos_acumulado: null,
            actividades_pendientes: 2,
          },
        ]),
      )

      const filas = await obtenerDesempenoPorComision("m1", "c1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toBe(
        "http://localhost:8000/analytics/materias/m1/comisiones/c1/desempeno",
      )
      expect(init?.method ?? "GET").toBe("GET")
      expect(filas).toEqual([
        { estudianteId: "u1", nombre: "Ana Pérez", porcentajeAciertosAcumulado: 82, actividadesPendientes: 1 },
        { estudianteId: "u2", nombre: "Juan Gómez", porcentajeAciertosAcumulado: null, actividadesPendientes: 2 },
      ])
    })

    it("mapea una lista vacía (comisión sin estudiantes)", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      const filas = await obtenerDesempenoPorComision("m1", "c1")

      expect(filas).toEqual([])
    })
  })

  describe("obtenerEvolucionTemporalEstudiante", () => {
    it("hace GET /analytics/materias/{materiaId}/estudiantes/{estudianteId}/evolucion-temporal y mapea a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          {
            actividad_id: "a1",
            titulo_actividad: "Parcial 1",
            finalizada_en: "2026-08-30T10:00:00Z",
            porcentaje_acierto: 82,
          },
        ]),
      )

      const puntos = await obtenerEvolucionTemporalEstudiante("m1", "u1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toBe(
        "http://localhost:8000/analytics/materias/m1/estudiantes/u1/evolucion-temporal",
      )
      expect(init?.method ?? "GET").toBe("GET")
      expect(puntos).toEqual([
        { actividadId: "a1", tituloActividad: "Parcial 1", finalizadaEn: "2026-08-30T10:00:00Z", porcentajeAcierto: 82 },
      ])
    })

    it("mapea una lista vacía (estudiante sin evaluaciones finalizadas)", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      const puntos = await obtenerEvolucionTemporalEstudiante("m1", "u1")

      expect(puntos).toEqual([])
    })
  })

  describe("obtenerEvolucionTemporalComision", () => {
    it("hace GET /analytics/materias/{materiaId}/comisiones/{comisionId}/evolucion-temporal y mapea a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          { actividad_id: "a1", titulo_actividad: "Parcial 1", porcentaje_aciertos_promedio: 74.5 },
        ]),
      )

      const puntos = await obtenerEvolucionTemporalComision("m1", "c1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toBe(
        "http://localhost:8000/analytics/materias/m1/comisiones/c1/evolucion-temporal",
      )
      expect(init?.method ?? "GET").toBe("GET")
      expect(puntos).toEqual([
        { actividadId: "a1", tituloActividad: "Parcial 1", porcentajeAciertosPromedio: 74.5 },
      ])
    })

    it("mapea una lista vacía (comisión sin evaluaciones finalizadas)", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      const puntos = await obtenerEvolucionTemporalComision("m1", "c1")

      expect(puntos).toEqual([])
    })
  })
})
