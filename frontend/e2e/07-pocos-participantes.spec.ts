import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS, datos } from "./soporte/datos"
import {
  cerrarPregunta,
  crearSesion,
  esperarSala,
  esperarTarjetas,
  finalizar,
  iniciar,
  mostrarOpciones,
  responder,
  unirse,
  verRanking,
} from "./soporte/flujos"
import { expect, test } from "./soporte/prueba"

/**
 * Circuito 7 — pocos participantes. Sin nadie unido no se puede iniciar (revisión manual 2026-09-26,
 * reemplaza el "podés iniciar igual" de H9); "Salir" deja la sesión activa y se retoma con
 * "Continuar"; con uno solo, ranking y podio de un puesto.
 */
test("sin participantes no se inicia; 'Salir' deja la sesión activa y se retoma", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est = await estudiante(browser, 1)
  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 1, tiempo: 60 })
  await expect(doc.page.getByRole("alert")).toContainText("al menos un estudiante")
  await expect(doc.page.getByRole("button", { name: "Iniciar sesión" })).toBeDisabled()
  await testInfo.attach("sala-sin-participantes", { body: await doc.page.screenshot(), contentType: "image/png" })

  // Salir no toca la sesión: sigue en "Sesiones en vivo activas" y se retoma.
  await doc.page.getByRole("button", { name: "‹ Salir" }).click()
  await expect(doc.page).toHaveURL(new RegExp(`/actividad-evaluativa/comisiones/${datos().comisionId}`))
  await doc.page.getByRole("button", { name: "Continuar" }).click()
  await expect(doc.page.getByRole("heading", { name: "Sala de espera" })).toBeVisible()

  // Con el primero unido, se habilita.
  await unirse(est)
  await esperarSala(est, 1)
  await expect(doc.page.getByRole("button", { name: "Iniciar sesión" })).toBeEnabled()
  await iniciar(doc)

  // "Salir" también desde la proyección, y se retoma en la misma etapa.
  await doc.page.getByRole("link", { name: "‹ Salir" }).click()
  await expect(doc.page).toHaveURL(new RegExp(`/actividad-evaluativa/comisiones/${datos().comisionId}`))
  await doc.page.getByRole("button", { name: "Continuar" }).click()
  await expect(doc.page.getByRole("button", { name: "Mostrar opciones" })).toBeVisible()

  await mostrarOpciones(doc)
  await cerrarPregunta(doc)
  await verRanking(doc)
  await finalizar(doc)
  await cerrar(doc, est)
})

test("un solo participante: ranking y podio con un puesto", async ({ browser }) => {
  const doc = await docente(browser)
  const est = await estudiante(browser, 1)
  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 1, tiempo: 60 })
  await unirse(est)
  await esperarSala(est, 1)
  await iniciar(doc)
  await mostrarOpciones(doc)
  await esperarTarjetas(est)
  await responder(est, "B")
  await cerrarPregunta(doc)
  await verRanking(doc)
  await expect(doc.page.getByRole("listitem")).toHaveCount(1)
  await finalizar(doc)
  await expect(doc.page.getByRole("list", { name: "Podio" }).getByRole("listitem")).toHaveCount(1)
  await expect(est.page.getByText(/Quedaste 1° con \d+ puntos/)).toBeVisible()
  await cerrar(doc, est)
})
