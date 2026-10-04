import { cleanup, render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router"
import { afterEach, describe, expect, it } from "vitest"

import { LoginCuentaBloqueadaError } from "@/pages/identidad/LoginCuentaBloqueadaError"

function renderizar() {
  render(
    <MemoryRouter>
      <LoginCuentaBloqueadaError />
    </MemoryRouter>,
  )
}

describe("LoginCuentaBloqueadaError", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje de cuenta bloqueada y ofrece pedirle a un Administrador que restablezca", () => {
    renderizar()

    const alert = screen.getByRole("alert")
    expect(alert).toHaveTextContent("Cuenta bloqueada")
    expect(alert).toHaveTextContent("pedirle a un Administrador que la restablezca")
  })

  it("ofrece la recuperación de contraseña por email con un link a /recuperar-password", () => {
    renderizar()

    const link = screen.getByRole("link", { name: "recuperar tu contraseña por email" })
    expect(link).toHaveAttribute("href", "/recuperar-password")
  })
})
