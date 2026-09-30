import { expect, test } from "./soporte/prueba"

import { cerrar, docente, estudiante, loginPorPantalla } from "./soporte/actores"
import { PASSWORD, TEMAS, datos } from "./soporte/datos"
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

/**
 * Circuito 1 — sesión completa: login real por pantalla, entrada por clic desde la Comisión, 3
 * Estudiantes, 3 preguntas (mostrar → responder → cerrar → histograma → ranking → avanzar), final.
 * Verifica que el podio coincide con los acumulados que vio cada Estudiante y que el canal no se
 * abre en bucle con `StrictMode`.
 */
test("sesión completa con 3 Estudiantes y 3 preguntas", async ({ browser }, testInfo) => {
  const doc = await docente(browser, { sesionInyectada: false })
  await loginPorPantalla(doc.page, datos().docente.email, PASSWORD)
  const alumnos = []
  for (let n = 1; n <= 3; n++) {
    const est = await estudiante(browser, n, { sesionInyectada: false })
    await loginPorPantalla(est.page, datos().estudiantes[n - 1].email, PASSWORD)
    alumnos.push(est)
  }

  await crearSesion(doc, { tema: TEMAS.opcionMultiple, cantidad: 3, tiempo: 60 })
  for (const [i, est] of alumnos.entries()) {
    await unirse(est)
    await esperarSala(est, i + 1)
  }
  await expect(doc.page.getByText("Participantes (3)")).toBeVisible()
  await testInfo.attach("sala-docente", { body: await doc.page.screenshot(), contentType: "image/png" })

  await iniciar(doc)
  // Respuestas: el 1 acierta siempre, el 2 acierta las dos primeras, el 3 nunca.
  const elecciones = [["B", "B", "B"], ["B", "B", "A"], ["C", "D", "A"]]
  const acumulados = [0, 0, 0]
  const latencias: number[] = []

  for (let p = 0; p < 3; p++) {
    for (const est of alumnos) await esperarEsperaOpciones(est, p + 1, 3)
    await mostrarOpciones(doc)
    for (const [i, est] of alumnos.entries()) {
      await esperarTarjetas(est)
      const resultado = await responder(est, elecciones[i][p])
      expect(resultado.correcta).toBe(elecciones[i][p] === "B")
      if (!resultado.correcta) expect(resultado.puntos).toBe(0)
      acumulados[i] = resultado.acumulado
    }
    await expect(doc.page.getByText("3 / 3 ya respondieron")).toBeVisible()
    if (p === 0) {
      await testInfo.attach("proyeccion-opciones", { body: await doc.page.screenshot(), contentType: "image/png" })
      await testInfo.attach("celular-resultado", { body: await alumnos[0].page.screenshot(), contentType: "image/png" })
    }
    latencias.push(await cerrarPregunta(doc))
    if (p === 0) await testInfo.attach("proyeccion-histograma", { body: await doc.page.screenshot(), contentType: "image/png" })
    // El histograma pasa solo al ranking a los 6 s.
    await expect(doc.page.getByText(/Ranking — tras la pregunta/)).toBeVisible({ timeout: 9_000 })
    if (p < 2) await siguiente(doc)
  }
  await testInfo.attach("proyeccion-ranking", { body: await doc.page.screenshot(), contentType: "image/png" })

  await finalizar(doc)
  await testInfo.attach("proyeccion-podio", { body: await doc.page.screenshot(), contentType: "image/png" })

  // Podio de la proyección = acumulados que vio cada Estudiante, en orden.
  const podio = doc.page.getByRole("list", { name: "Podio" })
  for (const [i, est] of alumnos.entries()) {
    const puesto = podio.getByRole("listitem").filter({ hasText: est.usuario.nombre })
    await expect(puesto).toContainText(`${acumulados[i]} pts`)
  }
  expect(acumulados[0]).toBeGreaterThan(acumulados[1])
  expect(acumulados[1]).toBeGreaterThan(acumulados[2])
  expect(acumulados[2]).toBe(0)

  // Resultado final en cada celular: posición y puntaje propios.
  for (const [i, est] of alumnos.entries()) {
    await expect(est.page.getByText(`Quedaste ${i + 1}° con ${acumulados[i]} puntos`)).toBeVisible()
  }
  await testInfo.attach("celular-final", { body: await alumnos[0].page.screenshot(), contentType: "image/png" })

  // StrictMode: un solo socket abierto por pantalla al final, sin reconexiones en bucle.
  for (const actor of [doc, ...alumnos]) {
    expect(actor.canal.abiertos).toBeLessThanOrEqual(1)
    expect(actor.canal.aperturas).toBeLessThanOrEqual(6)
  }
  // RNF: el histograma (con el ranking) aparece en menos de 1 s desde el cierre.
  testInfo.annotations.push({ type: "latencia-cierre-ms", description: latencias.join(", ") })
  for (const ms of latencias) expect(ms).toBeLessThan(1000)

  await cerrar(doc, ...alumnos)
})
