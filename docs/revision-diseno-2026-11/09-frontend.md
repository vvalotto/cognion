# 09 · Frontend

> Pregunta: ¿el cliente está bien estructurado y acompaña al backend?

## Qué se miró

- Estructura y tamaño de `frontend/src/` (263 archivos; 16.763 líneas sin tests).
- [`api-client.ts`](../../frontend/src/lib/api-client.ts), `session.ts` y los ocho módulos `*-api.ts`.
- Patrones de carga de datos, supresiones de lint y dependencias de `package.json`.

No se ejecutó la aplicación ni se revisó el diseño visual. La revisión es de estructura.

## Fortalezas

- **Tipado sin escapes.** 0 usos de `any` y ningún `@ts-ignore`.
- **Un solo punto de salida a la red.** Todo `fetch` pasa por `apiFetch`, que agrega el token y traduce los errores a `ApiError`.
- **La estructura refleja los contextos.** `pages/` se divide en `actividad-evaluativa`, `analytics`, `banco-preguntas`, `cuentas` e `identidad`, y hay un módulo de API por contexto.
- **Lógica fuera de los componentes.** Ranking, temporizador, fechas y reglas de contraseña están en `lib/` como funciones con su test.
- **Pocas dependencias.** Sin gestor de estado global ni librerías de datos: React, React Router, Tailwind y componentes base.

## Hallazgos

### FE-01 · El contrato con el backend se copia a mano

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:** los módulos `*-api.ts` exportan 67 tipos que reproducen los esquemas Pydantic de los routers (`schemas.py` tiene 380 líneas en Actividad Evaluativa y 301 en Identidad). No hay generación desde OpenAPI ni test que compare ambos lados.
- **Por qué importa:** FastAPI ya publica el contrato completo. Copiarlo a mano significa que un campo renombrado en el backend pasa todos los tests de los dos lados (Vitest usa `fetch` simulado) y falla en el navegador. `CLAUDE.md` reconoce el límite ("Vitest con `fetch` mockeado no ve…") y lo compensa con verificación manual.
- **Recomendación:** generar los tipos con `openapi-typescript` desde el esquema de la API y verificar en el CI que el archivo generado esté al día. Convierte una clase entera de hallazgos de UAT en errores de compilación.

### FE-02 · Cada página resuelve la carga de datos por su cuenta

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado (el patrón), Inferido (la duplicación) · **Esfuerzo:** M
- **Evidencia:** 58 páginas usan `useEffect` para pedir datos. No hay un hook compartido de consulta: los únicos hooks de `lib/` son el del canal en vivo y el de foco de errores. Hay 4 supresiones de `react-hooks/exhaustive-deps`, tres en páginas con carga de datos.
- **Por qué importa:** estados de carga, error, cancelación al desmontar y recarga se reescriben en cada página. Las supresiones de dependencias son el síntoma clásico de ese patrón y una fuente conocida de datos viejos en pantalla.
- **Recomendación:** un hook propio `useConsulta(fn, deps)` que resuelva carga, error, cancelación con `AbortSignal` y recarga. No hace falta una librería; alcanza con unificar lo que ya existe.

### FE-03 · El cliente HTTP depende del router

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `api-client.ts`, línea 1: `import { router } from "@/router"`, usado para navegar a `/login` ante un 401. `router.tsx` importa todas las páginas, y las páginas importan el cliente.
- **Por qué importa:** es un ciclo de dependencias entre la capa más baja (`lib/`) y la más alta (`router`). Cualquier test de un módulo de API arrastra el árbol completo de páginas, y la capa de acceso a datos conoce las rutas de la aplicación.
- **Recomendación:** que el cliente reciba un manejador (`alPerderSesion`) que el punto de entrada de la aplicación registra una vez.

### FE-04 · El token de sesión vive en `localStorage`

- **Vara:** Decisión · **Severidad:** Media · **Confianza:** Verificado · **Esfuerzo:** M
- **Evidencia:** `session.ts` guarda el JWT en `localStorage`. El token dura 60 minutos y no se renueva (`ADR-013`).
- **Por qué importa:** cualquier script que corra en la página puede leerlo. El riesgo es acotado (no hay contenido de terceros y los enunciados los carga el docente), pero los textos de preguntas son contenido escrito por usuarios y se muestran a toda la comisión. La consecuencia operativa del vencimiento está en [AQ-04](06-atributos-de-calidad.md#aq-04--la-sesión-de-usuario-puede-vencer-en-mitad-de-una-clase).
- **Recomendación:** dejar asentado el riesgo aceptado en `ADR-013` y agregar una cabecera `Content-Security-Policy` en Caddy. Pasar a cookie `HttpOnly` solo si cambia el modelo de amenazas.

### FE-05 · Todas las rutas en un archivo de 538 líneas

- **Vara:** Decisión · **Severidad:** Baja · **Confianza:** Verificado · **Esfuerzo:** S
- **Evidencia:** `router.tsx` es el archivo más grande del frontend sin contar tests.
- **Por qué importa:** es el punto donde todos los cambios de pantalla coinciden, y contradice la división por contexto que el resto del frontend respeta.
- **Recomendación:** un archivo de rutas por contexto, compuestos en `router.tsx`.

### FE-06 · Pocos componentes compartidos frente al tamaño de las páginas

- **Vara:** Decisión · **Severidad:** Baja · **Confianza:** Inferido · **Esfuerzo:** M
- **Evidencia:** `components/` tiene 24 archivos y 1.101 líneas; `pages/` supera las 25.000 con tests. Hay pares de páginas grandes y parecidas: `NuevaPreguntaOpcionMultiple.tsx` (295 líneas) y `EditarPregunta.tsx` (358).
- **Por qué importa:** sugiere formularios duplicados entre alta y edición. No se confirmó leyendo ambos archivos.
- **Recomendación:** revisar esos pares antes de implementar `RF-07`, que agrega otra vía de alta de preguntas.

## Juicio

El frontend es disciplinado en lo local (tipos, un cliente, lógica extraída, tests por página) y artesanal en lo transversal (contrato, carga de datos, navegación ante errores). FE-01 es la mejora de mayor impacto: ataca la causa de los defectos que hoy solo se detectan mirando la pantalla.
