import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { MisActividades } from "@/pages/actividad-evaluativa/MisActividades"

const MATERIA_ID = "m1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function actividadVisible(estado: string, evaluacionId: string | null = null) {
  return {
    id: "act-1",
    materia_id: MATERIA_ID,
    titulo: "Parcial 1",
    fecha_apertura: "2026-08-01T00:00:00+00:00",
    fecha_cierre: "2026-09-01T00:00:00+00:00",
    estado,
    evaluacion_id: evaluacionId,
  }
}

function mockMateriaYActividades(actividades: unknown[]) {
  vi.mocked(fetch)
    .mockResolvedValueOnce(
      jsonResponse(200, [{ id: MATERIA_ID, nombre: "Ingeniería de Software" }]),
    )
    .mockResolvedValueOnce(jsonResponse(200, actividades))
}

function renderMisActividades() {
  return render(
    <MemoryRouter initialEntries={[`/mis-actividades/materias/${MATERIA_ID}/actividades`]}>
      <Routes>
        <Route
          path="/mis-actividades/materias/:materiaId/actividades"
          element={<MisActividades />}
        />
        <Route path="/mis-actividades/:actividadId/fuera-de-periodo" element={<p>Fuera de período</p>} />
        <Route path="/mis-actividades/actividades/:actividadId/rendir" element={<p>Rendir</p>} />
        <Route
          path="/mis-actividades/evaluaciones/:evaluacionId/revision"
          element={<p>Revisión</p>}
        />
        <Route path="/mis-sesiones-en-vivo/:sesionId" element={<p>Mi sesión en vivo</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("MisActividades", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra el Badge 'Pendiente de responder' y navega a rendir", async () => {
    mockMateriaYActividades([actividadVisible("pendiente")])
    renderMisActividades()

    const badge = await screen.findByText("Pendiente de responder")
    expect(badge).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(screen.getByText("Parcial 1"))

    expect(await screen.findByText("Rendir")).toBeInTheDocument()
  })

  it("muestra el Badge 'Todavía no abrió' y navega a fuera de período", async () => {
    mockMateriaYActividades([actividadVisible("todavia_no_abrio")])
    renderMisActividades()

    expect(await screen.findByText("Todavía no abrió")).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(screen.getByText("Parcial 1"))

    expect(await screen.findByText("Fuera de período")).toBeInTheDocument()
  })

  it("muestra el Badge 'Finalizada — ver revisión' y navega a la revisión", async () => {
    mockMateriaYActividades([actividadVisible("finalizada", "eval-1")])
    renderMisActividades()

    expect(await screen.findByText("Finalizada — ver revisión")).toBeInTheDocument()

    const user = userEvent.setup()
    await user.click(screen.getByText("Parcial 1"))

    expect(await screen.findByText("Revisión")).toBeInTheDocument()
  })

  it("muestra mensaje de listado vacío cuando la materia no tiene actividades", async () => {
    mockMateriaYActividades([])
    renderMisActividades()

    expect(
      await screen.findByText("Todavía no hay actividades disponibles para esta materia."),
    ).toBeInTheDocument()
  })
})

function sesionApi(id: string, estado: string, materiaId = MATERIA_ID) {
  return {
    id,
    comision_id: "c1",
    materia_id: materiaId,
    materia_nombre: materiaId === MATERIA_ID ? "Ingeniería de Software" : "Gestión de Proyectos",
    cantidad_preguntas: 10,
    tiempo_limite_por_pregunta_segundos: 20,
    estado,
    unidad_tematica: null,
    tema: null,
    creada_en: "2026-09-24T10:00:00+00:00",
  }
}

/** Responde por URL: el orden de los pedidos no importa y el listado de sesiones se puede cambiar. */
function mockPorUrl(estado: { sesiones: unknown[]; unirse?: Response }) {
  vi.mocked(fetch).mockImplementation(async (input, init) => {
    const url = String(input)
    if (url.includes("/unirse") && (init as RequestInit)?.method === "POST") {
      return estado.unirse ?? jsonResponse(200, { sesion_id: "s1", estudiante_id: "e1", unido_en: "x" })
    }
    if (url.includes("/sesiones-en-vivo")) return jsonResponse(200, estado.sesiones)
    if (url.includes("actividades")) return jsonResponse(200, [])
    return jsonResponse(200, [{ id: MATERIA_ID, nombre: "Ingeniería de Software" }])
  })
}

function llamadasA(fragmento: string) {
  return vi.mocked(fetch).mock.calls.filter(([url]) => String(url).includes(fragmento))
}

describe("MisActividades — sesiones en vivo (US-6.3.8)", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra la sesión de la materia junto a las actividades, con su Badge", async () => {
    mockPorUrl({ sesiones: [sesionApi("s1", "en_espera")] })

    renderMisActividades()

    const tarjeta = await screen.findByRole("button", { name: /Ingeniería de Software/ })
    expect(tarjeta).toHaveTextContent("10 preguntas")
    expect(tarjeta).toHaveTextContent("En espera")
    expect(screen.getByRole("heading", { name: "Sesiones en vivo" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Actividades de período abierto" })).toBeInTheDocument()
    // El Estudiante no manda comision_id: el backend resuelve su Comisión.
    expect(String(llamadasA("/sesiones-en-vivo")[0][0])).not.toContain("comision_id")
  })

  it("no muestra sesiones de otra materia ni finalizadas", async () => {
    mockPorUrl({
      sesiones: [sesionApi("s2", "en_espera", "otra"), sesionApi("s3", "finalizada")],
    })

    renderMisActividades()

    expect(await screen.findByText("Por ahora no hay sesiones en vivo.")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /Gestión de Proyectos/ })).not.toBeInTheDocument()
  })

  it("una sesión en curso lleva el Badge 'En curso'", async () => {
    mockPorUrl({ sesiones: [sesionApi("s1", "en_curso")] })

    renderMisActividades()

    expect(await screen.findByRole("button", { name: /Ingeniería de Software/ })).toHaveTextContent(
      "En curso",
    )
  })

  it("el listado se refresca solo cada 10 segundos y deja de hacerlo al salir", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] })
    const estado = { sesiones: [] as unknown[] }
    mockPorUrl(estado)

    const { unmount } = renderMisActividades()
    await screen.findByText("Por ahora no hay sesiones en vivo.")

    estado.sesiones = [sesionApi("s1", "en_espera")]
    await act(async () => {
      vi.advanceTimersByTime(10_000)
    })
    expect(await screen.findByRole("button", { name: /Ingeniería de Software/ })).toBeInTheDocument()

    const pedidos = llamadasA("/sesiones-en-vivo").length
    unmount()
    await act(async () => {
      vi.advanceTimersByTime(30_000)
    })
    expect(llamadasA("/sesiones-en-vivo")).toHaveLength(pedidos)
  })

  it("con la pestaña oculta no pide la lista", async () => {
    vi.useFakeTimers({ toFake: ["setInterval", "clearInterval"] })
    mockPorUrl({ sesiones: [] })
    renderMisActividades()
    await screen.findByText("Por ahora no hay sesiones en vivo.")
    const pedidos = llamadasA("/sesiones-en-vivo").length

    const visibilidad = vi.spyOn(document, "visibilityState", "get").mockReturnValue("hidden")
    await act(async () => {
      vi.advanceTimersByTime(10_000)
    })
    expect(llamadasA("/sesiones-en-vivo")).toHaveLength(pedidos)
    visibilidad.mockRestore()
  })

  it("tocar la tarjeta une al Estudiante (una sola vez aunque toque dos) y abre su sesión", async () => {
    mockPorUrl({ sesiones: [sesionApi("s1", "en_espera")] })

    renderMisActividades()
    const tarjeta = await screen.findByRole("button", { name: /Ingeniería de Software/ })
    fireEvent.click(tarjeta)
    fireEvent.click(tarjeta)

    expect(await screen.findByText("Mi sesión en vivo")).toBeInTheDocument()
    expect(llamadasA("/sesiones-en-vivo/s1/unirse")).toHaveLength(1)
  })

  it("una sesión ya finalizada (422) muestra el mensaje y refresca la lista", async () => {
    const estado = {
      sesiones: [sesionApi("s1", "en_espera")] as unknown[],
      unirse: jsonResponse(422, { detail: "SesionYaFinalizada" }),
    }
    mockPorUrl(estado)

    renderMisActividades()
    const tarjeta = await screen.findByRole("button", { name: /Ingeniería de Software/ })
    estado.sesiones = []
    fireEvent.click(tarjeta)

    expect(await screen.findByRole("alert")).toHaveTextContent("Esa sesión ya no está disponible.")
    expect(await screen.findByText("Por ahora no hay sesiones en vivo.")).toBeInTheDocument()
  })

  it("una sesión que no existe (404) muestra el mismo mensaje", async () => {
    mockPorUrl({
      sesiones: [sesionApi("s1", "en_espera")],
      unirse: jsonResponse(404, { detail: "SesionNoEncontrada" }),
    })

    renderMisActividades()
    fireEvent.click(await screen.findByRole("button", { name: /Ingeniería de Software/ }))

    expect(await screen.findByRole("alert")).toHaveTextContent("Esa sesión ya no está disponible.")
  })

  it("un error inesperado al unirse avisa y deja reintentar", async () => {
    mockPorUrl({
      sesiones: [sesionApi("s1", "en_espera")],
      unirse: jsonResponse(500, { detail: "boom" }),
    })

    renderMisActividades()
    fireEvent.click(await screen.findByRole("button", { name: /Ingeniería de Software/ }))

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo unir")
    await waitFor(() => expect(llamadasA("/unirse")).toHaveLength(1))
  })
})

