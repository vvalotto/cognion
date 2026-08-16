import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { NuevaPreguntaVerdaderoFalso } from "@/pages/NuevaPreguntaVerdaderoFalso"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const materiaResponse = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 2 },
]

const preguntaCreadaResponse = {
  id: "p9",
  banco_id: "b1",
  texto: "Un Aggregate Root solo referencia a otro por identidad.",
  respuesta_correcta: true,
  unidad_tematica: "Unidad 2",
  tema: "DDD",
  dificultad: "medio",
  importancia: "alto",
  activa: true,
}

function renderFormulario() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/banco/preguntas/nueva/verdadero-falso"]}>
      <Routes>
        <Route
          path="/materias/:materiaId/banco/preguntas/nueva/verdadero-falso"
          element={<NuevaPreguntaVerdaderoFalso />}
        />
        <Route path="/materias/:materiaId/banco" element={<p>Banco</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("NuevaPreguntaVerdaderoFalso", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("completar texto, elegir Verdadero y guardar crea la pregunta y vuelve al banco", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiaResponse))
      .mockResolvedValueOnce(jsonResponse(201, preguntaCreadaResponse))
    const user = userEvent.setup()

    renderFormulario()
    await user.type(
      await screen.findByLabelText("Texto de la pregunta"),
      "Un Aggregate Root solo referencia a otro por identidad.",
    )
    await user.type(screen.getByLabelText("Unidad temática"), "Unidad 2")
    await user.type(screen.getByLabelText("Tema"), "DDD")
    await user.click(screen.getByText("Verdadero"))

    await user.click(screen.getByText("Guardar pregunta"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    const [, segundaLlamada] = vi.mocked(fetch).mock.calls
    const [, init] = segundaLlamada
    const body = JSON.parse((init as RequestInit).body as string)
    expect(body.respuesta_correcta).toBe(true)
  })

  it("guardar sin elegir Verdadero/Falso bloquea el envío y no llama al backend", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiaResponse))
    const user = userEvent.setup()

    renderFormulario()
    await user.type(await screen.findByLabelText("Texto de la pregunta"), "Afirmación")
    await user.type(screen.getByLabelText("Unidad temática"), "Unidad 2")
    await user.type(screen.getByLabelText("Tema"), "DDD")

    await user.click(screen.getByText("Guardar pregunta"))

    expect(
      await screen.findByText("Elegí si la respuesta correcta es Verdadero o Falso."),
    ).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(1)
  })

  it("'Cancelar' vuelve al banco sin guardar", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiaResponse))
    const user = userEvent.setup()

    renderFormulario()
    await screen.findByLabelText("Texto de la pregunta")

    await user.click(screen.getByText("Cancelar"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(1)
  })
})
