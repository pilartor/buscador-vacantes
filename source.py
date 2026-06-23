"""
Capa EXTRACT del pipeline.

Responsabilidad ÚNICA de este archivo:
    - Llamar a JobSpy (scrape_jobs) para traer vacantes "crudas" de LinkedIn.
    - NO filtra por relevancia, NO detecta idioma, NO clasifica remoto/no-remoto.
    - Todo eso es trabajo de transform.py.

Este archivo SOLO sabe "ir a buscar datos" y devolverlos en bruto.
"""

import time
from jobspy import scrape_jobs

from config import TERMINOS, PLANES_PAISES, CANTIDAD_POR_BUSQUEDA, HORAS_ANTIGUEDAD,SITIOS_BUSQUEDA


# ─────────────────────────────────────────────
def build_or_query(terminos):
    """
    Recibe una lista de términos, ej:
        ["a", "b", "c"]

    Devuelve un string armado para la búsqueda con OR, ej:
        '"a" OR "b" OR "c"'
    """
    query = " OR ".join(f'"{t}"' for t in terminos)
    return query


# ─────────────────────────────────────────────
def extraer_jobs_pais(query, pais, requiere_remoto):
    """
    Hace UNA llamada a scrape_jobs() para un país puntual.

    Devuelve:
        - El DataFrame que devuelve scrape_jobs(), o None si hubo
          error o no encontró resultados.
    """
    try:
        jobs = scrape_jobs(
            site_name=SITIOS_BUSQUEDA,
            search_term=query,
            location=pais,
            is_remote=requiere_remoto,
            results_wanted=CANTIDAD_POR_BUSQUEDA,
            hours_old=HORAS_ANTIGUEDAD,
            country_indeed=pais,
            linkedin_fetch_description=True,
        )
    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        return None

    if jobs is None or len(jobs) == 0:
        print("   (sin resultados)")
        return None

    return jobs


# ─────────────────────────────────────────────
def extraer_jobs_categoria(categoria):
    """
    Función principal de este módulo.

    Para UNA categoría (ej "IDMC", "ETL", "QA", "IDMC_SOPORT"):
        1. Toma sus términos desde TERMINOS[categoria]
        2. Construye la query con build_or_query()
        3. Recorre todos los (pais, requiere_remoto) de PLANES_PAISES[categoria]
        4. Por cada país, llama a extraer_jobs_pais()
        5. Convierte cada fila del resultado a un dict "crudo"

    Devuelve:
        Una lista de dicts (jobs "crudos"), uno por vacante encontrada
        en TODOS los países de esa categoría.
    """
    terminos = TERMINOS[categoria]
    paises_y_remoto = PLANES_PAISES[categoria]
    query = build_or_query(terminos)

    resultados = []

    for pais, requiere_remoto in paises_y_remoto:
        jobs = extraer_jobs_pais(query, pais, requiere_remoto)

        if jobs is None:
            continue

        for _, job in jobs.iterrows():
            titulo         = str(job.get('title', '') or '')
            empresa        = str(job.get('company', '') or '')
            ubicacion      = str(job.get('location', '') or '')
            descripcion    = str(job.get('description', '') or '')
            url            = str(job.get('job_url', '') or '')
            is_remote_flag = job.get('is_remote', None)

            vacante = {
                "categoria":       categoria,
                "pais_busqueda":   pais,
                "requiere_remoto": requiere_remoto,
                "titulo":          titulo,
                "empresa":         empresa,
                "ubicacion":       ubicacion,
                "descripcion":     descripcion,
                "url":             url,
                "is_remote_flag":  is_remote_flag,
                "sitio_origen":    str(job.get('site', '') or ''),  # linkedin / indeed 
            }

            resultados.append(vacante)

        time.sleep(2)

    return resultados


# ─────────────────────────────────────────────
# Prueba rápida del módulo (opcional).
# Podés correr "python source.py" para probar que la extracción
# funciona antes de conectarlo con el resto del pipeline.
if __name__ == "__main__":
    resultados = extraer_jobs_categoria("QA")
    print(f"Total extraído: {len(resultados)}")
    if resultados:
        print(resultados[0])