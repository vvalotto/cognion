import { describe, expect, it } from "vitest"

import { cerroAntesDeLoPrevisto } from "@/lib/cierre-actividad"

const AHORA = new Date("2026-10-05T12:00:00Z")

describe("cerroAntesDeLoPrevisto", () => {
  it("es true si la fecha de cierre programada todavía no llegó (cierre manual)", () => {
    expect(cerroAntesDeLoPrevisto("2026-10-12T12:00:00Z", AHORA)).toBe(true)
  })

  it("es false si la fecha de cierre ya pasó (venció por fecha)", () => {
    expect(cerroAntesDeLoPrevisto("2026-10-04T12:00:00Z", AHORA)).toBe(false)
  })

  it("es false si la fecha de cierre es exactamente ahora", () => {
    expect(cerroAntesDeLoPrevisto("2026-10-05T12:00:00Z", AHORA)).toBe(false)
  })
})
