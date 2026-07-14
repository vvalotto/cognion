# Visión — Cognión

| Campo | Valor |
|-------|-------|
| **Documento** | Visión del Producto |
| **Versión** | 1.0 |
| **Fecha** | 2026-07-14 |
| **Insumos** | `docs/rf/RF_v1.md`, `docs/rf/RNF_v1.md`, `docs/rf/ARQ_v1.md` |

---

## 1. El problema que resuelve

Un docente universitario (Ingeniería de Software y Gestión de Proyectos, FIUNER) evalúa
comisiones de 30 a 60 alumnos con cuestionarios. Hoy ese proceso depende de herramientas
genéricas y no ofrece ni seguimiento histórico del desempeño por alumno/tema, ni una dinámica
de evaluación en vivo gamificada para el aula.

**Cognión resuelve esto** con una plataforma web de evaluación universitaria que cubre dos
modalidades de sesión — período abierto (parcial/final asincrónico) y en vivo (estilo
Kahoot!) — sobre un banco de preguntas clasificado, con analytics de desempeño individual y
grupal.

---

## 2. Usuarios del sistema

| Rol | Responsabilidad principal | Acceso |
|-----|---------------------------|--------|
| **Administrador** | Resuelve problemas de cuentas de usuarios (bloqueos, recuperación) | Back-office |
| **Docente** | Arma y mantiene el banco de preguntas, crea y conduce sesiones, accede a analytics y KPIs | Web full |
| **Estudiante** | Se registra por invitación, participa en sesiones, consulta su propio desempeño | Web, cualquier dispositivo |

### Objetivos por rol

**Administrador:** resolver problemas de cuenta sin depender del docente.

**Docente:** armar el banco de preguntas una vez y reutilizarlo entre comisiones; conducir
sesiones de evaluación (abiertas y en vivo) con mínima fricción operativa; ver desempeño real
de alumnos y temas sin procesar planillas a mano.

**Estudiante:** registrarse con un link de invitación, rendir la evaluación en el modo que
corresponda, y consultar su propio historial de desempeño sin depender de terceros.

---

## 3. Alcance del sistema v1

### Dentro del alcance

- **Registro por invitación** — el docente genera un link por comisión; el estudiante se
  registra sin aprobación manual (RF-01).
- **Tres roles** con acceso segmentado: administrador, docente, estudiante (RF-02, RF-03).
- **Banco de preguntas** clasificado por materia, unidad temática, tema, dificultad e
  importancia conceptual; tipos opción múltiple y verdadero/falso, extensible a futuros tipos
  (RF-04, RF-05, RF-06).
- **Migración desde PDFs** existentes del docente (RF-07, mecanismo pendiente de decisión).
- **Sesión en vivo (Kahoot!-style)**: mismo set de preguntas para todos, ranking en tiempo real,
  puntaje por tiempo/corrección/dificultad/importancia (RF-08, RF-09, RF-10).
- **Sesión de período abierto**: ventana de disponibilidad configurable y modificable en
  caliente, set aleatorio por estudiante, persistencia respuesta a respuesta, revisión al
  finalizar (RF-11, RF-11b, RF-12, RF-13).
- **Notificaciones por email** de apertura/cierre de sesión de período abierto (RF-14).
- **Portal del estudiante** con historial de desempeño propio (RF-15).
- **Analytics del docente**: seguimiento por alumno, por curso/tema, KPIs históricos (RF-16,
  RF-17, RF-18).

### Fuera de alcance v1

- Múltiples docentes — uso personal del docente por ahora.
- Reportes exportables — se evalúa en una etapa posterior.

### Diferido

- Selección no aleatoria de preguntas (personalización por historial/desempeño).
- Notificaciones por canales distintos al email (la arquitectura debe preverlo, no
  implementarlo).
- Definición detallada de los KPIs del dashboard docente — se definen incrementalmente con uso
  real.

---

## 4. Restricciones de contexto

| Dimensión | Restricción |
|-----------|-------------|
| **Escala** | 30–60 alumnos por comisión, docente único |
| **Modalidad** | Sistema exclusivamente online — sin PWA, sin soporte offline |
| **Dispositivos** | Alumnos acceden desde PC, tablet o smartphone, cualquier browser vigente |
| **Proyección en aula** | El docente proyecta la sesión en vivo; legibilidad completa desde cualquier asiento (criterio de diseño UX pendiente) |
| **Infraestructura** | Fly.io confirmado para testing; producción pendiente de decisión institucional (nube vs. servidor FIUNER) |
| **Mantenimiento** | Equipo de desarrollo unipersonal — CI/CD sin fricción es una restricción de facto |

---

## 5. Criterios de éxito del producto

Derivados de los escenarios de calidad de `docs/rf/RNF_v1.md`:

| Criterio | Escenario RNF | Condición verificable |
|----------|---------------|------------------------|
| Ranking en tiempo real | Rendimiento §1 | Procesamiento server-side ≤ 100ms; percibido por el usuario < 1s |
| Cero pérdida de respuestas | Confiabilidad | Ninguna respuesta confirmada en período abierto se pierde ante desconexión |
| Continuidad ante caída en vivo | Disponibilidad §1 | Ventana de tolerancia de 5 minutos antes de cancelar la sesión |
| Extensión de plazo ante caída | Disponibilidad §2 | El docente puede modificar el cierre de una sesión activa (RF-11b) |
| Control de acceso por rol | Seguridad | Ningún actor accede a recursos fuera de su rol — verificable por revisión de API |
| Interfaz responsive | Usabilidad §1 | Funcional sin degradación en browsers vigentes, cualquier tamaño de dispositivo |
| Extensibilidad de tipos de pregunta | Mantenibilidad | Nuevo tipo de pregunta sin modificar lógica central de sesiones/scoring/analytics |
| Trazabilidad completa | Observabilidad | Event sourcing permite reconstruir la secuencia de hechos de una sesión |
| Deployment sin fricción | Administrabilidad §1 | Push a `main` despliega automáticamente sin intervención manual |

---

## 6. Lo que Cognión NO es

- No es un sistema de gestión académica general (no reemplaza al sistema de gestión de
  alumnos de la institución).
- No es una herramienta de proctoring ni de detección de fraude.
- No gestiona múltiples docentes ni cátedras compartidas en v1.
- No genera reportes exportables en v1.
- No tiene soporte offline — depende de conectividad activa.

---

## 7. Relación con el ensayo IEDD

Cognión es el segundo proyecto del ensayo IEDD (Ingeniería de Especificaciones DDD con IA),
después de AtaraxiaDive. La lección incorporada de ese proyecto anterior fue front-loading:
event storming del dominio y diseño UX **antes** de las US-IEDD constructivas, en vez de
descubrirlos sobre la marcha — ver `docs/rf/PLAN_v1.md`, sección "Modelado de dominio antes de
construir, por BC", y `docs/iedd/04-Hipotesis_Ensayo_IA_Ingenieria_Human_In_The_Loop.md`.

---

## 8. Vínculo con la cadena de artefactos

```
Este documento (vision.md)
  └── produce → RF_v1.md / RNF_v1.md   ← elicitación funcional y de calidad
        └── produce → ARQ_v1.md         ← arquitectura de referencia, ADRs
              └── produce → PLAN_v1.md  ← plan de incrementos
                    └── produce → Iteración 0 — Modelado (event storming por BC + UX)
                          └── produce → US-IEDD (docs/specs/incN/)
                                └── produce → src/
```

---

*Creado: 2026-07-14.*
*Mantenido por: Víctor Valotto + Claude.*
