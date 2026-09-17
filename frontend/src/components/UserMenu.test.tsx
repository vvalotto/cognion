import { cleanup, render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it } from "vitest"

import { MemoryRouter, Route, Routes } from "react-router"

import { UserMenu } from "@/components/UserMenu"
import { clearSession, getSession, setSession } from "@/lib/session"

function renderUserMenu(nombre: string | null, rol: "docente" | "estudiante" | "administrador") {
  return render(
    <MemoryRouter initialEntries={["/inicio"]}>
      <Routes>
        <Route path="/inicio" element={<UserMenu nombre={nombre} rol={rol} />} />
        <Route path="/mi-cuenta/cambiar-password" element={<p>pantalla cambiar contraseña</p>} />
        <Route path="/login" element={<p>pantalla login</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe("UserMenu", () => {
  beforeEach(() => {
    setSession({ token: "t", rol: "docente" })
  })

  afterEach(() => {
    cleanup()
    clearSession()
  })

  it("muestra el trigger con nombre y rol", () => {
    renderUserMenu("Víctor Valotto", "docente")

    expect(screen.getByRole("button", { name: /Víctor Valotto/ })).toBeInTheDocument()
    expect(screen.getByText("Docente")).toBeInTheDocument()
  })

  it("usa una sola inicial cuando el nombre no tiene apellido", () => {
    renderUserMenu("Víctor", "docente")

    expect(screen.getByText("V")).toBeInTheDocument()
  })

  it("abre el menú con los dos ítems al hacer clic en el trigger", async () => {
    const user = userEvent.setup()
    renderUserMenu("Víctor Valotto", "docente")

    await user.click(screen.getByRole("button", { name: /Víctor Valotto/ }))

    expect(await screen.findByText("🔑 Cambiar contraseña")).toBeInTheDocument()
    expect(screen.getByText("↩ Cerrar sesión")).toBeInTheDocument()
  })

  it("navega a Cambiar contraseña al hacer clic en el ítem", async () => {
    const user = userEvent.setup()
    renderUserMenu("Víctor Valotto", "docente")

    await user.click(screen.getByRole("button", { name: /Víctor Valotto/ }))
    await user.click(await screen.findByText("🔑 Cambiar contraseña"))

    expect(await screen.findByText("pantalla cambiar contraseña")).toBeInTheDocument()
  })

  it("cierra sesión y navega a /login al hacer clic en Cerrar sesión", async () => {
    const user = userEvent.setup()
    renderUserMenu("Víctor Valotto", "docente")

    await user.click(screen.getByRole("button", { name: /Víctor Valotto/ }))
    await user.click(await screen.findByText("↩ Cerrar sesión"))

    expect(await screen.findByText("pantalla login")).toBeInTheDocument()
    expect(getSession()).toBeNull()
  })

  it.each([
    ["docente", "Docente"],
    ["estudiante", "Estudiante"],
    ["administrador", "Administrador"],
  ] as const)("muestra los mismos dos ítems para el rol %s", async (rol, etiqueta) => {
    const user = userEvent.setup()
    renderUserMenu(null, rol)

    expect(screen.getByText(etiqueta)).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: new RegExp(etiqueta) }))

    expect(await screen.findByText("🔑 Cambiar contraseña")).toBeInTheDocument()
    expect(screen.getByText("↩ Cerrar sesión")).toBeInTheDocument()
  })
})
