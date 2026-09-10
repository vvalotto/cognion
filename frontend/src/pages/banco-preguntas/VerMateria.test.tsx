import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { VerMateria } from "@/pages/banco-preguntas/VerMateria"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const materiasResponse = [
  {
    id: "m1",
    nombre: "Ingeniería de Software",
    banco_id: "b1",
    cantidad_preguntas_activas: 3,
    activa: true,
  },
]

function renderVerMateria() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/ver"]}>
      <Routes>
        <Route path="/materias/:materiaId/ver" element={<VerMateria />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("VerMateria", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el nombre y la cantidad de preguntas activas, sin acciones de edición", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))

    renderVerMateria()

    expect(await screen.findByRole("heading", { name: "Ingeniería de Software" })).toBeInTheDocument()
    expect(screen.getByText("3")).toBeInTheDocument()
    expect(screen.getByText("Activa")).toBeInTheDocument()
    expect(screen.queryByRole("button")).not.toBeInTheDocument()
  })
})
