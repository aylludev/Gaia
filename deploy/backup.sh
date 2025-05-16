#!/bin/bash

#!/bin/bash

# Variables de entorno
FECHA=$(date +%d_%m_%Y_%H_%M_%S)
NAME="apolo_${FECHA}.dump"
DIR="/home/amawta/backup"
USER_DB="postgres"
NAME_DB="ams"
PASS_DB="Apolo39"

# Crear el archivo directamente al hacer el dump
export PGPASSWORD=$PASS_DB

echo "Procesando la copia de seguridad de la base de datos..."
pg_dump -U $USER_DB -h localhost --port 5432 -F c -b -v -f "${DIR}/${NAME}" $NAME_DB

# Cambiar permisos si el archivo fue creado
if [ -f "${DIR}/${NAME}" ]; then
    chmod 600 "${DIR}/${NAME}"
    echo "Backup terminado: ${DIR}/${NAME}"
else
    echo "Error: No se pudo crear el archivo de respaldo."
fi