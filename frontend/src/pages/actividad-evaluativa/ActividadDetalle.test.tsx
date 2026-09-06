import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ActividadDetalle } from "@/pages/actividad-evaluativa/ActividadDetalle"

const ACTIVIDAD_ID = "act-1"
const MATERIA_ID = "materia-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividadBody(overrides?: Partial<Record<string, unknown>>) {
  return {
    id: ACTIVIDAD_ID,
    materia_id: MATERIA_ID,
    titulo: "Parcial 1",
    fecha_apertura: "2026-09-20T09:00:00",
    fecha_cierre: "2026-09-27T23:59:00",
    cantidad_preguntas: 10,
    cantidad_intentos_permitidos: 1,
    estado: "en_curso",
    cerrada_manualmente: false,
    cantidad_evaluaciones_activas: 3,
    cantidad_evaluaciones_finalizadas: 2,
    ...overrides,
  }
}

function mockObtenerActividad(overrides?: Partial<Record<string, unknown>>) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, actividadBody(overrides)))
}

function mockListarMaterias() {
  vi.mocked(fetch).mockResolvedValueOnce(
    jsonResponse(200, [
      {
        id: MATERIA_ID,
        nombre: "Ingeniería de Software",
        banco_id: "banco-1",
        cantidad_preguntas_activas: 68,
      },
    ]),
  )
}

function renderActividadDetalle() {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/actividades/${ACTIVIDAD_ID}`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/actividades/:actividadId"
          element={<ActividadDetalle />}
        />
        <Route
          path="/actividad-evaluativa/actividades/:actividadId/extender-plazo"
          element={<p>Extender plazo</p>}
        />
        <Route
          path="/actividad-evaluativa/actividades/:actividadId/cerrar"
          element={<p>Cerrar actividad</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("ActividadDetalle", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra apertura, cierre, preguntas, intentos y conteos de evaluaciones", async () => {
    mockObtenerActividad()
    mockListarMaterias()

    renderActividadDetalle()

    expect(await screen.findByRole("heading", { name: "Parcial 1" })).toBeInTheDocument()
    expect(screen.getByText("10")).toBeInTheDocument()
    expect(screen.getByText(/3\s*\(en curso o suspendidas\)/)).toBeInTheDocument()
    expect(screen.getByText("2")).toBeInTheDocument()
  })

  it("muestra las acciones de extender plazo y cerrar cuando no está cerrada manualmente", async () => {
    mockObtenerActividad()
    mockListarMaterias()

    renderActividadDetalle()

    expect(await screen.findByRole("button", { name: "Extender plazo" })).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: "Cerrar actividad ahora" }),
    ).toBeInTheDocument()
  })

  it("oculta las acciones cuando la actividad ya está cerrada manualmente", async () => {
    mockObtenerActividad({ estado: "cerrada", cerrada_manualmente: true })
    mockListarMaterias()

    renderActividadDetalle()

    expect(await screen.findByRole("heading", { name: "Parcial 1" })).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Extender plazo" })).not.toBeInTheDocument()
    expect(
      screen.queryByRole("button", { name: "Cerrar actividad ahora" }),
    ).not.toBeInTheDocument()
  })

  it("navega a extender plazo al hacer clic en la acción", async () => {
    mockObtenerActividad()
    mockListarMaterias()

    renderActividadDetalle()
    const user = userEvent.setup()
    await user.click(await screen.findByRole("button", { name: "Extender plazo" }))

    expect(await screen.findByText("Extender plazo")).toBeInTheDocument()
  })

  it("navega a cerrar actividad al hacer clic en la acción", async () => {
    mockObtenerActividad()
    mockListarMaterias()

    renderActividadDetalle()
    const user = userEvent.setup()
    await user.click(await screen.findByRole("button", { name: "Cerrar actividad ahora" }))

    expect(await screen.findByText("Cerrar actividad")).toBeInTheDocument()
  })
})
