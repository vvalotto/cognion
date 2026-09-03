import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { NuevaPreguntaTipo } from "@/pages/banco-preguntas/NuevaPreguntaTipo"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const materiaResponse = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 2 },
]

function renderNuevaPreguntaTipo() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/banco/preguntas/nueva"]}>
      <Routes>
        <Route path="/materias/:materiaId/banco/preguntas/nueva" element={<NuevaPreguntaTipo />} />
        <Route
          path="/materias/:materiaId/banco/preguntas/nueva/opcion-multiple"
          element={<p>Formulario Opción múltiple</p>}
        />
        <Route
          path="/materias/:materiaId/banco/preguntas/nueva/verdadero-falso"
          element={<p>Formulario Verdadero/Falso</p>}
        />
        <Route path="/materias/:materiaId/banco" element={<p>Banco</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("NuevaPreguntaTipo", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(200, materiaResponse)))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("elegir 'Opción múltiple' navega al formulario correspondiente", async () => {
    const user = userEvent.setup()
    renderNuevaPreguntaTipo()

    await user.click(screen.getByText("Opción múltiple"))

    expect(await screen.findByText("Formulario Opción múltiple")).toBeInTheDocument()
  })

  it("elegir 'Verdadero/Falso' navega al formulario correspondiente", async () => {
    const user = userEvent.setup()
    renderNuevaPreguntaTipo()

    await user.click(screen.getByText("Verdadero / Falso"))

    expect(await screen.findByText("Formulario Verdadero/Falso")).toBeInTheDocument()
  })

  it("'Cancelar' vuelve al banco", async () => {
    const user = userEvent.setup()
    renderNuevaPreguntaTipo()

    await user.click(screen.getByText("Cancelar"))

    expect(await screen.findByText("Banco")).toBeInTheDocument()
  })
})
