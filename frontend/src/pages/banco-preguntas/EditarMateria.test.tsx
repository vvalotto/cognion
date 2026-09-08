import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EditarMateria } from "@/pages/banco-preguntas/EditarMateria"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const materiasApi = [
  { id: "m1", nombre: "Ges", banco_id: "b1", cantidad_preguntas_activas: 0 },
  { id: "m2", nombre: "Ingeniería de Software", banco_id: "b2", cantidad_preguntas_activas: 0 },
]

function renderEditarMateria() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/editar"]}>
      <Routes>
        <Route path="/materias/:materiaId/editar" element={<EditarMateria />} />
        <Route path="/materias" element={<p>Materias listado</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EditarMateria", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("precarga el nombre actual de la materia", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasApi))

    renderEditarMateria()

    expect(await screen.findByLabelText("Nombre de la materia")).toHaveValue("Ges")
  })

  it("guarda el nombre corregido y vuelve al listado", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiasApi))
      .mockResolvedValueOnce(jsonResponse(200, { id: "m1", nombre: "Gestión de Proyectos" }))
    const user = userEvent.setup()

    renderEditarMateria()
    await screen.findByLabelText("Nombre de la materia")

    await user.clear(screen.getByLabelText("Nombre de la materia"))
    await user.type(screen.getByLabelText("Nombre de la materia"), "Gestión de Proyectos")
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }))

    expect(await screen.findByText("Materias listado")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/materias\/m1$/)
    expect(ultimaLlamada?.[1]?.method).toBe("PATCH")
  })

  it("muestra un error si el nombre ya pertenece a otra materia (409)", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiasApi))
      .mockResolvedValueOnce(jsonResponse(409, { detail: "La materia 'Ingeniería de Software' ya existe." }))
    const user = userEvent.setup()

    renderEditarMateria()
    await screen.findByLabelText("Nombre de la materia")

    await user.clear(screen.getByLabelText("Nombre de la materia"))
    await user.type(screen.getByLabelText("Nombre de la materia"), "Ingeniería de Software")
    await user.click(screen.getByRole("button", { name: "Guardar cambios" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/ya existe otra materia/i)
  })

  it("cancelar vuelve al listado sin ejecutar ningún cambio", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasApi))
    const user = userEvent.setup()

    renderEditarMateria()
    await screen.findByLabelText("Nombre de la materia")

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Materias listado")).toBeInTheDocument()
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })
})
