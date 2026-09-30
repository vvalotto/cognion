import { expect, type Page } from "@playwright/test"

import type { Actor } from "./actores"
import { datos } from "./datos"

export interface OpcionesSesion {
  tema: string
  cantidad: number
  tiempo: number
}

/** Docente: desde el detalle de la Comisión crea la sesión y queda en la sala de espera. */
export async function crearSesion(docente: Actor, opciones: OpcionesSesion): Promise<string> {
  const { page } = docente
  await page.goto(`/actividad-evaluativa/comisiones/${datos().comisionId}`)
  await page.getByRole("button", { name: /Nueva sesión en vivo/ }).click()
  await page.getByLabel("Tema (opcional)").selectOption(opciones.tema)
  await page.getByLabel("Cantidad de preguntas").fill(String(opciones.cantidad))
  await page.getByLabel("Tiempo límite por pregunta (segundos)").fill(String(opciones.tiempo))
  await page.getByRole("button", { name: "Crear sesión" }).click()
  await expect(page).toHaveURL(/\/sesiones-en-vivo\/[^/]+\/sala/)
  await expect(page.getByRole("heading", { name: "Sala de espera" })).toBeVisible()
  return page.url().split("/sesiones-en-vivo/")[1].split("/")[0]
}

/** Estudiante: abre las actividades de su materia, toca la tarjeta de la sesión y queda en la sala. */
export async function unirse(estudiante: Actor) {
  const { page } = estudiante
  await page.goto(`/mis-actividades/materias/${datos().materiaId}/actividades`)
  await page.getByRole("button", { name: new RegExp(datos().materiaNombre) }).click()
  await expect(page).toHaveURL(/\/mis-sesiones-en-vivo\//)
}

export async function esperarSala(estudiante: Actor, participantes: number) {
  await expect(estudiante.page.getByRole("heading", { name: "¡Te uniste!" })).toBeVisible()
  await expect(
    estudiante.page.getByText(`${participantes} ${participantes === 1 ? "participante" : "participantes"}`),
  ).toBeVisible()
}

export async function iniciar(docente: Actor) {
  await docente.page.getByRole("button", { name: "Iniciar sesión" }).click()
  await expect(docente.page).toHaveURL(/\/proyeccion/)
  await expect(docente.page.getByRole("button", { name: "Mostrar opciones" })).toBeVisible()
}

export async function mostrarOpciones(docente: Actor) {
  await docente.page.getByRole("button", { name: "Mostrar opciones" }).click()
  await expect(docente.page.getByRole("button", { name: "Cerrar pregunta" })).toBeVisible()
}

/** Cierra la pregunta y devuelve cuánto tardó en aparecer el histograma (ms). */
export async function cerrarPregunta(docente: Actor): Promise<number> {
  const inicio = Date.now()
  await docente.page.getByRole("button", { name: "Cerrar pregunta" }).click()
  await expect(docente.page.getByText(/así respondió el aula/)).toBeVisible()
  return Date.now() - inicio
}

export async function verRanking(docente: Actor) {
  await docente.page.getByRole("button", { name: /Ver ranking ahora/ }).click()
  await expect(docente.page.getByText(/Ranking — tras la pregunta/)).toBeVisible()
}

export async function siguiente(docente: Actor) {
  await docente.page.getByRole("button", { name: "Siguiente pregunta" }).click()
  await expect(docente.page.getByRole("button", { name: "Mostrar opciones" })).toBeVisible()
}

export async function finalizar(docente: Actor) {
  await docente.page.getByRole("button", { name: "Finalizar sesión" }).click()
  await expect(docente.page.getByText("¡Gracias por participar!")).toBeVisible()
}

export interface ResultadoRespuesta {
  correcta: boolean
  puntos: number
  acumulado: number
}

/** Estudiante: toca la tarjeta con ese texto y lee su resultado. */
export async function responder(estudiante: Actor, texto: string): Promise<ResultadoRespuesta> {
  const { page } = estudiante
  await page.getByRole("button", { name: texto, exact: true }).click()
  const titulo = page.getByRole("heading", { name: /^(¡Correcto!|Incorrecto)$/ })
  await expect(titulo).toBeVisible()
  const correcta = (await titulo.textContent()) === "¡Correcto!"
  const puntos = Number((await page.getByText(/puntos en esta pregunta/).textContent())?.match(/\d+/)?.[0])
  return { correcta, puntos, acumulado: await acumulado(page) }
}

export async function acumulado(page: Page): Promise<number> {
  return Number((await page.getByText(/^\d+ pts$/).textContent())?.match(/\d+/)?.[0])
}

export async function esperarTarjetas(estudiante: Actor) {
  await expect(estudiante.page.getByText(/un solo intento, no se puede cambiar después/)).toBeVisible()
}

export async function esperarEsperaOpciones(estudiante: Actor, n: number, total: number) {
  await expect(estudiante.page.getByText(`Pregunta ${n} de ${total}`)).toBeVisible()
  await expect(estudiante.page.getByText("Esperá a que el Docente muestre las opciones.")).toBeVisible()
}
