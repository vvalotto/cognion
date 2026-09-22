import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  avanzarPregunta,
  cerrarPregunta,
  crearSesion,
  finalizarSesion,
  iniciarSesion,
  listarParticipantes,
  listarSesionesEnVivo,
  mostrarOpciones,
  obtenerEstadoSesion,
  obtenerRankingSesion,
  responderPregunta,
  unirseASesion,
} from "@/lib/sesion-en-vivo-api"
import { setSession } from "@/lib/session"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const SESION_API = {
  id: "s1",
  comision_id: "c1",
  materia_id: "m1",
  unidad_tematica: null,
  tema: null,
  cantidad_preguntas: 5,
  tiempo_limite_por_pregunta_segundos: 20,
  estado: "en_espera",
  pregunta_actual_indice: null,
}

const SESION_ESPERADA = {
  id: "s1",
  comisionId: "c1",
  materiaId: "m1",
  unidadTematica: null,
  tema: null,
  cantidadPreguntas: 5,
  tiempoLimitePorPreguntaSegundos: 20,
  estado: "en_espera",
  preguntaActualIndice: null,
}

describe("sesion-en-vivo-api", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal("fetch", vi.fn())
    setSession({ token: "jwt-de-prueba", rol: "docente" })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("adjunta el Authorization con el JWT de la sesión", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, SESION_API))

    await iniciarSesion("s1")

    const [, init] = vi.mocked(fetch).mock.calls[0]
    const headers = new Headers(init?.headers)
    expect(headers.get("Authorization")).toBe("Bearer jwt-de-prueba")
  })

  describe("crearSesion", () => {
    it("hace POST /sesiones-en-vivo y mapea a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(201, SESION_API))

      const sesion = await crearSesion({
        comisionId: "c1",
        cantidadPreguntas: 5,
        tiempoLimitePorPreguntaSegundos: 20,
      })

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({
        comision_id: "c1",
        cantidad_preguntas: 5,
        tiempo_limite_por_pregunta_segundos: 20,
        unidad_tematica: null,
        tema: null,
      })
      expect(sesion).toEqual(SESION_ESPERADA)
    })
  })

  describe("iniciarSesion", () => {
    it("hace POST /sesiones-en-vivo/{id}/iniciar", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, SESION_API))

      const sesion = await iniciarSesion("s1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/iniciar")
      expect(init?.method).toBe("POST")
      expect(sesion).toEqual(SESION_ESPERADA)
    })
  })

  describe("mostrarOpciones", () => {
    it("hace POST /sesiones-en-vivo/{id}/mostrar-opciones", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, SESION_API))

      await mostrarOpciones("s1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/mostrar-opciones")
      expect(init?.method).toBe("POST")
    })
  })

  describe("cerrarPregunta", () => {
    it("hace POST /sesiones-en-vivo/{id}/cerrar-pregunta", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, SESION_API))

      await cerrarPregunta("s1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/cerrar-pregunta")
      expect(init?.method).toBe("POST")
    })
  })

  describe("avanzarPregunta", () => {
    it("hace POST /sesiones-en-vivo/{id}/avanzar", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, SESION_API))

      await avanzarPregunta("s1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/avanzar")
      expect(init?.method).toBe("POST")
    })
  })

  describe("finalizarSesion", () => {
    it("hace POST /sesiones-en-vivo/{id}/finalizar", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, SESION_API))

      await finalizarSesion("s1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/finalizar")
      expect(init?.method).toBe("POST")
    })
  })

  describe("unirseASesion", () => {
    it("hace POST /sesiones-en-vivo/{id}/unirse y mapea a camelCase", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, { sesion_id: "s1", estudiante_id: "e1", unido_en: "2026-09-22T10:00:00Z" }),
      )

      const participacion = await unirseASesion("s1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/unirse")
      expect(init?.method).toBe("POST")
      expect(participacion).toEqual({
        sesionId: "s1",
        estudianteId: "e1",
        unidoEn: "2026-09-22T10:00:00Z",
      })
    })
  })

  describe("responderPregunta", () => {
    it("hace POST /sesiones-en-vivo/{id}/responder con el contenido enviado", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, { es_correcta: true, puntaje: 950, puntaje_acumulado: 950 }),
      )

      const respuesta = await responderPregunta("s1", "p1", { opcion_indice: 2 })

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/responder")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({
        pregunta_id: "p1",
        contenido: { opcion_indice: 2 },
      })
      expect(respuesta).toEqual({ esCorrecta: true, puntaje: 950, puntajeAcumulado: 950 })
    })
  })

  describe("obtenerEstadoSesion", () => {
    it("hace GET /sesiones-en-vivo/{id} y mapea el estado completo", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          estado: "en_curso",
          comision_id: "c1",
          cantidad_preguntas: 5,
          tiempo_limite_por_pregunta_segundos: 20,
          pregunta_actual_indice: 0,
          opciones_mostradas: true,
          opciones_mostradas_en: "2026-09-22T10:05:00Z",
          pregunta_actual_cerrada: false,
          pregunta_actual: {
            pregunta_id: "p1",
            enunciado: "¿SOLID?",
            tipo: "opcion_multiple",
            opciones: ["a", "b"],
            respuesta_correcta: null,
          },
          ya_respondio: false,
          puntaje_acumulado: 0,
          total_participantes: 3,
          cantidad_respuestas: 1,
          resultado_pregunta: null,
        }),
      )

      const estado = await obtenerEstadoSesion("s1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1")
      expect(init?.method ?? "GET").toBe("GET")
      expect(estado.preguntaActual).toEqual({
        preguntaId: "p1",
        enunciado: "¿SOLID?",
        tipo: "opcion_multiple",
        opciones: ["a", "b"],
        respuestaCorrecta: null,
      })
      expect(estado.totalParticipantes).toBe(3)
      expect(estado.cantidadRespuestas).toBe(1)
      expect(estado.resultadoPregunta).toBeNull()
    })

    it("mapea resultadoPregunta con distribución y ranking cuando la pregunta está cerrada", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          estado: "en_curso",
          comision_id: "c1",
          cantidad_preguntas: 5,
          tiempo_limite_por_pregunta_segundos: 20,
          pregunta_actual_indice: 0,
          opciones_mostradas: true,
          opciones_mostradas_en: "2026-09-22T10:05:00Z",
          pregunta_actual_cerrada: true,
          pregunta_actual: {
            pregunta_id: "p1",
            enunciado: "¿SOLID?",
            tipo: "opcion_multiple",
            opciones: ["a", "b"],
            respuesta_correcta: { contenido: { opcion_indice: 1 }, texto: "b", opciones: ["a", "b"] },
          },
          ya_respondio: null,
          puntaje_acumulado: null,
          total_participantes: 3,
          cantidad_respuestas: 3,
          resultado_pregunta: {
            distribucion: [
              { opcion: "0", cantidad: 1 },
              { opcion: "1", cantidad: 2 },
            ],
            ranking: [{ posicion: 1, estudiante_id: "e1", puntaje_acumulado: 950, nombre: "Ana" }],
          },
        }),
      )

      const estado = await obtenerEstadoSesion("s1")

      expect(estado.preguntaActual?.respuestaCorrecta).toEqual({
        contenido: { opcion_indice: 1 },
        texto: "b",
        opciones: ["a", "b"],
      })
      expect(estado.resultadoPregunta).toEqual({
        distribucion: [
          { opcion: "0", cantidad: 1 },
          { opcion: "1", cantidad: 2 },
        ],
        ranking: [{ posicion: 1, estudianteId: "e1", puntajeAcumulado: 950, nombre: "Ana" }],
      })
    })
  })

  describe("listarParticipantes", () => {
    it("hace GET /sesiones-en-vivo/{id}/participantes", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          { estudiante_id: "e1", unido_en: "2026-09-22T10:00:00Z", nombre: "Ana" },
        ]),
      )

      const participantes = await listarParticipantes("s1")

      const [url] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/participantes")
      expect(participantes).toEqual([
        { estudianteId: "e1", unidoEn: "2026-09-22T10:00:00Z", nombre: "Ana" },
      ])
    })
  })

  describe("obtenerRankingSesion", () => {
    it("hace GET /sesiones-en-vivo/{id}/ranking", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          { posicion: 1, estudiante_id: "e1", puntaje_acumulado: 950, nombre: "Ana" },
        ]),
      )

      const ranking = await obtenerRankingSesion("s1")

      const [url] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo/s1/ranking")
      expect(ranking).toEqual([
        { posicion: 1, estudianteId: "e1", puntajeAcumulado: 950, nombre: "Ana" },
      ])
    })
  })

  describe("listarSesionesEnVivo", () => {
    it("hace GET /sesiones-en-vivo?comision_id= y mapea el resumen", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: "s1",
            comision_id: "c1",
            materia_id: "m1",
            materia_nombre: "Ingeniería de Software",
            cantidad_preguntas: 5,
            tiempo_limite_por_pregunta_segundos: 20,
            estado: "finalizada",
            unidad_tematica: null,
            tema: null,
            creada_en: "2026-09-22T09:00:00Z",
          },
        ]),
      )

      const sesiones = await listarSesionesEnVivo("c1")

      const [url] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/sesiones-en-vivo?comision_id=c1")
      expect(sesiones).toEqual([
        {
          id: "s1",
          comisionId: "c1",
          materiaId: "m1",
          materiaNombre: "Ingeniería de Software",
          cantidadPreguntas: 5,
          tiempoLimitePorPreguntaSegundos: 20,
          estado: "finalizada",
          unidadTematica: null,
          tema: null,
          creadaEn: "2026-09-22T09:00:00Z",
        },
      ])
    })
  })
})
