import { describe, expect, it } from "vitest"

import { emailsCoinciden } from "./emails"

describe("emailsCoinciden", () => {
  it("dos emails iguales coinciden", () => {
    expect(emailsCoinciden("ada@uner.edu.ar", "ada@uner.edu.ar")).toBe(true)
  })

  it("ignora espacios en los bordes y mayúsculas", () => {
    expect(emailsCoinciden("Ada@Uner.edu.ar", "  ada@uner.edu.ar ")).toBe(true)
  })

  it("un error de tipeo no coincide (el caso que se dio en la UAT)", () => {
    expect(emailsCoinciden("est2.uat@test.com", "est2.uar@test.com")).toBe(false)
  })

  it("un email vacío no coincide con uno escrito", () => {
    expect(emailsCoinciden("ada@uner.edu.ar", "")).toBe(false)
  })
})
