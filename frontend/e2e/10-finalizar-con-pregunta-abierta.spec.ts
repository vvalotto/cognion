import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS } from "./soporte/datos"
import {
  crearSesion,
  esperarSala,
  esperarTarjetas,
  iniciar,
  mostrarOpciones,
  responder,
  unirse,
} from "./soporte/flujos"
import { expect, test } from "./soporte/prueba"

/**
 * Circuito 10 — finalizar con la pregunta abierta (US-ADJ-58, INV-AEV-03 modificado): con las opciones
 * a la vista, "Finalizar sesión" pide confirmación; "Volver a la pregunta" no cambia nada; al confirmar
 * la sesión termina sin histograma y la respuesta ya dada cuenta para el ranking final.
 */
test("finalizar con la pregunta abierta", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est1 = await estudiante(browser, 1)

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 3, tiempo: 90 })
  await unirse(est1)
  await esperarSala(est1, 1)
  await iniciar(doc)
  await mostrarOpciones(doc)
  await esperarTarjetas(est1)
  const { acumulado } = await responder(est1, "B")

  await doc.page.getByRole("button", { name: "Finalizar sesión" }).click()
  await expect(doc.page.getByRole("heading", { name: "¿Finalizar la sesión ahora?" })).toBeVisible()
  await testInfo.attach("proyeccion-confirmar-finalizar", { body: await doc.page.screenshot(), contentType: "image/png" })
  await doc.page.getByRole("button", { name: "Volver a la pregunta" }).click()
  await expect(doc.page.getByRole("button", { name: "Cerrar pregunta" })).toBeVisible()

  await doc.page.getByRole("button", { name: "Finalizar sesión" }).click()
  await doc.page.getByRole("button", { name: "Finalizar sesión" }).click()
  await expect(doc.page.getByText("¡Gracias por participar!")).toBeVisible()
  await expect(doc.page.getByText(/así respondió el aula/)).toHaveCount(0)

  await expect(est1.page.getByText(`Quedaste 1° con ${acumulado} puntos`)).toBeVisible()

  await cerrar(doc, est1)
})
