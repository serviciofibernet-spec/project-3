FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs uploads

# Crear usuario no-root
RUN useradd -m -u 1000 tr069 && chown -R tr069:tr069 /app
USER tr069

# Exponer puertos
EXPOSE 5000 7547

# Comando por defecto
CMD ["python", "app.py"]