"""
pipeline.py
===========
Orquesta UNA corrida completa del proceso:

    config (categorías)
        -> source.extraer_jobs_categoria()        [EXTRACT]
        -> transform.transformar_categoria()       [TRANSFORM]
        -> state (filtrar "ya vistos")             [STATE]
        -> notifier.construir_html() + enviar_email() [LOAD]
        -> state.guardar_vistos()                  [STATE]

Este archivo NO sabe CÓMO se scrapea, CÓMO se filtra, ni CÓMO se
envía un email -- solo conoce el ORDEN en que ocurren esas cosas.
"""

from datetime import datetime

from config import TERMINOS
from source import extraer_jobs_categoria
from transform import transformar_categoria
from cache import cargar_vistos, guardar_vistos
from alerts import construir_html, construir_html_rechazadas, enviar_email
from config import EMAIL_ASUNTO_RECHAZADAS


def ejecutar_corrida():
    print(f"\n{'#'*70}")
    print(f"#  INICIANDO CORRIDA — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}")

    # ── Paso 1: cargar vistos ──
    vistos = cargar_vistos()
    print(f"  URLs ya vistas en corridas anteriores: {len(vistos)}")

    # ── Paso 2: extraer + transformar, por categoría ──
    todas_calificadas = []
    todas_rechazadas = []

    for categoria in TERMINOS.keys():
        print(f"\n--- Categoría: {categoria} ---")

        crudas = extraer_jobs_categoria(categoria)
        print(f"  Crudas: {len(crudas)}")

        calificadas, rechazadas = transformar_categoria(crudas, categoria)
        print(f"  Calificadas: {len(calificadas)} | Rechazadas (AR, casi califican): {len(rechazadas)}")

        todas_calificadas.extend(calificadas)
        todas_rechazadas.extend(rechazadas)

    # ── Paso 3: filtrar solo las NUEVAS (no vistas antes) ──
    nuevas_calificadas = [v for v in todas_calificadas if v["url"] not in vistos]
    nuevas_rechazadas  = [v for v in todas_rechazadas if v["url"] not in vistos]

    print(f"\n  Total calificadas: {len(todas_calificadas)} | NUEVAS: {len(nuevas_calificadas)}")
    print(f"  Total rechazadas:  {len(todas_rechazadas)} | NUEVAS: {len(nuevas_rechazadas)}")

    # ── Paso 4: email de calificadas nuevas ──
    html_calificadas = construir_html(nuevas_calificadas)
    enviar_email(html_calificadas, len(nuevas_calificadas))

    # ── Paso 5: email de rechazadas nuevas (Argentina) ──
    html_rechazadas = construir_html_rechazadas(nuevas_rechazadas)
    enviar_email(html_rechazadas, len(nuevas_rechazadas), asunto_base=EMAIL_ASUNTO_RECHAZADAS)

    # ── Paso 6: actualizar "vistos" con TODO lo de esta corrida ──
    urls_de_esta_corrida = set()
    urls_de_esta_corrida.update(v["url"] for v in todas_calificadas)
    urls_de_esta_corrida.update(v["url"] for v in todas_rechazadas)

    vistos.update(urls_de_esta_corrida)
    guardar_vistos(vistos)

    print(f"\n  💾 'vistos' actualizado. Total URLs guardadas: {len(vistos)}")
    print(f"\n{'#'*70}")
    print(f"#  CORRIDA FINALIZADA — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*70}\n")


if __name__ == "__main__":
    ejecutar_corrida()