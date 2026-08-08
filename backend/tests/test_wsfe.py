from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.arca.config import ArcaEnv
from app.arca.wsaa import TicketAcceso
from app.arca.wsfe import WsfeClient

TA = TicketAcceso(
    token="TOKEN1",
    sign="SIGN1",
    expiration=datetime.now(timezone.utc) + timedelta(hours=1),
)


def _client_mock():
    client = MagicMock()
    client.service.FEDummy.return_value = SimpleNamespace(
        AppServer="OK", DbServer="OK", AuthServer="OK"
    )
    client.service.FECompUltimoAutorizado.return_value = SimpleNamespace(CbteNro=42)
    client.service.FECompConsultar.return_value = SimpleNamespace(
        ResultGet=SimpleNamespace(
            CodAutorizacion="75321098765432",
            FchVto="20260820",
            CbteFch="20260808",
            ImpTotal=1210.5,
            CbteTipo=6,
            PtoVta=1,
            CbteDesde=42,
        )
    )
    return client


def _wsfe(client=None):
    return WsfeClient(
        cuit="20273965239", ta=TA, env=ArcaEnv.HOMOLOGACION, client=client or _client_mock()
    )


def test_dummy_devuelve_estado_de_los_tres_servidores():
    assert _wsfe().dummy() == {
        "app_server": "OK",
        "db_server": "OK",
        "auth_server": "OK",
    }


def test_ultimo_autorizado_devuelve_numero_y_envia_auth_correcto():
    client = _client_mock()
    assert _wsfe(client).ultimo_autorizado(pto_vta=1, cbte_tipo=6) == 42
    kwargs = client.service.FECompUltimoAutorizado.call_args.kwargs
    assert kwargs["Auth"] == {"Token": "TOKEN1", "Sign": "SIGN1", "Cuit": 20273965239}
    assert kwargs["PtoVta"] == 1
    assert kwargs["CbteTipo"] == 6


def test_consultar_comprobante_mapea_cae_fecha_e_importe():
    c = _wsfe().consultar_comprobante(cbte_tipo=6, pto_vta=1, nro=42)
    assert c["cae"] == "75321098765432"
    assert c["cae_vto"] == "20260820"
    assert c["fecha"] == "20260808"
    assert c["importe"] == 1210.5
    assert c["nro"] == 42


def test_ticket_vencido_lanza_error():
    ta_vencido = TicketAcceso("T", "S", datetime.now(timezone.utc) - timedelta(hours=1))
    with pytest.raises(ValueError, match="vencido"):
        WsfeClient(cuit="20273965239", ta=ta_vencido, client=_client_mock())
