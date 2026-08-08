"""Lector de QR de comprobantes AFIP/ARCA.

El QR fiscal es una URL https://www.afip.gob.ar/fe/qr/?p=<base64(JSON)>.
QR legible → datos exactos con confianza 1.0, sin OCR (criterio del Plan v4).
"""

import base64
import binascii
import json

import cv2
import numpy as np

_PREFIJOS_QR_AFIP = (
    "https://www.afip.gob.ar/fe/qr/?p=",
    "http://www.afip.gob.ar/fe/qr/?p=",
)


def _decodificar_qr(imagen: bytes) -> str | None:
    arr = np.frombuffer(imagen, dtype=np.uint8)
    mat = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if mat is None:
        return None
    texto, _, _ = cv2.QRCodeDetector().detectAndDecode(mat)
    return texto or None


def extraer_qr(imagen: bytes) -> dict | None:
    """Devuelve el payload JSON del QR AFIP, o None si no hay QR fiscal legible."""
    texto = _decodificar_qr(imagen)
    if not texto:
        return None
    for prefijo in _PREFIJOS_QR_AFIP:
        if texto.startswith(prefijo):
            try:
                crudo = texto[len(prefijo):]
                # AFIP usa base64 estándar; tolerar variante URL-safe
                return json.loads(base64.b64decode(crudo + "==", altchars=b"-_"))
            except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
                return None
    return None
