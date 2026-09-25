import { execFileSync } from "node:child_process"
import { mkdirSync, writeFileSync } from "node:fs"
import { dirname, join } from "node:path"

import { api, idDeToken, login } from "./api"
import { ESTADO, PASSWORD, TEMAS, type DatosSembrados, type Usuario } from "./datos"

const RAIZ = join(import.meta.dirname, "..", "..", "..")
const CANTIDAD_ESTUDIANTES = 6

async function crearPreguntas(bancoId: string, token: string) {
  const comun = { banco_id: bancoId, unidad_tematica: "Unidad 1", dificultad: "medio", importancia: "alto" }
  for (let i = 1; i <= 6; i++) {
    await api("POST", "/preguntas/opcion-multiple", token, {
      ...comun,
      tema: TEMAS.opcionMultiple,
      texto: `Pregunta E2E de opción múltiple #${i}: ¿cuál es la opción B?`,
      opciones: ["A", "B", "C", "D"].map((texto) => ({ texto, es_correcta: texto === "B" })),
    })
  }
  for (let i = 1; i <= 3; i++) {
    await api("POST", "/preguntas/verdadero-falso", token, {
      ...comun,
      tema: TEMAS.verdaderoFalso,
      texto: `Pregunta E2E de Verdadero/Falso #${i}: esta afirmación es verdadera.`,
      respuesta_correcta: true,
    })
  }
  for (let i = 1; i <= 3; i++) {
    await api("POST", "/preguntas/opcion-multiple", token, {
      ...comun,
      tema: TEMAS.tresOpciones,
      texto: `Pregunta E2E de tres opciones #${i}: ¿cuál es la opción B?`,
      opciones: ["A", "B", "C"].map((texto) => ({ texto, es_correcta: texto === "B" })),
    })
  }
}

/**
 * Siembra por API real (sin tocar `pytest` ni la base con fixtures): Administrador, Docente asignado a
 * una Comisión, Materia con 12 preguntas (6 de opción múltiple, 3 V/F, 3 de tres opciones) y 6
 * Estudiantes. Prefijo único por corrida; `limpiar.ts` borra todo al final.
 */
export default async function sembrar() {
  const prefijo = `uat-e2e-${Date.now()}`
  const email = (rol: string) => `${prefijo}-${rol}@fiuner.edu.ar`

  execFileSync(join(RAIZ, ".venv/bin/python"), [join(RAIZ, "scripts/seed_admin.py")], {
    cwd: RAIZ,
    env: { ...process.env, ADMIN_NOMBRE: "UAT E2E Admin", ADMIN_EMAIL: email("admin"), ADMIN_PASSWORD: PASSWORD },
    stdio: "ignore",
  })
  const adminToken = await login(email("admin"))

  await api("POST", "/identidad/autoregistro/docente", undefined, {
    nombre: "UAT E2E Docente",
    email: email("docente"),
    password: PASSWORD,
  })
  const docenteToken = await login(email("docente"))
  const docente: Usuario = {
    id: idDeToken(docenteToken),
    email: email("docente"),
    nombre: "UAT E2E Docente",
    token: docenteToken,
  }

  const materiaNombre = `${prefijo}-materia`
  const materia = await api<{ id: string; banco_id: string }>("POST", "/materias", adminToken, {
    nombre: materiaNombre,
  })
  if (materia.status !== 201) throw new Error(`materia: HTTP ${materia.status}`)
  await crearPreguntas(materia.body.banco_id, docenteToken)

  const comision = await api<{ id: string }>("POST", "/comisiones", adminToken, {
    materia_id: materia.body.id,
    horario: "Lunes 18-22 (E2E)",
    administrador_id: idDeToken(adminToken),
  })
  if (comision.status !== 201) throw new Error(`comision: HTTP ${comision.status}`)
  await api("POST", `/comisiones/${comision.body.id}/docentes`, adminToken, { docente_id: docente.id })

  const estudiantes: Usuario[] = []
  for (let n = 1; n <= CANTIDAD_ESTUDIANTES; n++) {
    const nombre = `UAT E2E Estudiante ${n}`
    await api("POST", "/identidad/autoregistro/estudiante", undefined, {
      nombre,
      email: email(`est${n}`),
      password: PASSWORD,
      comision_id: comision.body.id,
    })
    const token = await login(email(`est${n}`))
    estudiantes.push({ id: idDeToken(token), email: email(`est${n}`), nombre, token })
  }

  const sembrados: DatosSembrados = {
    prefijo,
    materiaId: materia.body.id,
    materiaNombre,
    comisionId: comision.body.id,
    docente,
    estudiantes,
  }
  mkdirSync(dirname(ESTADO), { recursive: true })
  writeFileSync(ESTADO, JSON.stringify(sembrados, null, 2))
}
