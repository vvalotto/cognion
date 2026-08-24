import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { CuentaDetalle } from "@/pages/CuentaDetalle"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

const cuentaActiva = {
  id: "u1",
  nombre: "Ana Docente",
  email: "ana@fiuner.edu.ar",
  perfil: "docente",
  bloqueada: false,
  creado_en: "2026-08-01T10:00:00Z",
  comision_id: null,
}

const cuentaBloqueada = {
  id: "u2",
  nombre: "Luis Estudiante",
  email: "luis@fiuner.edu.ar",
  perfil: "estudiante",
  bloqueada: true,
  creado_en: "2026-08-01T10:00:00Z",
  comision_id: "c1",
}

function renderCuentaDetalle(usuarioId: string) {
  return render(
    <MemoryRouter initialEntries={[`/cuentas/${usuarioId}`]}>
      <Routes>
        <Route path="/cuentas/:usuarioId" element={<CuentaDetalle />} />
        <Route path="/cuentas/:usuarioId/resetear-password" element={<p>Resetear contraseña</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("CuentaDetalle", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("muestra los datos de una cuenta activa sin alerta de bloqueo", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaActiva))

    renderCuentaDetalle("u1")

    expect(await screen.findByText("ana@fiuner.edu.ar")).toBeInTheDocument()
    expect(screen.getByText("Activa")).toBeInTheDocument()
    expect(screen.queryByRole("alert")).not.toBeInTheDocument()
  })

  it("ve el detalle de una cuenta bloqueada y ve una alerta indicando que está bloqueada", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaBloqueada))

    renderCuentaDetalle("u2")

    expect(await screen.findByRole("alert")).toHaveTextContent(/bloqueada/i)
    expect(screen.getByText("Bloqueada")).toBeInTheDocument()
  })

  it("[US-ADJ-04] breadcrumb, tarjeta de datos y tags de color", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaBloqueada))

    renderCuentaDetalle("u2")
    await screen.findByRole("alert")

    expect(screen.getByText("Administración")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Luis Estudiante" })).toBeInTheDocument()
    const badge = (texto: string) =>
      screen.getAllByText(texto).find((el) => el.getAttribute("data-slot") === "badge")
    expect(badge("Estudiante")).toHaveClass("bg-violet-50")
    expect(badge("Bloqueada")).toHaveClass("bg-red-50")
  })

  it("botón 'Resetear contraseña y desbloquear' navega al formulario de reseteo", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(jsonResponse(200, cuentaBloqueada))
    const user = userEvent.setup()

    renderCuentaDetalle("u2")
    await screen.findByRole("alert")

    await user.click(screen.getByText("Resetear contraseña y desbloquear"))

    expect(await screen.findByText("Resetear contraseña")).toBeInTheDocument()
  })
})
