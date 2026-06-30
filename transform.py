"""
Capa TRANSFORM del pipeline.

Responsabilidad ÚNICA de este archivo:
    - Recibir vacantes "crudas" (las que devuelve source.py)
    - Filtrar por relevancia (cantidad de coincidencias con TERMINOS)
    - Detectar idioma (español / no español)
    - Detectar modalidad real (remoto / híbrido / presencial)
    - Clasificar en Plan (A/B/C) según la categoría
    - Separar en dos grupos:
        - "calificadas"  -> cumplen el mínimo de coincidencias
        - "rechazadas"   -> tienen >=1 coincidencia pero no llegan al mínimo
                            (solo para Argentina, en español -> "casi califican")

NO hace scraping (eso es source.py) y NO envía emails ni
guarda archivos (eso es notifier.py / state.py).
"""

from langdetect import detect, LangDetectException

from config import (
    TERMINOS,
    MIN_MATCHES_POR_CATEGORIA,
    CATEGORIA_A_PLAN,
    REMOTE_KEYWORDS,
    HYBRID_KEYWORDS,
    DEBUG,
)


# ─────────────────────────────────────────────
def contar_coincidencias(texto, terminos):
    """
    Cuenta cuántos términos de `terminos` aparecen en `texto`.

    Soporta términos con "/" como sinónimos, ej "IDMC/IICS":
    si aparece CUALQUIERA de las dos partes, cuenta como 1 coincidencia.

    Devuelve:
        (hits, matched)
        - hits:    cantidad de términos que matchearon
        - matched: lista de los términos que matchearon (para debug)
    """
    texto_l = texto.lower()
    hits = 0
    matched = []

    for t in terminos:
        if "/" in t:
            partes = t.lower().split("/")
            if any(p.strip() in texto_l for p in partes if p.strip()):
                hits += 1
                matched.append(t)
        else:
            if t.lower() in texto_l:
                hits += 1
                matched.append(t)

    return hits, matched


# ─────────────────────────────────────────────
def es_espanol(texto):
    """
    Determina si una descripción está en español.

    Usa dos señales:
        1. Palabras típicas de avisos laborales en español
           (beneficios, vacante, experiencia, etc.)
        2. Detección automática de idioma con langdetect

    Si CUALQUIERA de las dos da positivo, se considera español.
    Esto cubre el caso de títulos en inglés ("Data Engineer")
    con descripción en español.
    """
    if not texto or len(str(texto).strip()) < 50:
        return False

    palabras_es = [
        "beneficios", "prestaciones", "vacante", "equipo",
        "experiencia", "postularse", "desarrollo","cuenta","llevamos"
    ]
    contiene_es = any(p in texto.lower() for p in palabras_es)

    try:
        es_es = detect(texto) == 'es'
    except LangDetectException:
        es_es = False

    return es_es or contiene_es


# ─────────────────────────────────────────────
def es_remoto_real(ubicacion, descripcion, is_remote_flag):
    """
    Determina la modalidad real de la vacante.

    Reglas (en este orden):
        1. Si menciona palabras de presencial/híbrido -> NO es remoto,
           sin importar lo que diga is_remote_flag.
        2. Si JobSpy ya marcó is_remote_flag=True -> es remoto.
        3. Si el texto contiene palabras de "remoto" -> es remoto.
        4. Si nada de lo anterior aplica -> NO es remoto.
    """
    texto = f"{ubicacion} {str(descripcion)[:1000]}".lower()

    if any(k in texto for k in HYBRID_KEYWORDS):
        return False

    if is_remote_flag is True:
        return True

    if any(k in texto for k in REMOTE_KEYWORDS):
        return True

    return False


# ─────────────────────────────────────────────
def transformar_categoria(vacantes_crudas, categoria,vistos_corrida=None):
    """
    Función principal de este módulo.

    Recibe:
        vacantes_crudas: lista de dicts "crudos" (output de
                          source.extraer_jobs_categoria())
        categoria:       string, ej "IDMC", "ETL", "QA", "IDMC_SOPORT"

    Devuelve:
        (calificadas, rechazadas)

        calificadas: lista de dicts enriquecidos, solo las vacantes
                      que cumplen MIN_MATCHES_POR_CATEGORIA[categoria].
                      Cada dict incluye:
                        plan, categoria, pais_busqueda, titulo, empresa,
                        ubicacion, remoto, idioma_es, coincidencias,
                        terminos_match, url

        rechazadas:  lista de dicts (mismo formato, sin 'remoto' ni
                      'idioma_es') para vacantes de Argentina, en
                      español, con >=1 coincidencia pero por debajo
                      del mínimo. Sirven para revisar manualmente
                      "casi califican".
    """
    if vistos_corrida is None:
        vistos_corrida = set()
    terminos = TERMINOS[categoria]
    min_matches = MIN_MATCHES_POR_CATEGORIA[categoria]
    plan = CATEGORIA_A_PLAN[categoria]

    calificadas = []
    rechazadas = []

    for vacante in vacantes_crudas:
        titulo       = vacante["titulo"]
        empresa      = vacante["empresa"]
        ubicacion    = vacante["ubicacion"]
        descripcion  = vacante["descripcion"]
        url          = vacante["url"]
        pais         = vacante["pais_busqueda"]
        is_remote_flag = vacante["is_remote_flag"]

        texto_completo = f"{titulo} {descripcion}"
        hits, matched = contar_coincidencias(texto_completo, terminos)

        # No llega al mínimo de coincidencias
        if hits < min_matches:
            if DEBUG:
                print(f"      ✗ DESCARTADO ({hits} match: {matched}) -> '{titulo}'")

            # Capturar "casi califican" SOLO para Argentina y en español
            if pais == "Argentina" and hits >= 2 and es_espanol(descripcion):
                rechazadas.append({
                    "plan":           plan,
                    "categoria":      categoria,
                    "pais_busqueda":  pais,
                    "titulo":         titulo,
                    "empresa":        empresa,
                    "ubicacion":      ubicacion,
                    "coincidencias":  hits,
                    "terminos_match": ", ".join(matched),
                    "sitio_origen":   vacante.get("sitio_origen", ""),
                    "url":            url,
                })
            continue

        # Cumple el mínimo de coincidencias
        idioma_es = es_espanol(descripcion)

        # Descartar si la descripción NO está en español
        if not idioma_es:
            continue

        remoto = es_remoto_real(ubicacion, descripcion, is_remote_flag)
        
        # Vacantes fuera de Argentina que NO son remotas se descartan
        #if pais != "Argentina" and not remoto:
        #    continue
        if url in vistos_corrida:
            if DEBUG:
                print(f"      ✗ DUPLICADO EN CORRIDA -> '{titulo}'")
            continue
        
        calificadas.append({
            "plan":            plan,
            "categoria":       categoria,
            "pais_busqueda":   pais,
            "titulo":          titulo,
            "empresa":         empresa,
            "ubicacion":       ubicacion,
            "remoto":          remoto,
            "idioma_es":       idioma_es,
            "coincidencias":   hits,
            "terminos_match":  ", ".join(matched),
            "url":             url,
        })

    return calificadas, rechazadas


# ─────────────────────────────────────────────
# Prueba rápida del módulo (opcional).
# Encadena con source.py para probar el pipeline parcial:
# extracción -> transformación, sin enviar emails ni guardar nada.
if __name__ == "__main__":
    from source import extraer_jobs_categoria

    categoria = "QA"
    print(f"Extrayendo categoría '{categoria}'...")
    crudas = extraer_jobs_categoria(categoria)
    print(f"Total crudas: {len(crudas)}")

    calificadas, rechazadas = transformar_categoria(crudas, categoria)

    print(f"\nCalificadas: {len(calificadas)}")
    if calificadas:
        print(calificadas[0])

    print(f"\nRechazadas (casi califican, Argentina, español): {len(rechazadas)}")
    if rechazadas:
        print(rechazadas[0])