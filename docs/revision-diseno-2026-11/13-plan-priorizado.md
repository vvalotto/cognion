# 13 · Plan priorizado

> Pregunta: ¿en qué orden conviene actuar, y qué quedó sin revisar?

## Todos los hallazgos

60 hallazgos: 11 de severidad alta, 35 media y 14 baja.

| Capítulo | Alta | Media | Baja |
|---|---|---|---|
| 02 Conformidad | — | CA-01, CA-03 | CA-02 |
| 03 Contextos | AC-01, AC-03 | AC-02, AC-04 | — |
| 04 Dominio | DM-01, DM-02, DM-05 | DM-03, DM-04, DM-06, DM-07 | — |
| 05 Implementación | IM-02, IM-03 | IM-01, IM-04, IM-05, IM-06 | IM-07 |
| 06 Calidad | AQ-01 | AQ-02, AQ-03, AQ-04 | — |
| 07 Verificación | — | VT-01, VT-02, VT-03, VT-04 | VT-05 |
| 08 Instrumentos | IQ-01 | IQ-02, IQ-03 | IQ-04, IQ-05, IQ-06 |
| 09 Frontend | — | FE-01, FE-02, FE-03, FE-04 | FE-05, FE-06 |
| 10 Despliegue | DO-02 | DO-01, DO-03, DO-04, DO-06 | DO-05 |
| 11 Proceso | PR-01 | PR-02, PR-03, PR-04 | PR-05, PR-06 |
| 12 Documentación | — | DC-01, DC-02, DC-04 | DC-03, DC-05, DC-06 |

## Hallazgos de severidad alta por atributo de calidad

| Hallazgo | Confiabilidad | Mantenibilidad | Seguridad | Rendimiento | Administrabilidad |
|---|:-:|:-:|:-:|:-:|:-:|
| IM-03 Transacción en el repositorio | ● | | | | |
| DO-02 Respaldo manual | ● | | | | ● |
| DM-01 Evento armado fuera del agregado | ● | ● | | | |
| DM-02 Eventos sin versión | ● | ● | | | |
| AC-03 Analytics sobre eventos crudos | | ● | | ● | |
| AC-01 Contextos sin interfaz pública | | ● | | | |
| DM-05 Tipo de pregunta con primitivos | | ● | | | |
| AQ-01 Mantenibilidad sin probar | | ● | | | |
| IM-02 Errores traducidos a mano | | ● | | | |
| IQ-01 CBO moldea el diseño | | ● | | | |
| PR-01 Retrabajo detectado en UAT | | ● | | | |

La concentración en mantenibilidad es el resultado central: el sistema funciona y es confiable en su núcleo; lo que está en riesgo es el costo de cambiarlo.

## Orden recomendado

El criterio es riesgo irreversible primero, después lo que abarata todo lo demás.

### Etapa 0 — Cierres rápidos (horas cada uno, sin diseño)

| Hallazgo | Acción |
|---|---|
| DO-02 | Programar el respaldo desde `cognion.sh` y avisar si está vencido |
| VT-03 | Guarda en `conftest.py`: abortar si la base no es de test |
| IM-04 | Verificar pertenencia antes de conectar al canal en vivo |
| AQ-04 | Probar el vencimiento del token durante una sesión en vivo |
| DC-01, DC-02 | Reescribir `README.md` y corregir las afirmaciones falsas de `CLAUDE.md` |
| CA-02, IQ-04, DO-05 | Alinear versión de Python, comando de `tsc` del CI y borrar `fly.toml` |

Varios tocan `src/`, así que por la regla del proyecto van por historia con especificación. Pueden agruparse en una iteración de ajuste.

### Etapa 1 — Los bordes de cada contexto (una iteración)

| Hallazgo | Acción | Por qué acá |
|---|---|---|
| IM-03 | Unidad de trabajo por caso de uso | Cierra el único riesgo de datos inconsistentes |
| IM-02 | Jerarquía de errores y manejadores centrales | Elimina 138 traducciones y baja el acoplamiento real |
| IQ-01 | Recalibrar CBO y revertir los tipos `object` | Después de IM-02 el umbral deja de apretar |
| IM-01 | Decidir el destino de los controllers (ADR) | Depende de IM-02 |
| VT-01, VT-02 | Medir `frameworks/`; cobertura y Playwright del frontend en el CI | Da red de seguridad para las etapas siguientes |

### Etapa 2 — Los eventos (una iteración)

| Hallazgo | Acción | Por qué acá |
|---|---|---|
| DM-02 | Versión de esquema en cada evento | Barato hoy, caro con datos reales acumulados |
| DM-01, DM-03 | Eventos tipados; el agregado emite y aplica | Un solo lugar conoce el formato |
| DM-06 | Reloj inyectado y una sola marca de tiempo | Se hace junto con DM-01 |
| AQ-01, DM-05 | Probar el tercer tipo de pregunta; mover la corrección a Banco | La prueba decide cuánto invertir |
| DM-07 | Actualizar `ADR-002` con lo decidido | Cierra la etapa |

### Etapa 3 — Las fronteras entre contextos (antes de `RF-18`)

| Hallazgo | Acción | Por qué acá |
|---|---|---|
| AC-01 | Interfaz pública por contexto y contrato que la exija | Es el cambio más grande; necesita las etapas 1 y 2 |
| AC-02 | Declarar la dirección entre contextos e invertir tres dependencias | Sale casi gratis con AC-01 |
| AC-03, AQ-03 | Proyección de desempeño para Analytics y escenario de historial | Requisito previo de `RF-18` |
| FE-01 | Tipos del frontend generados desde OpenAPI | Reduce el retrabajo de PR-01 |

### En paralelo — Proceso y documentación

| Hallazgo | Acción |
|---|---|
| AQ-02, DO-06 | Emitir `RNF_v2.md` con los dos escenarios renegociados |
| PR-01, PR-05 | Clasificar los ajustes por causa y retomar las métricas |
| PR-02 | Revisión independiente automatizada en cada PR |
| PR-03, PR-04, DC-04 | Separar evidencia de documentación viva; convertir reglas en mecanismos |
| IQ-02, IQ-03 | Trinquete de advertencias; retirar las métricas que no informan |

## Qué no hacer

- **No extraer "Estructura académica" de Identidad todavía** (AC-04). Es una observación, no una urgencia.
- **No automatizar el despliegue** (DO-06). Con un servidor y un operador, un comando alcanza; hay que cambiar el requerimiento.
- **No reorganizar todos los tests** (VT-04). Alcanza con ubicar bien los nuevos.
- **No agregar gates.** El proyecto tiene suficientes; hay que recalibrar los que existen.

## No revisado

Lo que este informe no cubre, para que no se lea como una aprobación:

- **Ejecución.** No se corrió la suite de tests, la aplicación ni la composición Docker. No hay mediciones nuevas de rendimiento.
- **Seguridad en profundidad.** No se revisó el hash de contraseñas, el bloqueo por intentos, la validez del token de una cuenta deshabilitada, los tokens de invitación ni la exposición a inyección o XSS.
- **Modelo de datos y migraciones.** No se leyeron los modelos ORM ni las migraciones de Alembic.
- **Contextos menores.** De Analytics se leyó un adaptador; de Notificaciones, nada en detalle. Los casos de uso de Identidad y Banco se muestrearon (2 de 41).
- **ADR.** No se leyeron uno por uno; se citan por lo que el código y `CLAUDE.md` dicen de ellos.
- **Scripts de operación.** `respaldar.sh`, `restaurar.sh` y `deploy/gcp/` no se leyeron en detalle. No se comprobó que una restauración funcione.
- **Diseño de UX.** No se evaluaron prototipos, accesibilidad ni la interfaz en un navegador.
- **Especificaciones.** No se evaluó la calidad de las 176 especificaciones ni el contenido de las fases de `implement-us`.

Los hallazgos marcados *Inferido* (AC-04, AQ-01, AQ-04, FE-06 y parte de AC-03, IM-03, IM-06, FE-02, DO-03 y PR-01) necesitan confirmación antes de invertir en ellos.
