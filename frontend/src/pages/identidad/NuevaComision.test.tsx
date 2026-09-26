import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { fetchConMaterias, llamadasSinMaterias } from "@/test/fetch-con-materias"

import { NuevaComision } from "@/pages/identidad/NuevaComision"
import { setSession } from "@/lib/session"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

/** Arma un JWT con el payload dado — sin firma real, alcanza para testear el decode del cliente. */
function jwtFalso(payload: Record<string, unknown>): string {
  const base64url = (obj: unknown) =>
    btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
  return `${base64url({ alg: "HS256" })}.${base64url(payload)}.firma`
}

function renderNuevaComision(initialPath = "/comisiones/nueva") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route path="/comisiones/nueva" element={<NuevaComision />} />
        <Route path="/materias/:materiaId/ver" element={<p>Detalle de materia</p>} />
        <Route path="/comisiones/:comisionId" element={<p>Comisión detalle</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

const materias = [
  { id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 0 },
  { id: "m2", nombre: "Gestión de Proyectos", banco_id: "b2", cantidad_preguntas_activas: 0 },
]

describe("NuevaComision", () => {
  beforeEach(() => {
    setSession({
      token: jwtFalso({ sub: "admin-1", rol: "administrador" }),
      rol: "administrador",
    })
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("preselecciona la materia si llega con ?materiaId= y crea la comisión con éxito", async () => {
    // GET /materias (selector y breadcrumb) se responde por URL; el resto, en orden.
    fetchConMaterias([jsonResponse(201, { id: "c1" })], materias)

    renderNuevaComision("/comisiones/nueva?materiaId=m2")
    await waitFor(() =>
      expect(screen.getByLabelText("Materia")).toHaveValue("m2"),
    )

    const user = userEvent.setup()
    await user.type(screen.getByLabelText("Horario"), "Martes y Jueves 18-20hs")
    await user.click(screen.getByRole("button", { name: "Crear Comisión" }))

    expect(await screen.findByText("Comisión detalle")).toBeInTheDocument()
    const [, init] = llamadasSinMaterias()[0]
    expect(JSON.parse(init?.body as string)).toEqual({
      materia_id: "m2",
      horario: "Martes y Jueves 18-20hs",
      administrador_id: "admin-1",
    })
  })

  it("permite cambiar la materia seleccionada", async () => {
    fetchConMaterias([], materias)
    renderNuevaComision("/comisiones/nueva?materiaId=m1")
    await waitFor(() => expect(screen.getByLabelText("Materia")).toHaveValue("m1"))

    const user = userEvent.setup()
    await user.selectOptions(screen.getByLabelText("Materia"), "m2")

    expect(screen.getByLabelText("Materia")).toHaveValue("m2")
  })

  it("sin preselección, usa la primera materia del listado", async () => {
    fetchConMaterias([], materias)

    renderNuevaComision()

    await waitFor(() => expect(screen.getByLabelText("Materia")).toHaveValue("m1"))
  })

  it("cancelar vuelve al detalle de la materia sin crear nada", async () => {
    fetchConMaterias([], materias)
    renderNuevaComision("/comisiones/nueva?materiaId=m1")
    await waitFor(() => expect(screen.getByLabelText("Materia")).toHaveValue("m1"))

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Detalle de materia")).toBeInTheDocument()
    expect(llamadasSinMaterias()).toHaveLength(0)
  })

  it("el breadcrumb cuelga de la materia", async () => {
    fetchConMaterias([], materias)
    renderNuevaComision("/comisiones/nueva?materiaId=m2")

    expect(await screen.findByRole("link", { name: "Gestión de Proyectos" })).toHaveAttribute(
      "href",
      "/materias/m2/ver",
    )
  })
})
