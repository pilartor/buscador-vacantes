"""
PRÁCTICA PySpark — transform.py reescrito con Spark
=====================================================
Toma datos REALES de tu bot (vía extract.py) y aplica
la MISMA lógica de transform.py, pero con sintaxis PySpark.

Esto es solo para PRACTICAR y entender PySpark.
Tu pipeline real sigue usando transform.py (con Pandas/listas).
Este archivo NO se conecta al pipeline ni reemplaza nada.

Requisitos:
    pip install pyspark langdetect

Ejecutar con:
    python transform_pyspark_practica.py
"""

import os
import sys

# ─────────────────────────────────────────────
#  0. DECIRLE A SPARK QUÉ PYTHON USAR
# ─────────────────────────────────────────────
# Problema común en Windows + entornos virtuales (venv):
# Spark lanza procesos "worker" para correr las UDFs, y por
# defecto busca "python" en el PATH del sistema -> puede
# encontrar el Python del Microsoft Store en vez del de tu venv.
#
# sys.executable = el python.exe que está corriendo AHORA MISMO
# (el de tu venv). Le decimos a Spark que use ese mismo.
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lower, udf
from pyspark.sql.types import IntegerType, StringType, BooleanType, ArrayType

from langdetect import detect, LangDetectException

from config import (
    TERMINOS,
    MIN_MATCHES_POR_CATEGORIA,
    CATEGORIA_A_PLAN,
    REMOTE_KEYWORDS,
    HYBRID_KEYWORDS,
)
from source import extraer_jobs_categoria


# ─────────────────────────────────────────────
#  1. CREAR SESIÓN DE SPARK
# ─────────────────────────────────────────────
spark = SparkSession.builder \
    .appName("TransformPracticaPySpark") \
    .master("local[*]") \
    .getOrCreate()

print("✅ Spark Session creada\n")


# ─────────────────────────────────────────────
#  2. FUNCIONES AUXILIARES (las mismas que transform.py)
# ─────────────────────────────────────────────
# En PySpark, las funciones Python normales NO se pueden usar
# directo sobre columnas de un DataFrame. Hay que "envolverlas"
# como UDF (User Defined Function) para que Spark sepa cómo
# aplicarlas fila por fila.

def _contar_coincidencias(texto, terminos):
    """Misma lógica que transform.contar_coincidencias(), pero
    devuelve solo el número de hits (para simplificar el UDF)."""
    if texto is None:
        return 0
    texto_l = texto.lower()
    hits = 0
    for t in terminos:
        if "/" in t:
            partes = t.lower().split("/")
            if any(p.strip() in texto_l for p in partes if p.strip()):
                hits += 1
        else:
            if t.lower() in texto_l:
                hits += 1
    return hits


def _es_espanol(texto):
    """Misma lógica que transform.es_espanol()."""
    if not texto or len(str(texto).strip()) < 50:
        return False

    palabras_es = [
        "beneficios", "prestaciones", "vacante", "equipo",
        "experiencia", "postularse", "desarrollo",
    ]
    contiene_es = any(p in texto.lower() for p in palabras_es)

    try:
        es_es = detect(texto) == 'es'
    except LangDetectException:
        es_es = False

    return es_es or contiene_es


def _es_remoto_real(ubicacion, descripcion, is_remote_flag):
    """Misma lógica que transform.es_remoto_real()."""
    texto = f"{ubicacion or ''} {str(descripcion)[:1000]}".lower()

    if any(k in texto for k in HYBRID_KEYWORDS):
        return False

    if is_remote_flag is True:
        return True

    if any(k in texto for k in REMOTE_KEYWORDS):
        return True

    return False


# ─────────────────────────────────────────────
#  3. EXTRAER DATOS REALES (usando tu extract.py)
# ─────────────────────────────────────────────
CATEGORIA = "QA"  # cambiá esto para probar otras categorías: IDMC, ETL, IDMC_SOPORT

print(f"🔍 Extrayendo categoría '{CATEGORIA}' (datos reales de LinkedIn)...")
vacantes_crudas = extraer_jobs_categoria(CATEGORIA)
print(f"✅ Total extraído: {len(vacantes_crudas)}\n")

if len(vacantes_crudas) == 0:
    print("⚠️ No se encontraron vacantes. Probá con otra categoría o más HORAS_ANTIGUEDAD en config.py")
    spark.stop()
    exit()


# ─────────────────────────────────────────────
#  4. CREAR DataFrame DE PySpark
# ─────────────────────────────────────────────
# extraer_jobs_categoria() devuelve una lista de dicts -> Spark
# puede crear un DataFrame directo desde eso, igual que Pandas.

df = spark.createDataFrame(vacantes_crudas)

print("📋 Esquema del DataFrame (tipos de cada columna):")
df.printSchema()

print(f"\n📋 Total de filas: {df.count()}")
df.select("titulo", "empresa", "pais_busqueda").show(5, truncate=False)


# ─────────────────────────────────────────────
#  5. REGISTRAR LAS FUNCIONES COMO UDF
# ─────────────────────────────────────────────
# UDF = User Defined Function. Le decimos a Spark:
#   "esta función Python, aplicala a cada fila, y el resultado
#    va a ser de este tipo (Integer, String, Boolean)"

terminos_categoria = TERMINOS[CATEGORIA]

contar_coincidencias_udf = udf(
    lambda titulo, desc: _contar_coincidencias(f"{titulo} {desc}", terminos_categoria),
    IntegerType()
)

es_espanol_udf = udf(_es_espanol, BooleanType())

es_remoto_udf = udf(_es_remoto_real, BooleanType())


# ─────────────────────────────────────────────
#  6. APLICAR TRANSFORMACIONES (equivalente a transform.py)
# ─────────────────────────────────────────────

# 6.1 - Calcular coincidencias para cada fila
df_enriquecido = df.withColumn(
    "coincidencias",
    contar_coincidencias_udf(col("titulo"), col("descripcion"))
)

# 6.2 - Detectar idioma
df_enriquecido = df_enriquecido.withColumn(
    "idioma_es",
    es_espanol_udf(col("descripcion"))
)

# 6.3 - Detectar modalidad remota
df_enriquecido = df_enriquecido.withColumn(
    "remoto",
    es_remoto_udf(col("ubicacion"), col("descripcion"), col("is_remote_flag"))
)

print("\n📊 DataFrame enriquecido (con coincidencias, idioma, remoto):")
df_enriquecido.select("titulo", "empresa", "coincidencias", "idioma_es", "remoto").show(10, truncate=False)


# ─────────────────────────────────────────────
#  7. FILTRAR — equivalente al "if hits < min_matches"
# ─────────────────────────────────────────────
min_matches = MIN_MATCHES_POR_CATEGORIA[CATEGORIA]

df_calificadas = df_enriquecido.filter(col("coincidencias") >= min_matches)

print(f"\n🎯 Vacantes CALIFICADAS (coincidencias >= {min_matches}):")
print(f"   Total: {df_calificadas.count()} de {df_enriquecido.count()}")
df_calificadas.select("titulo", "empresa", "coincidencias", "idioma_es", "remoto").show(10, truncate=False)


# ─────────────────────────────────────────────
#  8. AGREGAR COLUMNA "plan" (equivalente a CATEGORIA_A_PLAN)
# ─────────────────────────────────────────────
plan_categoria = CATEGORIA_A_PLAN[CATEGORIA]

df_final = df_calificadas.withColumn("plan", when(col("categoria") == CATEGORIA, plan_categoria))

print(f"\n📈 Vacantes calificadas con Plan asignado:")
df_final.select("plan", "titulo", "empresa", "coincidencias").show(10, truncate=False)


# ─────────────────────────────────────────────
#  9. RESUMEN FINAL
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"RESUMEN — Categoría: {CATEGORIA} (Plan {plan_categoria})")
print("=" * 60)
print(f"  Total extraídas:    {df.count()}")
print(f"  Calificadas:        {df_calificadas.count()}")
print(f"  En español:         {df_calificadas.filter(col('idioma_es') == True).count()}")
print(f"  Remotas:            {df_calificadas.filter(col('remoto') == True).count()}")


spark.stop()
print("\n✅ Spark Session cerrada")