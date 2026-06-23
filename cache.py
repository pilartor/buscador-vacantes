"""
========
Capa de PERSISTENCIA / ESTADO del pipeline.

Responsabilidad ÚNICA de este archivo:
    - Leer y escribir el archivo vacantes_vistas.json
    - Ese archivo guarda las URLs de vacantes ya enviadas en
      corridas anteriores, para no repetirlas.

NO hace scraping, NO transforma datos, NO envía emails.
Solo lee/escribe un archivo en disco.
"""

import os
import json
from datetime import datetime

from config import ARCHIVO_VISTOS


def cargar_vistos():
    """Carga el set de URLs ya enviadas en corridas anteriores."""
    if os.path.exists(ARCHIVO_VISTOS):
        try:
            with open(ARCHIVO_VISTOS, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("urls", []))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def guardar_vistos(vistos):
    """Guarda el set actualizado de URLs ya enviadas, con timestamp."""
    data = {
        "ultima_actualizacion": datetime.now().isoformat(),
        "total_urls": len(vistos),
        "urls": list(vistos),
    }
    with open(ARCHIVO_VISTOS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    vistos = cargar_vistos()
    print(f"URLs ya vistas: {len(vistos)}")

    vistos.add("https://www.linkedin.com/jobs/view/EJEMPLO")
    guardar_vistos(vistos)
    print(f"Guardado OK. Total ahora: {len(vistos)}")