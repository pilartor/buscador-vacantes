"""
Se debe colocar datos sensibles como credenciales,terminos de busquedas, horarios , umbrales
 """
import os
from dotenv import load_dotenv
load_dotenv()

SITIOS_BUSQUEDA = ["linkedin", "indeed"]


# ─────────────────────────────────────────────
#  CONFIG EMAIL (Gmail)
# ─────────────────────────────────────────────

EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
EMAIL_REMITENTE = os.getenv("EMAIL_REMITENTE")
EMAIL_DESTINATARIO = os.getenv("EMAIL_REMITENTE")
EMAIL_ASUNTO       = "Vacantes nuevas - Plan A/B/C/D"
EMAIL_ASUNTO_RECHAZADAS = "Vacantes rechazadas (Argentina, casi califican)"

# ─────────────────────────────────────────────
#  CONFIG GENERAL
# ─────────────────────────────────────────────
CANTIDAD_POR_BUSQUEDA = 25
HORAS_ANTIGUEDAD = 48
MIN_MATCHES_POR_CATEGORIA = {
    "IDMC":        1,
    "SOPORT":      3,
    "ETL":         2,
    "QA":          2,
}
DEBUG = True

# Archivo donde se guardan las URLs de vacantes ya enviadas
ARCHIVO_VISTOS = "Data/vacantes_vistas.json"

# Horarios fijos de ejecución (formato 24hs "HH:MM")
HORARIOS_EJECUCION = ["10:00", "15:00", "17:00"]

# ─────────────────────────────────────────────
#  CATEGORÍAS -> PLAN
# ─────────────────────────────────────────────
CATEGORIA_A_PLAN = {
    "IDMC":        "A",
    "SOPORT":      "B",
    "ETL":         "C",
    "QA":          "D",
}

TERMINOS = {
    "IDMC": [
        "Informatica Cloud", "IDMC/IICS", "IICS/IDMC",
        "IICS", "iics","idmc","IDMC", "CAI", "Informatica Cloud Application Integration",
        "CDI", "Cloud Data Integration", "powercenter", "PowerCenter", "Power Center",
    ],
    "SOPORT": [
        "ETL","ELT", "SQL","monitoreo", "user FTP", 
        "administracion","soporte","desarrollo de pipelines"
    ],
    "ETL": [
        "ETL/ELT", "ETL", "desarrollador ETL", "Developer ETL",
        "Snowflake", "Medallion", "DWH", "Data Engineer Python",
        "pipeline de datos", "data pipeline","Data Engineer","DataEngineer","pipeline","scraping",
        "Data Integration", "Integración de datos", "python"
    ],
    "QA": [
        "Data Quality", "Data Governance", "Cloud Migration Engineer",
        "Data Validation", "QA Data", "Data Steward",
        "Validación de datos", "Gobierno de Datos","iics","idmc","PowerCenter",
        "Data Steward", "Validación de datos", 
        "Calidad de datos", "Analyst", "Master Data Management", "MDM",
    ],
}

PAISES_HISPANOS_REMOTO = [
    "Chile", "Peru", "Mexico", "Colombia", "Uruguay",
    "Costa Rica", "Spain", "Venezuela", "Ecuador", "Panama","Worldwide"
]

PLANES_PAISES = {
    "IDMC":        [("Argentina", False)] + [(p, False) for p in PAISES_HISPANOS_REMOTO],
    "SOPORT":      [("Argentina", False)] ,
    "ETL":         [("Argentina", False)] ,
    "QA":          [("Argentina", False)],
}

REMOTE_KEYWORDS = [
    "remote", "remoto", "100% remoto", "full remote", "trabajo remoto",
    "home office", "teletrabajo", "work from home", "wfh", "open to latam",
    "ubicación: remoto", "remota",
]
HYBRID_KEYWORDS = ["híbrido", "hibrido", "hybrid", "presencial", "on-site", "onsite"]