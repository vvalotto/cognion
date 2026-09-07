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

  it("genera el link de invitación y lo muestra con botón Copiar", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(
        jsonResponse(201, {
          id: "i1",
          comision_id: "c1",
          docente_id: "d1",
          expira_en: "2026-09-14T00:00:00Z",
          token: "tok-123",
        }),
      )

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Generar link de invitación" }))

    expect(await screen.findByText(/tok-123/)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Generar un link nuevo" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Copiar" })).toBeInTheDocument()

    const [, init] = vi.mocked(fetch).mock.calls[2]
    expect(JSON.parse(init?.body as string)).toEqual({ docente_id: "d1" })
  })

  it("copia el link generado al portapapeles", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(
        jsonResponse(201, {
          id: "i1",
          comision_id: "c1",
          docente_id: "d1",
          expira_en: "2026-09-14T00:00:00Z",
          token: "tok-123",
        }),
      )

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    const user = userEvent.setup()
    const clipboardWriteText = stubClipboard()
    await user.click(screen.getByRole("button", { name: "Generar link de invitación" }))
    await screen.findByText(/tok-123/)
    await user.click(screen.getByRole("button", { name: "Copiar" }))

    expect(await screen.findByText("Copiado ✓")).toBeInTheDocument()
    expect(clipboardWriteText).toHaveBeenCalledWith(expect.stringContaining("token=tok-123"))
  })

  it("muestra un mensaje de error si el docente no está asignado (422)", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))
      .mockResolvedValueOnce(errorResponse(422, "El docente no está asignado a esta comisión"))

    renderDetalle()
    await screen.findByRole("heading", { name: "Lunes 18-20hs" })

    const user = userEvent.setup()
    await user.click(screen.getByRole("button", { name: "Generar link de invitación" }))

    expect(
      await screen.findByText(/No estás asignado a esta comisión/),
    ).toBeInTheDocument()
  })

  it("lista los estudiantes inscriptos", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, [{ id: "e1", nombre: "Ana Gómez" }]))

    renderDetalle()

    expect(await screen.findByText("Ana Gómez")).toBeInTheDocument()
  })

  it("muestra el estado vacío de estudiantes", async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce(jsonResponse(200, comision))
      .mockResolvedValueOnce(jsonResponse(200, []))

    renderDetalle()

    await waitFor(() =>
      expect(
        screen.getByText("Esta comisión todavía no tiene estudiantes inscriptos."),
      ).toBeInTheDocument(),
    )
  })
})
