import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { Materias } from "@/pages/banco-preguntas/Materias"
import { clearSession, setSession } from "@/lib/session"

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
        <Route path="/materias/:materiaId/editar" element={<p>Editar materia</p>} />
        <Route path="/materias/:materiaId/ver" element={<p>Ver materia</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

const materiasResponse = [
  {
    id: "m1",
    nombre: "Ingeniería de Software",
    banco_id: "b1",
    cantidad_preguntas_activas: 3,
    activa: true,
  },
  {
    id: "m2",
    nombre: "Gestión de Proyectos",
    banco_id: "b2",
    cantidad_preguntas_activas: 1,
    activa: true,
  },
]

describe("Materias", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    setSession({ token: "t", rol: "docente" })
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    clearSession()
    cleanup()
  })

  it("renderiza una fila por materia con su cantidad de preguntas activas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))

    renderMaterias()

    expect(await screen.findByText("Ingeniería de Software")).toBeInTheDocument()
    expect(screen.getByText("3")).toBeInTheDocument()
    expect(screen.getByText("Gestión de Proyectos")).toBeInTheDocument()
    expect(screen.getByText("1")).toBeInTheDocument()
  })

  it("sin materias muestra un mensaje en vez de una tabla vacía", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))

    renderMaterias()

    expect(await screen.findByText("Todavía no hay materias creadas.")).toBeInTheDocument()
  })

  it("Docente: hacer clic en una fila navega al banco de esa materia", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))
    const user = userEvent.setup()

    renderMaterias()
    await screen.findByText("Ingeniería de Software")

    await user.click(screen.getByText("Ingeniería de Software"))

    expect(await screen.findByText("Banco de la materia")).toBeInTheDocument()
  })

  it("Docente: el botón 'Ver banco' navega al banco sin duplicar la navegación de la fila", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))
    const user = userEvent.setup()

    renderMaterias()
    await screen.findByText("Ingeniería de Software")

    await user.click(screen.getAllByRole("button", { name: "Ver banco" })[0])

    expect(await screen.findByText("Banco de la materia")).toBeInTheDocument()
  })

  it("Administrador: la fila y el botón 'Ver' navegan al detalle de solo lectura, no al banco", async () => {
    setSession({ token: "t", rol: "administrador" })
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))
    const user = userEvent.setup()

    renderMaterias()
    await screen.findByText("Ingeniería de Software")

    expect(screen.queryByRole("button", { name: "Ver banco" })).not.toBeInTheDocument()
    await user.click(screen.getAllByRole("button", { name: "Ver" })[0])

    expect(await screen.findByText("Ver materia")).toBeInTheDocument()
  })

  it("el botón 'Editar' navega a la edición del nombre sin disparar la navegación de la fila", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, materiasResponse))
    const user = userEvent.setup()

    renderMaterias()
    await screen.findByText("Ingeniería de Software")

    await user.click(screen.getAllByRole("button", { name: "Editar" })[0])

    expect(await screen.findByText("Editar materia")).toBeInTheDocument()
  })

  it("una materia inactiva muestra 'Activar' en vez de 'Editar'/'Eliminar', y al activarla pasa a 'Activa'", async () => {
    const inactivaResponse = [
      { id: "m3", nombre: "Materia Retirada", banco_id: "b3", cantidad_preguntas_activas: 0, activa: false },
    ]
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, inactivaResponse))
      .mockResolvedValueOnce(jsonResponse(200, { id: "m3", nombre: "Materia Retirada", activa: true }))
    const user = userEvent.setup()

    renderMaterias()
    await screen.findByText("Materia Retirada")

    expect(screen.getByText("Inactiva")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Editar" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Eliminar" })).not.toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "Activar" }))

    expect(await screen.findByText("Activa")).toBeInTheDocument()
    const ultimaLlamada = vi.mocked(fetch).mock.calls.at(-1)
    expect(String(ultimaLlamada?.[0])).toMatch(/\/materias\/m3\/activar$/)
    expect(ultimaLlamada?.[1]?.method).toBe("POST")
  })

  it("'+ Nueva materia' navega al formulario de alta", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, []))
    const user = userEvent.setup()

    renderMaterias()
    await screen.findByText("Todavía no hay materias creadas.")

    await user.click(screen.getByText("+ Nueva materia"))

    expect(await screen.findByText("Nueva materia")).toBeInTheDocument()
  })
})
