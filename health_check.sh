#!/bin/bash
# Script de salud diario para StreamRip
LOG_FILE="/home/ubuntu/ytdownloader/health_check.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')
VIDEO_URL="https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Rick Astley (video de prueba estándar)

echo "[$DATE] Iniciando comprobación de salud..." >> $LOG_FILE

# Intentar descargar vía local API
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:5000/api/download?url=$VIDEO_URL&format=mp3")

if [ "$STATUS_CODE" -eq 200 ]; then
    echo "[$DATE] ÉXITO: Descarga completada correctamente (HTTP 200)." >> $LOG_FILE
else
    echo "[$DATE] ERROR: La descarga falló con código HTTP $STATUS_CODE." >> $LOG_FILE
    # Aquí se podría añadir una notificación automática si se desea
fi

# Limpieza: el servidor borra los archivos después de servirlos por streaming, 
# pero nos aseguramos de no llenar el disco si algo falló.
rm -f /home/ubuntu/ytdownloader/downloads/*_health.mp3
