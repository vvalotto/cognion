"""UAT Capa 2 de regresión de la v1.0.1 (BL-018): lo que cambió en las Iteraciones 1 y 2 del Incremento 12.

Contra un servidor real con base descartable y el pool de conexiones activo (la ejecución real; los tests usan
`NullPool`). Comprueba que los cuerpos y códigos de error no cambiaron (manejador único, `US-12.2.2`), que un error
controlado conserva lo escrito (unidad de trabajo, `US-12.2.1`) y que 60 respuestas casi simultáneas en una sesión en
vivo terminan bien con el pool (`US-12.2.5`).

Uso:  UAT_URL=http://localhost:8010 UAT_ADMIN_EMAIL=... UAT_ADMIN_PASSWORD=... \
      .venv/bin/python tests/uat/inc12/capa2_regresion.py
Evidencia en `quality/reports/uat/inc12/capa2-regresion.json` (sin tokens ni contraseñas).
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import statistics
import sys
import time
import uuid

import httpx

URL = os.environ.get("UAT_URL", "http://localhost:8010").rstrip("/") + "/api"
ADMIN_EMAIL = os.environ["UAT_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["UAT_ADMIN_PASSWORD"]
N = int(os.environ.get("UAT_N", "60"))
SALIDA = os.environ.get("UAT_SALIDA", "quality/reports/uat/inc12/capa2-regresion.json")

resultados: list[dict] = []
sufijo = secrets.token_hex(3)


def clave() -> str:
    """Contraseña de prueba válida."""
    return f"Uat{secrets.token_hex(5)}!Aa1"


def verificar(nombre: str, ok: bool, detalle: str = "") -> None:
    """Registra y muestra un resultado."""
    resultados.append({"verificacion": nombre, "ok": bool(ok), "detalle": detalle})
    print(f"{'OK  ' if ok else 'FALLA'} {nombre} {detalle}")


def auth(token: str) -> dict[str, str]:
    """Cabecera de autorización."""
    return {"Authorization": f"Bearer {token}"}


async def main() -> int:
    """Corre el recorrido; devuelve 0 si todo pasó."""
    async with httpx.AsyncClient(
        base_url=URL, timeout=60, limits=httpx.Limits(max_connections=N + 10)
    ) as c:
        # --- Preparación: administrador, materia, comisión, docente ---------------------------------
        r = await c.post(
            "/identidad/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        verificar("login del administrador", r.status_code == 200, str(r.status_code))
        admin = r.json()["access_token"]
        lista = (
            await c.get("/usuarios", headers=auth(admin), params={"rol": "administrador"})
        ).json()
        admin_id = (lista["cuentas"] if isinstance(lista, dict) else lista)[0]["id"]
        materia = (
            await c.post("/materias", json={"nombre": f"Materia R {sufijo}"}, headers=auth(admin))
        ).json()
        comision = (
            await c.post(
                "/comisiones",
                json={
                    "materia_id": materia["id"],
                    "horario": "Ma 8-10",
                    "administrador_id": admin_id,
                },
                headers=auth(admin),
            )
        ).json()["id"]
        pwd_doc = clave()
        mail_doc = f"doc.r.{sufijo}@fiuner.edu.ar"
        docente = (
            await c.post(
                "/usuarios",
                json={
                    "nombre": "Docente R",
                    "email": mail_doc,
                    "password": pwd_doc,
                    "perfil": "docente",
                },
                headers=auth(admin),
            )
        ).json()
        await c.post(
            f"/comisiones/{comision}/docentes",
            json={"docente_id": docente["id"]},
            headers=auth(admin),
        )
        doc = (
            await c.post("/identidad/login", json={"email": mail_doc, "password": pwd_doc})
        ).json()["access_token"]

        # --- Errores: códigos y cuerpos (manejador único) --------------------------------------------
        r = await c.get("/comisiones/" + str(uuid.uuid4()))
        verificar("sin token → 401", r.status_code == 401, str(r.status_code))
        r = await c.get(f"/comisiones/{uuid.uuid4()}", headers=auth(admin))
        verificar(
            "comisión inexistente → 404 con detail de texto",
            r.status_code == 404 and isinstance(r.json().get("detail"), str),
            f"{r.status_code}",
        )
        r = await c.post("/materias", json={"nombre": "x"}, headers=auth(doc))
        verificar("un docente no crea materias → 403", r.status_code == 403, str(r.status_code))
        r = await c.post("/materias", json={"nombre": ""}, headers=auth(admin))
        verificar("cuerpo inválido → 422 de validación", r.status_code == 422, str(r.status_code))
        r = await c.post(
            "/usuarios",
            json={"nombre": "Dup", "email": mail_doc, "password": clave(), "perfil": "docente"},
            headers=auth(admin),
        )
        verificar("email repetido → 409", r.status_code == 409, str(r.status_code))
        r = await c.post("/identidad/login", json={"email": mail_doc, "password": "incorrecta"})
        det = r.json().get("detail")
        verificar(
            "1.er fallo → 401 con detail de texto y sin aviso",
            r.status_code == 401 and isinstance(det, str),
            f"{r.status_code} {det}",
        )
        r = await c.post("/identidad/login", json={"email": mail_doc, "password": "incorrecta"})
        det = r.json().get("detail")
        verificar(
            "2.º fallo → 401 con intentos_restantes = 1 (US-ADJ-69)",
            r.status_code == 401 and isinstance(det, dict) and det.get("intentos_restantes") == 1,
            f"{r.status_code} {det}",
        )
        r = await c.post("/identidad/login", json={"email": mail_doc, "password": "incorrecta"})
        verificar(
            "3.er fallo → 401 y la cuenta queda bloqueada", r.status_code == 401, str(r.status_code)
        )
        r = await c.post("/identidad/login", json={"email": mail_doc, "password": pwd_doc})
        det = r.json().get("detail")
        verificar(
            "con la cuenta bloqueada, la clave correcta → 403 con detail de texto",
            r.status_code == 403 and isinstance(det, str),
            f"{r.status_code} {det}",
        )
        # el administrador resetea la clave: desbloquea y se puede entrar de nuevo
        nueva = clave()
        r = await c.post(
            f"/usuarios/{docente['id']}/resetear-password",
            json={"password_nueva": nueva},
            headers=auth(admin),
        )
        verificar(
            "el administrador resetea la contraseña", r.status_code == 200, str(r.status_code)
        )
        r = await c.post("/identidad/login", json={"email": mail_doc, "password": nueva})
        verificar("tras el reseteo el docente entra", r.status_code == 200, str(r.status_code))
        doc = r.json()["access_token"]

        # --- Sesión en vivo con N estudiantes y el pool real -----------------------------------------
        for i in range(3):
            await c.post(
                "/preguntas/opcion-multiple",
                json={
                    "banco_id": materia["banco_id"],
                    "texto": f"Pregunta R{i} {sufijo}",
                    "opciones": [
                        {"texto": "A", "es_correcta": True},
                        {"texto": "B", "es_correcta": False},
                    ],
                    "unidad_tematica": "U1",
                    "tema": "T1",
                    "dificultad": "medio",
                    "importancia": "alto",
                },
                headers=auth(doc),
            )
        inv = (
            await c.post(
                f"/comisiones/{comision}/invitaciones-grupales",
                json={"duracion_minutos": 60},
                headers=auth(doc),
            )
        ).json()
        passwords = [clave() for _ in range(N)]

        async def registrar(i: int) -> int:
            r = await c.post(
                "/identidad/registro",
                json={
                    "token": inv["token"],
                    "nombre": f"Est {i}",
                    "email": f"e{i}.r.{sufijo}@fiuner.edu.ar",
                    "password": passwords[i],
                },
            )
            return r.status_code

        codigos = await asyncio.gather(*[registrar(i) for i in range(N)])
        verificar(
            f"{N} registros simultáneos con el mismo link",
            all(x == 201 for x in codigos),
            f"{sorted(set(codigos))}",
        )

        async def entrar(i: int) -> str:
            r = await c.post(
                "/identidad/login",
                json={"email": f"e{i}.r.{sufijo}@fiuner.edu.ar", "password": passwords[i]},
            )
            return r.json()["access_token"]

        tokens = await asyncio.gather(*[entrar(i) for i in range(N)])
        sesion = await c.post(
            "/sesiones-en-vivo",
            json={
                "comision_id": comision,
                "cantidad_preguntas": 1,
                "tiempo_limite_por_pregunta_segundos": 60,
            },
            headers=auth(doc),
        )
        verificar(
            "el docente crea la sesión en vivo", sesion.status_code == 201, str(sesion.status_code)
        )
        sid = sesion.json()["id"]
        unidos = await asyncio.gather(
            *[c.post(f"/sesiones-en-vivo/{sid}/unirse", headers=auth(t)) for t in tokens]
        )
        verificar(
            f"{N} estudiantes se unen a la vez",
            all(u.status_code == 200 for u in unidos),
            f"{sorted({u.status_code for u in unidos})}",
        )
        r = await c.post(f"/sesiones-en-vivo/{sid}/iniciar", headers=auth(doc))
        verificar("el docente inicia la sesión", r.status_code == 200, str(r.status_code))
        r = await c.post(f"/sesiones-en-vivo/{sid}/mostrar-opciones", headers=auth(doc))
        verificar("el docente muestra las opciones", r.status_code == 200, str(r.status_code))

        async def responder(t: str) -> tuple[int, float]:
            estado = (await c.get(f"/sesiones-en-vivo/{sid}", headers=auth(t))).json()
            t0 = time.perf_counter()
            r = await c.post(
                f"/sesiones-en-vivo/{sid}/responder",
                json={
                    "pregunta_id": estado["pregunta_actual"]["pregunta_id"],
                    "contenido": {"opcion_indice": 0},
                },
                headers=auth(t),
            )
            return r.status_code, (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        res = await asyncio.gather(*[responder(t) for t in tokens])
        total = (time.perf_counter() - t0) * 1000
        lat = [ms for _, ms in res]
        verificar(
            f"{N} respuestas casi simultáneas → todas 200",
            all(code == 200 for code, _ in res),
            f"códigos={sorted({code for code, _ in res})} total={total:.0f} ms mediana={statistics.median(lat):.0f} ms máx={max(lat):.0f} ms",
        )
        r = await c.post(f"/sesiones-en-vivo/{sid}/cerrar-pregunta", headers=auth(doc))
        verificar("el docente cierra la pregunta", r.status_code == 200, str(r.status_code))
        rk = await c.get(f"/sesiones-en-vivo/{sid}/ranking", headers=auth(doc))
        verificar(
            f"el ranking tiene {N} participantes",
            rk.status_code == 200 and len(rk.json()) == N,
            f"{rk.status_code} {len(rk.json()) if rk.status_code == 200 else ''}",
        )
        r = await c.get("/health/ready")
        verificar("la base sigue disponible al terminar", r.status_code == 200, str(r.status_code))

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    with open(SALIDA, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=1)
    fallas = [x for x in resultados if not x["ok"]]
    print(f"\n{len(resultados) - len(fallas)}/{len(resultados)} comprobaciones OK")
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
