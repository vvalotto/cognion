import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { MisActividades } from "@/pages/MisActividades"

const MATERIA_ID = "m1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividadVisible(estado: string, evaluacionId: string | null = null) {
  return {
    id: "act-1",
    materia_id: MATERIA_ID,
    titulo: "Parcial 1",
    fecha_apertura: "2026-08-01T00:00:00+00:00",
    fecha_cierre: "2026-09-01T00:00:00+00:00",
    estado,
    evaluacion_id: evaluacionId,
  }
}

function mockMateriaYActividades(actividades: unknown[]) {
  vi.mocked(fetch)
    .mockResolvedValueOnce(
      jsonResponse(200, [{ id: MATERIA_ID, nombre: "Ingeniería de Software" }]),
    )
    .mockResolvedValueOnce(jsonResponse(200, actividades))
}

function renderMisActividades() {
  return render(
    <MemoryRouter initialEntries={[`/mis-actividades/materias/${MATERIA_ID}/actividades`]}>
      <Routes>
        <Route
          path="/mis-actividades/materias/:materiaId/actividades"
          element={<MisActividades />}
        />
        <Route path="/mis-actividades/:actividadId/fuera-de-periodo" element={<p>Fuera de período</p>} />
        <Route path="/mis-actividades/actividades/:actividadId/rendir" element={<p>Rendir</p>} />
        <Route
          path="/mis-actividades/evaluaciones/:evaluacionId/revision"
          element={<p>Revisión</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("MisActividades", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el Badge 'Pendiente de responder' y navega a rendir", async () => {
    mockMateriaYActividades([actividadVisible("pendiente")])
    renderMisActividades()

    const badge = await screen.findByText("Pendiente de responder")
    expect(badge).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(screen.getByText("Parcial 1"))

    expect(await screen.findByText("Rendir")).toBeInTheDocument()
  })

  it("muestra el Badge 'Todavía no abrió' y navega a fuera de período", async () => {
    mockMateriaYActividades([actividadVisible("todavia_no_abrio")])
    renderMisActividades()

    expect(await screen.findByText("Todavía no abrió")).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(screen.getByText("Parcial 1"))

    expect(await screen.findByText("Fuera de período")).toBeInTheDocument()
  })

  it("muestra el Badge 'Finalizada — ver revisión' y navega a la revisión", async () => {
    mockMateriaYActividades([actividadVisible("finalizada", "eval-1")])
    renderMisActividades()

    expect(await screen.findByText("Finalizada — ver revisión")).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(screen.getByText("Parcial 1"))

    expect(await screen.findByText("Revisión")).toBeInTheDocument()
  })

  it("muestra mensaje de listado vacío cuando la materia no tiene actividades", async () => {
    mockMateriaYActividades([])
    renderMisActividades()

    expect(
      await screen.findByText("Todavía no hay actividades disponibles para esta materia."),
    ).toBeInTheDocument()
  })
})
