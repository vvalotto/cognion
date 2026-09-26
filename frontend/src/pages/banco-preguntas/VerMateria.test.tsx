import { cleanup, render, screen, within } from "@testing-library/react"
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

const comisionesResponse = [
  { id: "c1", horario: "Comision 1 - Martes de 10 a 13:30", docentes_asignados: ["d1"], activa: true },
  { id: "c2", horario: "Comision 2 - Jueves", docentes_asignados: [], activa: false },
]

/** Responde por URL: materias y comisiones se piden en paralelo. */
function mockPorUrl(comisiones: unknown[]) {
  vi.mocked(fetch).mockImplementation(async (input) =>
    String(input).includes("/comisiones")
      ? jsonResponse(200, comisiones)
      : jsonResponse(200, materiasResponse),
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
    mockPorUrl([])

    renderVerMateria()

    expect(await screen.findByRole("heading", { name: "Ingeniería de Software" })).toBeInTheDocument()
    expect(screen.getByText("3")).toBeInTheDocument()
    expect(screen.getByText("Activa")).toBeInTheDocument()
    expect(screen.queryByRole("button")).not.toBeInTheDocument()
  })

  it("lista las comisiones de la materia con su estado, docentes y link al detalle", async () => {
    mockPorUrl(comisionesResponse)

    renderVerMateria()

    const lista = await screen.findByRole("list", { name: "Comisiones de la materia" })
    const filas = within(lista).getAllByRole("listitem")
    expect(filas).toHaveLength(2)
    expect(within(filas[0]).getByRole("link", { name: "Comision 1 - Martes de 10 a 13:30" })).toHaveAttribute(
      "href",
      "/comisiones/c1",
    )
    expect(filas[0]).toHaveTextContent("1 docente")
    expect(filas[0]).toHaveTextContent("Activa")
    expect(filas[1]).toHaveTextContent("Sin docente asignado")
    expect(filas[1]).toHaveTextContent("Inactiva")
    expect(String(vi.mocked(fetch).mock.calls.find(([u]) => String(u).includes("/comisiones"))?.[0])).toContain(
      "incluir_inactivas=true",
    )
  })

  it("sin comisiones lo dice", async () => {
    mockPorUrl([])

    renderVerMateria()

    expect(await screen.findByText("Sin comisiones")).toBeInTheDocument()
  })
})
