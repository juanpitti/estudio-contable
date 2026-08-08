import base64
from datetime import datetime, timezone
from unittest.mock import MagicMock
from xml.etree import ElementTree as ET

import pytest

from app.arca.config import ArcaEnv
from app.arca.wsaa import TicketAcceso, construir_tra, firmar_cms, login

TA_XML = """<?xml version="1.0"?>
<loginTicketResponse>
  <header><source>CN=wsaahomo</source><destination>CN=wsfe</destination></header>
  <credentials>
    <token>TOKEN1</token>
    <sign>SIGN1</sign>
  </credentials>
  <expirationTime>2026-08-09T01:00:00.000+0000</expirationTime>
</loginTicketResponse>
"""


def _client_mock():
    client = MagicMock()
    client.service.loginCms.return_value = TA_XML
    return client


def test_tra_contiene_servicio_y_tiempos_coherentes():
    tra = construir_tra("wsfe", ttl=600)
    assert b"<service>wsfe</service>" in tra
    raiz = ET.fromstring(tra)
    gen = datetime.strptime(raiz.findtext("header/generationTime"), "%Y-%m-%dT%H:%M:%S%z")
    exp = datetime.strptime(raiz.findtext("header/expirationTime"), "%Y-%m-%dT%H:%M:%S%z")
    delta = (exp - gen).total_seconds()
    assert delta == pytest.approx(660, abs=5)  # ttl + 60s de margen de reloj
    assert raiz.findtext("header/uniqueId").isdigit()


def test_login_parsea_token_sign_y_expiracion():
    ta = login(b"Y21zLWZhbHNv", ArcaEnv.HOMOLOGACION, client=_client_mock())
    assert ta.token == "TOKEN1"
    assert ta.sign == "SIGN1"
    assert ta.expiration == datetime(2026, 8, 9, 1, 0, tzinfo=timezone.utc)


def test_ticket_vencido():
    ta = login(b"Y21zLWZhbHNv", ArcaEnv.HOMOLOGACION, client=_client_mock())
    assert ta.vencido(datetime(2026, 8, 9, 2, 0, tzinfo=timezone.utc)) is True
    assert ta.vencido(datetime(2026, 8, 9, 0, 0, tzinfo=timezone.utc)) is False


def test_firmar_cms_devuelve_base64_decodable():
    cert_pem, key_pem = _cert_autofirmado()
    cms = firmar_cms(b"<tra/>", cert_pem, key_pem)
    assert len(base64.b64decode(cms)) > 100  # CMS DER con contenido real


def _cert_autofirmado():
    import datetime as dt

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-homo")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(nombre)
        .issuer_name(nombre)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1))
        .not_valid_after(dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    return (
        cert.public_bytes(serialization.Encoding.PEM),
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ),
    )
