import { cleanup, render, screen, waitFor, within } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { CompletitudActividad } from "@/pages/analytics/CompletitudActividad"

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
    cantidad_evaluaciones_activas: 1,
    cantidad_evaluaciones_finalizadas: 1,
    comisiones_ids: [],
    unidad_tematica: null,
    tema: null,
    ...overrides,
  }
}

function materia() {
  return {
    id: MATERIA_ID,
    nombre: "Ingeniería de Software",
    banco_id: "banco-1",
    cantidad_preguntas_activas: 68,
  }
}

function comision(id: string, horario: string) {
  return { id, horario, docentes_asignados: [], activa: true }
}

function estudiante(id: string, nombre: string) {
  return { id, nombre }
}

function filaCompletitud(estudianteId: string, nombre: string, estado: string) {
  return { estudiante_id: estudianteId, nombre, estado }
}

function completitudBody(
  detalle: ReturnType<typeof filaCompletitud>[],
  resumen: Partial<Record<string, number>> = {},
) {
  return {
    detalle,
    resumen: {
      finalizadas: 0,
      en_curso: 0,
      suspendidas: 0,
      sin_iniciar: 0,
      ...resumen,
    },
  }
}

function mockObtenerActividad(overrides?: Partial<Record<string, unknown>>) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, actividadBody(overrides)))
}

function mockObtenerCompletitud(body: ReturnType<typeof completitudBody>) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, body))
}

function mockListarMaterias() {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, [materia()]))
}

function mockListarComisiones(comisiones: ReturnType<typeof comision>[]) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, comisiones))
}

function mockListarEstudiantes(estudiantes: ReturnType<typeof estudiante>[]) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estudiantes))
}

function renderPantalla() {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/actividades/${ACTIVIDAD_ID}/completitud`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/actividades/:actividadId/completitud"
          element={<CompletitudActividad />}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("CompletitudActividad", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("actividad restringida a una sola comisión: no muestra la columna Comisión", async () => {
    mockObtenerActividad()
    mockObtenerCompletitud(
      completitudBody(
        [
          filaCompletitud("e1", "María González", "finalizada"),
          filaCompletitud("e2", "Juan Pérez", "en_curso"),
        ],
        { finalizadas: 1, en_curso: 1 },
      ),
    )
    mockListarMaterias()
    mockListarComisiones([comision("c1", "Lunes 18-20hs")])
    mockListarEstudiantes([estudiante("e1", "María González"), estudiante("e2", "Juan Pérez")])

    renderPantalla()

    expect(
      await screen.findByRole("heading", { name: "Completitud de la actividad" }),
    ).toBeInTheDocument()
    expect(screen.getByText("María González")).toBeInTheDocument()
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(5))
    expect(screen.queryByText("Comisión")).not.toBeInTheDocument()
  })

  it("actividad sin restricción, con más de una comisión: muestra la columna Comisión", async () => {
    mockObtenerActividad()
    mockObtenerCompletitud(
      completitudBody(
        [
          filaCompletitud("e1", "María González", "finalizada"),
          filaCompletitud("e2", "Tomás Ríos", "sin_iniciar"),
        ],
        { finalizadas: 1, sin_iniciar: 1 },
      ),
    )
    mockListarMaterias()
    mockListarComisiones([comision("c1", "Lunes 18-20hs"), comision("c2", "Martes 18-20hs")])
    mockListarEstudiantes([estudiante("e1", "María González")])
    mockListarEstudiantes([estudiante("e2", "Tomás Ríos")])

    renderPantalla()

    await screen.findByRole("heading", { name: "Completitud de la actividad" })
    expect(await screen.findByText("Comisión")).toBeInTheDocument()
    expect(await screen.findByText("Lunes 18-20hs")).toBeInTheDocument()
    expect(screen.getByText("Martes 18-20hs")).toBeInTheDocument()
  })

  it("resumen y badges: 4 números coinciden con el detalle, cada estado con su propia variante", async () => {
    mockObtenerActividad()
    mockObtenerCompletitud(
      completitudBody(
        [
          filaCompletitud("e1", "Finalizada Uno", "finalizada"),
          filaCompletitud("e2", "En Curso Uno", "en_curso"),
          filaCompletitud("e3", "Suspendida Uno", "suspendida"),
          filaCompletitud("e4", "Sin Iniciar Uno", "sin_iniciar"),
        ],
        { finalizadas: 1, en_curso: 1, suspendidas: 1, sin_iniciar: 1 },
      ),
    )
    mockListarMaterias()
    mockListarComisiones([comision("c1", "Lunes 18-20hs")])
    mockListarEstudiantes([
      estudiante("e1", "Finalizada Uno"),
      estudiante("e2", "En Curso Uno"),
      estudiante("e3", "Suspendida Uno"),
      estudiante("e4", "Sin Iniciar Uno"),
    ])

    renderPantalla()

    await screen.findByRole("heading", { name: "Completitud de la actividad" })
    const filas = screen.getAllByRole("row").slice(1) // sin el header
    expect(within(filas[0]).getByText("Finalizada")).toBeInTheDocument()
    expect(within(filas[1]).getByText("En curso")).toBeInTheDocument()
    expect(within(filas[2]).getByText("Suspendida")).toBeInTheDocument()
    expect(within(filas[3]).getByText("Sin iniciar")).toBeInTheDocument()
  })

  it("error de red al cargar la completitud: muestra el mensaje de error", async () => {
    mockObtenerActividad()
    vi.mocked(fetch).mockRejectedValueOnce(new Error("network error"))
    mockListarMaterias()
    mockListarComisiones([])

    renderPantalla()

    expect(
      await screen.findByText(
        "No se pudo cargar la completitud de la actividad. Intentá de nuevo más tarde.",
      ),
    ).toBeInTheDocument()
  })
})
