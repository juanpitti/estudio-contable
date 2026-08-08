"""Configuración de entornos ARCA. Homologación por defecto (Plan v4)."""

from enum import Enum


class ArcaEnv(str, Enum):
    HOMOLOGACION = "homologacion"
    PRODUCCION = "produccion"


WSAA_URLS = {
    ArcaEnv.HOMOLOGACION: "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl",
    ArcaEnv.PRODUCCION: "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl",
}

WSFE_URLS = {
    ArcaEnv.HOMOLOGACION: "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
    ArcaEnv.PRODUCCION: "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
}
