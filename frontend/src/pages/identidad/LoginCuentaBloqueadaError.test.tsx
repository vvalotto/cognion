import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { LoginCuentaBloqueadaError } from "@/pages/identidad/LoginCuentaBloqueadaError"

describe("LoginCuentaBloqueadaError", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje de cuenta bloqueada y dirige a contactar a un Administrador", () => {
    render(<LoginCuentaBloqueadaError />)

    const alert = screen.getByRole("alert")
    expect(alert).toHaveTextContent("Cuenta bloqueada")
    expect(alert).toHaveTextContent("Contactá a un Administrador")
  })
})
