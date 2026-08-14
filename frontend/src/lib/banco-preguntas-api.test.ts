import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/router", () => ({
  router: { navigate: vi.fn() },
}))

import {
  cargarPreguntaOpcionMultiple,
  cargarPreguntaVerdaderoFalso,
  crearMateria,
  editarPregunta,
  eliminarPregunta,
  filtrarBanco,
} from "@/lib/banco-preguntas-api"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("banco-preguntas-api", () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  describe("crearMateria", () => {
    it("hace POST /materias y mapea banco_id a bancoId", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(201, { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1" }),
      )

      const materia = await crearMateria("Ingeniería de Software")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/materias")
      expect(init?.method).toBe("POST")
      expect(JSON.parse(init?.body as string)).toEqual({ nombre: "Ingeniería de Software" })
      expect(materia).toEqual({ id: "m1", nombre: "Ingeniería de Software", bancoId: "b1" })
    })
  })

  describe("filtrarBanco", () => {
    it("hace GET /bancos/{id}/preguntas sin query string cuando no hay filtros", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      await filtrarBanco("b1")

      const [url] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/bancos/b1/preguntas")
      expect(String(url)).not.toContain("?")
    })

    it("arma el query string solo con los filtros presentes", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      await filtrarBanco("b1", { dificultad: "alto", tema: "Cohesión" })

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.searchParams.get("dificultad")).toBe("alto")
      expect(parsed.searchParams.get("tema")).toBe("Cohesión")
      expect(parsed.searchParams.has("unidad")).toBe(false)
      expect(parsed.searchParams.has("importancia")).toBe(false)
    })

    it("incluye unidad e importancia en el query string cuando se proveen", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

      await filtrarBanco("b1", { unidad: "u1", importancia: "medio" })

      const [url] = vi.mocked(fetch).mock.calls[0]
      const parsed = new URL(String(url))
      expect(parsed.searchParams.get("unidad")).toBe("u1")
      expect(parsed.searchParams.get("importancia")).toBe("medio")
    })

    it("mapea preguntas de opción múltiple y verdadero/falso desde snake_case", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: "p1",
            banco_id: "b1",
            texto: "¿Cuál es SOLID?",
            opciones: [{ texto: "a", es_correcta: true }],
            unidad_tematica: "u1",
            tema: "t1",
            dificultad: "alto",
            importancia: "alto",
            activa: true,
          },
          {
            id: "p2",
            banco_id: "b1",
            texto: "¿Verdadero?",
            respuesta_correcta: false,
            unidad_tematica: "u2",
            tema: "t2",
            dificultad: "bajo",
            importancia: "medio",
            activa: true,
          },
        ]),
      )

      const preguntas = await filtrarBanco("b1")

      expect(preguntas[0]).toEqual({
        id: "p1",
        bancoId: "b1",
        texto: "¿Cuál es SOLID?",
        opciones: [{ texto: "a", esCorrecta: true }],
        unidadTematica: "u1",
        tema: "t1",
        dificultad: "alto",
        importancia: "alto",
        activa: true,
      })
      expect(preguntas[1]).toEqual({
        id: "p2",
        bancoId: "b1",
        texto: "¿Verdadero?",
        respuestaCorrecta: false,
        unidadTematica: "u2",
        tema: "t2",
        dificultad: "bajo",
        importancia: "medio",
        activa: true,
      })
    })
  })

  describe("cargarPreguntaOpcionMultiple", () => {
    it("hace POST /preguntas/opcion-multiple con body en snake_case", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(201, {
          id: "p1",
          banco_id: "b1",
          texto: "texto",
          opciones: [{ texto: "a", es_correcta: true }],
          unidad_tematica: "u1",
          tema: "t1",
          dificultad: "alto",
          importancia: "alto",
          activa: true,
        }),
      )

      const pregunta = await cargarPreguntaOpcionMultiple({
        bancoId: "b1",
        texto: "texto",
        opciones: [{ texto: "a", esCorrecta: true }],
        unidadTematica: "u1",
        tema: "t1",
        dificultad: "alto",
        importancia: "alto",
      })

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/preguntas/opcion-multiple")
      expect(JSON.parse(init?.body as string)).toEqual({
        banco_id: "b1",
        texto: "texto",
        opciones: [{ texto: "a", es_correcta: true }],
        unidad_tematica: "u1",
        tema: "t1",
        dificultad: "alto",
        importancia: "alto",
      })
      expect(pregunta.opciones).toEqual([{ texto: "a", esCorrecta: true }])
    })
  })

  describe("cargarPreguntaVerdaderoFalso", () => {
    it("hace POST /preguntas/verdadero-falso con body en snake_case", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(201, {
          id: "p1",
          banco_id: "b1",
          texto: "texto",
          respuesta_correcta: true,
          unidad_tematica: "u1",
          tema: "t1",
          dificultad: "medio",
          importancia: "bajo",
          activa: true,
        }),
      )

      const pregunta = await cargarPreguntaVerdaderoFalso({
        bancoId: "b1",
        texto: "texto",
        respuestaCorrecta: true,
        unidadTematica: "u1",
        tema: "t1",
        dificultad: "medio",
        importancia: "bajo",
      })

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/preguntas/verdadero-falso")
      expect(JSON.parse(init?.body as string)).toEqual({
        banco_id: "b1",
        texto: "texto",
        respuesta_correcta: true,
        unidad_tematica: "u1",
        tema: "t1",
        dificultad: "medio",
        importancia: "bajo",
      })
      expect(pregunta.respuestaCorrecta).toBe(true)
    })
  })

  describe("editarPregunta", () => {
    it("hace PUT /preguntas/{id} con body en snake_case", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          id: "p1",
          banco_id: "b1",
          texto: "editado",
          respuesta_correcta: false,
          unidad_tematica: "u1",
          tema: "t1",
          dificultad: "alto",
          importancia: "alto",
          activa: true,
        }),
      )

      await editarPregunta("p1", {
        texto: "editado",
        unidadTematica: "u1",
        tema: "t1",
        dificultad: "alto",
        importancia: "alto",
        respuestaCorrecta: false,
      })

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/preguntas/p1")
      expect(init?.method).toBe("PUT")
      expect(JSON.parse(init?.body as string)).toMatchObject({
        texto: "editado",
        respuesta_correcta: false,
      })
    })

    it("mapea opciones a snake_case cuando la pregunta es de opción múltiple", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(
        jsonResponse(200, {
          id: "p1",
          banco_id: "b1",
          texto: "editado",
          opciones: [{ texto: "a", es_correcta: true }],
          unidad_tematica: "u1",
          tema: "t1",
          dificultad: "alto",
          importancia: "alto",
          activa: true,
        }),
      )

      await editarPregunta("p1", {
        texto: "editado",
        unidadTematica: "u1",
        tema: "t1",
        dificultad: "alto",
        importancia: "alto",
        opciones: [{ texto: "a", esCorrecta: true }],
      })

      const [, init] = vi.mocked(fetch).mock.calls[0]
      expect(JSON.parse(init?.body as string)).toMatchObject({
        opciones: [{ texto: "a", es_correcta: true }],
      })
    })
  })

  describe("eliminarPregunta", () => {
    it("hace DELETE /preguntas/{id}", async () => {
      vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 204 }))

      await eliminarPregunta("p1")

      const [url, init] = vi.mocked(fetch).mock.calls[0]
      expect(String(url)).toContain("/preguntas/p1")
      expect(init?.method).toBe("DELETE")
    })
  })
})
