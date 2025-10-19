#!/bin/bash

# Script de inicio para el servidor TR-069
# Este script configura el entorno y inicia todos los servicios necesarios

set -e

echo "=== Iniciando Servidor TR-069 ==="

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    exit 1
fi

# Verificar si MySQL está instalado y ejecutándose
if ! command -v mysql &> /dev/null; then
    echo "Error: MySQL no está instalado"
    exit 1
fi

# Verificar conexión a MySQL
if ! mysql -u root -e "SELECT 1;" &> /dev/null; then
    echo "Error: No se puede conectar a MySQL"
    echo "Asegúrate de que MySQL esté ejecutándose y configurado correctamente"
    exit 1
fi

# Crear directorios necesarios
mkdir -p logs uploads

# Verificar si la base de datos existe
if ! mysql -u root -e "USE tr069_onts;" &> /dev/null; then
    echo "Base de datos no encontrada. Ejecutando configuración inicial..."
    python3 setup_database.py
fi

# Verificar dependencias de Python
echo "Verificando dependencias..."
pip install -r requirements.txt

# Configurar permisos
chmod +x app.py
chmod +x setup_database.py

# Iniciar el servidor
echo "Iniciando servidor TR-069..."
echo "Panel web: http://localhost:5000"
echo "Servidor TR-069 ACS: puerto 7547"
echo "Credenciales por defecto: admin / admin123"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

python3 app.py