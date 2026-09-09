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
    expect(fetch).toHaveBeenCalledTimes(2)
  })

  it("rechazo del servidor por preguntas insuficientes muestra el error inline", async () => {
    mockListarMaterias()
    mockListarComisiones()
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
    mockListarMaterias(42)
    mockListarComisiones()

    renderNuevaActividad()

    expect(await screen.findByText(/42 disponibles/)).toBeInTheDocument()
  })

  it("cancelar vuelve al listado sin llamar al backend", async () => {
    mockListarMaterias()
    mockListarComisiones()

    renderNuevaActividad()
    expect(await screen.findByLabelText("Apertura (fecha y hora)")).toBeInTheDocument()
    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Cancelar" }))

    expect(await screen.findByText("Actividades listado")).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledTimes(2)
  })
})
