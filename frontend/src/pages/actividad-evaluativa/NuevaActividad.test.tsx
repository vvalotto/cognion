import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { NuevaActividad } from "@/pages/actividad-evaluativa/NuevaActividad"

const MATERIA_ID = "materia-1"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function mockListarMaterias(cantidadPreguntasActivas = 68) {
  vi.mocked(fetch).mockResolvedValueOnce(
    jsonResponse(200, [
      {
        id: MATERIA_ID,
        nombre: "Ingeniería de Software",
        banco_id: "banco-1",
        cantidad_preguntas_activas: cantidadPreguntasActivas,
      },
    ]),
  )
}

function mockListarComisiones(comisiones: unknown[] = []) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, comisiones))
}

function pregunta(id: string, tema: string, unidadTematica = "Unidad 1") {
  return {
    id,
    texto: `Pregunta ${id}`,
    opciones: [{ texto: "a", es_correcta: true }, { texto: "b", es_correcta: false }],
    unidad_tematica: unidadTematica,
    tema,
    dificultad: "medio",
    importancia: "medio",
    activa: true,
  }
}

function mockFiltrarBanco(preguntas: unknown[] = []) {
  vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, { preguntas, total: preguntas.length }))
}

function renderNuevaActividad() {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/materias/${MATERIA_ID}/actividades/nueva`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/materias/:materiaId/actividades/nueva"
          element={<NuevaActividad />}
        />
        <Route
          path="/actividad-evaluativa/materias/:materiaId/actividades"
          element={<p>Actividades listado</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

async function completarFormulario(opciones?: {
  apertura?: string
  cierre?: string
  preguntas?: string
  intentos?: string
}) {
  const user = userEvent.setup()
  const apertura = opciones?.apertura ?? "2026-09-20T09:00"
  const cierre = opciones?.cierre ?? "2026-09-27T23:59"

  const inputApertura = screen.getByLabelText("Apertura (fecha y hora)")
  await user.clear(inputApertura)
  await user.type(inputApertura, apertura)

  const inputCierre = screen.getByLabelText("Cierre (fecha y hora)")
  await user.clear(inputCierre)
  await user.type(inputCierre, cierre)

  if (opciones?.preguntas !== undefined) {
    const inputPreguntas = screen.getByLabelText("Cantidad de preguntas")
    await user.clear(inputPreguntas)
    await user.type(inputPreguntas, opciones.preguntas)
  }

  if (opciones?.intentos !== undefined) {
    const inputIntentos = screen.getByLabelText("Intentos permitidos por pregunta")
    await user.clear(inputIntentos)
    await user.type(inputIntentos, opciones.intentos)
  }

  await user.click(screen.getByRole("button", { name: "Crear actividad" }))
}

describe("NuevaActividad", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("creación exitosa crea la actividad y vuelve al listado", async () => {
    mockListarMaterias()
    mockListarComisiones()
    mockFiltrarBanco()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "act-1",
        materia_id: MATERIA_ID,
        fecha_apertura: "2026-09-20T09:00:00",
        fecha_cierre: "2026-09-27T23:59:00",
        cantidad_preguntas: 10,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: false,
        titulo: "",
      }),
    )

    renderNuevaActividad()
    expect(await screen.findByLabelText("Apertura (fecha y hora)")).toBeInTheDocument()
    await completarFormulario({ preguntas: "10", intentos: "1" })

    expect(await screen.findByText("Actividades listado")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/actividades"),
      expect.objectContaining({ method: "POST" }),
    )
  })

  it("marcar una comisión la manda en comisiones_ids al crear", async () => {
    mockListarMaterias()
    mockListarComisiones([
      { id: "comision-1", horario: "Martes 10 a 13", docentes_asignados: [], activa: true },
      { id: "comision-2", horario: "Jueves 18 a 21", docentes_asignados: [], activa: true },
    ])
    mockFiltrarBanco()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "act-1",
        materia_id: MATERIA_ID,
        fecha_apertura: "2026-09-20T09:00:00",
        fecha_cierre: "2026-09-27T23:59:00",
        cantidad_preguntas: 10,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: false,
        titulo: "",
        comisiones_ids: ["comision-1"],
      }),
    )

    renderNuevaActividad()
    expect(await screen.findByLabelText("Martes 10 a 13")).toBeInTheDocument()
    const user = userEvent.setup()
    await user.click(screen.getByLabelText("Martes 10 a 13"))
    await completarFormulario({ preguntas: "10", intentos: "1" })

    expect(await screen.findByText("Actividades listado")).toBeInTheDocument()
    const [, opciones] = vi.mocked(fetch).mock.calls.find(([url]) =>
      String(url).includes("/actividades"),
    )!
    const body = JSON.parse(String((opciones as RequestInit).body))
    expect(body.comisiones_ids).toEqual(["comision-1"])
  })

  it("sin comisiones marcadas manda comisiones_ids vacío", async () => {
    mockListarMaterias()
    mockListarComisiones([
      { id: "comision-1", horario: "Martes 10 a 13", docentes_asignados: [], activa: true },
    ])
    mockFiltrarBanco()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "act-1",
        materia_id: MATERIA_ID,
        fecha_apertura: "2026-09-20T09:00:00",
        fecha_cierre: "2026-09-27T23:59:00",
        cantidad_preguntas: 10,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: false,
        titulo: "",
        comisiones_ids: [],
      }),
    )

    renderNuevaActividad()
    expect(await screen.findByLabelText("Martes 10 a 13")).toBeInTheDocument()
    await completarFormulario({ preguntas: "10", intentos: "1" })

    expect(await screen.findByText("Actividades listado")).toBeInTheDocument()
    const [, opciones] = vi.mocked(fetch).mock.calls.find(([url]) =>
      String(url).includes("/actividades"),
    )!
    const body = JSON.parse(String((opciones as RequestInit).body))
    expect(body.comisiones_ids).toEqual([])
  })

  it("rechazo de cliente por período inválido no llama al backend", async () => {
    mockListarMaterias()
    mockListarComisiones()
    mockFiltrarBanco()

    renderNuevaActividad()
    expect(await screen.findByLabelText("Apertura (fecha y hora)")).toBeInTheDocument()
    await completarFormulario({
      apertura: "2026-09-27T23:59",
      cierre: "2026-09-20T09:00",
      preguntas: "10",
      intentos: "1",
    })

    expect(
      await screen.findByText("La fecha de cierre debe ser posterior a la de apertura."),
    ).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(3)
  })

  it("rechazo del servidor por preguntas insuficientes muestra el error inline", async () => {
    mockListarMaterias()
    mockListarComisiones()
    mockFiltrarBanco()
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(422, { detail: "PreguntasInsuficientes: el banco no tiene suficientes." }),
    )

    renderNuevaActividad()
    expect(await screen.findByLabelText("Apertura (fecha y hora)")).toBeInTheDocument()
    await completarFormulario({ preguntas: "500", intentos: "1" })

    expect(
      await screen.findByText("PreguntasInsuficientes: el banco no tiene suficientes."),
    ).toBeInTheDocument()
  })

  it("muestra la cantidad de preguntas activas del banco como hint", async () => {
    mockListarMaterias()
    mockListarComisiones()
    mockFiltrarBanco([
      pregunta("p1", "Cohesión"),
      pregunta("p2", "Cohesión"),
      pregunta("p3", "Acoplamiento"),
    ])

    renderNuevaActividad()

    expect(await screen.findByText(/3 disponibles/)).toBeInTheDocument()
  })

  it("elegir un tema restringe la cantidad disponible y lo manda en el body", async () => {
    mockListarMaterias()
    mockListarComisiones()
    mockFiltrarBanco([
      pregunta("p1", "Cohesión"),
      pregunta("p2", "Cohesión"),
      pregunta("p3", "Acoplamiento"),
    ])
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "act-1",
        materia_id: MATERIA_ID,
        fecha_apertura: "2026-09-20T09:00:00",
        fecha_cierre: "2026-09-27T23:59:00",
        cantidad_preguntas: 2,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: false,
        titulo: "",
        comisiones_ids: [],
        tema: "Cohesión",
      }),
    )
    const user = userEvent.setup()

    renderNuevaActividad()
    await screen.findByRole("option", { name: "Cohesión" })
    await user.selectOptions(screen.getByLabelText("Tema"), "Cohesión")

    expect(await screen.findByText(/2 disponibles/)).toBeInTheDocument()

    await completarFormulario({ preguntas: "2", intentos: "1" })

    expect(await screen.findByText("Actividades listado")).toBeInTheDocument()
    const [, opciones] = vi.mocked(fetch).mock.calls.find(([url]) =>
      String(url).includes("/actividades"),
    )!
    const body = JSON.parse(String((opciones as RequestInit).body))
    expect(body.tema).toBe("Cohesión")
  })

  it("combinar unidad temática y tema restringe la cantidad a la intersección y lo manda en el body", async () => {
    mockListarMaterias()
    mockListarComisiones()
    mockFiltrarBanco([
      pregunta("p1", "Cohesión", "Principios de Diseño"),
      pregunta("p2", "Cohesión", "Principios de Diseño"),
      // Mismo tema, otra unidad — no debería contar en la intersección.
      pregunta("p3", "Cohesión", "Arquitectura de Software"),
      // Misma unidad, otro tema — tampoco.
      pregunta("p4", "Acoplamiento", "Principios de Diseño"),
    ])
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "act-1",
        materia_id: MATERIA_ID,
        fecha_apertura: "2026-09-20T09:00:00",
        fecha_cierre: "2026-09-27T23:59:00",
        cantidad_preguntas: 2,
        cantidad_intentos_permitidos: 1,
        cerrada_manualmente: false,
        titulo: "",
        comisiones_ids: [],
        unidad_tematica: "Principios de Diseño",
        tema: "Cohesión",
      }),
    )
    const user = userEvent.setup()

    renderNuevaActividad()
    await screen.findByRole("option", { name: "Principios de Diseño" })
    await user.selectOptions(screen.getByLabelText("Unidad temática"), "Principios de Diseño")
    await user.selectOptions(screen.getByLabelText("Tema"), "Cohesión")

    expect(await screen.findByText(/2 disponibles/)).toBeInTheDocument()

    await completarFormulario({ preguntas: "2", intentos: "1" })

    expect(await screen.findByText("Actividades listado")).toBeInTheDocument()
    const [, opciones] = vi.mocked(fetch).mock.calls.find(([url]) =>
      String(url).includes("/actividades"),
    )!
    const body = JSON.parse(String((opciones as RequestInit).body))
    expect(body.unidad_tematica).toBe("Principios de Diseño")
    expect(body.tema).toBe("Cohesión")
  })

  it("cancelar vuelve al listado sin llamar al backend", async () => {
    mockListarMaterias()
    mockListarComisiones()
    mockFiltrarBanco()

    renderNuevaActividad()
    expect(await screen.findByLabelText("Apertura (fecha y hora)")).toBeInTheDocument()
    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Actividades listado")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(3)
  })
})
