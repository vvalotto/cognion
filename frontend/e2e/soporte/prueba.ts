import { test as base } from "@playwright/test"

import { finalizarSesionesAbiertas } from "./api"
import { datos } from "./datos"

/** `test` de los circuitos: al terminar cada uno, cierra por API las sesiones que hayan quedado abiertas. */
export const test = base.extend<{ limpiarSesiones: void }>({
  limpiarSesiones: [
    // Playwright exige desestructurar los fixtures aunque este no use ninguno.
    // oxlint-disable-next-line no-empty-pattern
    async ({}, use) => {
      await use()
      await finalizarSesionesAbiertas(datos().comisionId, datos().docente.token)
    },
    { auto: true },
  ],
})

export { expect } from "@playwright/test"
