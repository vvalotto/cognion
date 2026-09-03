import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { NuevaMateria } from "@/pages/banco-preguntas/NuevaMateria"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderNuevaMateria() {
  return render(
    <MemoryRouter initialEntries={["/materias/nueva"]}>
      <Routes>
        <Route path="/materias/nueva" element={<NuevaMateria />} />
        <Route path="/materias" element={<p>Materias listado</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

async function completarFormulario(nombre: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText("Nombre de la materia"), nombre)
  await user.click(screen.getByRole("button", { name: "Crear materia" }))
}

describe("NuevaMateria", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("alta exitosa crea la materia y vuelve al listado", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1" }),
    )

    renderNuevaMateria()
    await completarFormulario("Ingeniería de Software")

    expect(await screen.findByText("Materias listado")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/materias"),
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("nombre duplicado (409) muestra error inline sin navegar", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(409, { detail: "Ya existe una materia con ese nombre." }),
    )

    renderNuevaMateria()
    await completarFormulario("Ingeniería de Software")

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ya existe una materia con ese nombre.",
    )
    expect(screen.getByLabelText("Nombre de la materia")).toHaveValue("Ingeniería de Software")
  })

  it("cancelar vuelve al listado sin llamar al backend", async () => {
    renderNuevaMateria()
    const user = userEvent.setup()

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Materias listado")).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalled()
  })
})
