import { createBrowserRouter } from "react-router"

import { RequireRole } from "@/components/RequireRole"
import { AppLayout } from "@/layouts/AppLayout"
import { AuthLayout } from "@/layouts/AuthLayout"
import { AltaDocente } from "@/pages/AltaDocente"
import { AltaDocenteExito } from "@/pages/AltaDocenteExito"
import { ActividadEvaluativaPlaceholder, InicioPlaceholder } from "@/pages/_placeholders"
import { Actividades } from "@/pages/Actividades"
import { ActividadDetalle } from "@/pages/ActividadDetalle"
import { Banco } from "@/pages/Banco"
import { CambiarPassword } from "@/pages/CambiarPassword"
import { CerrarActividad } from "@/pages/CerrarActividad"
import { CuentaDetalle } from "@/pages/CuentaDetalle"
import { CuentaReseteada } from "@/pages/CuentaReseteada"
import { Cuentas } from "@/pages/Cuentas"
import { EditarPregunta } from "@/pages/EditarPregunta"
import { EditarTituloActividad } from "@/pages/EditarTituloActividad"
import { EliminarPregunta } from "@/pages/EliminarPregunta"
import { EvaluacionSuspendida } from "@/pages/EvaluacionSuspendida"
import { ExtenderPlazo } from "@/pages/ExtenderPlazo"
import { FueraDePeriodo } from "@/pages/FueraDePeriodo"
import { Login } from "@/pages/Login"
import { Materias } from "@/pages/Materias"
import { MateriasActividades } from "@/pages/MateriasActividades"
import { MisActividades } from "@/pages/MisActividades"
import { MisMaterias } from "@/pages/MisMaterias"
import { NuevaActividad } from "@/pages/NuevaActividad"
import { NuevaMateria } from "@/pages/NuevaMateria"
import { NuevaPreguntaOpcionMultiple } from "@/pages/NuevaPreguntaOpcionMultiple"
import { NuevaPreguntaTipo } from "@/pages/NuevaPreguntaTipo"
import { NuevaPreguntaVerdaderoFalso } from "@/pages/NuevaPreguntaVerdaderoFalso"
import { Registro } from "@/pages/Registro"
import { RegistroError } from "@/pages/RegistroError"
import { RegistroExito } from "@/pages/RegistroExito"
import { RendirEvaluacion } from "@/pages/RendirEvaluacion"
import { ResetearPassword } from "@/pages/ResetearPassword"

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
            <ActividadEvaluativaPlaceholder />
          </RequireRole>
        ),
      },
    ],
  },
])
