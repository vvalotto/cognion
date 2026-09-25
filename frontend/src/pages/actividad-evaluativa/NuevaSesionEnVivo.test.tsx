import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { NuevaSesionEnVivo } from "@/pages/actividad-evaluativa/NuevaSesionEnVivo"
import { setSession } from "@/lib/session"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function errorResponse(status: number, detail: string): Response {
  return new Response(JSON.stringify({ detail }), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const comision = {
  id: "c1",
  materia_id: "m1",
  horario: "Lunes 18-20hs",
  administrador_id: "a1",
  docentes_asignados: ["d1"],
}

const materias = [{ id: "m1", nombre: "Ingeniería de Software", banco_id: "b1", cantidad_preguntas_activas: 10, activa: true }]

const preguntas = {
  preguntas: [
    { id: "p1", texto: "P1", tipo: "opcion_multiple", opciones: [], unidad_tematica: "U1", tema: "T1", dificultad: "medio", importancia: "medio", activa: true },
  ],
  total: 1,
}

function renderFormulario(comisionId = "c1") {
  return render(
    <MemoryRouter initialEntries={[`/sesiones-en-vivo/comisiones/${comisionId}/nueva`]}>
      <Routes>
        <Route
          path="/sesiones-en-vivo/comisiones/:comisionId/nueva"
          element={<NuevaSesionEnVivo />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("NuevaSesionEnVivo", () => {
  beforeEach(() => {
    setSession({ token: "t", rol: "docente" })
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el breadcrumb de la Comisión, sin selector de Comisión", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))
      .mockResolvedValueOnce(jsonResponse(200, preguntas))

    renderFormulario()

    expect(await screen.findByRole("heading", { name: "Nueva sesión en vivo" })).toBeInTheDocument()
    expect(screen.getAllByText(/Lunes 18-20hs/).length).toBeGreaterThan(0)
    expect(screen.queryByLabelText(/Comisión/)).not.toBeInTheDocument()
  })

  it("crea la sesión y navega a la sala de espera", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))
      .mockResolvedValueOnce(jsonResponse(200, preguntas))
      .mockResolvedValueOnce(
        jsonResponse(201, {
          id: "s1",
          comision_id: "c1",
          materia_id: "m1",
          unidad_tematica: null,
          tema: null,
          cantidad_preguntas: 5,
          tiempo_limite_por_pregunta_segundos: 20,
          estado: "EnEspera",
          pregunta_actual_indice: null,
        }),
      )

    renderFormulario()
    await screen.findByRole("heading", { name: "Nueva sesión en vivo" })

    const user = userEvent.setup()
    await user.clear(screen.getByLabelText("Cantidad de preguntas"))
    await user.type(screen.getByLabelText("Cantidad de preguntas"), "5")
    await user.clear(screen.getByLabelText("Tiempo límite por pregunta (segundos)"))
    await user.type(screen.getByLabelText("Tiempo límite por pregunta (segundos)"), "20")
    await user.click(screen.getByRole("button", { name: "Crear sesión" }))

    const [url, init] = vi.mocked(fetch).mock.calls[3]
    expect(String(url)).toContain("/sesiones-en-vivo")
    expect(JSON.parse(init?.body as string)).toEqual({
      comision_id: "c1",
      cantidad_preguntas: 5,
      tiempo_limite_por_pregunta_segundos: 20,
      unidad_tematica: null,
      tema: null,
    })
  })

  it("valida tiempo límite 0 en el cliente, sin enviar la request", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))
      .mockResolvedValueOnce(jsonResponse(200, preguntas))

    renderFormulario()
    await screen.findByRole("heading", { name: "Nueva sesión en vivo" })

    const user = userEvent.setup()
    await user.clear(screen.getByLabelText("Tiempo límite por pregunta (segundos)"))
    await user.type(screen.getByLabelText("Tiempo límite por pregunta (segundos)"), "0")
    const llamadasAntes = vi.mocked(fetch).mock.calls.length
    await user.click(screen.getByRole("button", { name: "Crear sesión" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/tiempo límite/i)
    expect(vi.mocked(fetch).mock.calls.length).toBe(llamadasAntes)
  })

  it("muestra el error del servidor (preguntas insuficientes) y permanece en el formulario", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, materias))
      .mockResolvedValueOnce(jsonResponse(200, preguntas))
      .mockResolvedValueOnce(errorResponse(422, "No hay suficientes preguntas activas en el banco"))

    renderFormulario()
    await screen.findByRole("heading", { name: "Nueva sesión en vivo" })

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Crear sesión" }))

    expect(await screen.findByText(/No hay suficientes preguntas/)).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Nueva sesión en vivo" })).toBeInTheDocument()
  })
})
