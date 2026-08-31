import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  cerrarActividad,
  crearActividad,
  finalizarEvaluacion,
  iniciarEvaluacion,
  listarActividades,
  modificarPeriodoDisponibilidad,
  obtenerRevision,
  reanudarEvaluacion,
  registrarRespuesta,
  suspenderEvaluacion,
} from "@/lib/actividad-evaluativa-api"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const ACTIVIDAD_API = {
  id: "a1",
  materia_id: "m1",
  fecha_apertura: "2026-08-30T00:00:00Z",
  fecha_cierre: "2026-09-10T00:00:00Z",
  cantidad_preguntas: 10,
  cantidad_intentos_permitidos: 1,
  cerrada_manualmente: false,
  titulo: "",
}

const EVALUACION_API = {
  id: "e1",
  actividad_id: "a1",
  estudiante_id: "s1",
  preguntas_asignadas: [{ pregunta_id: "p1", orden: 1 }],
  estado: "EnCurso",
  iniciada_en: "2026-08-30T10:00:00Z",
}

describe("actividad-evaluativa-api", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe("crearActividad", () => {
    it("hace POST /actividades y mapea la respuesta a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(201, ACTIVIDAD_API))

      const actividad = await crearActividad({
        materiaId: "m1",
        fechaApertura: "2026-08-30T00:00:00Z",
        fechaCierre: "2026-09-10T00:00:00Z",
        cantidadPreguntas: 10,
        cantidadIntentosPermitidos: 1,
      })

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/actividades")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({
        materia_id: "m1",
        fecha_apertura: "2026-08-30T00:00:00Z",
        fecha_cierre: "2026-09-10T00:00:00Z",
        cantidad_preguntas: 10,
        cantidad_intentos_permitidos: 1,
      })
      expect(actividad).toEqual({
        id: "a1",
        materiaId: "m1",
        fechaApertura: "2026-08-30T00:00:00Z",
        fechaCierre: "2026-09-10T00:00:00Z",
        cantidadPreguntas: 10,
        cantidadIntentosPermitidos: 1,
        cerradaManualmente: false,
        titulo: "",
      })
    })

    it("incluye titulo en el body cuando se lo pasa", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(201, { ...ACTIVIDAD_API, titulo: "Parcial 1" }),
      )

      const actividad = await crearActividad({
        materiaId: "m1",
        fechaApertura: "2026-08-30T00:00:00Z",
        fechaCierre: "2026-09-10T00:00:00Z",
        cantidadPreguntas: 10,
        cantidadIntentosPermitidos: 1,
        titulo: "Parcial 1",
      })

      const [, init] = vi.mocked(fetch).mock.calls[0]
      expect(JSON.parse(init?.body as string).titulo).toBe("Parcial 1")
      expect(actividad.titulo).toBe("Parcial 1")
    })
  })

  describe("listarActividades", () => {
    it("hace GET /actividades con materia_id y mapea el resumen a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: "a1",
            materia_id: "m1",
            titulo: "Parcial 1",
            fecha_apertura: "2026-08-30T00:00:00Z",
            fecha_cierre: "2026-09-10T00:00:00Z",
            cantidad_preguntas: 10,
            cantidad_intentos_permitidos: 1,
            estado: "en_curso",
            cantidad_evaluaciones_activas: 3,
            cantidad_evaluaciones_finalizadas: 0,
          },
        ]),
      )

      const actividades = await listarActividades("m1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/actividades?materia_id=m1")
      expect(init?.method ?? "GET").toBe("GET")
      expect(actividades).toEqual([
        {
          id: "a1",
          materiaId: "m1",
          titulo: "Parcial 1",
          fechaApertura: "2026-08-30T00:00:00Z",
          fechaCierre: "2026-09-10T00:00:00Z",
          cantidadPreguntas: 10,
          cantidadIntentosPermitidos: 1,
          estado: "en_curso",
          cantidadEvaluacionesActivas: 3,
          cantidadEvaluacionesFinalizadas: 0,
        },
      ])
    })

    it("devuelve lista vacía si la materia no tiene actividades", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      const actividades = await listarActividades("m1")

      expect(actividades).toEqual([])
    })
  })

  describe("modificarPeriodoDisponibilidad", () => {
    it("hace PATCH /actividades/{id}/periodo", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, { ...ACTIVIDAD_API, fecha_cierre: "2026-09-20T00:00:00Z" }),
      )

      const actividad = await modificarPeriodoDisponibilidad("a1", "2026-09-20T00:00:00Z")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/actividades/a1/periodo")
      expect(init?.method).toBe("PATCH")
      expect(JSON.parse(init?.body as string)).toEqual({
        nueva_fecha_cierre: "2026-09-20T00:00:00Z",
      })
      expect(actividad.fechaCierre).toBe("2026-09-20T00:00:00Z")
    })
  })

  describe("cerrarActividad", () => {
    it("hace POST /actividades/{id}/cerrar", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, { ...ACTIVIDAD_API, cerrada_manualmente: true }),
      )

      const actividad = await cerrarActividad("a1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/actividades/a1/cerrar")
      expect(init?.method).toBe("POST")
      expect(actividad.cerradaManualmente).toBe(true)
    })
  })

  describe("iniciarEvaluacion", () => {
    it("hace POST /evaluaciones y mapea preguntas_asignadas", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, EVALUACION_API))

      const evaluacion = await iniciarEvaluacion("a1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/evaluaciones")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({ actividad_id: "a1" })
      expect(evaluacion).toEqual({
        id: "e1",
        actividadId: "a1",
        estudianteId: "s1",
        preguntasAsignadas: [{ preguntaId: "p1", orden: 1 }],
        estado: "EnCurso",
        iniciadaEn: "2026-08-30T10:00:00Z",
      })
    })
  })

  describe("registrarRespuesta", () => {
    it("hace POST /evaluaciones/{id}/respuestas", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(201, {
          id: "r1",
          pregunta_id: "p1",
          numero_intento: 1,
          confirmada_en: "2026-08-30T10:05:00Z",
        }),
      )

      const respuesta = await registrarRespuesta("e1", "p1", { opcion_id: "op1" })

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/evaluaciones/e1/respuestas")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({
        pregunta_id: "p1",
        contenido: { opcion_id: "op1" },
      })
      expect(respuesta).toEqual({
        id: "r1",
        preguntaId: "p1",
        numeroIntento: 1,
        confirmadaEn: "2026-08-30T10:05:00Z",
      })
    })
  })

  describe("suspenderEvaluacion", () => {
    it("hace POST /evaluaciones/{id}/suspender", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, { ...EVALUACION_API, estado: "Suspendida" }),
      )

      const evaluacion = await suspenderEvaluacion("e1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/evaluaciones/e1/suspender")
      expect(init?.method).toBe("POST")
      expect(evaluacion.estado).toBe("Suspendida")
    })
  })

  describe("reanudarEvaluacion", () => {
    it("hace POST /evaluaciones/{id}/reanudar", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, EVALUACION_API))

      const evaluacion = await reanudarEvaluacion("e1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/evaluaciones/e1/reanudar")
      expect(init?.method).toBe("POST")
      expect(evaluacion.estado).toBe("EnCurso")
    })
  })

  describe("finalizarEvaluacion", () => {
    it("hace POST /evaluaciones/{id}/finalizar", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, { ...EVALUACION_API, estado: "Finalizada" }),
      )

      const evaluacion = await finalizarEvaluacion("e1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/evaluaciones/e1/finalizar")
      expect(init?.method).toBe("POST")
      expect(evaluacion.estado).toBe("Finalizada")
    })
  })

  describe("obtenerRevision", () => {
    it("hace GET /evaluaciones/{id}/revision y mapea el detalle a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          evaluacion_id: "e1",
          cantidad_preguntas: 2,
          cantidad_correctas: 1,
          cantidad_incorrectas: 1,
          detalle: [
            {
              pregunta_id: "p1",
              orden: 1,
              texto: "¿2+2?",
              respondida: true,
              contenido_propio: { opcion_indice: 1 },
              es_correcta: true,
              contenido_correcto: null,
              opciones: ["3", "4"],
            },
          ],
        }),
      )

      const revision = await obtenerRevision("e1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/evaluaciones/e1/revision")
      expect(init?.method ?? "GET").toBe("GET")
      expect(revision).toEqual({
        evaluacionId: "e1",
        cantidadPreguntas: 2,
        cantidadCorrectas: 1,
        cantidadIncorrectas: 1,
        detalle: [
          {
            preguntaId: "p1",
            orden: 1,
            texto: "¿2+2?",
            respondida: true,
            contenidoPropio: { opcion_indice: 1 },
            esCorrecta: true,
            contenidoCorrecto: null,
            opciones: ["3", "4"],
          },
        ],
      })
    })
  })
})
