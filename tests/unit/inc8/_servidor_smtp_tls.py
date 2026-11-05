"""Servidor SMTP mínimo con STARTTLS para probar la validación del certificado (`US-ADJ-66`).

Corre en un hilo sobre `127.0.0.1`, registra los comandos que recibe y genera sus certificados con
`cryptography` (autoridad de prueba, certificado emitido por ella, autofirmado y emitido para otro nombre).
No usa internet ni toca ninguna base de datos.
"""

from __future__ import annotations

import base64
import datetime
import socket
import ssl
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID


@dataclass(frozen=True)
class ParCertificado:
    """Certificado y clave privada en PEM."""

    certificado: bytes
    clave: bytes


def _clave() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


def _pem_clave(clave: ec.EllipticCurvePrivateKey) -> bytes:
    return clave.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _construir(
    nombre: str,
    clave: ec.EllipticCurvePrivateKey,
    emisor_nombre: x509.Name,
    firmante: ec.EllipticCurvePrivateKey,
    *,
    es_ca: bool,
    dns: tuple[str, ...] = (),
) -> x509.Certificate:
    """Arma un certificado válido por un día; `es_ca` lo habilita para firmar otros."""
    ahora = datetime.datetime.now(datetime.UTC)
    sujeto = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, nombre)])
    builder = (
        x509.CertificateBuilder()
        .subject_name(sujeto)
        .issuer_name(emisor_nombre)
        .public_key(clave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora - datetime.timedelta(minutes=5))
        .not_valid_after(ahora + datetime.timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=es_ca, path_length=None), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(clave.public_key()), critical=False
        )
    )
    if dns:
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(d) for d in dns]), critical=False
        )
    return builder.sign(firmante, hashes.SHA256())


@dataclass(frozen=True)
class Certificados:
    """Juego de certificados de una prueba."""

    autoridad_pem: bytes
    valido: ParCertificado  # emitido por la autoridad de prueba para `localhost`
    autofirmado: ParCertificado  # para `localhost`, pero sin autoridad de confianza
    otro_nombre: ParCertificado  # emitido por la autoridad, pero para `otro.example`


def generar_certificados() -> Certificados:
    """Genera la autoridad de prueba y los tres certificados de servidor."""
    clave_ca = _clave()
    nombre_ca = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Autoridad de prueba")])
    ca = _construir("Autoridad de prueba", clave_ca, nombre_ca, clave_ca, es_ca=True)

    def emitido(nombre: str, dns: str) -> ParCertificado:
        clave = _clave()
        cert = _construir(nombre, clave, ca.subject, clave_ca, es_ca=False, dns=(dns,))
        return ParCertificado(cert.public_bytes(serialization.Encoding.PEM), _pem_clave(clave))

    clave_auto = _clave()
    nombre_auto = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    auto = _construir(
        "localhost", clave_auto, nombre_auto, clave_auto, es_ca=False, dns=("localhost",)
    )
    return Certificados(
        autoridad_pem=ca.public_bytes(serialization.Encoding.PEM),
        valido=emitido("localhost", "localhost"),
        autofirmado=ParCertificado(
            auto.public_bytes(serialization.Encoding.PEM), _pem_clave(clave_auto)
        ),
        otro_nombre=emitido("otro.example", "otro.example"),
    )


@dataclass
class ServidorSmtpTls:
    """Servidor SMTP de prueba. `par=None` no ofrece STARTTLS (servidor local sin cifrado)."""

    par: ParCertificado | None
    comandos: list[str] = field(default_factory=list)
    mensajes: list[str] = field(default_factory=list)
    puerto: int = 0
    _socket: socket.socket | None = None
    _hilo: threading.Thread | None = None
    _contexto: ssl.SSLContext | None = None

    def iniciar(self) -> None:
        """Abre el socket en un puerto libre y empieza a atender conexiones."""
        if self.par is not None:
            self._contexto = _contexto_servidor(self.par)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("127.0.0.1", 0))
        self._socket.listen(5)
        self.puerto = self._socket.getsockname()[1]
        self._hilo = threading.Thread(target=self._atender, daemon=True)
        self._hilo.start()

    def detener(self) -> None:
        """Cierra el socket de escucha."""
        if self._socket is not None:
            self._socket.close()

    def _atender(self) -> None:
        assert self._socket is not None
        while True:
            try:
                conexion, _ = self._socket.accept()
            except OSError:
                return
            try:
                self._conversar(conexion)
            except (OSError, ssl.SSLError):
                pass  # el cliente abortó (p. ej. rechazó el certificado)
            finally:
                conexion.close()

    def _conversar(self, conexion: socket.socket) -> None:
        conexion.settimeout(5)
        lector = conexion.makefile("rb")
        conexion.sendall(b"220 localhost ESMTP prueba\r\n")
        cifrado = False
        while True:
            linea = lector.readline().decode().rstrip("\r\n")
            if not linea:
                return
            verbo = linea.split(" ", 1)[0].upper()
            self.comandos.append(verbo)
            if verbo in {"EHLO", "HELO"}:
                extra = "250-STARTTLS\r\n" if self._contexto and not cifrado else ""
                auth = "250-AUTH PLAIN\r\n" if cifrado or self._contexto is None else ""
                conexion.sendall(f"250-localhost\r\n{extra}{auth}250 8BITMIME\r\n".encode())
            elif verbo == "STARTTLS" and self._contexto is not None:
                conexion.sendall(b"220 Ready to start TLS\r\n")
                conexion = self._contexto.wrap_socket(conexion, server_side=True)
                lector = conexion.makefile("rb")
                cifrado = True
            elif verbo == "AUTH":
                partes = linea.split(" ")
                self.comandos.append(
                    "AUTH:" + base64.b64decode(partes[-1]).decode(errors="replace")
                )
                conexion.sendall(b"235 2.7.0 Accepted\r\n")
            elif verbo == "DATA":
                conexion.sendall(b"354 End data with <CR><LF>.<CR><LF>\r\n")
                cuerpo: list[str] = []
                while (renglon := lector.readline().decode()) not in {".\r\n", ""}:
                    cuerpo.append(renglon)
                self.mensajes.append("".join(cuerpo))
                conexion.sendall(b"250 2.0.0 Queued\r\n")
            elif verbo == "QUIT":
                conexion.sendall(b"221 Bye\r\n")
                return
            else:
                conexion.sendall(b"250 OK\r\n")


def _contexto_servidor(par: ParCertificado) -> ssl.SSLContext:
    """Contexto TLS del lado servidor con el certificado indicado."""
    contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    with tempfile.TemporaryDirectory() as carpeta:
        ruta_cert, ruta_clave = Path(carpeta) / "c.pem", Path(carpeta) / "k.pem"
        ruta_cert.write_bytes(par.certificado)
        ruta_clave.write_bytes(par.clave)
        contexto.load_cert_chain(ruta_cert, ruta_clave)
    return contexto
