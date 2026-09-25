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

import { clearSession, setSession } from "@/lib/session"
import { SesionEnVivoEstudiante } from "@/pages/actividad-evaluativa/SesionEnVivoEstudiante"

/** JWT sin firma real con el `sub` del Estudiante — alcanza para el decode del cliente. */
function jwtFalso(payload: Record<string, unknown>): string {
  const base64url = (obj: unknown) =>
    btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
  return `${base64url({ alg: "HS256" })}.${base64url(payload)}.firma`
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const participacion = { sesion_id: "s1", estudiante_id: "e1", unido_en: "2026-09-24T10:00:00+00:00" }

const estadoApi = (extra: Record<string, unknown> = {}) => ({
  estado: "EnEspera",
  comision_id: "c1",
  cantidad_preguntas: 5,
  tiempo_limite_por_pregunta_segundos: 20,
  pregunta_actual_indice: null,
  opciones_mostradas: false,
  opciones_mostradas_en: null,
  pregunta_actual_cerrada: false,
  pregunta_actual: null,
  ya_respondio: false,
  puntaje_acumulado: 0,
  total_participantes: 3,
  cantidad_respuestas: 0,
  resultado_pregunta: null,
  ...extra,
})

const preguntaApi = {
  pregunta_id: "p2",
  enunciado: "¿Qué principio viola depender de una clase concreta?",
  tipo: "opcion_multiple",
  opciones: ["Liskov", "Inversión de dependencias", "Segregación", "Responsabilidad única"],
  respuesta_correcta: null,
}

const estadoEnCurso = (extra: Record<string, unknown> = {}) =>
  estadoApi({
    estado: "EnCurso",
    pregunta_actual_indice: 0,
    opciones_mostradas: true,
    opciones_mostradas_en: new Date().toISOString(),
    pregunta_actual: preguntaApi,
    puntaje_acumulado: 1200,
    ...extra,
  })

const rankingApi = [1, 2, 3, 4, 5].map((posicion) => ({
  posicion,
  estudiante_id: `e${posicion}`,
  nombre: `Estudiante ${posicion}`,
  puntaje_acumulado: 6000 - posicion * 1000,
}))

const rankingCanal = rankingApi.map((r) => ({
  posicion: r.posicion,
  estudianteId: r.estudiante_id,
  nombre: r.nombre,
  puntajeAcumulado: r.puntaje_acumulado,
}))

function llamadasA(fragmento: string) {
  return vi.mocked(fetch).mock.calls.filter(([url]) => String(url).includes(fragmento))
}

function renderSesion() {
  return render(
    <MemoryRouter initialEntries={["/mis-sesiones-en-vivo/s1"]}>
      <Routes>
        <Route path="/mis-sesiones-en-vivo/:sesionId" element={<SesionEnVivoEstudiante />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("SesionEnVivoEstudiante", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
    hookState.estado = "conectado"
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    clearSession()
    cleanup()
  })

  it("al abrir se une y muestra la sala con la cantidad de participantes", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()

    expect(await screen.findByRole("heading", { name: "¡Te uniste!" })).toBeInTheDocument()
    expect(screen.getByText("3 participantes")).toBeInTheDocument()
    expect(llamadasA("/sesiones-en-vivo/s1/unirse")).toHaveLength(1)
    // Primero se une, después pide el estado.
    expect(String(vi.mocked(fetch).mock.calls[0][0])).toContain("/unirse")
  })

  it("el conteo de la sala es en vivo", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()
    await screen.findByText("3 participantes")

    act(() => {
      hookState.onMensaje({ tipo: "participantes_actualizados", cantidad: 4, participantes: [] })
    })
    expect(screen.getByText("4 participantes")).toBeInTheDocument()
  })

  it("pasa solo a la pregunta cuando el Docente inicia", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()
    await screen.findByRole("heading", { name: "¡Te uniste!" })

    act(() => {
      hookState.onMensaje({
        tipo: "pregunta_presentada",
        preguntaActualIndice: 0,
        pregunta: { preguntaId: "p1", enunciado: "¿Qué es SOLID?", tipo: "opcion_multiple" },
      })
    })
    expect(screen.queryByRole("heading", { name: "¡Te uniste!" })).not.toBeInTheDocument()
    expect(screen.getByRole("status")).toHaveTextContent("Esperá a que el Docente muestre las opciones.")
    expect(screen.getByRole("heading", { name: "¿Qué es SOLID?" })).toBeInTheDocument()
  })

  it("unión tardía a una sesión en curso entra a la etapa de la pregunta", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ pregunta_actual_indice: 1 })))

    renderSesion()

    expect(await screen.findByText("Pregunta 2 de 5")).toBeInTheDocument()
    expect(screen.getAllByRole("button")).toHaveLength(4)
    expect(screen.queryByRole("heading", { name: "¡Te uniste!" })).not.toBeInTheDocument()
  })

  it("recargar vuelve a la sala: se une de nuevo (idempotente) sin guardar nada en el cliente", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ total_participantes: 5 })))

    const { unmount } = renderSesion()
    await screen.findByText("3 participantes")
    unmount()

    renderSesion()
    expect(await screen.findByText("5 participantes")).toBeInTheDocument()
    expect(llamadasA("/unirse")).toHaveLength(2)
  })

  it("una sesión ya finalizada (422 al unirse) no corta: el estado lleva al final", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(422, { detail: "SesionYaFinalizada" }))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ estado: "Finalizada" })))
      .mockResolvedValueOnce(jsonResponse(200, rankingApi))

    renderSesion()

    expect(await screen.findByRole("heading", { name: "¡Terminó la sesión!" })).toBeInTheDocument()
    expect(llamadasA("/sesiones-en-vivo/s1/ranking")).toHaveLength(1)
  })

  it("una sesión que no existe (404) avisa y ofrece volver", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(404, { detail: "SesionNoEncontrada" }))

    renderSesion()

    expect(await screen.findByRole("alert")).toHaveTextContent("Esta sesión ya no está disponible.")
    expect(screen.getByRole("link", { name: /Volver a mis materias/ })).toHaveAttribute(
      "href",
      "/mis-actividades/materias",
    )
    expect(llamadasA("/sesiones-en-vivo/s1")).toHaveLength(1)
  })

  it("si el estado da 404 también avisa", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(404, { detail: "SesionNoEncontrada" }))

    renderSesion()

    expect(await screen.findByRole("alert")).toHaveTextContent("Esta sesión ya no está disponible.")
  })

  it("el final llega por el canal", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ opciones_mostradas: false })))

    renderSesion()
    await screen.findByText("Esperá a que el Docente muestre las opciones.")

    act(() => {
      hookState.onMensaje({ tipo: "sesion_finalizada", ranking: rankingCanal })
    })
    expect(screen.getByRole("heading", { name: "¡Terminó la sesión!" })).toBeInTheDocument()
  })

  it("al reconectar recalcula la etapa y el conteo desde el servidor, con el chip de conexión", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi({ total_participantes: 8 })))

    hookState.estado = "reconectando"
    renderSesion()
    await screen.findByText("3 participantes")
    expect(screen.getByText("Reconectando…")).toBeInTheDocument()

    await act(async () => {
      hookState.onReconectado()
    })
    await waitFor(() => expect(screen.getByText("8 participantes")).toBeInTheDocument())
  })

  it("los mensajes que llegan antes del estado se ignoran", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, participacion))
      .mockResolvedValueOnce(jsonResponse(200, estadoApi()))

    renderSesion()
    act(() => {
      hookState.onMensaje({ tipo: "participantes_actualizados", cantidad: 9, participantes: [] })
    })

    expect(await screen.findByText("3 participantes")).toBeInTheDocument()
  })

  describe("responder (US-6.3.9)", () => {
    function cuerpoDeRespuesta() {
      const llamada = llamadasA("/responder")[0]
      return JSON.parse(String((llamada[1] as RequestInit).body))
    }

    it("cuando llegan las opciones aparecen las tarjetas; tocar una responde sin confirmar y muestra el resultado", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ opciones_mostradas: false, opciones_mostradas_en: null })))
        .mockResolvedValueOnce(jsonResponse(200, { es_correcta: true, puntaje: 1850, puntaje_acumulado: 3050 }))

      renderSesion()
      await screen.findByText("Esperá a que el Docente muestre las opciones.")

      act(() => {
        hookState.onMensaje({
          tipo: "opciones_mostradas",
          preguntaActualIndice: 0,
          opciones: preguntaApi.opciones,
          tiempoLimitePorPreguntaSegundos: 20,
          cantidadRespuestas: 0,
        })
      })
      expect(screen.getByRole("timer")).toHaveTextContent("00:20")

      const tarjeta = screen.getByRole("button", { name: "Inversión de dependencias" })
      fireEvent.click(tarjeta)
      fireEvent.click(screen.getByRole("button", { name: "Liskov" }))

      expect(await screen.findByRole("heading", { name: "¡Correcto!" })).toBeInTheDocument()
      expect(screen.getByText("+ 1850 puntos en esta pregunta")).toBeInTheDocument()
      expect(screen.getByText("3050 pts")).toBeInTheDocument()
      expect(llamadasA("/responder")).toHaveLength(1)
      expect(cuerpoDeRespuesta()).toEqual({ pregunta_id: "p2", contenido: { opcion_indice: 1 } })
    })

    it("respuesta incorrecta: 'Incorrecto' y +0", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))
        .mockResolvedValueOnce(jsonResponse(200, { es_correcta: false, puntaje: 0, puntaje_acumulado: 1200 }))

      renderSesion()
      fireEvent.click(await screen.findByRole("button", { name: "Liskov" }))

      expect(await screen.findByRole("heading", { name: "Incorrecto" })).toBeInTheDocument()
      expect(screen.getByText("+ 0 puntos en esta pregunta")).toBeInTheDocument()
    })

    it("Verdadero/Falso responde con el valor booleano", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(
          jsonResponse(200, estadoEnCurso({ pregunta_actual: { ...preguntaApi, tipo: "verdadero_falso", opciones: null } })),
        )
        .mockResolvedValueOnce(jsonResponse(200, { es_correcta: true, puntaje: 1000, puntaje_acumulado: 2200 }))

      renderSesion()
      fireEvent.click(await screen.findByRole("button", { name: "Verdadero" }))

      await screen.findByRole("heading", { name: "¡Correcto!" })
      expect(cuerpoDeRespuesta().contenido).toEqual({ valor: true })
    })

    it("tiempo agotado (422 con la pregunta todavía abierta): 'Se acabó el tiempo' con el acumulado", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))
        .mockResolvedValueOnce(jsonResponse(422, { detail: "La respuesta llegó fuera del tiempo límite" }))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))

      renderSesion()
      fireEvent.click(await screen.findByRole("button", { name: "Liskov" }))

      expect(await screen.findByRole("heading", { name: "Se acabó el tiempo" })).toBeInTheDocument()
      expect(screen.getByText("1200 pts")).toBeInTheDocument()
    })

    it("422 con la respuesta ya registrada: muestra el resultado con el acumulado del servidor", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))
        .mockResolvedValueOnce(jsonResponse(422, { detail: "Ya registraste tu respuesta" }))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ ya_respondio: true, puntaje_acumulado: 3050 })))

      renderSesion()
      fireEvent.click(await screen.findByRole("button", { name: "Liskov" }))

      expect(await screen.findByRole("heading", { name: "Ya respondiste" })).toBeInTheDocument()
      expect(screen.getByText("3050 pts")).toBeInTheDocument()
    })

    it("404 al responder: se vuelve a unir y recalcula", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))
        .mockResolvedValueOnce(jsonResponse(404, { detail: "ParticipacionNoExiste" }))
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))

      renderSesion()
      fireEvent.click(await screen.findByRole("button", { name: "Liskov" }))

      await waitFor(() => expect(llamadasA("/unirse")).toHaveLength(2))
      await waitFor(() => expect(screen.getByRole("button", { name: "Liskov" })).toBeEnabled())
    })

    it("un error inesperado avisa y rehabilita las tarjetas", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))
        .mockResolvedValueOnce(jsonResponse(500, { detail: "boom" }))

      renderSesion()
      fireEvent.click(await screen.findByRole("button", { name: "Liskov" }))

      expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo enviar la respuesta")
      expect(screen.getByRole("button", { name: "Liskov" })).toBeEnabled()
    })

    it("no respondió y el Docente cierra la pregunta: 'No respondiste (+0)'", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))

      renderSesion()
      await screen.findByRole("button", { name: "Liskov" })

      act(() => {
        hookState.onMensaje({
          tipo: "pregunta_cerrada",
          preguntaActualIndice: 0,
          respuestaCorrecta: { contenido: { opcion_indice: 1 }, texto: "", opciones: null },
          distribucion: [],
          ranking: rankingCanal,
        })
      })
      expect(screen.getByText("No respondiste (+0)")).toBeInTheDocument()
      expect(screen.queryByText("Estudiante 1")).not.toBeInTheDocument()
    })

    it("desde el resultado pasa solo a la espera de la siguiente pregunta", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ ya_respondio: true })))

      renderSesion()
      await screen.findByRole("heading", { name: "Ya respondiste" })

      act(() => {
        hookState.onMensaje({
          tipo: "pregunta_presentada",
          preguntaActualIndice: 1,
          pregunta: { preguntaId: "p3", enunciado: "Siguiente pregunta", tipo: "opcion_multiple" },
        })
      })
      expect(screen.getByText("Pregunta 2 de 5")).toBeInTheDocument()
      expect(screen.getByText("Esperá a que el Docente muestre las opciones.")).toBeInTheDocument()
    })

    it("recargar después de responder muestra el resultado y no deja volver a responder", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ ya_respondio: true, puntaje_acumulado: 3050 })))

      renderSesion()

      expect(await screen.findByRole("heading", { name: "Ya respondiste" })).toBeInTheDocument()
      expect(screen.getByText("3050 pts")).toBeInTheDocument()
      expect(screen.queryByRole("button")).not.toBeInTheDocument()
    })

    it("reconectar con la pregunta abierta recupera la pregunta, el tiempo restante y el avance", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso()))
        .mockResolvedValueOnce(
          jsonResponse(
            200,
            estadoEnCurso({ opciones_mostradas_en: new Date(Date.now() - 10_000).toISOString(), puntaje_acumulado: 1500 }),
          ),
        )

      hookState.estado = "reconectando"
      renderSesion()
      await screen.findByRole("button", { name: "Liskov" })
      expect(screen.getByText("Reconectando…")).toBeInTheDocument()

      await act(async () => {
        hookState.onReconectado()
      })
      await waitFor(() => expect(screen.getByRole("timer").textContent).toMatch(/^00:(09|10)$/))
      expect(llamadasA("/unirse")).toHaveLength(1)
    })

    it("resultado final: posición propia, Top 3 y su fila resaltada", async () => {
      setSession({ token: jwtFalso({ sub: "e2" }), rol: "estudiante" })
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ opciones_mostradas: false })))

      renderSesion()
      await screen.findByText("Esperá a que el Docente muestre las opciones.")
      act(() => {
        hookState.onMensaje({ tipo: "sesion_finalizada", ranking: rankingCanal })
      })

      expect(screen.getByText("Quedaste 2° con 4000 puntos")).toBeInTheDocument()
      const filas = within(screen.getByRole("list", { name: "Ranking final" })).getAllByRole("listitem")
      expect(filas).toHaveLength(3)
      expect(filas[1]).toHaveAttribute("data-propia", "true")
    })

    it("fuera del Top 3: el Top 3 y su propia fila debajo", async () => {
      setSession({ token: jwtFalso({ sub: "e5" }), rol: "estudiante" })
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoApi({ estado: "Finalizada" })))
        .mockResolvedValueOnce(jsonResponse(200, rankingApi))

      renderSesion()

      expect(await screen.findByText("Quedaste 5° con 1000 puntos")).toBeInTheDocument()
      const filas = within(screen.getByRole("list", { name: "Ranking final" })).getAllByRole("listitem")
      expect(filas).toHaveLength(4)
      expect(filas[3]).toHaveAttribute("data-propia", "true")
    })

    it("un mensaje de otra pregunta recalcula con el estado", async () => {
      vi.mocked(fetch)
        .mockResolvedValueOnce(jsonResponse(200, participacion))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ opciones_mostradas: false })))
        .mockResolvedValueOnce(jsonResponse(200, estadoEnCurso({ pregunta_actual_indice: 3 })))

      renderSesion()
      await screen.findByText("Esperá a que el Docente muestre las opciones.")
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
  })
})
