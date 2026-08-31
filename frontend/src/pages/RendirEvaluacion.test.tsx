import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { RendirEvaluacion } from "@/pages/RendirEvaluacion"

const ACTIVIDAD_ID = "act-1"
const EVALUACION_ID = "eval-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function preguntaOpcionMultiple(preguntaId: string, orden: number) {
  return {
    pregunta_id: preguntaId,
    orden,
    enunciado: `Enunciado ${orden}`,
    opciones: ["Opción A", "Opción B", "Opción C"],
  }
}

function evaluacionBody(overrides?: Partial<Record<string, unknown>>) {
  return {
    id: EVALUACION_ID,
    actividad_id: ACTIVIDAD_ID,
    estudiante_id: "est-1",
    preguntas_asignadas: [preguntaOpcionMultiple("p1", 0), preguntaOpcionMultiple("p2", 1)],
    preguntas_respondidas: [],
    estado: "EnCurso",
    iniciada_en: "2026-09-01T00:00:00+00:00",
    ...overrides,
  }
}

function renderRendirEvaluacion() {
  return render(
    <MemoryRouter initialEntries={[`/mis-actividades/actividades/${ACTIVIDAD_ID}/rendir`]}>
      <Routes>
        <Route
          path="/mis-actividades/actividades/:actividadId/rendir"
          element={<RendirEvaluacion />}
        />
        <Route
          path="/mis-actividades/actividades/:actividadId/suspendida"
          element={<p>Suspendida</p>}
        />
        <Route path="/mis-actividades/:actividadId/fuera-de-periodo" element={<p>Fuera de período</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("RendirEvaluacion", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra la pregunta actual con sus opciones, sin marcar cuál es correcta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, evaluacionBody()))
    renderRendirEvaluacion()

    expect(await screen.findByText("Enunciado 0")).toBeInTheDocument()
    expect(screen.getByText("Opción A")).toBeInTheDocument()
    expect(screen.getByText("Pregunta 1 de 2")).toBeInTheDocument()
  })

  it("confirmar una respuesta la persiste y avanza a la siguiente pregunta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, evaluacionBody()))
    renderRendirEvaluacion()
    await screen.findByText("Enunciado 0")

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "resp-1",
        pregunta_id: "p1",
        numero_intento: 1,
        confirmada_en: "2026-09-01T00:05:00+00:00",
      }),
    )

    const user = userEvent.setup()
    await user.click(screen.getByText("Opción A"))
    await user.click(screen.getByRole("button", { name: "Confirmar y siguiente" }))

    expect(await screen.findByText("Enunciado 1")).toBeInTheDocument()

    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(ultimaLlamada?.[0]).toContain(`/evaluaciones/${EVALUACION_ID}/respuestas`)
    const body = JSON.parse((ultimaLlamada?.[1] as RequestInit).body as string)
    expect(body).toEqual({ pregunta_id: "p1", contenido: { opcion_indice: 0 } })
  })

  it("reconexión: retoma con las respuestas previas marcadas y en la primera pendiente", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, evaluacionBody({ preguntas_respondidas: ["p1"] })),
    )
    renderRendirEvaluacion()

    expect(await screen.findByText("Enunciado 1")).toBeInTheDocument()
    expect(screen.getByText("Pregunta 2 de 2")).toBeInTheDocument()
    expect(screen.getByText("1 respondidas")).toBeInTheDocument()
  })

  it("pausar y salir suspende la evaluación y navega a la pantalla de suspendida", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, evaluacionBody()))
    renderRendirEvaluacion()
    await screen.findByText("Enunciado 0")

    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, evaluacionBody({ estado: "Suspendida" })),
    )

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Pausar y salir" }))

    expect(await screen.findByText("Suspendida")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(ultimaLlamada?.[0]).toContain(`/evaluaciones/${EVALUACION_ID}/suspender`)
  })

  it("si la evaluación ya está suspendida al entrar, redirige sin mostrar la pregunta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, evaluacionBody({ estado: "Suspendida" })),
    )
    renderRendirEvaluacion()

    expect(await screen.findByText("Suspendida")).toBeInTheDocument()
    expect(screen.queryByText("Enunciado 0")).not.toBeInTheDocument()
  })

  it("fuera de período redirige a la pantalla correspondiente", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(422, { detail: "La actividad no está en su período vigente." }),
    )
    renderRendirEvaluacion()

    expect(await screen.findByText("Fuera de período")).toBeInTheDocument()
  })

  it("una pregunta de Verdadero/Falso muestra las dos opciones fijas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(
        200,
        evaluacionBody({
          preguntas_asignadas: [
            {
              pregunta_id: "p1",
              orden: 0,
              enunciado: "Python es interpretado.",
              opciones: null,
            },
          ],
        }),
      ),
    )
    renderRendirEvaluacion()

    expect(await screen.findByText("Verdadero")).toBeInTheDocument()
    expect(screen.getByText("Falso")).toBeInTheDocument()
  })
})
