import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { EliminarMateria } from "@/pages/banco-preguntas/EliminarMateria"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const materiasResponse = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 0 },
]

function renderEliminarMateria() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/eliminar"]}>
      <Routes>
        <Route path="/materias/:materiaId/eliminar" element={<EliminarMateria />} />
        <Route path="/materias" element={<p>Materias listado</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("EliminarMateria", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el nombre de la materia a eliminar", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))

    renderEliminarMateria()

    expect(await screen.findByText("Ingeniería de Software")).toBeInTheDocument()
  })

  it("confirmar elimina y vuelve al listado de materias", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, materiasResponse))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    const user = userEvent.setup()

    renderEliminarMateria()
    await screen.findByText("Ingeniería de Software")

    await user.click(screen.getByRole("button", { name: "Sí, eliminar" }))

    expect(await screen.findByText("Materias listado")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/materias\/m1$/)
    expect(ultimaLlamada?.[1]?.method).toBe("DELETE")
  })

  it("cancelar vuelve al listado sin eliminar nada", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))
    const user = userEvent.setup()

    renderEliminarMateria()
    await screen.findByText("Ingeniería de Software")

    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Materias listado")).toBeInTheDocument()
    expect(vi.mocked(fetch)).toHaveBeenCalledTimes(1)
  })
})
