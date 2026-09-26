import { cleanup, fireEvent, render, screen, within } from "@testing-library/react"
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
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 107, activa: true },
]

const comisionesResponse = [
  { id: "c1", horario: "Comision 1 - Martes de 10 a 13:30", docentes_asignados: ["d1"], activa: true },
  { id: "c2", horario: "Jueves - 9:00 a 11:00", docentes_asignados: [], activa: false },
]

const cuentasResponse = {
  cuentas: [{ id: "d1", nombre: "Victor Valotto", email: "v@f.edu.ar", rol: "docente", estado: "activa" }],
  total: 1,
}

/** Responde por URL: materia, comisiones, estudiantes y docentes se piden en paralelo. */
function mockPorUrl(comisiones: unknown[]) {
  vi.mocked(fetch).mockImplementation(async (input) => {
    const url = String(input)
    if (url.includes("/comisiones/c1/estudiantes")) return jsonResponse(200, new Array(17).fill({}))
    if (url.includes("/estudiantes")) return jsonResponse(200, [])
    if (url.includes("/comisiones")) return jsonResponse(200, comisiones)
    if (url.includes("/usuarios")) return jsonResponse(200, cuentasResponse)
    return jsonResponse(200, materiasResponse)
  })
}

function renderVerMateria() {
  return render(
    <MemoryRouter initialEntries={["/materias/m1/ver"]}>
      <Routes>
        <Route path="/materias/:materiaId/ver" element={<VerMateria />} />
        <Route path="/comisiones/:comisionId" element={<p>Detalle de comisión</p>} />
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

  it("muestra el nombre con su estado y el resumen de la materia, sin acciones de edición", async () => {
    mockPorUrl(comisionesResponse)

    renderVerMateria()

    expect(await screen.findByRole("heading", { name: "Ingeniería de Software" })).toBeInTheDocument()
    expect(screen.getAllByText("Activa").length).toBeGreaterThan(0)
    expect(screen.getByText("107")).toBeInTheDocument()
    expect(await screen.findByText("1 de 2")).toBeInTheDocument()
    expect(await screen.findByText("Comisiones activas")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /editar|eliminar/i })).not.toBeInTheDocument()
  })

  it("lista las comisiones con docentes, estudiantes y estado; activas e inactivas", async () => {
    mockPorUrl(comisionesResponse)

    renderVerMateria()

    const fila1 = (await screen.findByText("Comision 1 - Martes de 10 a 13:30")).closest("tr") as HTMLElement
    await within(fila1).findByText("Victor Valotto")
    expect(within(fila1).getByText("17")).toBeInTheDocument()
    expect(within(fila1).getByText("Activa")).toBeInTheDocument()

    const fila2 = screen.getByText("Jueves - 9:00 a 11:00").closest("tr") as HTMLElement
    expect(within(fila2).getByText("Sin docente asignado")).toBeInTheDocument()
    expect(within(fila2).getByText("Inactiva")).toBeInTheDocument()

    const pedido = vi.mocked(fetch).mock.calls.find(([u]) => String(u).includes("/m1/comisiones"))
    expect(String(pedido?.[0])).toContain("incluir_inactivas=true")
  })

  it("tocar una fila abre el detalle de la comisión", async () => {
    mockPorUrl(comisionesResponse)

    renderVerMateria()
    fireEvent.click(await screen.findByText("Comision 1 - Martes de 10 a 13:30"))

    expect(await screen.findByText("Detalle de comisión")).toBeInTheDocument()
  })

  it("el botón de ver detalle también navega", async () => {
    mockPorUrl(comisionesResponse)

    renderVerMateria()
    await screen.findByText("Jueves - 9:00 a 11:00")
    fireEvent.click(screen.getAllByRole("button", { name: "Ver detalle" })[1])

    expect(await screen.findByText("Detalle de comisión")).toBeInTheDocument()
  })

  it("sin comisiones lo dice", async () => {
    mockPorUrl([])

    renderVerMateria()

    expect(await screen.findByText("Esta materia todavía no tiene comisiones.")).toBeInTheDocument()
    expect(await screen.findByText("0 de 0")).toBeInTheDocument()
  })
})
