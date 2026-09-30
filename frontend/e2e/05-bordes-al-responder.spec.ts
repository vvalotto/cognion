import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS } from "./soporte/datos"
import {
  acumulado,
  cerrarPregunta,
  crearSesion,
  esperarSala,
  esperarTarjetas,
  finalizar,
  iniciar,
  mostrarOpciones,
  unirse,
  verRanking,
} from "./soporte/flujos"
import { expect, test } from "./soporte/prueba"

/**
 * Circuito 5 — bordes al responder, con 5 s de tiempo límite: doble toque (un solo envío), toque
 * después del tiempo (H5, "Se acabó el tiempo") y no responder hasta que el Docente cierra (H4, +0).
 */
test("doble toque, tiempo agotado y sin respuesta", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const rapido = await estudiante(browser, 1)
  const tarde = await estudiante(browser, 2)
  const ausente = await estudiante(browser, 3)

  const envios: string[] = []
  rapido.page.on("request", (r) => {
    if (r.method() === "POST" && r.url().endsWith("/responder")) envios.push(r.url())
  })

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 1, tiempo: 5 })
  for (const [i, est] of [rapido, tarde, ausente].entries()) {
    await unirse(est)
    await esperarSala(est, i + 1)
  }
  await iniciar(doc)
  await mostrarOpciones(doc)

  // Doble toque inmediato: un solo POST y el resultado.
  await esperarTarjetas(rapido)
  await rapido.page.getByRole("button", { name: "B", exact: true }).dblclick()
  await expect(rapido.page.getByRole("heading", { name: "¡Correcto!" })).toBeVisible()
  expect(envios).toHaveLength(1)

  // Toque después del tiempo límite: el servidor lo rechaza y la pantalla lo explica.
  await esperarTarjetas(tarde)
  await expect(tarde.page.getByRole("timer")).toHaveText("00:00", { timeout: 8_000 })
  await tarde.page.waitForTimeout(1_000)
  await tarde.page.getByRole("button", { name: "B", exact: true }).click()
  await expect(tarde.page.getByRole("heading", { name: "Se acabó el tiempo" })).toBeVisible()
  await expect(tarde.page.getByText("Se acabó el tiempo antes de tu respuesta (+0)")).toBeVisible()
  expect(await acumulado(tarde.page)).toBe(0)
  await testInfo.attach("celular-tiempo-agotado", { body: await tarde.page.screenshot(), contentType: "image/png" })

  // El temporizador en 0 no cierra la pregunta: la cierra el Docente.
  await expect(doc.page.getByRole("button", { name: "Cerrar pregunta" })).toBeVisible()
  await cerrarPregunta(doc)
  await expect(ausente.page.getByText("No respondiste (+0)")).toBeVisible()
  await testInfo.attach("celular-sin-respuesta", { body: await ausente.page.screenshot(), contentType: "image/png" })

  // El celular no revela la correcta ni el ranking al cerrar.
  await expect(ausente.page.getByText(/Ranking/)).toHaveCount(0)

  await verRanking(doc)
  await finalizar(doc)
  await cerrar(doc, rapido, tarde, ausente)
})
