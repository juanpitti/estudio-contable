"""WSAA — Web Service de Autenticación y Autorización (ARCA).

Flujo: construir TRA (loginTicketRequest) → firmar CMS PKCS#7 → loginCms
→ Ticket de Acceso (token + sign) usable por wsfe y demás servicios.

Todo el transporte es inyectable para testear sin certificado ni red.
"""

import base64
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree as ET

from app.arca.config import WSAA_URLS, ArcaEnv

_FORMATO_FECHA = "%Y-%m-%dT%H:%M:%S%z"


@dataclass(frozen=True)
class TicketAcceso:
    token: str
    sign: str
    expiration: datetime

    def vencido(self, ahora: datetime | None = None) -> bool:
        return (ahora or datetime.now(timezone.utc)) >= self.expiration


def construir_tra(service: str, ttl: int = 3600) -> bytes:
    """Construye el Ticket de Requerimiento de Acceso en XML."""
    ahora = datetime.now(timezone.utc)
    raiz = ET.Element("loginTicketRequest", version="1.0")
    header = ET.SubElement(raiz, "header")
    ET.SubElement(header, "uniqueId").text = str(int(time.time()))
    ET.SubElement(header, "generationTime").text = (
        ahora - timedelta(seconds=60)
    ).strftime(_FORMATO_FECHA)
    ET.SubElement(header, "expirationTime").text = (
        ahora + timedelta(seconds=ttl)
    ).strftime(_FORMATO_FECHA)
    ET.SubElement(raiz, "service").text = service
    return ET.tostring(raiz, encoding="utf-8", xml_declaration=True)


def firmar_cms(tra: bytes, cert_pem: bytes, key_pem: bytes) -> bytes:
    """Firma el TRA como CMS/PKCS#7 y lo devuelve en base64 (lo que pide loginCms)."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.serialization import pkcs7

    cert = x509.load_pem_x509_certificate(cert_pem)
    key = serialization.load_pem_private_key(key_pem, password=None)
    cms_der = (
        pkcs7.PKCS7SignatureBuilder()
        .set_data(tra)
        .add_signer(cert, key, hashes.SHA256())
        .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.Binary])
    )
    return base64.b64encode(cms_der)


def login(cms_b64: bytes, env: ArcaEnv, client=None) -> TicketAcceso:
    """Ejecuta loginCms y parsea el Ticket de Acceso devuelto por ARCA."""
    if client is None:
        from zeep import Client

        client = Client(WSAA_URLS[env])
    respuesta = client.service.loginCms(in0=cms_b64.decode("ascii"))
    xml = respuesta if isinstance(respuesta, str) else str(respuesta)
    raiz = ET.fromstring(xml)
    return TicketAcceso(
        token=raiz.findtext(".//token") or "",
        sign=raiz.findtext(".//sign") or "",
        expiration=datetime.strptime(
            raiz.findtext(".//expirationTime") or "", "%Y-%m-%dT%H:%M:%S.%f%z"
        ),
    )
