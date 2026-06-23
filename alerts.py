"""
notifier.py
===========
Capa LOAD del pipeline.

Responsabilidad ÚNICA de este archivo:
    - Construir el HTML del email a partir de listas de dicts
      (las que devuelve transform.transformar_categoria).
    - Enviar emails por Gmail (SMTP).

NO hace scraping, NO transforma datos, NO guarda archivos.

Nota: trabaja con LISTAS DE DICTS (no DataFrames de pandas), para
ser coherente con source.py y transform.py.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    EMAIL_REMITENTE,
    EMAIL_DESTINATARIO,
    EMAIL_APP_PASSWORD,
    EMAIL_ASUNTO,
)


# ─────────────────────────────────────────────
def construir_html(calificadas):
    """
    Recibe:
        calificadas -> lista de dicts (vacantes que pasaron el filtro),
                       cada dict con keys: plan, titulo, empresa,
                       ubicacion, remoto, categoria, terminos_match, url

    Devuelve:
        Un string con el HTML completo del email, con una tabla
        que tiene una fila por vacante.
    """
    if not calificadas:
        return "<p>No se encontraron vacantes NUEVAS en esta corrida.</p>"

    filas_html = ""
    for vacante in calificadas:
        remoto_tag = "🌍 Remoto" if vacante["remoto"] else "—"
        filas_html += f"""
        <tr>
            <td style="padding:6px; border:1px solid #ddd; font-weight:bold;">{vacante['plan']}</td>
            <td style="padding:6px; border:1px solid #ddd;">
                <a href="{vacante['url']}">{vacante['titulo']}</a>
            </td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['empresa']}</td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['ubicacion']}</td>
            <td style="padding:6px; border:1px solid #ddd;">{remoto_tag}</td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['categoria']}</td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['terminos_match']}</td>
        </tr>"""

    # Conteo por plan: recorremos la lista y contamos cuántas
    # vacantes tienen plan == "A", "B", "C"
    total_a = sum(1 for v in calificadas if v["plan"] == "A")
    total_b = sum(1 for v in calificadas if v["plan"] == "B")
    total_c = sum(1 for v in calificadas if v["plan"] == "C")

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Vacantes NUEVAS encontradas</h2>
        <p>Total: {len(calificadas)} vacantes nuevas
        (Plan A: {total_a}, Plan B: {total_b}, Plan C: {total_c})</p>
        <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
            <thead>
                <tr style="background-color:#1F4E79; color:white;">
                    <th style="padding:6px; border:1px solid #ddd;">Plan</th>
                    <th style="padding:6px; border:1px solid #ddd;">Título</th>
                    <th style="padding:6px; border:1px solid #ddd;">Empresa</th>
                    <th style="padding:6px; border:1px solid #ddd;">Ubicación</th>
                    <th style="padding:6px; border:1px solid #ddd;">Modalidad</th>
                    <th style="padding:6px; border:1px solid #ddd;">Categoría</th>
                    <th style="padding:6px; border:1px solid #ddd;">Coincidencias</th>
                    <th style="padding:6px; border:1px solid #ddd;">Fuente</th>
                </tr>
            </thead>
            <tbody>
                {filas_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


# ─────────────────────────────────────────────
def construir_html_rechazadas(rechazadas):
    """
    Recibe:
        rechazadas -> lista de dicts (vacantes "casi califican" de
                      Argentina), cada dict con keys: plan, titulo,
                      empresa, ubicacion, categoria, coincidencias,
                      terminos_match, url

    Devuelve:
        Un string con el HTML completo del email de rechazadas.
    """
    if not rechazadas:
        return "<p>No hubo vacantes 'casi calificadas' NUEVAS en Argentina en esta corrida.</p>"

    filas_html = ""
    for vacante in rechazadas:
        filas_html += f"""
        <tr>
            <td style="padding:6px; border:1px solid #ddd; font-weight:bold;">{vacante['plan']}</td>
            <td style="padding:6px; border:1px solid #ddd;">
                <a href="{vacante['url']}">{vacante['titulo']}</a>
            </td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['empresa']}</td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['ubicacion']}</td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['categoria']}</td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['coincidencias']}</td>
            <td style="padding:6px; border:1px solid #ddd;">{vacante['terminos_match']}</td>
        </tr>"""

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Vacantes rechazadas NUEVAS - Argentina (casi califican)</h2>
        <p>Total: {len(rechazadas)} vacantes con al menos 1 coincidencia pero por debajo del mínimo requerido.</p>
        <table style="border-collapse: collapse; width: 100%; font-size: 13px;">
            <thead>
                <tr style="background-color:#A04040; color:white;">
                    <th style="padding:6px; border:1px solid #ddd;">Plan</th>
                    <th style="padding:6px; border:1px solid #ddd;">Título</th>
                    <th style="padding:6px; border:1px solid #ddd;">Empresa</th>
                    <th style="padding:6px; border:1px solid #ddd;">Ubicación</th>
                    <th style="padding:6px; border:1px solid #ddd;">Categoría</th>
                    <th style="padding:6px; border:1px solid #ddd;">Matches</th>
                    <th style="padding:6px; border:1px solid #ddd;">Términos</th>
                    <th style="padding:6px; border:1px solid #ddd;">Fuente</th>
                </tr>
            </thead>
            <tbody>
                {filas_html}
            </tbody>
        </table>
    </body>
    </html>
    """
    return html


# ─────────────────────────────────────────────
#  EMAIL
# ─────────────────────────────────────────────

def enviar_email(html_content, total_vacantes, asunto_base=None):
    """
    Envía un email HTML por Gmail (SMTP).

    Parámetros:
        html_content -> string con el HTML completo del email
        total_vacantes -> int, se muestra en el asunto entre paréntesis
        asunto_base -> string opcional; si no se pasa, usa EMAIL_ASUNTO
    """
    asunto_base = asunto_base or EMAIL_ASUNTO
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{asunto_base} ({total_vacantes})"
    msg["From"] = EMAIL_REMITENTE
    msg["To"] = EMAIL_DESTINATARIO

    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_REMITENTE, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_REMITENTE, EMAIL_DESTINATARIO, msg.as_string())
        print(f"\n📧 Email '{asunto_base}' enviado a {EMAIL_DESTINATARIO}")
    except Exception as e:
        print(f"\n⚠️ Error enviando email '{asunto_base}': {e}")


if __name__ == "__main__":
    # Prueba rápida con datos de ejemplo (sin scraping real)
    ejemplo_calificadas = [
        {
            "plan": "A", "titulo": "Data Engineer - Snowflake", "empresa": "Empresa X",
            "ubicacion": "Buenos Aires, Argentina", "remoto": False,
            "categoria": "IDMC", "terminos_match": "Data Engineer, Snowflake",
            "url": "https://www.linkedin.com/jobs/view/EJEMPLO",
        }
    ]
    html = construir_html(ejemplo_calificadas)
    enviar_email(html, len(ejemplo_calificadas))