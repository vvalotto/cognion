import { cleanup, render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { MateriasActividades } from "@/pages/actividad-evaluativa/MateriasActividades"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderMateriasActividades() {
  return render(
    <MemoryRouter initialEntries={["/actividad-evaluativa/materias"]}>
      <Routes>
        <Route path="/actividad-evaluativa/materias" element={<MateriasActividades />} />
        <Route
          path="/actividad-evaluativa/materias/:materiaId/actividades"
          element={<p>Actividades de la materia</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("MateriasActividades", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("lista las materias en una tabla", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [
        { id: "m1", nombre: "Ingeniería de Software" },
        { id: "m2", nombre: "Gestión de Proyectos" },
      ]),
    )

    renderMateriasActividades()

    expect(await screen.findByText("Ingeniería de Software")).toBeInTheDocument()
    expect(screen.getByText("Gestión de Proyectos")).toBeInTheDocument()
    expect(screen.getByRole("table")).toBeInTheDocument()
  })

  it("muestra el estado vacío sin materias", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

    renderMateriasActividades()

    expect(await screen.findByText("Todavía no hay materias creadas.")).toBeInTheDocument()
  })

  it("una fila navega a las actividades de esa materia", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]),
      )
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))
    const user = userEvent.setup()

    renderMateriasActividades()
    await user.click(await screen.findByText("Ingeniería de Software"))

    expect(await screen.findByText("Actividades de la materia")).toBeInTheDocument()
  })

  it("muestra cantidad de comisiones y actividades por estado", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(
        jsonResponse(200, [{ id: "m1", nombre: "Ingeniería de Software" }]),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "c1", horario: "Martes 10 a 13", docentes_asignados: [] },
          { id: "c2", horario: "Jueves 18 a 21", docentes_asignados: [] },
        ]),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, [
          { id: "a1", materia_id: "m1", titulo: "P1", fecha_apertura: "2026-08-01T00:00:00Z", fecha_cierre: "2026-09-01T00:00:00Z", cantidad_preguntas: 10, cantidad_intentos_permitidos: 1, estado: "en_curso", cerrada_manualmente: false, cantidad_evaluaciones_activas: 0, cantidad_evaluaciones_finalizadas: 0, comisiones_ids: [] },
          { id: "a2", materia_id: "m1", titulo: "P2", fecha_apertura: "2026-10-01T00:00:00Z", fecha_cierre: "2026-11-01T00:00:00Z", cantidad_preguntas: 10, cantidad_intentos_permitidos: 1, estado: "programada", cerrada_manualmente: false, cantidad_evaluaciones_activas: 0, cantidad_evaluaciones_finalizadas: 0, comisiones_ids: [] },
          { id: "a3", materia_id: "m1", titulo: "P3", fecha_apertura: "2026-01-01T00:00:00Z", fecha_cierre: "2026-02-01T00:00:00Z", cantidad_preguntas: 10, cantidad_intentos_permitidos: 1, estado: "cerrada", cerrada_manualmente: true, cantidad_evaluaciones_activas: 0, cantidad_evaluaciones_finalizadas: 0, comisiones_ids: [] },
        ]),
      )

    renderMateriasActividades()
    await screen.findByText("Ingeniería de Software")

    const fila = await screen.findByRole("row", { name: /Ingeniería de Software/ })
    const celdas = within(fila).getAllByRole("cell")
    expect(celdas[1]).toHaveTextContent("2") // comisiones
    expect(celdas[2]).toHaveTextContent("1") // en curso
    expect(celdas[3]).toHaveTextContent("1") // planificadas
    expect(celdas[4]).toHaveTextContent("3") // totales
  })
})
