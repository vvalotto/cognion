import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter, Route, Routes } from "react-router"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const { navigateMock } = vi.hoisted(() => ({ navigateMock: vi.fn() }))
vi.mock("@/router", () => ({
  router: { navigate: navigateMock },
}))

import { Login } from "@/pages/identidad/Login"
import { clearSession, getSession } from "@/lib/session"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

function renderLogin() {
  return render(
    <MemoryRouter initialEntries={["/login"]}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/docentes/nuevo" element={<p>Alta de Docente</p>} />
        <Route path="/" element={<p>Inicio</p>} />
      </Routes>
    </MemoryRouter>
  )
}

async function completarFormulario(email: string, password: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText("Email"), email)
  await user.type(screen.getByLabelText("Contraseña"), password)
  await user.click(screen.getByRole("button", { name: "Ingresar" }))
}

describe("Login", () => {
  beforeEach(() => {
    clearSession()
    navigateMock.mockClear()
    vi.stubGlobal("fetch", vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    cleanup()
  })

  it("login exitoso guarda el JWT y redirige a /docentes/nuevo para administrador", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        access_token: "token-admin",
        rol: "administrador",
        expira_en: "2026-01-01T00:00:00Z",
      })
    )

    renderLogin()
    await completarFormulario("admin@fiuner.edu.ar", "Docente#2026")

    expect(await screen.findByText("Alta de Docente")).toBeInTheDocument()
    expect(getSession()).toEqual({ token: "token-admin", rol: "administrador" })
  })

  it("login exitoso redirige a / para docente/estudiante", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(200, {
        access_token: "token-docente",
        rol: "docente",
        expira_en: "2026-01-01T00:00:00Z",
      })
    )

    renderLogin()
    await completarFormulario("docente@fiuner.edu.ar", "Docente#2026")

    expect(await screen.findByText("Inicio")).toBeInTheDocument()
  })

  it("credenciales inválidas muestra el error genérico y limpia la contraseña", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, { detail: "Email o contraseña incorrectos." })
    )

    renderLogin()
    await completarFormulario("estudiante@fiuner.edu.ar", "contraseña-incorrecta")

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Email o contraseña incorrectos"
    )
    expect(screen.getByLabelText("Contraseña")).toHaveValue("")
    expect(screen.getByLabelText("Email")).toHaveValue("estudiante@fiuner.edu.ar")
    expect(getSession()).toBeNull()
  })

  it("email inexistente muestra la misma pantalla de error que credenciales inválidas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(401, { detail: "Email o contraseña incorrectos." })
    )

    renderLogin()
    await completarFormulario("no-existe@fiuner.edu.ar", "cualquiera")

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Email o contraseña incorrectos"
    )
  })

  it("cuenta bloqueada muestra la alerta específica y deshabilita el formulario", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(403, { detail: "La cuenta está bloqueada. Contactá a un administrador." })
    )

    renderLogin()
    await completarFormulario("bloqueado@fiuner.edu.ar", "cualquiera")

    expect(await screen.findByRole("alert")).toHaveTextContent("Cuenta bloqueada")
    expect(screen.getByLabelText("Email")).toBeDisabled()
    expect(screen.getByLabelText("Contraseña")).toBeDisabled()
    expect(screen.getByRole("button", { name: "Ingresar" })).toBeDisabled()
    expect(getSession()).toBeNull()
  })

  it("cuenta bloqueada no muestra el mensaje genérico de credenciales inválidas", async () => {
    vi.mocked(fetch).mockResolvedValueOnce(
      jsonResponse(403, { detail: "La cuenta está bloqueada. Contactá a un administrador." })
    )

    renderLogin()
    await completarFormulario("bloqueado@fiuner.edu.ar", "cualquiera")

    expect(await screen.findByRole("alert")).not.toHaveTextContent(
      "Email o contraseña incorrectos"
    )
  })
})
