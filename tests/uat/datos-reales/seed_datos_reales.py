"""Siembra la base de datos con datos cercanos a la realidad para la prueba manual E2E.

No es un smoke test (no limpia al terminar) — deja los datos sembrados en la base para que
Víctor navegue la UI manualmente. Requiere backend real corriendo (ver
.claude/skills/run-cognion/SKILL.md, "Run (human path)") y un fake SMTP si se quiere que las
invitaciones "envíen" el mail (opcional — el token ya viene en la respuesta de la API desde
US-ADJ-26, no hace falta leer el email).

Uso:
    .venv/bin/python tests/uat/datos-reales/seed_datos_reales.py

Antes de correr: completar tests/uat/datos-reales/config.json con los Docentes reales
(los campos marcados "PENDIENTE").
"""

from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = "http://localhost:8000"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent


def api(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {path} -> {exc.code}: {detail}") from exc


def login(email: str, password: str) -> str:
    resp = api("POST", "/identidad/login", {"email": email, "password": password})
    return resp["access_token"]


def usuario_id_de(token: str) -> str:
    """Decodifica el claim 'sub' del JWT sin verificar firma (el backend ya la valida en cada
    request) — mismo mecanismo que session.ts::obtenerUsuarioId() en el frontend."""
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (-len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(payload_b64))["sub"]


def bootstrap_admin(admin_cfg: dict) -> None:
    env = {
        "ADMIN_NOMBRE": admin_cfg["nombre"],
        "ADMIN_EMAIL": admin_cfg["email"],
        "ADMIN_PASSWORD": admin_cfg["password"],
    }
    result = subprocess.run(
        [str(REPO_ROOT / ".venv/bin/python"), "scripts/seed_admin.py"],
        cwd=REPO_ROOT,
        env={**os.environ, **env},
        capture_output=True,
        text=True,
    )
    print(result.stdout.strip())
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        raise SystemExit("Fallo el bootstrap del Administrador — ver stderr arriba.")


def crear_o_loguear_docente(admin_token: str, docente_cfg: dict) -> tuple[str, str]:
    """Devuelve (docente_id, docente_token). Idempotente: si el email ya existe, solo loguea."""
    try:
        creado = api(
            "POST",
            "/usuarios",
            {
                "nombre": docente_cfg["nombre"],
                "email": docente_cfg["email"],
                "password": docente_cfg["password"],
                "perfil": "docente",
            },
            token=admin_token,
        )
        docente_id = creado["id"]
        print(f"  Docente creado: {docente_cfg['nombre']} ({docente_cfg['email']})")
    except RuntimeError as exc:
        if "409" not in str(exc):
            raise
        print(f"  Docente ya existía: {docente_cfg['email']}")
        docente_id = None
    token = login(docente_cfg["email"], docente_cfg["password"])
    if docente_id is None:
        # No hay endpoint de "quién soy" simple sin decodificar el JWT — se resuelve
        # más abajo si hace falta (asignación a comisión ya funciona con email/token).
        docente_id = "(existente)"
    return docente_id, token


def crear_materia(docente_token: str, nombre: str) -> tuple[str, str]:
    materia = api("POST", "/materias", {"nombre": nombre}, token=docente_token)
    return materia["id"], materia["banco_id"]


def cargar_preguntas(docente_token: str, banco_id: str, preguntas: list[dict]) -> int:
    cargadas = 0
    for q in preguntas:
        comunes = {
            "banco_id": banco_id,
            "texto": q["texto"],
            "unidad_tematica": q["unidad_tematica"],
            "tema": q["tema"],
            "dificultad": q["dificultad"],
            "importancia": q["importancia"],
        }
        if q["tipo"] == "opcion_multiple":
            opciones = [
                {"texto": o, "es_correcta": i == q["indice_correcta"]}
                for i, o in enumerate(q["opciones"])
            ]
            api(
                "POST",
                "/preguntas/opcion-multiple",
                {**comunes, "opciones": opciones},
                token=docente_token,
            )
        else:
            api(
                "POST",
                "/preguntas/verdadero-falso",
                {**comunes, "respuesta_correcta": q["respuesta_correcta"]},
                token=docente_token,
            )
        cargadas += 1
    return cargadas


def crear_comision(admin_token: str, admin_id: str, materia_id: str, horario: str) -> str:
    comision = api(
        "POST",
        "/comisiones",
        {"materia_id": materia_id, "horario": horario, "administrador_id": admin_id},
        token=admin_token,
    )
    return comision["id"]


def asignar_docente(
    admin_token: str, comision_id: str, docente_email: str, docente_password: str
) -> None:
    docente_id = usuario_id_de(login(docente_email, docente_password))
    api(
        "POST", f"/comisiones/{comision_id}/docentes", {"docente_id": docente_id}, token=admin_token
    )


def generar_invitacion(
    docente_token: str, comision_id: str, docente_email: str, docente_password: str
) -> str:
    docente_id = usuario_id_de(login(docente_email, docente_password))
    resp = api(
        "POST",
        f"/comisiones/{comision_id}/invitaciones",
        {"docente_id": docente_id},
        token=docente_token,
    )
    return resp["token"]


def registrar_estudiante(invitacion_token: str, nombre: str, email: str, password: str) -> None:
    api(
        "POST",
        "/identidad/registro",
        {"token": invitacion_token, "nombre": nombre, "email": email, "password": password},
    )


def main() -> None:
    config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
    preguntas = json.loads((HERE / "preguntas.json").read_text(encoding="utf-8"))

    pendientes = [d for d in config["docentes"] if d["nombre"] == "PENDIENTE"]
    if pendientes:
        print(
            "config.json todavía tiene Docentes 'PENDIENTE' — completar antes de sembrar "
            "datos reales. Abortando.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print("== Bootstrap del Administrador ==")
    bootstrap_admin(config["administrador"])
    admin_token = login(config["administrador"]["email"], config["administrador"]["password"])
    admin_id = usuario_id_de(admin_token)

    print("\n== Docentes ==")
    docente_tokens: dict[str, str] = {}
    for d in config["docentes"]:
        _id, token = crear_o_loguear_docente(admin_token, d)
        docente_tokens[d["email"]] = token

    print("\n== Materias y banco de preguntas ==")
    materias_por_nombre: dict[str, dict] = {}
    for d in config["docentes"]:
        token = docente_tokens[d["email"]]
        for nombre_materia in d["materias"]:
            materia_id, banco_id = crear_materia(token, nombre_materia)
            preguntas_materia = [q for q in preguntas if q["materia"] == nombre_materia]
            n = cargar_preguntas(token, banco_id, preguntas_materia)
            materias_por_nombre[nombre_materia] = {
                "materia_id": materia_id,
                "banco_id": banco_id,
                "docente_email": d["email"],
            }
            print(f"  {nombre_materia}: materia_id={materia_id}, {n} preguntas cargadas")

    print("\n== Comisiones, invitaciones y estudiantes ==")
    resumen_estudiantes: list[dict] = []
    for c in config["comisiones"]:
        materia_info = materias_por_nombre[c["materia"]]
        comision_id = crear_comision(
            admin_token, admin_id, materia_info["materia_id"], c["horario"]
        )
        docente_cfg = next(d for d in config["docentes"] if d["email"] == c["docente_email"])
        asignar_docente(admin_token, comision_id, docente_cfg["email"], docente_cfg["password"])
        docente_token = docente_tokens[docente_cfg["email"]]
        print(f"  Comisión '{c['horario']}' ({c['materia']}): id={comision_id}, docente asignado")

        for est in c["estudiantes"]:
            inv_token = generar_invitacion(
                docente_token, comision_id, docente_cfg["email"], docente_cfg["password"]
            )
            registrar_estudiante(
                inv_token, est["nombre"], est["email"], config["password_estudiante"]
            )
            resumen_estudiantes.append(
                {
                    "nombre": est["nombre"],
                    "email": est["email"],
                    "comision": c["horario"],
                    "materia": c["materia"],
                }
            )
        print(f"    {len(c['estudiantes'])} estudiantes registrados")

    print("\n" + "=" * 70)
    print("SIEMBRA COMPLETA — credenciales para la prueba manual")
    print("=" * 70)
    print(
        f"\nAdministrador: {config['administrador']['email']} / {config['administrador']['password']}"
    )
    for d in config["docentes"]:
        print(f"Docente ({', '.join(d['materias'])}): {d['email']} / {d['password']}")
    print(f"\nContraseña de todos los Estudiantes: {config['password_estudiante']}")
    for e in resumen_estudiantes:
        print(f"  {e['nombre']} <{e['email']}> — {e['materia']} / {e['comision']}")
    print(f"\nFrontend: http://localhost:5173/login")


if __name__ == "__main__":
    main()
