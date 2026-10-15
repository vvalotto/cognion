import { cleanup, render, screen } from "@testing-library/react"
import { afterEach, describe, expect, it } from "vitest"

import { LoginCuentaDeshabilitadaError } from "@/pages/identidad/LoginCuentaDeshabilitadaError"

describe("LoginCuentaDeshabilitadaError", () => {
  afterEach(() => {
    cleanup()
  })

  it("muestra el mensaje de cuenta deshabilitada y dirige a contactar a un Administrador", () => {
    render(<LoginCuentaDeshabilitadaError />)

    const alert = screen.getByRole("alert")
    expect(alert).toHaveTextContent("Cuenta deshabilitada")
    expect(alert).toHaveTextContent("dada de baja")
    expect(alert).toHaveTextContent("Contactá a un Administrador")
  })

  it("no ofrece recuperar la contraseña: no reactiva una cuenta dada de baja", () => {
    render(<LoginCuentaDeshabilitadaError />)

    expect(screen.queryByRole("link")).toBeNull()
  })
})
