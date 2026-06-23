"""
main.py
=======
Punto de entrada del programa.

Dos modos de uso:

    Modo manual (corre una vez y termina):
        python main.py --once

    Modo programado (queda corriendo, ejecuta automáticamente
    en los horarios definidos en config.HORARIOS_EJECUCION):
        python main.py
"""

import sys
import time
import schedule

from pipeline import ejecutar_corrida
from config import HORARIOS_EJECUCION


def modo_programado():
    print("🤖 Bot de vacantes iniciado en modo PROGRAMADO")
    print(f"⏰ Horarios de ejecución: {', '.join(HORARIOS_EJECUCION)}")
    print("🛑 Para detener: Ctrl + C\n")
    print("Dejá esta ventana abierta. El script se ejecutará automáticamente")
    print("en los horarios configurados, sin que tengas que hacer nada más.\n")

    for hora in HORARIOS_EJECUCION:
        schedule.every().day.at(hora).do(ejecutar_corrida)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    if "--once" in sys.argv:
        # Ejecución manual: corre una vez y termina
        ejecutar_corrida()
    else:
        # Modo programado: corre a los horarios configurados, todos los días
        modo_programado()