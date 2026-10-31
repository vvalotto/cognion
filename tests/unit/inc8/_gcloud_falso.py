"""`gcloud` simulado para los tests de US-8.6.4.

No es un test: el helper lo copia a un PATH aislado con el nombre `gcloud`. Lleva un estado en JSON
(qué recursos existen), registra cada llamada y muta ese estado al "crear" o "borrar". Imita la API
real de presupuestos, que exige un proyecto de cuota existente con la API habilitada.
"""

import os
import sys

from _comun_falso import (  # pylint: disable=import-error  # está junto al simulador
    cargar,
    guardar,
    registrar,
)

APIS = ["compute.googleapis.com", "billingbudgets.googleapis.com"]
RECURSOS = {"firewall-rules": "reglas", "addresses": "ips", "instances": "vms"}


def _opcion(args: list[str], nombre: str) -> str:
    prefijo = f"--{nombre}="
    valores = [a.removeprefix(prefijo) for a in args if a.startswith(prefijo)]
    return valores[0] if valores else ""


def _proyectos(args: list[str], linea: str, estado: dict) -> int:
    if args[1] == "describe":
        if "projectNumber" in linea:
            print("888211184158")
            return 0
        if estado["proyecto"]:
            print("ACTIVE")
            return 0
        return 1
    if args[1] in ("create", "delete"):
        estado["proyecto"] = args[1] == "create"
        guardar(estado)
    return 0


def _facturacion(args: list[str], estado: dict) -> int:
    if args[2] == "describe":
        print("True" if estado["facturacion"] else "False")
    elif args[2] == "link":
        estado["facturacion"] = True
        guardar(estado)
    return 0


def _servicios(args: list[str], estado: dict) -> int:
    if args[1] == "list":
        print("\n".join(estado["apis"]))
    elif args[1] == "enable":
        estado["apis"] = list(APIS)
        # En un proyecto nuevo, habilitar Compute Engine hace que Google cree la regla de RDP.
        if estado.get("rdp_al_habilitar_compute") and "default-allow-rdp" not in estado["reglas"]:
            estado["reglas"].append("default-allow-rdp")
        guardar(estado)
    return 0


def _presupuestos(args: list[str], estado: dict) -> int:
    sin_cuota = not _opcion(args, "billing-project") or not estado["proyecto"]
    sin_api = "billingbudgets.googleapis.com" not in estado["apis"]
    if sin_cuota or sin_api or os.environ.get("FAKE_PRESUPUESTOS_FALLA"):
        sys.stderr.write("ERROR: la API de presupuestos requiere un proyecto de cuota\n")
        return 1
    if args[2] == "list":
        print("\n".join(estado["presupuestos"]))
    elif args[2] == "create":
        estado["presupuestos"].append(_opcion(args, "display-name"))
        guardar(estado)
    return 0


def _ssh() -> int:
    """Guarda lo que llegue por stdin (la sincronización por `tar`) en un archivo por llamada."""
    if sys.stdin.isatty():
        return 0
    datos = sys.stdin.buffer.read()
    with open(os.environ["FAKE_LOG"], encoding="utf-8") as archivo:
        numero = sum(1 for linea in archivo if " compute ssh " in linea)
    base = os.environ.get("FAKE_STDIN")
    if base:
        with open(f"{base}.{numero}", "wb") as archivo:
            archivo.write(datos)
    return 0


def _recurso(accion: str, clave: str, nombre: str, linea: str, estado: dict) -> int:
    """Simula describe/create/delete sobre una lista de recursos del estado."""
    if accion == "describe":
        if nombre not in estado[clave]:
            return 1
        if "value(address)" in linea:
            print("34.30.252.89")
    elif accion == "create":
        estado[clave].append(nombre)
        guardar(estado)
    elif accion == "delete":
        estado[clave] = [x for x in estado[clave] if x != nombre]
        guardar(estado)
    return 0


def _compute(args: list[str], linea: str, estado: dict) -> int:
    if args[1] == "ssh":
        return _ssh()
    clave = RECURSOS.get(args[1])
    if clave is None:
        return 0
    nombre = args[3] if len(args) > 3 else ""
    return _recurso(args[2], clave, nombre, linea, estado)


def _auth(estado: dict) -> int:
    if estado.get("cuenta"):
        print(estado["cuenta"])
    return 0


def main(args: list[str]) -> int:
    """Despacha el comando simulado y devuelve el código de salida."""
    linea = " ".join(args)
    registrar("gcloud " + linea)
    estado = cargar()
    manejadores = {
        "auth": lambda: _auth(estado),
        "projects": lambda: _proyectos(args, linea, estado),
        "services": lambda: _servicios(args, estado),
        "compute": lambda: _compute(args, linea, estado),
        "billing": lambda: (
            _facturacion(args, estado) if args[1] == "projects" else _presupuestos(args, estado)
        ),
    }
    return manejadores.get(args[0], lambda: 0)()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
