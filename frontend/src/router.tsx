import { createBrowserRouter } from "react-router"

import { RequireRole } from "@/components/RequireRole"
import { AppLayout } from "@/layouts/AppLayout"
import { AuthLayout } from "@/layouts/AuthLayout"
import { AltaDocente } from "@/pages/identidad/AltaDocente"
import { AltaDocenteExito } from "@/pages/identidad/AltaDocenteExito"
import { InicioPlaceholder } from "@/pages/_placeholders"
import { Actividades } from "@/pages/actividad-evaluativa/Actividades"
import { ActividadDetalle } from "@/pages/actividad-evaluativa/ActividadDetalle"
import { Banco } from "@/pages/banco-preguntas/Banco"
import { CambiarPassword } from "@/pages/identidad/CambiarPassword"
import { CerrarActividad } from "@/pages/actividad-evaluativa/CerrarActividad"
import { CuentaDetalle } from "@/pages/cuentas/CuentaDetalle"
import { CuentaReseteada } from "@/pages/cuentas/CuentaReseteada"
import { Cuentas } from "@/pages/cuentas/Cuentas"
import { EditarPregunta } from "@/pages/banco-preguntas/EditarPregunta"
import { EditarTituloActividad } from "@/pages/actividad-evaluativa/EditarTituloActividad"
import { EliminarPregunta } from "@/pages/banco-preguntas/EliminarPregunta"
import { EvaluacionSuspendida } from "@/pages/actividad-evaluativa/EvaluacionSuspendida"
import { ExtenderPlazo } from "@/pages/actividad-evaluativa/ExtenderPlazo"
import { FueraDePeriodo } from "@/pages/actividad-evaluativa/FueraDePeriodo"
import { Login } from "@/pages/identidad/Login"
import { Materias } from "@/pages/banco-preguntas/Materias"
import { MateriasActividades } from "@/pages/actividad-evaluativa/MateriasActividades"
import { MisActividades } from "@/pages/actividad-evaluativa/MisActividades"
import { MisMaterias } from "@/pages/actividad-evaluativa/MisMaterias"
import { NuevaActividad } from "@/pages/actividad-evaluativa/NuevaActividad"
import { NuevaMateria } from "@/pages/banco-preguntas/NuevaMateria"
import { NuevaPreguntaOpcionMultiple } from "@/pages/banco-preguntas/NuevaPreguntaOpcionMultiple"
import { NuevaPreguntaTipo } from "@/pages/banco-preguntas/NuevaPreguntaTipo"
import { NuevaPreguntaVerdaderoFalso } from "@/pages/banco-preguntas/NuevaPreguntaVerdaderoFalso"
import { Registro } from "@/pages/identidad/Registro"
import { RegistroError } from "@/pages/identidad/RegistroError"
import { RegistroExito } from "@/pages/identidad/RegistroExito"
import { RendirEvaluacion } from "@/pages/actividad-evaluativa/RendirEvaluacion"
import { ResetearPassword } from "@/pages/cuentas/ResetearPassword"
import { RevisionEvaluacion } from "@/pages/actividad-evaluativa/RevisionEvaluacion"

/**
 * Router de la aplicación (React Router v7, modo data).
 *
 * Se exporta la instancia (en vez de solo el componente `<RouterProvider>`) para que
 * `api-client.ts` pueda navegar imperativamente a `/login` ante un 401, sin depender de un
 * hook de React (`useNavigate`) fuera del árbol de componentes.
 */
export const router = createBrowserRouter([
  {
    element: <AuthLayout />,
    children: [
      { path: "/login", element: <Login /> },
      { path: "/registro", element: <Registro /> },
      { path: "/registro/error", element: <RegistroError /> },
      { path: "/registro/exito", element: <RegistroExito /> },
    ],
  },
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <InicioPlaceholder /> },
      { path: "/mi-cuenta/cambiar-password", element: <CambiarPassword /> },
      {
        path: "/docentes/nuevo",
        element: (
          <RequireRole rol="administrador">
            <AltaDocente />
          </RequireRole>
        ),
      },
      {
        path: "/docentes/nuevo/exito",
        element: (
          <RequireRole rol="administrador">
            <AltaDocenteExito />
          </RequireRole>
        ),
      },
      {
        path: "/materias",
        element: (
          <RequireRole rol="docente">
            <Materias />
          </RequireRole>
        ),
      },
      {
        path: "/materias/nueva",
        element: (
          <RequireRole rol="docente">
            <NuevaMateria />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco",
        element: (
          <RequireRole rol="docente">
            <Banco />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/nueva",
        element: (
          <RequireRole rol="docente">
            <NuevaPreguntaTipo />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/nueva/opcion-multiple",
        element: (
          <RequireRole rol="docente">
            <NuevaPreguntaOpcionMultiple />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/nueva/verdadero-falso",
        element: (
          <RequireRole rol="docente">
            <NuevaPreguntaVerdaderoFalso />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/:preguntaId/editar",
        element: (
          <RequireRole rol="docente">
            <EditarPregunta />
          </RequireRole>
        ),
      },
      {
        path: "/materias/:materiaId/banco/preguntas/:preguntaId/eliminar",
        element: (
          <RequireRole rol="docente">
            <EliminarPregunta />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas",
        element: (
          <RequireRole rol="administrador">
            <Cuentas />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId",
        element: (
          <RequireRole rol="administrador">
            <CuentaDetalle />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId/resetear-password",
        element: (
          <RequireRole rol="administrador">
            <ResetearPassword />
          </RequireRole>
        ),
      },
      {
        path: "/cuentas/:usuarioId/reseteada",
        element: (
          <RequireRole rol="administrador">
            <CuentaReseteada />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/materias",
        element: (
          <RequireRole rol="docente">
            <MateriasActividades />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/materias/:materiaId/actividades",
        element: (
          <RequireRole rol="docente">
            <Actividades />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/materias/:materiaId/actividades/nueva",
        element: (
          <RequireRole rol="docente">
            <NuevaActividad />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId",
        element: (
          <RequireRole rol="docente">
            <ActividadDetalle />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId/editar-titulo",
        element: (
          <RequireRole rol="docente">
            <EditarTituloActividad />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId/extender-plazo",
        element: (
          <RequireRole rol="docente">
            <ExtenderPlazo />
          </RequireRole>
        ),
      },
      {
        path: "/actividad-evaluativa/actividades/:actividadId/cerrar",
        element: (
          <RequireRole rol="docente">
            <CerrarActividad />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/materias",
        element: (
          <RequireRole rol="estudiante">
            <MisMaterias />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/materias/:materiaId/actividades",
        element: (
          <RequireRole rol="estudiante">
            <MisActividades />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/:actividadId/fuera-de-periodo",
        element: (
          <RequireRole rol="estudiante">
            <FueraDePeriodo />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/actividades/:actividadId/rendir",
        element: (
          <RequireRole rol="estudiante">
            <RendirEvaluacion />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/actividades/:actividadId/suspendida",
        element: (
          <RequireRole rol="estudiante">
            <EvaluacionSuspendida />
          </RequireRole>
        ),
      },
      {
        path: "/mis-actividades/evaluaciones/:evaluacionId/revision",
        element: (
          <RequireRole rol="estudiante">
            <RevisionEvaluacion />
          </RequireRole>
        ),
      },
    ],
  },
])
