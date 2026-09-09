import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { Actividades } from "@/pages/actividad-evaluativa/Actividades"

const MATERIA_ID = "materia-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividad(
  id: string,
  estado: "en_curso" | "programada" | "cerrada",
  overrides: Record<string, unknown> = {},
) {
  return {
    id,
    materia_id: MATERIA_ID,
    titulo: `Actividad ${id}`,
    fecha_apertura: "2026-08-01T00:00:00+00:00",
    fecha_cierre: "2026-09-01T00:00:00+00:00",
    cantidad_preguntas: 10,
    cantidad_intentos_permitidos: 1,
    estado,
    cerrada_manualmente: estado === "cerrada",
    cantidad_evaluaciones_activas: 0,
    cantidad_evaluaciones_finalizadas: 0,
    comisiones_ids: [],
    ...overrides,
  }
}

function comision(id: string, horario: string) {
  return { id, horario, docentes_asignados: [], activa: true }
}

function mockMateriaYActividades(
  actividades: unknown[],
  comisiones: ReturnType<typeof comision>[] = [],
  estudiantesPorComision: Record<string, number> = {},
) {
  vi.mocked(fetch)
    .mockResolvedValueOnce(
      jsonResponse(200, [
        {
          id: MATERIA_ID,
          nombre: "Ingeniería de Software",
          banco_id: "banco-1",
          cantidad_preguntas_activas: 68,
        },
      ]),
    )
    .mockResolvedValueOnce(jsonResponse(200, actividades))
    .mockResolvedValueOnce(jsonResponse(200, comisiones))
  for (const c of comisiones) {
    const cantidad = estudiantesPorComision[c.id] ?? 0
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, Array.from({ length: cantidad }, (_, i) => ({ id: `est-${c.id}-${i}` }))),
    )
  }
}

function renderActividades() {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/materias/${MATERIA_ID}/actividades`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/materias/:materiaId/actividades"
          element={<Actividades />}
        />
        <Route
          path="/actividad-evaluativa/actividades/:actividadId"
          element={<p>Detalle de actividad</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe("Actividades", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("por defecto muestra solo las actividades abiertas (en_curso/programada)", async () => {
    mockMateriaYActividades([
      actividad("act-en-curso", "en_curso"),
      actividad("act-programada", "programada"),
      actividad("act-cerrada", "cerrada"),
    ])

    renderActividades()

    expect(await screen.findByText("Actividad act-en-curso")).toBeInTheDocument()
    expect(screen.getByText("Actividad act-programada")).toBeInTheDocument()
    expect(screen.queryByText("Actividad act-cerrada")).not.toBeInTheDocument()
    expect(screen.getByText("2 actividades")).toBeInTheDocument()
  })

  it("cambiar el filtro a Cerradas muestra solo las cerradas", async () => {
    mockMateriaYActividades([
      actividad("act-en-curso", "en_curso"),
      actividad("act-cerrada", "cerrada"),
    ])
    const user = userEvent.setup()

    renderActividades()
    await screen.findByText("Actividad act-en-curso")

    await user.selectOptions(screen.getByLabelText("Estado"), "cerradas")

    expect(screen.queryByText("Actividad act-en-curso")).not.toBeInTheDocument()
    expect(screen.getByText("Actividad act-cerrada")).toBeInTheDocument()
  })

  it("el filtro Todas muestra abiertas y cerradas juntas", async () => {
    mockMateriaYActividades([
      actividad("act-en-curso", "en_curso"),
      actividad("act-cerrada", "cerrada"),
    ])
    const user = userEvent.setup()

    renderActividades()
    await screen.findByText("Actividad act-en-curso")

    await user.selectOptions(screen.getByLabelText("Estado"), "todas")

    expect(screen.getByText("Actividad act-en-curso")).toBeInTheDocument()
    expect(screen.getByText("Actividad act-cerrada")).toBeInTheDocument()
  })

  it("actividad sin comisiones marcadas muestra 'Todas' y suma los estudiantes de todas las comisiones", async () => {
    mockMateriaYActividades(
      [actividad("act-en-curso", "en_curso")],
      [comision("com-1", "Martes 10 a 13"), comision("com-2", "Jueves 18 a 21")],
      { "com-1": 5, "com-2": 3 },
    )

    renderActividades()

    expect(await screen.findByText("Todas")).toBeInTheDocument()
    expect(await screen.findByText("8")).toBeInTheDocument()
  })

  it("actividad restringida a una comisión muestra su horario y solo esos estudiantes", async () => {
    mockMateriaYActividades(
      [actividad("act-en-curso", "en_curso", { comisiones_ids: ["com-1"] })],
      [comision("com-1", "Martes 10 a 13"), comision("com-2", "Jueves 18 a 21")],
      { "com-1": 5, "com-2": 3 },
    )

    renderActividades()

    expect(await screen.findByText("Martes 10 a 13")).toBeInTheDocument()
    expect(await screen.findByText("5")).toBeInTheDocument()
  })

  it("una fila navega al detalle de esa actividad", async () => {
    mockMateriaYActividades([actividad("act-en-curso", "en_curso")])
    const user = userEvent.setup()

    renderActividades()
    await user.click(await screen.findByText("Actividad act-en-curso"))

    expect(await screen.findByText("Detalle de actividad")).toBeInTheDocument()
  })

  it("sin actividades creadas todavía muestra el mensaje correspondiente", async () => {
    mockMateriaYActividades([])

    renderActividades()

    expect(
      await screen.findByText("Todavía no hay actividades creadas para esta materia."),
    ).toBeInTheDocument()
  })

  it("con actividades pero ninguna del filtro elegido muestra el mensaje correspondiente", async () => {
    mockMateriaYActividades([actividad("act-en-curso", "en_curso")])
    const user = userEvent.setup()

    renderActividades()
    await screen.findByText("Actividad act-en-curso")

    await user.selectOptions(screen.getByLabelText("Estado"), "cerradas")

    expect(
      await screen.findByText("No hay actividades cerradas para esta materia."),
    ).toBeInTheDocument()
  })
})
