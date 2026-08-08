#!/usr/bin/env python
"""Prototipo Etapa 0 / Tarea B — chequeo del canal WS ARCA en homologación.

Es el "portón" del Plan v4: prueba WSAA (login con certificado) y wsfe
(FEDummy + último comprobante autorizado) contra el ambiente de homologación.

Requiere certificado propio gestionado vía WSASS (nunca se commitea):

    python scripts/etapa0_arca_check.py --cert cert.pem --key key.pem --cuit 20273965239
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.arca.config import ArcaEnv  # noqa: E402
from app.arca.wsaa import construir_tra, firmar_cms, login  # noqa: E402
from app.arca.wsfe import WsfeClient  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(
        description="Chequeo de portón Etapa 0: WSAA + wsfe (homologación por defecto)"
    )
    p.add_argument("--cert", required=True, help="Certificado PEM de homologación")
    p.add_argument("--key", required=True, help="Clave privada PEM")
    p.add_argument("--cuit", required=True, help="CUIT del contribuyente de prueba")
    p.add_argument(
        "--env",
        default=ArcaEnv.HOMOLOGACION.value,
        choices=[e.value for e in ArcaEnv],
    )
    args = p.parse_args()

    env = ArcaEnv(args.env)
    cert = Path(args.cert).read_bytes()
    key = Path(args.key).read_bytes()

    print(f"[1/3] WSAA loginCms ({env.value})...")
    ta = login(firmar_cms(construir_tra("wsfe"), cert, key), env)
    print(f"      OK — ticket vence {ta.expiration.isoformat()}")

    print("[2/3] wsfe FEDummy...")
    wsfe = WsfeClient(cuit=args.cuit, ta=ta, env=env)
    print(f"      {wsfe.dummy()}")

    print("[3/3] wsfe FECompUltimoAutorizado (pto 1, Factura B)...")
    print(f"      Último autorizado: {wsfe.ultimo_autorizado(pto_vta=1, cbte_tipo=6)}")

    print("\nPORTÓN ETAPA 0: canal WS ARCA operativo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
