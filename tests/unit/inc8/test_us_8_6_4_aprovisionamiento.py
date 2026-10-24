"""Scripts de aprovisionamiento y destrucción de la VM de GCP (US-8.6.4), con `gcloud` simulado.

`gcloud` es un ejecutable falso que lleva un estado (qué recursos existen), registra cada llamada y
muta ese estado al "crear" o "borrar". Así se verifican el orden, la idempotencia y las
confirmaciones sin tocar la nube.
"""

# pylint: disable=line-too-long  # contiene el código de ejecutables simulados como texto

import json
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[3]
GCP = RAIZ / "deploy" / "gcp"
BASICOS = (
    "bash sh env dirname sed grep cut head tail tr seq sleep cat mktemp chmod mv rm awk wc id touch tee date "
    "basename sort uniq mkdir tar gzip ls"
).split()

GCLOUD_FALSO = r"""#!{python}
import json, os, sys
a = sys.argv[1:]
linea = " ".join(a)
open(os.environ["FAKE_LOG"], "a").write("gcloud " + linea + "\n")
ruta = os.environ["FAKE_ESTADO"]
e = json.load(open(ruta))
def guardar(): json.dump(e, open(ruta, "w"))
def nombre(): return a[3] if len(a) > 3 else ""
if a[:2] == ["auth", "list"]:
    if e.get("cuenta"): print(e["cuenta"])
    sys.exit(0)
if a[:2] == ["projects", "describe"]:
    if "projectNumber" in linea: print("888211184158"); sys.exit(0)
    if e["proyecto"]: print("ACTIVE"); sys.exit(0)
    sys.exit(1)
if a[:2] == ["projects", "create"]: e["proyecto"] = True; guardar(); sys.exit(0)
if a[:2] == ["projects", "delete"]: e["proyecto"] = False; guardar(); sys.exit(0)
if a[:3] == ["billing", "projects", "describe"]: print("True" if e["facturacion"] else "False"); sys.exit(0)
if a[:3] == ["billing", "projects", "link"]: e["facturacion"] = True; guardar(); sys.exit(0)
if a[:2] == ["services", "list"]: print("\n".join(e["apis"])); sys.exit(0)
if a[:2] == ["services", "enable"]:
    e["apis"] = ["compute.googleapis.com", "billingbudgets.googleapis.com"]
    if e.get("rdp_al_habilitar_compute") and "default-allow-rdp" not in e["reglas"]: e["reglas"].append("default-allow-rdp")
    guardar(); sys.exit(0)
if a[:2] == ["billing", "budgets"]:
    # Como la API real: exige un proyecto de cuota que exista y tenga la API habilitada.
    cuota = [x.split("=", 1)[1] for x in a if x.startswith("--billing-project=")]
    if (not cuota or not e["proyecto"] or "billingbudgets.googleapis.com" not in e["apis"]
            or os.environ.get("FAKE_PRESUPUESTOS_FALLA")):
        sys.stderr.write("ERROR: la API de presupuestos requiere un proyecto de cuota\n"); sys.exit(1)
    if a[2] == "list": print("\n".join(e["presupuestos"])); sys.exit(0)
    if a[2] == "create":
        e["presupuestos"].append([x.split("=", 1)[1] for x in a if x.startswith("--display-name=")][0]); guardar(); sys.exit(0)
if a[0] == "compute" and a[1] in ("firewall-rules", "addresses", "instances"):
    clave = {"firewall-rules": "reglas", "addresses": "ips", "instances": "vms"}[a[1]]
    if a[2] == "describe":
        if nombre() not in e[clave]: sys.exit(1)
        if "value(address)" in linea: print("34.30.252.89")
        sys.exit(0)
    if a[2] == "create": e[clave].append(nombre()); guardar(); sys.exit(0)
    if a[2] == "delete": e[clave] = [x for x in e[clave] if x != nombre()]; guardar(); sys.exit(0)
if a[:2] == ["compute", "ssh"]:
    if not sys.stdin.isatty():
        datos = sys.stdin.buffer.read()
        n = sum(1 for l in open(os.environ["FAKE_LOG"]) if " compute ssh " in l)
        if os.environ.get("FAKE_STDIN"): open(os.environ["FAKE_STDIN"] + "." + str(n), "wb").write(datos)
    sys.exit(0)
sys.exit(0)
"""


def _entorno(tmp_path: Path, con_gcloud: bool = True) -> dict:
    """PATH mínimo: solo las utilidades básicas y los ejecutables falsos; sin ningún gcloud real."""
    carpeta = tmp_path / "bin"
    carpeta.mkdir(exist_ok=True)
    for programa in BASICOS:
        destino = carpeta / programa
        real = shutil.which(programa)
        if real and not destino.exists():
            destino.symlink_to(real)
    if con_gcloud:
        gcloud = carpeta / "gcloud"
        gcloud.write_text(GCLOUD_FALSO.replace("{python}", sys.executable))
        gcloud.chmod(gcloud.stat().st_mode | stat.S_IXUSR)
    return {
        "PATH": str(carpeta),
        "FAKE_LOG": str(tmp_path / "llamadas.log"),
        "FAKE_ESTADO": str(tmp_path / "estado.json"),
        "FAKE_STDIN": str(tmp_path / "stdin.bin"),
        "HOME": str(tmp_path),
    }


def _estado(tmp_path: Path, **cambios) -> None:
    base = {
        "cuenta": "vvalotto@gmail.com",
        "proyecto": False,
        "facturacion": False,
        "apis": [],
        "presupuestos": [],
        "reglas": ["default-allow-rdp", "default-allow-ssh", "default-allow-icmp"],
        "ips": [],
        "vms": [],
    }
    base.update(cambios)
    (tmp_path / "estado.json").write_text(json.dumps(base))


def _completo(tmp_path: Path, **cambios) -> None:
    _estado(
        tmp_path,
        proyecto=True,
        facturacion=True,
        apis=["compute.googleapis.com", "billingbudgets.googleapis.com"],
        presupuestos=["cognion-prueba"],
        reglas=["default-allow-ssh", "default-allow-icmp", "cognion-web"],
        ips=["cognion-ip"],
        vms=["cognion-vm"],
        **cambios,
    )


def _correr(
    tmp_path: Path,
    script: str,
    *args: str,
    entrada: str = "",
    extra: dict | None = None,
    con_gcloud=True,
):
    env = _entorno(tmp_path, con_gcloud)
    env.update({"PROYECTO": "cognion-prueba-2410", "CUENTA_FACTURACION": "019D68-E7FC7F-247D34"})
    env.update(extra or {})
    return subprocess.run(  # noqa: S603
        ["bash", str(GCP / script), *args],  # noqa: S607
        input=entrada,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def _llamadas(tmp_path: Path) -> list[str]:
    ruta = tmp_path / "llamadas.log"
    return ruta.read_text().splitlines() if ruta.exists() else []


def _mutan(llamadas: list[str]) -> list[str]:
    """Llamadas que crean, borran, vinculan o habilitan algo."""
    verbos = (" create", " delete", " link", " enable")
    return [x for x in llamadas if any(v in x for v in verbos)]


def _indice(llamadas: list[str], fragmento: str) -> int:
    for i, linea in enumerate(llamadas):
        if fragmento in linea:
            return i
    raise AssertionError(f"no se encontró '{fragmento}' en {llamadas}")


# ---------------------------------------------------------------- aprovisionar.sh


def test_sin_gcloud_falla_con_mensaje_claro(tmp_path: Path) -> None:
    """Escenario 7: sin gcloud sale con código ≠ 0, sin traza."""
    _estado(tmp_path)
    r = _correr(tmp_path, "aprovisionar.sh", "--si", con_gcloud=False)
    assert r.returncode != 0
    assert "Falta gcloud" in r.stderr
    assert "Traceback" not in r.stderr


@pytest.mark.parametrize("falta", ["PROYECTO", "CUENTA_FACTURACION"])
def test_exige_proyecto_y_cuenta_de_facturacion(tmp_path: Path, falta: str) -> None:
    """Sin el proyecto o la cuenta de facturación no hace nada."""
    _estado(tmp_path)
    r = _correr(tmp_path, "aprovisionar.sh", "--si", extra={falta: ""})
    assert r.returncode != 0
    assert f"Falta {falta}" in r.stderr
    assert _mutan(_llamadas(tmp_path)) == []


def test_rechaza_un_identificador_de_proyecto_invalido(tmp_path: Path) -> None:
    """Mayúsculas o espacios no son un ID de proyecto válido."""
    _estado(tmp_path)
    r = _correr(tmp_path, "aprovisionar.sh", "--si", extra={"PROYECTO": "Proyecto Raro"})
    assert r.returncode != 0
    assert "PROYECTO inválido" in r.stderr


def test_sin_sesion_de_gcloud_falla(tmp_path: Path) -> None:
    """Sin sesión activa pide `gcloud auth login`."""
    _estado(tmp_path, cuenta="")
    r = _correr(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode != 0
    assert "gcloud auth login" in r.stderr


def test_sobre_un_proyecto_vacio_crea_todo_en_orden(tmp_path: Path) -> None:
    """Escenario 1: crea lo que falta, en el orden que funcionó en la prueba manual."""
    _estado(tmp_path, proyecto=False, facturacion=False)
    r = _correr(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0, r.stderr
    ll = _llamadas(tmp_path)
    orden = [
        "projects create cognion-prueba-2410",
        "billing projects link cognion-prueba-2410",
        "services enable",
        "billing budgets create",
        "firewall-rules create cognion-web",
        "instances create cognion-vm",
        "compute ssh cognion-vm",
    ]
    posiciones = [_indice(ll, x) for x in orden]
    assert posiciones == sorted(posiciones)
    assert _indice(ll, "addresses create cognion-ip") < _indice(ll, "instances create cognion-vm")
    assert "34.30.252.89" in r.stdout


def test_la_regla_de_firewall_solo_abre_80_y_443(tmp_path: Path) -> None:
    """Escenario 2: ningún otro puerto, y solo hacia la etiqueta de la VM."""
    _estado(tmp_path)
    _correr(tmp_path, "aprovisionar.sh", "--si")
    regla = next(x for x in _llamadas(tmp_path) if "firewall-rules create cognion-web" in x)
    assert "--rules=tcp:80,tcp:443" in regla
    assert "--target-tags=cognion-web" in regla
    assert (
        "tcp:22" not in regla
        and "tcp:5432" not in regla
        and "all" not in regla.split("--rules=")[1].split()[0]
    )


def test_la_vm_usa_la_ip_reservada_y_la_capa_gratuita(tmp_path: Path) -> None:
    """La IP queda asignada a la VM (una reservada sin asignar se cobra) y el tipo es el de la capa gratuita."""
    _estado(tmp_path)
    _correr(tmp_path, "aprovisionar.sh", "--si")
    vm = next(x for x in _llamadas(tmp_path) if "instances create cognion-vm" in x)
    for esperado in (
        "--address=cognion-ip",
        "--machine-type=e2-micro",
        "--zone=us-central1-a",
        "--boot-disk-size=30GB",
        "--boot-disk-type=pd-standard",
        "--image-family=debian-12",
        "--tags=cognion-web",
    ):
        assert esperado in vm


def test_el_presupuesto_es_de_5_usd_con_alertas_al_50_y_100(tmp_path: Path) -> None:
    """El presupuesto queda acotado al proyecto por su número."""
    _estado(tmp_path)
    _correr(tmp_path, "aprovisionar.sh", "--si")
    pres = next(x for x in _llamadas(tmp_path) if "billing budgets create" in x)
    assert "--budget-amount=5USD" in pres
    assert "--filter-projects=projects/888211184158" in pres
    assert "--threshold-rule=percent=0.5" in pres and "--threshold-rule=percent=1.0" in pres


def test_cierra_el_rdp_abierto_a_internet(tmp_path: Path) -> None:
    """Elimina `default-allow-rdp` si el proyecto ya existía con esa regla."""
    _estado(
        tmp_path,
        proyecto=True,
        facturacion=True,
        apis=["compute.googleapis.com", "billingbudgets.googleapis.com"],
    )
    _correr(tmp_path, "aprovisionar.sh", "--si")
    assert any("firewall-rules delete default-allow-rdp" in x for x in _llamadas(tmp_path))


def test_en_un_proyecto_nuevo_cierra_el_rdp_que_crea_google_al_habilitar_compute(
    tmp_path: Path,
) -> None:
    """Regresión: la regla default-allow-rdp aparece recién al habilitar Compute Engine; debe cerrarse en la MISMA corrida."""
    _estado(tmp_path, proyecto=False, facturacion=False, reglas=[], rdp_al_habilitar_compute=True)
    r = _correr(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0, r.stderr
    ll = _llamadas(tmp_path)
    assert _indice(ll, "services enable") < _indice(ll, "firewall-rules delete default-allow-rdp")
    estado = json.loads((tmp_path / "estado.json").read_text())
    assert "default-allow-rdp" not in estado["reglas"]
    (tmp_path / "llamadas.log").unlink()
    assert "Nada que crear" in _correr(tmp_path, "aprovisionar.sh", "--si").stdout


def test_todos_los_comandos_llevan_project_y_no_cambian_la_configuracion_activa(
    tmp_path: Path,
) -> None:
    """No toca `gcloud config` ni activa configuraciones: la terminal de Víctor queda como estaba."""
    _estado(tmp_path)
    _correr(tmp_path, "aprovisionar.sh", "--si")
    ll = _llamadas(tmp_path)
    assert not any(" config " in x or "configurations" in x for x in ll)
    for x in ll:
        if "compute " in x and " ssh " not in x:
            assert "--project=cognion-prueba-2410" in x, x


def test_es_idempotente_la_segunda_corrida_no_crea_nada(tmp_path: Path) -> None:
    """Escenario: ejecutarlo dos veces no duplica recursos."""
    _estado(tmp_path)
    assert _correr(tmp_path, "aprovisionar.sh", "--si").returncode == 0
    (tmp_path / "llamadas.log").unlink()
    r = _correr(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0
    assert "Nada que crear" in r.stdout
    assert _mutan(_llamadas(tmp_path)) == []


def test_solo_crea_lo_que_falta(tmp_path: Path) -> None:
    """Con todo creado salvo la regla de firewall, solo crea esa regla."""
    _completo(tmp_path)
    estado = json.loads((tmp_path / "estado.json").read_text())
    estado["reglas"] = ["default-allow-ssh", "default-allow-icmp"]
    (tmp_path / "estado.json").write_text(json.dumps(estado))
    r = _correr(tmp_path, "aprovisionar.sh", "--si")
    assert r.returncode == 0
    mutaciones = _mutan(_llamadas(tmp_path))
    assert len(mutaciones) == 1 and "firewall-rules create cognion-web" in mutaciones[0]


def test_si_no_puede_consultar_los_presupuestos_no_crea_un_duplicado(tmp_path: Path) -> None:
    """Regresión: un error de la consulta no se interpreta como 'no existe' (eso duplicaba el presupuesto)."""
    _completo(tmp_path)
    r = _correr(tmp_path, "aprovisionar.sh", "--si", extra={"FAKE_PRESUPUESTOS_FALLA": "1"})
    assert r.returncode != 0
    assert "No pude consultar los presupuestos" in r.stderr
    assert not any("budgets create" in x for x in _llamadas(tmp_path))


def test_los_comandos_de_presupuestos_indican_el_proyecto_de_cuota(tmp_path: Path) -> None:
    """No dependen de la configuración activa de gcloud: llevan `--billing-project` del despliegue."""
    _estado(tmp_path)
    _correr(tmp_path, "aprovisionar.sh", "--si")
    presupuestos = [x for x in _llamadas(tmp_path) if "billing budgets" in x]
    assert presupuestos and all("--billing-project=cognion-prueba-2410" in x for x in presupuestos)


def test_sin_confirmacion_no_crea_nada(tmp_path: Path) -> None:
    """Sin `--si`, cualquier respuesta distinta de SI cancela."""
    _estado(tmp_path)
    r = _correr(tmp_path, "aprovisionar.sh", entrada="no\n")
    assert r.returncode != 0
    assert "Cancelado" in r.stderr
    assert _mutan(_llamadas(tmp_path)) == []


def test_con_confirmacion_escrita_crea(tmp_path: Path) -> None:
    """Escribir SI confirma el plan y se muestra qué se va a hacer."""
    _estado(tmp_path)
    r = _correr(tmp_path, "aprovisionar.sh", entrada="SI\n")
    assert r.returncode == 0, r.stderr
    assert "crear la VM cognion-vm" in r.stdout
    assert any("instances create" in x for x in _llamadas(tmp_path))


def test_advierte_del_costo_antes_de_crear(tmp_path: Path) -> None:
    """El plan avisa que la IPv4 pública en uso se cobra."""
    _estado(tmp_path)
    r = _correr(tmp_path, "aprovisionar.sh", entrada="no\n")
    assert "IPv4" in r.stdout


# ---------------------------------------------------------------- destruir.sh


def test_destruir_borra_solo_vm_regla_e_ip_por_nombre(tmp_path: Path) -> None:
    """Escenario 3: la VM primero, y ni el proyecto ni nada más."""
    _completo(tmp_path)
    r = _correr(tmp_path, "destruir.sh", "--si")
    assert r.returncode == 0, r.stderr
    ll = _llamadas(tmp_path)
    borrados = [x for x in ll if " delete " in x]
    assert [x.split(" delete ")[0].split()[-1] for x in borrados] == [
        "instances",
        "firewall-rules",
        "addresses",
    ]
    assert "instances delete cognion-vm" in borrados[0]
    assert not any("projects delete" in x for x in ll)
    assert not any("default-allow" in x and " delete " in x for x in ll)
    assert not any("budgets" in x and " delete" in x for x in ll)


def test_destruir_el_proyecto_exige_escribir_su_id(tmp_path: Path) -> None:
    """Con `--proyecto` y el ID correcto borra el proyecto; con otro ID no borra nada."""
    _completo(tmp_path)
    mal = _correr(tmp_path, "destruir.sh", "--si", "--proyecto", entrada="otro-proyecto\n")
    assert mal.returncode != 0
    assert "no coincide" in mal.stderr
    assert not any("projects delete" in x for x in _llamadas(tmp_path))
    assert not any(" delete " in x for x in _llamadas(tmp_path))
    bien = _correr(tmp_path, "destruir.sh", "--si", "--proyecto", entrada="cognion-prueba-2410\n")
    assert bien.returncode == 0, bien.stderr
    assert any("projects delete cognion-prueba-2410" in x for x in _llamadas(tmp_path))
    assert "projects undelete" in bien.stdout


def test_destruir_sin_confirmacion_no_borra_nada(tmp_path: Path) -> None:
    """Sin `--si`, solo SI confirma."""
    _completo(tmp_path)
    r = _correr(tmp_path, "destruir.sh", entrada="quizas\n")
    assert r.returncode != 0
    assert not any(" delete " in x for x in _llamadas(tmp_path))


def test_destruir_sin_recursos_no_falla(tmp_path: Path) -> None:
    """Si ya no existe nada, lo dice y sale bien sin borrar."""
    _estado(tmp_path, proyecto=True, reglas=[])
    r = _correr(tmp_path, "destruir.sh", "--si")
    assert r.returncode == 0
    assert "Nada que borrar" in r.stdout
    assert not any(" delete " in x for x in _llamadas(tmp_path))


def test_destruir_sin_gcloud_falla_sin_traza(tmp_path: Path) -> None:
    """Error claro cuando falta gcloud."""
    _estado(tmp_path)
    r = _correr(tmp_path, "destruir.sh", "--si", con_gcloud=False)
    assert r.returncode != 0 and "Falta gcloud" in r.stderr and "Traceback" not in r.stderr


# ---------------------------------------------------------------- desplegar.sh (desde la Mac)


def _copia_de_gcp(tmp_path: Path) -> Path:
    destino = tmp_path / "deploy" / "gcp"
    shutil.copytree(GCP, destino, ignore=shutil.ignore_patterns(".env"))
    (destino / ".env").write_text("SECRETO=no-debe-viajar\n")
    return destino


@pytest.mark.parametrize(
    ("entrada", "imagen"),
    [
        ("v0.8.2", "ghcr.io/vvalotto/cognion:v0.8.2"),
        ("ghcr.io/otro/imagen:v1", "ghcr.io/otro/imagen:v1"),
        ("cognion:ci", "cognion:ci"),
    ],
)
def test_desplegar_completa_la_version_a_una_imagen(
    tmp_path: Path, entrada: str, imagen: str
) -> None:
    """Una versión sola va a GHCR; una imagen completa se usa tal cual."""
    _estado(tmp_path)
    carpeta = _copia_de_gcp(tmp_path)
    env = _entorno(tmp_path)
    env["PROYECTO"] = "cognion-prueba-2410"
    r = subprocess.run(
        ["bash", str(carpeta / "desplegar.sh"), entrada],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )  # noqa: S603,S607
    assert r.returncode == 0, r.stderr
    assert f"./cognion.sh desplegar '{imagen}'" in "\n".join(_llamadas(tmp_path))


def test_desplegar_no_envia_el_env_a_la_vm(tmp_path: Path) -> None:
    """La sincronización lleva la configuración, pero nunca el `.env` con los secretos."""
    _estado(tmp_path)
    carpeta = _copia_de_gcp(tmp_path)
    assert (
        carpeta / ".env"
    ).exists()  # el .env existe en la copia: si viajara, se vería en el paquete
    env = _entorno(tmp_path)
    env["PROYECTO"] = "cognion-prueba-2410"
    r = subprocess.run(
        ["bash", str(carpeta / "desplegar.sh"), "v0.8.2"],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )  # noqa: S603,S607
    assert r.returncode == 0, r.stderr
    paquete = (
        tmp_path / "stdin.bin.1"
    )  # lo que recibió la primera llamada por SSH: la sincronización
    nombres = subprocess.run(
        ["tar", "tzf", str(paquete)], capture_output=True, text=True, check=True
    ).stdout.split()
    assert "gcp/docker-compose.yml" in nombres and "gcp/cognion.sh" in nombres
    assert "gcp/.env" not in nombres
    contenido = subprocess.run(
        ["tar", "xzOf", str(paquete)], capture_output=True, text=True, check=True
    ).stdout
    assert "no-debe-viajar" not in contenido


def test_desplegar_exige_proyecto_y_version(tmp_path: Path) -> None:
    """Sin proyecto o sin versión, error claro y sin llamar a la nube."""
    _estado(tmp_path)
    sin_proyecto = _correr(tmp_path, "desplegar.sh", "v0.8.2", extra={"PROYECTO": ""})
    assert sin_proyecto.returncode != 0 and "Falta PROYECTO" in sin_proyecto.stderr
    sin_version = _correr(tmp_path, "desplegar.sh")
    assert sin_version.returncode != 0 and "Indicá la versión" in sin_version.stderr
    assert not any("compute ssh" in x for x in _llamadas(tmp_path))


# ---------------------------------------------------------------- estáticos


@pytest.mark.parametrize(
    "script", ["aprovisionar.sh", "destruir.sh", "desplegar.sh", "preparar-vm.sh", "cognion.sh"]
)
def test_los_scripts_tienen_sintaxis_valida_y_son_ejecutables(script: str) -> None:
    """`bash -n` y permiso de ejecución."""
    assert (
        subprocess.run(["bash", "-n", str(GCP / script)], check=False).returncode == 0
    )  # noqa: S603,S607
    assert (GCP / script).stat().st_mode & stat.S_IXUSR


def test_preparar_vm_verifica_la_huella_de_la_clave_de_docker() -> None:
    """Docker se instala del repositorio oficial y se aborta si la huella no coincide."""
    texto = (GCP / "preparar-vm.sh").read_text()
    assert 'HUELLA_DOCKER="9DC858229FC7DD38854AE2D88D81803C0EBFCD88"' in texto
    assert 'if [ "$HUELLA" != "$HUELLA_DOCKER" ]' in texto
    assert "https://download.docker.com/linux/debian/gpg" in texto
    assert "get.docker.com" not in texto
    assert "swapon --show" in texto and "/etc/fstab" in texto


def test_la_publicacion_en_ci_ocurre_solo_con_etiquetas() -> None:
    """Escenario 4: login y push en GHCR solo para `vX.Y.Z`, sin `latest`, con la etiqueta de origen."""
    workflow = yaml.safe_load((RAIZ / ".github" / "workflows" / "cd.yml").read_text())
    job = workflow["jobs"]["build-and-deploy"]
    assert job["permissions"]["packages"] == "write"
    condicionados = [
        p
        for p in job["steps"]
        if p.get("if")
        == "startswith(github.ref, 'refs/tags/v')".replace("startswith", "startsWith")
    ]
    nombres = " ".join(p["name"] for p in condicionados)
    assert "GHCR" in nombres and len(condicionados) == 2
    texto = (RAIZ / ".github" / "workflows" / "cd.yml").read_text()
    assert "IMAGEN: ghcr.io/${{ github.repository }}" in texto
    assert "docker push" in texto and "${{ github.ref_name }}" in texto
    assert ":latest" not in texto
    assert "org.opencontainers.image.source" in texto
    assert "# - name: Deploy a Fly.io" in texto  # los pasos de Fly.io siguen comentados
