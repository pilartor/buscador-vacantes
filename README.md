# Job Alert Bot — LinkedIn Vacancy Finder

Bot personal de búsqueda de empleo que automatiza la detección de vacantes relevantes en LinkedIn, las clasifica según distintos perfiles de búsqueda (Planes A/B/C), y envía notificaciones por email solo con resultados nuevos.

## ¿Qué hace?

1. **Extrae** vacantes de LinkedIn vía [JobSpy](https://github.com/Bunsly/JobSpy), usando búsquedas OR con términos técnicos específicos (Informatica IDMC/IICS, Snowflake, ETL, etc.).
2. **Transforma** los resultados: filtra por relevancia (cantidad de coincidencias técnicas), detecta el idioma de la descripción, y verifica si la modalidad es remota o híbrida.
3. **Clasifica** cada vacante en un "Plan" (A, B, C) según el perfil al que mejor se ajusta.
4. **Evita duplicados**: guarda un registro de las vacantes ya notificadas (`vacantes_vistas.json`) para enviar solo las nuevas en cada corrida.
5. **Notifica** por email (Gmail SMTP) con una tabla HTML resumen.
6. **Se ejecuta automáticamente** a horarios fijos (10:00, 15:00 y 17:00) mientras la PC esté encendida.

## Arquitectura (patrón ETL modular)

```
proyecto/
├── config.py        # Credenciales, términos de búsqueda, horarios
├── source.py        # Llama a JobSpy / LinkedIn (Extract)
├── transform.py      # Filtros de relevancia, idioma, clasificación (Transform)
├── cache.py          # Lectura/escritura de vacantes_vistas.json (deduplicación)
├── alerts.py        # Construcción de HTML y envío por email (Load)
├── pipeline.py       # Orquesta una corrida completa
├── main.py           # Punto de entrada: modo manual o programado
└── data/
    └── vacantes_vistas.json
```

## Requisitos

```bash
pip install python-jobspy langdetect pandas schedule
```

## Configuración

1. Activar verificación en 2 pasos en tu cuenta de Gmail.
2. Generar una contraseña de aplicación: https://myaccount.google.com/apppasswords
3. Completar en `config.py`:
   - `EMAIL_REMITENTE`
   - `EMAIL_DESTINATARIO`
   - `EMAIL_APP_PASSWORD` (la contraseña de 16 caracteres generada)

## Uso

**Ejecución manual (una sola corrida, para probar):**
```bash
python main.py --once
```

**Modo programado (corre solo a las 10:00, 15:00 y 17:00):**
```bash
python main.py
```

> ⚠️ La PC debe permanecer encendida y con el script corriendo durante esos horarios para que la ejecución automática funcione.

## Decisiones de diseño

- **Deduplicación por URL**: cada vacante se identifica por su URL única; se compara contra un registro persistente para no notificar lo mismo dos veces.
- **Filtro de idioma**: se usa `langdetect` sobre la descripción completa (no solo el título), ya que muchas vacantes tienen título en inglés ("Data Engineer") pero contenido en español.
- **Clasificación por planes**: permite priorizar distintos perfiles de búsqueda (por ejemplo, Plan A = Data Engineer / Informatica, Plan B = ETL general, Plan C = QA de Datos) sin duplicar lógica.
- **Separación ETL**: cada módulo tiene una única responsabilidad, facilitando pruebas, mantenimiento y reemplazo de componentes (por ejemplo, cambiar el notificador de email a Slack sin tocar el resto del pipeline).

## Próximas mejoras posibles

- Soporte para más fuentes
- Dashboard simple para visualizar el historial de vacantes enviadas
- Métricas de postulación (cuántas vacantes nuevas por semana, por plan)