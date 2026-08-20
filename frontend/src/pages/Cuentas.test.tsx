import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { Cuentas } from "@/pages/Cuentas"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const cuentasResponse = [
  { id: "u1", nombre: "Ana Docente", email: "ana@fiuner.edu.ar", perfil: "docente", bloqueada: false },
  {
    id: "u2",
    nombre: "Luis Estudiante",
    email: "luis@fiuner.edu.ar",
    perfil: "estudiante",
    bloqueada: true,
  },
]

function renderCuentas() {
  return render(
    <MemoryRouter initialEntries={["/cuentas"]}>
      <Routes>
        <Route path="/cuentas" element={<Cuentas />} />
        <Route path="/cuentas/:usuarioId" element={<p>Detalle de cuenta</p>} />
        <Route path="/docentes/nuevo" element={<p>Alta de docente</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("Cuentas", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra todas las cuentas sin filtros al entrar a la pantalla", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentasResponse))

    renderCuentas()

    expect(await screen.findByText("Ana Docente")).toBeInTheDocument()
    expect(screen.getByText("Luis Estudiante")).toBeInTheDocument()
  })

  it("filtrar por rol y estado consulta el backend con ambos filtros combinados", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, cuentasResponse))
      .mockResolvedValueOnce(jsonResponse(200, [cuentasResponse[1]]))
      .mockResolvedValueOnce(jsonResponse(200, [cuentasResponse[1]]))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.selectOptions(screen.getByLabelText("Rol"), "estudiante")
    await user.selectOptions(screen.getByLabelText("Estado"), "bloqueada")

    await screen.findByText("Luis Estudiante")
    expect(screen.queryByText("Ana Docente")).not.toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).toContain("rol=estudiante")
    expect(ultimaLlamada).toContain("estado=bloqueada")
  })

  it("una combinación de filtros sin resultados deja la tabla vacía sin mensaje de error", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, cuentasResponse))
      .mockResolvedValueOnce(jsonResponse(200, []))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.selectOptions(screen.getByLabelText("Rol"), "administrador")

    expect(await screen.findByText(/No hay cuentas/)).toBeInTheDocument()
    expect(screen.queryByText(/error/i)).not.toBeInTheDocument()
  })

  it("'Limpiar filtros' vuelve al listado sin filtros", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, cuentasResponse))
      .mockResolvedValueOnce(jsonResponse(200, [cuentasResponse[1]]))
      .mockResolvedValueOnce(jsonResponse(200, cuentasResponse))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")
    await user.selectOptions(screen.getByLabelText("Rol"), "estudiante")
    await screen.findByText("Luis Estudiante")

    await user.click(screen.getByText("Limpiar filtros"))

    await screen.findByText("Ana Docente")
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)?.[0] as string
    expect(ultimaLlamada).not.toContain("rol=")
  })

  it("hacer clic en una fila navega al detalle de esa cuenta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentasResponse))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.click(screen.getByText("Ana Docente"))

    expect(await screen.findByText("Detalle de cuenta")).toBeInTheDocument()
  })

  it("'+ Nueva cuenta' navega al alta de docente existente", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentasResponse))
    const user = userEvent.setup()

    renderCuentas()
    await screen.findByText("Ana Docente")

    await user.click(screen.getByText("+ Nueva cuenta"))

    expect(await screen.findByText("Alta de docente")).toBeInTheDocument()
  })
})
