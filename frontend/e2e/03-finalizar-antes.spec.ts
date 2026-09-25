import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS, datos } from "./soporte/datos"
import {
  cerrarPregunta,
  crearSesion,
  esperarSala,
  esperarTarjetas,
  iniciar,
  mostrarOpciones,
  responder,
  unirse,
  verRanking,
} from "./soporte/flujos"
import { expect, test } from "./soporte/prueba"

/**
 * Circuito 3 — finalizar antes de agotar el set (pregunta 1 de 3): podio en la proyección, resultado
 * final en el celular, y la sesión deja de figurar como activa para el Docente y el Estudiante.
 */
test("finalizar en la pregunta 1 de 3", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est1 = await estudiante(browser, 1)

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 3, tiempo: 60 })
  await unirse(est1)
  await esperarSala(est1, 1)
  await iniciar(doc)
  await mostrarOpciones(doc)
  await esperarTarjetas(est1)
  const { acumulado } = await responder(est1, "B")
  await cerrarPregunta(doc)
  await verRanking(doc)

  await expect(doc.page.getByRole("button", { name: "Siguiente pregunta" })).toBeVisible()
  await doc.page.getByRole("button", { name: "Finalizar sesión" }).click()
  await expect(doc.page.getByText("¡Gracias por participar!")).toBeVisible()
  await expect(doc.page.getByRole("list", { name: "Podio" }).getByRole("listitem")).toHaveCount(1)

  await expect(est1.page.getByText(`Quedaste 1° con ${acumulado} puntos`)).toBeVisible()
  await testInfo.attach("celular-final-anticipado", { body: await est1.page.screenshot(), contentType: "image/png" })

  // Ya no figura como activa (hallazgo del estado de la sesión, corregido en esta UAT).
  await doc.page.getByRole("link", { name: /Volver a la Comisión/ }).click()
  await expect(doc.page).toHaveURL(new RegExp(`/actividad-evaluativa/comisiones/${datos().comisionId}`))
  await expect(doc.page.getByRole("button", { name: "Continuar" })).toHaveCount(0)
  await est1.page.goto(`/mis-actividades/materias/${datos().materiaId}/actividades`)
  await expect(est1.page.getByText("Por ahora no hay sesiones en vivo.")).toBeVisible()

  await cerrar(doc, est1)
})
