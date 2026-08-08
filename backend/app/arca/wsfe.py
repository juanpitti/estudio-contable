"""WSFE — Web Service de Facturación Electrónica (ARCA), modo consulta.

Cubre los canales de la Etapa 0/2: FEDummy (salud), FECompUltimoAutorizado
y FECompConsultar. El transporte zeep es inyectable para tests sin red.
"""

from typing import Any

from app.arca.config import WSFE_URLS, ArcaEnv
from app.arca.wsaa import TicketAcceso


class WsfeClient:
    def __init__(
        self,
        cuit: str,
        ta: TicketAcceso,
        env: ArcaEnv = ArcaEnv.HOMOLOGACION,
        client: Any = None,
    ) -> None:
        if ta.vencido():
            raise ValueError("Ticket de acceso vencido: renovar con WSAA login")
        self._auth = {"Token": ta.token, "Sign": ta.sign, "Cuit": int(cuit)}
        if client is None:
            from zeep import Client

            client = Client(WSFE_URLS[env])
        self._client = client

    def dummy(self) -> dict:
        """Salud del servicio: app/db/auth servers."""
        r = self._client.service.FEDummy()
        return {
            "app_server": r.AppServer,
            "db_server": r.DbServer,
            "auth_server": r.AuthServer,
        }

    def ultimo_autorizado(self, pto_vta: int, cbte_tipo: int) -> int:
        """Último número de comprobante autorizado para un punto de venta/tipo."""
        r = self._client.service.FECompUltimoAutorizado(
            Auth=self._auth, PtoVta=pto_vta, CbteTipo=cbte_tipo
        )
        return int(r.CbteNro)

    def consultar_comprobante(self, cbte_tipo: int, pto_vta: int, nro: int) -> dict:
        """Datos de un comprobante ya autorizado (CAE, fecha, importe)."""
        r = self._client.service.FECompConsultar(
            Auth=self._auth,
            FeCompConsReq={"CbteTipo": cbte_tipo, "PtoVta": pto_vta, "CbteNro": nro},
        )
        c = r.ResultGet
        return {
            "cae": c.CodAutorizacion,
            "cae_vto": c.FchVto,
            "fecha": c.CbteFch,
            "importe": float(c.ImpTotal),
            "cbte_tipo": int(c.CbteTipo),
            "pto_vta": int(c.PtoVta),
            "nro": int(c.CbteDesde),
        }
