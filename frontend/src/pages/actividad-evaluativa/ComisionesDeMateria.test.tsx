import { cleanup, render, screen, within } from "@testing-library/react"
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
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))

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
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderComisionesDeMateria()
    const tarjeta = await screen.findByText("Lunes 18-20hs")

    const user = userEvent.setup()
    await user.click(tarjeta)

    expect(await screen.findByText("Detalle de la comisión")).toBeInTheDocument()
  })

  it("muestra cantidad de alumnos y actividades en curso/planificadas que aplican a la comisión", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "c1", horario: "Lunes 18-20hs", docentes_asignados: [] },
          { id: "c2", horario: "Martes 10-13hs", docentes_asignados: [] },
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "a1", materia_id: "m1", titulo: "Sin restricción", fecha_apertura: "2026-08-01T00:00:00Z", fecha_cierre: "2026-09-01T00:00:00Z", cantidad_preguntas: 10, cantidad_intentos_permitidos: 1, estado: "en_curso", cerrada_manualmente: false, cantidad_evaluaciones_activas: 0, cantidad_evaluaciones_finalizadas: 0, comisiones_ids: [] },
          { id: "a2", materia_id: "m1", titulo: "Solo c1", fecha_apertura: "2026-10-01T00:00:00Z", fecha_cierre: "2026-11-01T00:00:00Z", cantidad_preguntas: 10, cantidad_intentos_permitidos: 1, estado: "programada", cerrada_manualmente: false, cantidad_evaluaciones_activas: 0, cantidad_evaluaciones_finalizadas: 0, comisiones_ids: ["c1"] },
        ]),
      )
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "e1" }, { id: "e2" }]))
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "e3" }]))

    renderComisionesDeMateria()
    await screen.findByText("Lunes 18-20hs")

    const filaC1 = await screen.findByRole("row", { name: /Lunes 18-20hs/ })
    const celdasC1 = within(filaC1).getAllByRole("cell")
    expect(celdasC1[1]).toHaveTextContent("2") // alumnos
    expect(celdasC1[2]).toHaveTextContent("1") // en curso (sin restricción, aplica)
    expect(celdasC1[3]).toHaveTextContent("1") // planificadas (restringida a c1, aplica)

    const filaC2 = screen.getByRole("row", { name: /Martes 10-13hs/ })
    const celdasC2 = within(filaC2).getAllByRole("cell")
    expect(celdasC2[1]).toHaveTextContent("1") // alumnos
    expect(celdasC2[2]).toHaveTextContent("1") // en curso (sin restricción, aplica)
    expect(celdasC2[3]).toHaveTextContent("0") // planificadas (restringida a c1, no aplica)
  })
})
