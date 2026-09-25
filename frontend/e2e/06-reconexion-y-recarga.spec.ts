import { cerrar, docente, estudiante } from "./soporte/actores"
import { TEMAS } from "./soporte/datos"
import {
  cerrarPregunta,
  crearSesion,
  esperarEsperaOpciones,
  esperarSala,
  esperarTarjetas,
  finalizar,
  iniciar,
  mostrarOpciones,
  responder,
  siguiente,
  unirse,
} from "./soporte/flujos"
import { expect, test } from "./soporte/prueba"

/**
 * Circuito 6 — reconexión y recarga (F5). El Estudiante pierde el canal mientras el Docente muestra
 * las opciones y lo recupera; el Docente cierra la pregunta con el canal caído (respaldo de 2 s); y
 * cada pantalla vuelve a la misma etapa al recargar.
 */
test("reconexión del Estudiante y del Docente, y recarga en cada etapa", async ({ browser }, testInfo) => {
  const doc = await docente(browser)
  const est = await estudiante(browser, 1)

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 2, tiempo: 90 })
  // F5 en la sala de espera del Docente y del Estudiante.
  await doc.page.reload()
  await expect(doc.page.getByRole("heading", { name: "Sala de espera" })).toBeVisible()
  await unirse(est)
  await esperarSala(est, 1)
  await est.page.reload()
  await esperarSala(est, 1)

  await iniciar(doc)
  await esperarEsperaOpciones(est, 1, 2)

  // El Estudiante pierde la conexión y se pierde "opciones_mostradas".
  await est.canal.cortar()
  await expect(est.page.getByText("Reconectando…")).toBeVisible()
  await testInfo.attach("celular-reconectando", { body: await est.page.screenshot(), contentType: "image/png" })
  await mostrarOpciones(doc)
  await est.page.waitForTimeout(3_000)
  est.canal.restablecer()
  await expect(est.page.getByText("Reconectando…")).toBeHidden({ timeout: 20_000 })
  await esperarTarjetas(est)
  const restante = Number((await est.page.getByRole("timer").textContent())?.split(":")[1])
  expect(restante).toBeLessThan(90)

  // F5 del Docente con las opciones a la vista: misma etapa, temporizador que sigue descontando.
  await doc.page.reload()
  await expect(doc.page.getByRole("button", { name: "Cerrar pregunta" })).toBeVisible()
  // F5 del Estudiante con las tarjetas: sigue pudiendo responder (no perdió la participación).
  await est.page.reload()
  await esperarTarjetas(est)
  await responder(est, "B")
  await expect(doc.page.getByText("1 / 1 ya respondieron")).toBeVisible()
  // F5 después de responder: el resultado, sin tarjetas.
  await est.page.reload()
  await expect(est.page.getByRole("heading", { name: "Ya respondiste" })).toBeVisible()
  await expect(est.page.getByRole("button", { name: "B", exact: true })).toHaveCount(0)

  // El Docente cierra con su canal caído: el respaldo de 2 s recalcula y muestra el histograma.
  await doc.canal.cortar()
  await expect(doc.page.getByText("Reconectando…")).toBeVisible()
  await cerrarPregunta(doc)
  doc.canal.restablecer()
  await expect(doc.page.getByText("Reconectando…")).toBeHidden({ timeout: 20_000 })
  // F5 en el histograma/ranking: vuelve al histograma con sus datos.
  await doc.page.reload()
  await expect(doc.page.getByText(/así respondió el aula/)).toBeVisible()
  await expect(doc.page.getByTestId("barra-histograma").nth(1)).toHaveText("1")

  await expect(doc.page.getByText(/Ranking — tras la pregunta/)).toBeVisible({ timeout: 9_000 })
  await siguiente(doc)
  await esperarEsperaOpciones(est, 2, 2)
  await est.page.reload()
  await esperarEsperaOpciones(est, 2, 2)
  await mostrarOpciones(doc)
  await cerrarPregunta(doc)
  await expect(est.page.getByText("No respondiste (+0)")).toBeVisible()
  await expect(doc.page.getByText(/Ranking — tras la pregunta/)).toBeVisible({ timeout: 9_000 })
  await finalizar(doc)

  // F5 con la sesión finalizada: podio en la proyección, resultado final en el celular.
  await doc.page.reload()
  await expect(doc.page.getByText("¡Gracias por participar!")).toBeVisible()
  await est.page.reload()
  await expect(est.page.getByText(/Quedaste 1° con \d+ puntos/)).toBeVisible()

  await cerrar(doc, est)
})
