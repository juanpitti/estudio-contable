import subprocess
import sys

msg = "feat(facturacion): Etapa 4 - API de facturacion con CAE\n\n- POST /clientes/{id}/facturacion/emitir\n- Integracion con WSFE (mock en tests)\n- Generacion de PDF con QR\n- Registro automatico en comprobantes\n- Tests de exito y 404\n\nSuite completa: 100% pass"

subprocess.run(["git", "commit", "-m", msg], check=True)
