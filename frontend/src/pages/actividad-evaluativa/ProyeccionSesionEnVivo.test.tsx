import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import type { MensajeSesionEnVivo } from "@/lib/canal-sesion-en-vivo"

const hookState = vi.hoisted(() => ({
  onMensaje: (_mensaje: MensajeSesionEnVivo) => {},
  onReconectado: () => {},
  estado: "conectado" as "conectado" | "reconectando" | "desconectado",
}))

vi.mock("@/lib/use-canal-sesion-en-vivo", () => ({
  useCanalSesionEnVivo: (
    _sesionId: string,
    onMensaje: (mensaje: MensajeSesionEnVivo) => void,
    onReconectado: () => void,
  ) => {
    hookState.onMensaje = onMensaje
    hookState.onReconectado = onReconectado
    return hookState.estado
  },
}))

const navigateMock = vi.fn()
vi.mock("react-router", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router")>()
  return { ...actual, useNavigate: () => navigateMock }
})

import { ProyeccionSesionEnVivo } from "@/pages/actividad-evaluativa/ProyeccionSesionEnVivo"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const preguntaSola = {
  pregunta_id: "p1",
  enunciado: "¿Qué principio de SOLID viola depender de una clase concreta?",
  tipo: "opcion_multiple",
  opciones: null,
  respuesta_correcta: null,
}

const estadoBase = {
  estado: "EnCurso",
  comision_id: "c1",
  cantidad_preguntas: 5,
  tiempo_limite_por_pregunta_segundos: 20,
  pregunta_actual_indice: 0,
  opciones_mostradas: false,
  opciones_mostradas_en: null,
  pregunta_actual_cerrada: false,
  pregunta_actual: preguntaSola,
  ya_respondio: null,
  puntaje_acumulado: null,
  total_participantes: 5,
  cantidad_respuestas: 0,
  resultado_pregunta: null,
}

const estadoOpciones = (extra: Record<string, unknown> = {}) => ({
  ...estadoBase,
  opciones_mostradas: true,
  opciones_mostradas_en: new Date().toISOString(),
  pregunta_actual: { ...preguntaSola, opciones: ["Liskov", "DIP", "ISP", "SRP"] },
  ...extra,
})

const sesionResponse = {
  id: "s1",
  comision_id: "c1",
  materia_id: "m1",
  unidad_tematica: null,
  tema: null,
  cantidad_preguntas: 5,
  tiempo_limite_por_pregunta_segundos: 20,
  estado: "EnCurso",
  pregunta_actual_indice: 0,
}

function rankingApi(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    posicion: i + 1,
    estudiante_id: `e${i + 1}`,
    puntaje_acumulado: 4000 - i * 500,
    nombre: `Estudiante ${i + 1}`,
  }))
}

function rankingCanal(n: number) {
  return rankingApi(n).map((r) => ({
    posicion: r.posicion,
    estudianteId: r.estudiante_id,
    puntajeAcumulado: r.puntaje_acumulado,
    nombre: r.nombre,
  }))
}

const estadoCerrada = (extra: Record<string, unknown> = {}) =>
  estadoOpciones({
    pregunta_actual_cerrada: true,
    pregunta_actual: {
      ...preguntaSola,
      opciones: ["Liskov", "DIP", "ISP", "SRP"],
      respuesta_correcta: {
        contenido: { opcion_indice: 1 },
        texto: preguntaSola.enunciado,
        opciones: ["Liskov", "DIP", "ISP", "SRP"],
      },
    },
    resultado_pregunta: {
      distribucion: [
        { opcion: "0", cantidad: 1 },
        { opcion: "1", cantidad: 3 },
      ],
      ranking: rankingApi(6),
    },
    ...extra,
  })

function llamadasA(fragmento: string, metodo?: string) {
  return vi
    .mocked(fetch)
    .mock.calls.filter(
      ([url, init]) =>
        String(url).includes(fragmento) && (!metodo || (init as RequestInit)?.method === metodo),
    )
}

function renderProyeccion() {
  return render(
    <MemoryRouter initialEntries={["/sesiones-en-vivo/s1/proyeccion"]}>
      <Routes>
        <Route path="/sesiones-en-vivo/:sesionId/proyeccion" element={<ProyeccionSesionEnVivo />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("ProyeccionSesionEnVivo", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    hookState.estado = "conectado"
    navigateMock.mockClear()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
    cleanup()
  })

  it("una sesión recién iniciada muestra la pregunta sola, sin opciones", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estadoBase))

    renderProyeccion()

    expect(await screen.findByText("Pregunta 1 de 5")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: /depender de una clase concreta/ })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Mostrar opciones" })).toBeInTheDocument()
    expect(screen.queryByRole("listitem")).not.toBeInTheDocument()
  })

  it("una sesión en espera redirige a la sala", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, { ...estadoBase, estado: "EnEspera", pregunta_actual: null }),
    )

    renderProyeccion()

    await waitFor(() => expect(navigateMock).toHaveBeenCalledWith("/sesiones-en-vivo/s1/sala"))
  })

  it("mostrar opciones envía el comando y el mensaje del canal muestra las cajas con el temporizador", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, sesionResponse))

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: "Mostrar opciones" }))
    await waitFor(() => expect(llamadasA("/mostrar-opciones", "POST")).toHaveLength(1))

    act(() => {
      hookState.onMensaje({
        tipo: "opciones_mostradas",
        preguntaActualIndice: 0,
        opciones: ["Liskov", "DIP", "ISP", "SRP"],
        tiempoLimitePorPreguntaSegundos: 20,
        cantidadRespuestas: 0,
      })
    })

    expect(screen.getAllByRole("listitem")).toHaveLength(4)
    expect(screen.getByRole("timer")).toHaveTextContent("00:20")
    expect(screen.getByRole("button", { name: "Cerrar pregunta" })).toBeInTheDocument()
  })

  it("el doble click en 'Mostrar opciones' envía una sola request", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, sesionResponse))

    renderProyeccion()
    const boton = await screen.findByRole("button", { name: "Mostrar opciones" })
    fireEvent.click(boton)
    fireEvent.click(boton)

    await waitFor(() => expect(llamadasA("/mostrar-opciones", "POST")).toHaveLength(1))
  })

  it("422 OpcionesYaMostradas pasa igual a la etapa siguiente recalculando con el estado", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(422, { detail: "OpcionesYaMostradas" }))
      .mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: "Mostrar opciones" }))

    expect(await screen.findByRole("button", { name: "Cerrar pregunta" })).toBeInTheDocument()
    expect(screen.getAllByRole("listitem")).toHaveLength(4)
  })

  it("si el mensaje no llega en 2 s recalcula la etapa con el estado del servidor", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, sesionResponse))
      .mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))

    renderProyeccion()
    const boton = await screen.findByRole("button", { name: "Mostrar opciones" })
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] })
    fireEvent.click(boton)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2100)
    })
    vi.useRealTimers()

    expect(await screen.findByRole("button", { name: "Cerrar pregunta" })).toBeInTheDocument()
  })

  it("si el mensaje llega a tiempo no se pide el estado de nuevo", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(200, sesionResponse))

    renderProyeccion()
    const boton = await screen.findByRole("button", { name: "Mostrar opciones" })
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] })
    fireEvent.click(boton)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10)
    })
    act(() => {
      hookState.onMensaje({
        tipo: "opciones_mostradas",
        preguntaActualIndice: 0,
        opciones: ["a", "b"],
        tiempoLimitePorPreguntaSegundos: 20,
        cantidadRespuestas: 0,
      })
    })
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000)
    })

    expect(llamadasA("/sesiones-en-vivo/s1")).toHaveLength(2) // estado inicial + POST
    expect(llamadasA("/sesiones-en-vivo/s1", "GET").length).toBeLessThanOrEqual(1)
  })

  it("no revela la correcta ni marca ninguna opción", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))

    renderProyeccion()

    await screen.findByRole("button", { name: "Cerrar pregunta" })
    screen.getAllByRole("listitem").forEach((caja) => {
      expect(caja).not.toHaveAttribute("aria-current")
    })
  })

  it("Verdadero/Falso con las opciones mostradas: dos cajas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(
        200,
        estadoOpciones({
          pregunta_actual: { ...preguntaSola, tipo: "verdadero_falso", opciones: null },
        }),
      ),
    )

    renderProyeccion()

    await screen.findByRole("button", { name: "Cerrar pregunta" })
    expect(screen.getAllByRole("listitem").map((c) => c.textContent)).toEqual(["Verdadero", "Falso"])
  })

  it("el conteo se actualiza en vivo con las respuestas y los participantes", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))

    renderProyeccion()
    await screen.findByText(/ya respondieron/)
    expect(screen.getByText(/ya respondieron/)).toHaveTextContent("0 / 5 ya respondieron")

    act(() => {
      hookState.onMensaje({
        tipo: "conteo_respuestas_actualizado",
        preguntaActualIndice: 0,
        cantidadRespuestas: 3,
      })
    })
    expect(screen.getByText(/ya respondieron/)).toHaveTextContent("3 / 5 ya respondieron")

    act(() => {
      hookState.onMensaje({ tipo: "participantes_actualizados", cantidad: 6, participantes: [] })
    })
    expect(screen.getByText(/ya respondieron/)).toHaveTextContent("3 / 6 ya respondieron")
  })

  it("recargar en medio de la pregunta descuenta el tiempo transcurrido y muestra el conteo actual", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(
        200,
        estadoOpciones({
          opciones_mostradas_en: new Date(Date.now() - 10_000).toISOString(),
          cantidad_respuestas: 4,
        }),
      ),
    )

    renderProyeccion()

    await screen.findByRole("timer")
    expect(screen.getByRole("timer").textContent).toMatch(/^00:(09|10)$/)
    expect(screen.getByText(/ya respondieron/)).toHaveTextContent("4 / 5 ya respondieron")
  })

  it("cerrar la pregunta envía el comando y pasa a la etapa de resultado con el mensaje del canal", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))
      .mockResolvedValueOnce(jsonResponse(200, sesionResponse))

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: "Cerrar pregunta" }))
    await waitFor(() => expect(llamadasA("/cerrar-pregunta", "POST")).toHaveLength(1))

    act(() => {
      hookState.onMensaje({
        tipo: "pregunta_cerrada",
        preguntaActualIndice: 0,
        respuestaCorrecta: { contenido: {}, texto: "DIP", opciones: null },
        distribucion: [{ opcion: "DIP", cantidad: 3 }],
        ranking: [],
      })
    })

    expect(screen.queryByRole("button", { name: "Cerrar pregunta" })).not.toBeInTheDocument()
    expect(screen.getByText(/así respondió el aula/)).toBeInTheDocument()
  })

  it("422 PreguntaYaCerrada recalcula con el estado del servidor", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))
      .mockResolvedValueOnce(jsonResponse(422, { detail: "PreguntaYaCerrada" }))
      .mockResolvedValueOnce(
        jsonResponse(
          200,
          estadoOpciones({
            pregunta_actual_cerrada: true,
            resultado_pregunta: { distribucion: [], ranking: [] },
          }),
        ),
      )

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: "Cerrar pregunta" }))

    expect(await screen.findByText(/así respondió el aula/)).toBeInTheDocument()
  })

  it("un error inesperado al enviar el comando avisa y deja reintentar", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(jsonResponse(500, { detail: "boom" }))

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: "Mostrar opciones" }))

    expect(await screen.findByRole("alert")).toHaveTextContent(/No se pudo enviar/)
    expect(screen.getByRole("button", { name: "Mostrar opciones" })).toBeEnabled()
  })

  it("una pregunta nueva presentada vuelve a la pregunta sola", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))

    renderProyeccion()
    await screen.findByRole("button", { name: "Cerrar pregunta" })

    act(() => {
      hookState.onMensaje({
        tipo: "pregunta_presentada",
        preguntaActualIndice: 1,
        pregunta: { preguntaId: "p2", enunciado: "Segunda pregunta", tipo: "opcion_multiple" },
      })
    })

    expect(screen.getByText("Pregunta 2 de 5")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Mostrar opciones" })).toBeInTheDocument()
  })

  it("un mensaje de otra pregunta recalcula con el estado del servidor", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoBase))
      .mockResolvedValueOnce(
        jsonResponse(200, estadoOpciones({ pregunta_actual_indice: 3 })),
      )

    renderProyeccion()
    await screen.findByText("Pregunta 1 de 5")

    act(() => {
      hookState.onMensaje({
        tipo: "opciones_mostradas",
        preguntaActualIndice: 3,
        opciones: null,
        tiempoLimitePorPreguntaSegundos: 20,
        cantidadRespuestas: 0,
      })
    })

    expect(await screen.findByText("Pregunta 4 de 5")).toBeInTheDocument()
  })

  it("los mensajes que llegan antes de cargar el estado se ignoran", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estadoBase))

    renderProyeccion()
    act(() => {
      hookState.onMensaje({ tipo: "participantes_actualizados", cantidad: 1, participantes: [] })
    })

    expect(await screen.findByText("Pregunta 1 de 5")).toBeInTheDocument()
  })

  it("al reconectar recalcula la etapa y el conteo desde el estado del servidor", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoOpciones()))
      .mockResolvedValueOnce(jsonResponse(200, estadoOpciones({ cantidad_respuestas: 4 })))

    hookState.estado = "reconectando"
    renderProyeccion()
    await screen.findByText(/ya respondieron/)
    expect(screen.getByRole("status")).toHaveTextContent("Reconectando…")

    await act(async () => {
      hookState.onReconectado()
    })

    await waitFor(() =>
      expect(screen.getByText(/ya respondieron/)).toHaveTextContent("4 / 5 ya respondieron"),
    )
  })

  it("recargar con la sesión finalizada muestra el podio con el ranking del servidor", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, { ...estadoBase, estado: "Finalizada" }))
      .mockResolvedValueOnce(jsonResponse(200, rankingApi(4)))

    renderProyeccion()

    expect(await screen.findByText("¡Gracias por participar!")).toBeInTheDocument()
    expect(within(screen.getByRole("list", { name: "Podio" })).getAllByRole("listitem")).toHaveLength(3)
    expect(screen.getByText("Estudiante 1")).toBeInTheDocument()
    expect(llamadasA("/sesiones-en-vivo/s1/ranking")).toHaveLength(1)
    expect(screen.queryByRole("link", { name: "‹ Salir" })).not.toBeInTheDocument()
  })

  it("si falla el estado inicial queda en 'Cargando…'", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(500, { detail: "boom" }))

    renderProyeccion()

    await waitFor(() => expect(fetch).toHaveBeenCalled())
    expect(screen.getByText("Cargando…")).toBeInTheDocument()
  })

  it("recargar tras el cierre recupera el histograma con sus datos y pasa al ranking", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estadoCerrada()))

    renderProyeccion()

    await screen.findByText(/así respondió el aula/)
    expect(screen.getAllByTestId("barra-histograma").map((b) => b.textContent)).toEqual([
      "1",
      "3",
      "0",
      "0",
    ])
    fireEvent.click(screen.getByRole("button", { name: /Ver ranking ahora/ }))

    expect(screen.getByText(/Ranking — tras la pregunta 1 de 5/)).toBeInTheDocument()
    expect(screen.getAllByRole("listitem")).toHaveLength(3)
  })

  it("siguiente pregunta envía el comando y vuelve a la pregunta sola con el mensaje del canal", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoCerrada()))
      .mockResolvedValueOnce(jsonResponse(200, { ...sesionResponse, pregunta_actual_indice: 1 }))

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: /Ver ranking ahora/ }))
    const siguiente = screen.getByRole("button", { name: "Siguiente pregunta" })
    fireEvent.click(siguiente)
    fireEvent.click(siguiente)
    await waitFor(() => expect(llamadasA("/avanzar", "POST")).toHaveLength(1))

    act(() => {
      hookState.onMensaje({
        tipo: "pregunta_presentada",
        preguntaActualIndice: 1,
        pregunta: { preguntaId: "p2", enunciado: "Segunda pregunta", tipo: "opcion_multiple" },
      })
    })

    expect(screen.getByText("Pregunta 2 de 5")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Segunda pregunta" })).toBeInTheDocument()
  })

  it("422 NoQuedanPreguntas al avanzar recalcula sin volver del ranking al histograma", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoCerrada()))
      .mockResolvedValueOnce(jsonResponse(422, { detail: "NoQuedanPreguntas" }))
      .mockResolvedValueOnce(jsonResponse(200, estadoCerrada()))

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: /Ver ranking ahora/ }))
    fireEvent.click(screen.getByRole("button", { name: "Siguiente pregunta" }))

    await waitFor(() => expect(vi.mocked(fetch)).toHaveBeenCalledTimes(3))
    // El servidor dice "pregunta cerrada" (histograma), pero la proyección ya estaba en el ranking:
    // resincronizar no retrocede (hallazgo #7).
    expect(await screen.findByText(/Ranking — tras la pregunta/)).toBeInTheDocument()
  })

  it("finalizar antes de tiempo muestra el podio con el ranking del mensaje", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, estadoCerrada({ pregunta_actual_indice: 1 })))
      .mockResolvedValueOnce(jsonResponse(200, { ...sesionResponse, estado: "Finalizada" }))

    renderProyeccion()
    fireEvent.click(await screen.findByRole("button", { name: /Ver ranking ahora/ }))
    expect(screen.getByText(/tras la pregunta 2 de 5/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "Finalizar sesión" }))
    await waitFor(() => expect(llamadasA("/finalizar", "POST")).toHaveLength(1))

    act(() => {
      hookState.onMensaje({ tipo: "sesion_finalizada", ranking: rankingCanal(2) })
    })

    expect(screen.getByText("¡Gracias por participar!")).toBeInTheDocument()
    expect(within(screen.getByRole("list", { name: "Podio" })).getAllByRole("listitem")).toHaveLength(2)
    expect(screen.getByRole("link", { name: /Volver a la Comisión/ })).toHaveAttribute(
      "href",
      "/actividad-evaluativa/comisiones/c1",
    )
  })

  it("'Salir' vuelve a la Comisión sin tocar la sesión", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, estadoBase))

    renderProyeccion()

    expect(await screen.findByRole("link", { name: "‹ Salir" })).toHaveAttribute(
      "href",
      "/actividad-evaluativa/comisiones/c1",
    )
  })
})
