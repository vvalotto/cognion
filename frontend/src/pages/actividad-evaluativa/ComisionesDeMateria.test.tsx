import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ComisionesDeMateria } from "@/pages/actividad-evaluativa/ComisionesDeMateria"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderComisionesDeMateria(materiaId = "m1") {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/materias/${materiaId}/comisiones`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/materias/:materiaId/comisiones"
          element={<ComisionesDeMateria />}
        />
        <Route
          path="/actividad-evaluativa/comisiones/:comisionId"
          element={<p>Detalle de la comisión</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("ComisionesDeMateria", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("lista las comisiones de la materia con su horario", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(
        jsonResponse(200, [{ id: "c1", horario: "Lunes 18-20hs", docentes_asignados: ["d1"] }]),
      )

    renderComisionesDeMateria()

    expect(await screen.findByText("Lunes 18-20hs")).toBeInTheDocument()
  })

  it("muestra el estado vacío cuando la materia no tiene comisiones", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderComisionesDeMateria()

    expect(
      await screen.findByText("Todavía no hay comisiones creadas para esta materia."),
    ).toBeInTheDocument()
  })

  it("navega al detalle de la comisión al hacer clic", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(
        jsonResponse(200, [{ id: "c1", horario: "Lunes 18-20hs", docentes_asignados: [] }]),
      )

    renderComisionesDeMateria()
    const tarjeta = await screen.findByText("Lunes 18-20hs")

    const user = userEvent.setup()
    await user.click(tarjeta)

    expect(await screen.findByText("Detalle de la comisión")).toBeInTheDocument()
  })
})
