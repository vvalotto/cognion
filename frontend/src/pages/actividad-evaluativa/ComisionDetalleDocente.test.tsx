import { cleanup, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ComisionDetalleDocente } from "@/pages/actividad-evaluativa/ComisionDetalleDocente"
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

/** Arma un JWT con el payload dado — sin firma real, alcanza para testear el decode del cliente. */
function jwtFalso(payload: Record<string, unknown>): string {
  const base64url = (obj: unknown) =>
    btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "")
  return `${base64url({ alg: "HS256" })}.${base64url(payload)}.firma`
}

function renderDetalle(comisionId = "c1") {
  return render(
    <MemoryRouter initialEntries={[`/actividad-evaluativa/comisiones/${comisionId}`]}>
      <Routes>
        <Route
          path="/actividad-evaluativa/comisiones/:comisionId"
          element={<ComisionDetalleDocente />}
        />
        <Route path="/sesiones-en-vivo/:sesionId/sala" element={<p>Sala de espera (destino)</p>} />
        <Route
          path="/sesiones-en-vivo/:sesionId/proyeccion"
          element={<p>Proyección (destino)</p>}
        />
        <Route
          path="/sesiones-en-vivo/comisiones/:comisionId/nueva"
          element={<p>Nueva sesión (destino)</p>}
        />
      </Routes>
    </MemoryRouter>,
  )
}

const comision = {
  id: "c1",
  materia_id: "m1",
  horario: "Lunes 18-20hs",
  administrador_id: "a1",
  docentes_asignados: ["d1"],
}

function stubClipboard(): ReturnType<typeof vi.fn> {
  // Se define después de `userEvent.setup()`, que instala su propio stub del Clipboard API y
  // pisaría uno definido antes.
  const writeText = vi.fn().mockResolvedValue(undefined)
  Object.defineProperty(navigator, "clipboard", { value: { writeText }, configurable: true })
  return writeText
}

describe("ComisionDetalleDocente", () => {
  beforeEach(() => {
    setSession({ token: jwtFalso({ sub: "d1", rol: "docente" }), rol: "docente" })
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  /** Las tres cargas iniciales (comisión, estudiantes, sesiones) y la última invitación grupal. */
  function cargasIniciales(ultima: unknown = null) {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, ultima))
  }

  const enUnaHora = () => new Date(Date.now() + 60 * 60 * 1000).toISOString()
  const ayer = () => new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString()

  function ultimaInvitacion(parcial: Record<string, unknown> = {}) {
    return {
      id: "i1",
      estado: "vigente",
      token: "tok-123",
      generada_en: new Date().toISOString(),
      expira_en: enUnaHora(),
      usos: 0,
      ...parcial,
    }
  }

  it("genera el link grupal con la duración por defecto y lo muestra con botón Copiar", async () => {
    cargasIniciales(null)
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, {
        id: "i1",
        comision_id: "c1",
        expira_en: enUnaHora(),
        token: "tok-123",
      }),
    )

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    expect(screen.getByLabelText("Duración del link")).toHaveValue("60")
    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Generar link grupal" }))

    expect(await screen.findByText(/tok-123/)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Generar un link nuevo" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Copiar" })).toBeInTheDocument()
    expect(screen.getByText(/Todavía nadie se registró con este link/)).toBeInTheDocument()
    expect(screen.getByText("Si generás un link nuevo, el anterior se desactiva.")).toBeInTheDocument()

    const [url, init] = vi.mocked(fetch).mock.calls[4]
    expect(String(url)).toContain("/comisiones/c1/invitaciones-grupales")
    expect(JSON.parse(init?.body as string)).toEqual({ duracion_minutos: 60 })
  })

  it("ofrece las tres duraciones y envía la elegida", async () => {
    cargasIniciales(null)
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(201, { id: "i1", comision_id: "c1", expira_en: enUnaHora(), token: "tok-9" }),
    )

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    const selector = screen.getByLabelText("Duración del link")
    expect(Array.from((selector as HTMLSelectElement).options).map((o) => o.text)).toEqual([
      "15 minutos",
      "1 hora",
      "1 día",
    ])
    const user = userEvent.setup()
    await user.selectOptions(selector, "1440")
    await user.click(screen.getByRole("button", { name: "Generar link grupal" }))
    await screen.findByText(/tok-9/)

    const [, init] = vi.mocked(fetch).mock.calls[4]
    expect(JSON.parse(init?.body as string)).toEqual({ duracion_minutos: 1440 })
  })

  it("copia el link generado al portapapeles", async () => {
    cargasIniciales(ultimaInvitacion())

    renderDetalle()
    await screen.findByText(/tok-123/)

    const user = userEvent.setup()
    const clipboardWriteText = stubClipboard()
    await user.click(screen.getByRole("button", { name: "Copiar" }))

    expect(await screen.findByText("Copiado ✓")).toBeInTheDocument()
    expect(clipboardWriteText).toHaveBeenCalledWith(expect.stringContaining("token=tok-123"))
  })

  it("al volver a la pantalla muestra el link vigente con su vencimiento y los registrados", async () => {
    cargasIniciales(ultimaInvitacion({ usos: 12 }))

    renderDetalle()

    expect(await screen.findByText(/tok-123/)).toBeInTheDocument()
    expect(screen.getByText("Vigente")).toBeInTheDocument()
    expect(screen.getByText(/12 estudiantes se registraron con este link/)).toBeInTheDocument()
    expect(screen.getByText(/Vence en/)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Desactivar link" })).toBeInTheDocument()
  })

  it("desactivar el link avisa y ya no muestra el link ni el botón Copiar", async () => {
    cargasIniciales(ultimaInvitacion({ usos: 2 }))
    vi.mocked(fetch).mockResolvedValueOnce(new Response(null, { status: 204 }))

    renderDetalle()
    await screen.findByText(/tok-123/)

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Desactivar link" }))

    expect(await screen.findByText("Desactivado")).toBeInTheDocument()
    expect(screen.queryByText(/tok-123/)).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Copiar" })).not.toBeInTheDocument()
    expect(screen.getByText(/2 estudiantes se registraron con este link/)).toBeInTheDocument()

    const [url, init] = vi.mocked(fetch).mock.calls[4]
    expect(String(url)).toContain("/comisiones/c1/invitaciones-grupales/i1/revocar")
    expect(init?.method).toBe("POST")
  })

  it("un link que ya venció se muestra como vencido, sin link ni botón Copiar", async () => {
    cargasIniciales(ultimaInvitacion({ estado: "vencida", token: null, expira_en: ayer(), usos: 1 }))

    renderDetalle()

    expect(await screen.findByText("Venció")).toBeInTheDocument()
    expect(screen.getByText(/1 estudiante se registró con este link/)).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Copiar" })).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Generar un link nuevo" })).toBeInTheDocument()
  })

  it("si el servidor todavía lo da por vigente pero ya pasó el vencimiento, lo muestra vencido", async () => {
    cargasIniciales(ultimaInvitacion({ expira_en: ayer() }))

    renderDetalle()

    expect(await screen.findByText("Venció")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Copiar" })).not.toBeInTheDocument()
  })

  it("muestra un mensaje de error si el docente no está asignado (403)", async () => {
    cargasIniciales(null)
    vi.mocked(fetch).mockResolvedValueOnce(
      errorResponse(403, "No estás asignado a esta comisión"),
    )

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Generar link grupal" }))

    expect(
      await screen.findByText(/No estás asignado a esta comisión, no podés generar/),
    ).toBeInTheDocument()
  })

  it("lista los estudiantes inscriptos", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "e1", nombre: "Ana Gómez" }]))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderDetalle()

    expect(await screen.findByText("Ana Gómez")).toBeInTheDocument()
  })

  it("muestra el estado vacío de estudiantes", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderDetalle()

    await waitFor(() =>
      expect(
        screen.getByText("Esta comisión todavía no tiene estudiantes inscriptos."),
      ).toBeInTheDocument(),
    )
  })

  it("el botón + Nueva sesión en vivo navega al formulario", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "+ Nueva sesión en vivo" }))

    expect(await screen.findByText("Nueva sesión (destino)")).toBeInTheDocument()
  })

  it("muestra el bloque de sesiones en vivo activas, excluyendo las finalizadas", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: "s1",
            comision_id: "c1",
            materia_id: "m1",
            materia_nombre: "Ingeniería de Software",
            cantidad_preguntas: 5,
            tiempo_limite_por_pregunta_segundos: 20,
            estado: "EnEspera",
            unidad_tematica: null,
            tema: null,
            creada_en: "2026-09-23T10:00:00Z",
          },
          {
            id: "s2",
            comision_id: "c1",
            materia_id: "m1",
            materia_nombre: "Ingeniería de Software",
            cantidad_preguntas: 5,
            tiempo_limite_por_pregunta_segundos: 20,
            estado: "Finalizada",
            unidad_tematica: null,
            tema: null,
            creada_en: "2026-09-23T09:00:00Z",
          },
        ]),
      )

    renderDetalle()

    expect(await screen.findByText("Sesiones en vivo activas")).toBeInTheDocument()
    expect(screen.getByText("En espera")).toBeInTheDocument()
    expect(screen.getAllByRole("button", { name: "Continuar" })).toHaveLength(1)
  })

  it("Continuar navega a la sala si la sesión está EnEspera, o a la proyección si está EnCurso", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(
        jsonResponse(200, [
          {
            id: "s-en-curso",
            comision_id: "c1",
            materia_id: "m1",
            materia_nombre: "Ingeniería de Software",
            cantidad_preguntas: 5,
            tiempo_limite_por_pregunta_segundos: 20,
            estado: "EnCurso",
            unidad_tematica: null,
            tema: null,
            creada_en: "2026-09-23T10:00:00Z",
          },
        ]),
      )

    renderDetalle()
    await screen.findByText("Sesiones en vivo activas")

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Continuar" }))

    expect(await screen.findByText("Proyección (destino)")).toBeInTheDocument()
  })

  it("no muestra el bloque de sesiones activas si no hay ninguna", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    expect(screen.queryByText("Sesiones en vivo activas")).not.toBeInTheDocument()
  })
})
