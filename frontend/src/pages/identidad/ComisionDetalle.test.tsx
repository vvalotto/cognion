import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { fetchConMaterias, llamadasSinMaterias } from "@/test/fetch-con-materias"

import { ComisionDetalle } from "@/pages/identidad/ComisionDetalle"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderComisionDetalle(comisionId = "c1") {
  return render(
    <MemoryRouter initialEntries={[`/comisiones/${comisionId}`]}>
      <Routes>
        <Route path="/comisiones/:comisionId" element={<ComisionDetalle />} />
        <Route path="/materias/:materiaId/ver" element={<p>Detalle de materia</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

const comisionSinDocente = {
  id: "c1",
  materia_id: "m1",
  horario: "Lunes 18-20hs",
  administrador_id: "a1",
  docentes_asignados: [],
}

const comisionConDocente = {
  ...comisionSinDocente,
  docentes_asignados: ["d1"],
}

const docentes = {
  cuentas: [{ id: "d1", nombre: "Juan Pérez", email: "juan@x.com", perfil: "docente", bloqueada: false }],
  total: 1,
}

describe("ComisionDetalle", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra la alerta de 'sin docente asignado' cuando la comisión no tiene ninguno", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionSinDocente),
      jsonResponse(200, docentes),
      jsonResponse(200, []),
    ])

    renderComisionDetalle()

    expect(
      await screen.findByText(/no puede generar link de invitación/),
    ).toBeInTheDocument()
    expect(screen.getByText("Sin docente asignado")).toBeInTheDocument()
  })

  it("no muestra la alerta cuando ya hay un docente asignado", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionConDocente),
      jsonResponse(200, docentes),
      jsonResponse(200, []),
    ])

    renderComisionDetalle()

    expect(await screen.findByText("Juan Pérez")).toBeInTheDocument()
    expect(screen.queryByText(/no puede generar link de invitación/)).not.toBeInTheDocument()
  })

  it("asigna un docente y actualiza la vista sin recargar", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionSinDocente),
      jsonResponse(200, docentes),
      jsonResponse(200, []),
      jsonResponse(200, comisionConDocente),
    ])

    renderComisionDetalle()
    await screen.findByText("Sin docente asignado")

    const user = userEvent.setup()
    await user.selectOptions(screen.getByLabelText("Asignar Docente"), "d1")
    await user.click(screen.getByRole("button", { name: "Asignar" }))

    expect(await screen.findByText("Juan Pérez")).toBeInTheDocument()
    expect(screen.queryByText("Sin docente asignado")).not.toBeInTheDocument()
    const [url, init] = llamadasSinMaterias()[3]
    expect(String(url)).toContain("/comisiones/c1/docentes")
    expect(JSON.parse(init?.body as string)).toEqual({ docente_id: "d1" })
  })

  it("muestra el estado vacío de estudiantes", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionSinDocente),
      jsonResponse(200, docentes),
      jsonResponse(200, []),
    ])

    renderComisionDetalle()

    expect(
      await screen.findByText("Esta comisión todavía no tiene estudiantes inscriptos."),
    ).toBeInTheDocument()
  })

  it("lista los estudiantes inscriptos", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionSinDocente),
      jsonResponse(200, docentes),
      jsonResponse(200, [{ id: "e1", nombre: "Ana Gómez" }]),
    ])

    renderComisionDetalle()

    expect(await screen.findByText("Ana Gómez")).toBeInTheDocument()
  })

  it("el botón 'Volver a la materia' navega al detalle de la materia", async () => {
    fetchConMaterias([
      jsonResponse(200, comisionSinDocente),
      jsonResponse(200, docentes),
      jsonResponse(200, []),
    ])

    renderComisionDetalle()
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Lunes 18-20hs" })).toBeInTheDocument(),
    )

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "‹ Volver a la materia" }))

    expect(await screen.findByText("Detalle de materia")).toBeInTheDocument()
  })
})
