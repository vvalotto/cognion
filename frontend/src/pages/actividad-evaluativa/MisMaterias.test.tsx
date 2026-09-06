import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { MisMaterias } from "@/pages/actividad-evaluativa/MisMaterias"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividadVisible(estado: string) {
  return {
    id: "act-1",
    materia_id: "m1",
    titulo: "Parcial 1",
    fecha_apertura: "2026-08-01T00:00:00+00:00",
    fecha_cierre: "2026-09-01T00:00:00+00:00",
    estado,
    evaluacion_id: null,
  }
}

function renderMisMaterias() {
  return render(
    <MemoryRouter initialEntries={["/mis-actividades/materias"]}>
      <Routes>
        <Route path="/mis-actividades/materias" element={<MisMaterias />} />
        <Route
          path="/mis-actividades/materias/:materiaId/actividades"
          element={<p>Actividades de la materia</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("MisMaterias", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra 'N pendiente' cuando la materia tiene actividades pendientes", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(jsonResponse(200, [actividadVisible("pendiente")]))

    renderMisMaterias()

    expect(await screen.findByText("Ingeniería de Software")).toBeInTheDocument()
    expect(screen.getByText("1 pendiente")).toBeInTheDocument()
  })

  it("muestra 'Sin actividades disponibles' cuando no hay pendientes", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Gestión de Proyectos" }]))
      .mockResolvedValueOnce(jsonResponse(200, [actividadVisible("finalizada")]))

    renderMisMaterias()

    expect(await screen.findByText("Sin actividades disponibles")).toBeInTheDocument()
  })

  it("navega al listado de actividades al hacer clic en una materia", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderMisMaterias()
    const tarjeta = await screen.findByText("Ingeniería de Software")

    const user = userEvent.setup()
    await user.click(tarjeta)

    expect(await screen.findByText("Actividades de la materia")).toBeInTheDocument()
  })
})
