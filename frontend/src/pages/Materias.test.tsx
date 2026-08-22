import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { Materias } from "@/pages/Materias"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderMaterias() {
  return render(
    <MemoryRouter initialEntries={["/materias"]}>
      <Routes>
        <Route path="/materias" element={<Materias />} />
        <Route path="/materias/nueva" element={<p>Nueva materia</p>} />
        <Route path="/materias/:materiaId/banco" element={<p>Banco de la materia</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("Materias", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("renderiza una tarjeta por materia con su cantidad de preguntas activas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [
        {
          id: "m1",
          nombre: "Ingeniería de Software",
          banco_id: "b1",
          cantidad_preguntas_activas: 3,
        },
        { id: "m2", nombre: "Gestión de Proyectos", banco_id: "b2", cantidad_preguntas_activas: 1 },
      ]),
    )

    renderMaterias()

    expect(await screen.findByText("Ingeniería de Software")).toBeInTheDocument()
    expect(screen.getByText("3 preguntas activas")).toBeInTheDocument()
    expect(screen.getByText("Gestión de Proyectos")).toBeInTheDocument()
    expect(screen.getByText("1 pregunta activa")).toBeInTheDocument()
  })

  it("[US-ADJ-01] muestra el breadcrumb y la tarjeta 'Nueva materia' con borde punteado", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

    renderMaterias()
    await screen.findByRole("button", { name: /nueva materia/i })

    expect(screen.getByText("Banco de preguntas")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Materias" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /nueva materia/i })).toHaveClass("border-dashed")
  })

  it("la tarjeta de una materia navega a su banco", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, [
        {
          id: "m1",
          nombre: "Ingeniería de Software",
          banco_id: "b1",
          cantidad_preguntas_activas: 0,
        },
      ]),
    )
    const user = userEvent.setup()

    renderMaterias()
    await user.click(await screen.findByText("Ingeniería de Software"))

    expect(await screen.findByText("Banco de la materia")).toBeInTheDocument()
  })

  it("la tarjeta 'Nueva materia' navega al formulario de alta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))
    const user = userEvent.setup()

    renderMaterias()
    await user.click(await screen.findByRole("button", { name: /nueva materia/i }))

    expect(await screen.findByText("Nueva materia")).toBeInTheDocument()
  })
})
