# Guía de Instalación del Servidor TR-069

Esta guía proporciona instrucciones detalladas para instalar y configurar el servidor TR-069 en diferentes sistemas operativos.

## Instalación Automática en Windows

### Método Recomendado: Instalador Batch

1. **Descargar** todos los archivos del proyecto a una carpeta local
2. **Hacer clic derecho** en `install_tr069_server.bat`
3. **Seleccionar** "Ejecutar como administrador"
4. **Seguir** las instrucciones en pantalla

El instalador automáticamente:
- ✅ Verifica la instalación de Python
- ✅ Crea un entorno virtual
- ✅ Instala todas las dependencias
- ✅ Configura directorios necesarios
- ✅ Crea archivos de configuración por defecto
- ✅ Genera scripts de inicio/parada
- ✅ Opcionalmente crea acceso directo en el escritorio
- ✅ Configura reglas de firewall

### Requisitos Previos Windows

- **Sistema Operativo**: Windows 7, 8, 10, o 11
- **Python**: Versión 3.8 o superior
- **Permisos**: Ejecutar como administrador
- **Conexión a Internet**: Para descargar dependencias

### Verificar Instalación de Python

Abrir **Símbolo del sistema** y ejecutar:
```cmd
python --version
```

Si Python no está instalado:
1. Ir a https://python.org/downloads/
2. Descargar Python 3.8 o superior
3. **IMPORTANTE**: Marcar "Add Python to PATH" durante la instalación

## Instalación Manual

### Windows Manual

```cmd
# 1. Abrir símbolo del sistema como administrador
# 2. Navegar al directorio del proyecto
cd C:\ruta\al\proyecto\tr069-server

# 3. Crear entorno virtual
python -m venv venv

# 4. Activar entorno virtual
venv\Scripts\activate

# 5. Actualizar pip
python -m pip install --upgrade pip

# 6. Instalar dependencias
pip install -r requirements.txt

# 7. Crear directorios necesarios
mkdir config data logs

# 8. Ejecutar servidor
python tr069_server.py
```

### Linux/Ubuntu

```bash
# 1. Actualizar sistema
sudo apt update && sudo apt upgrade -y

# 2. Instalar Python y pip
sudo apt install python3 python3-pip python3-venv -y

# 3. Clonar o descargar proyecto
cd /opt
sudo git clone <repository-url> tr069-server
cd tr069-server

# 4. Crear entorno virtual
python3 -m venv venv

# 5. Activar entorno virtual
source venv/bin/activate

# 6. Instalar dependencias
pip install -r requirements.txt

# 7. Crear directorios
mkdir -p config data logs

# 8. Configurar permisos
sudo chown -R $USER:$USER /opt/tr069-server

# 9. Ejecutar servidor
python tr069_server.py
```

### CentOS/RHEL

```bash
# 1. Instalar Python 3.8+
sudo yum install python3 python3-pip python3-venv -y

# 2. Seguir pasos similares a Ubuntu
# (resto de pasos idénticos)
```

### macOS

```bash
# 1. Instalar Homebrew (si no está instalado)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Instalar Python
brew install python3

# 3. Seguir pasos similares a Linux
# (resto de pasos idénticos)
```

## Instalación con Docker

### Dockerfile

Crear un archivo `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p config data logs

EXPOSE 7547

CMD ["python", "tr069_server.py"]
```

### Docker Compose

Crear `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tr069-server:
    build: .
    ports:
      - "7547:7547"
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

### Comandos Docker

```bash
# Construir imagen
docker build -t tr069-server .

# Ejecutar contenedor
docker run -d -p 7547:7547 --name tr069-server tr069-server

# Con Docker Compose
docker-compose up -d
```

## Configuración Post-Instalación

### 1. Configuración Básica

Editar `config/server_config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 7547,
    "ssl_enabled": false
  },
  "database": {
    "devices_db": "data/tr069_devices.db",
    "auth_db": "data/tr069_auth.db"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/tr069_server.log"
  },
  "security": {
    "max_failed_attempts": 5,
    "block_duration_minutes": 15
  }
}
```

### 2. Configuración SSL/HTTPS

Para habilitar SSL:

```json
{
  "server": {
    "ssl_enabled": true,
    "ssl_cert_path": "path/to/certificate.pem",
    "ssl_key_path": "path/to/private_key.pem"
  }
}
```

Generar certificados auto-firmados (desarrollo):
```bash
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

### 3. Configuración de Firewall

#### Windows Firewall
```cmd
# Permitir puerto 7547
netsh advfirewall firewall add rule name="TR-069 Server" dir=in action=allow protocol=TCP localport=7547
```

#### Linux iptables
```bash
# Permitir puerto 7547
sudo iptables -A INPUT -p tcp --dport 7547 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4
```

#### Linux ufw
```bash
sudo ufw allow 7547/tcp
```

### 4. Configuración como Servicio

#### Windows Service

Crear `tr069_service.py`:
```python
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os

class TR069Service(win32serviceutil.ServiceFramework):
    _svc_name_ = "TR069Server"
    _svc_display_name_ = "TR-069 ACS Server"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        # Importar y ejecutar servidor
        import tr069_server
        tr069_server.main()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(TR069Service)
```

Instalar servicio:
```cmd
python tr069_service.py install
python tr069_service.py start
```

#### Linux Systemd

Crear `/etc/systemd/system/tr069-server.service`:
```ini
[Unit]
Description=TR-069 ACS Server
After=network.target

[Service]
Type=simple
User=tr069
WorkingDirectory=/opt/tr069-server
Environment=PATH=/opt/tr069-server/venv/bin
ExecStart=/opt/tr069-server/venv/bin/python tr069_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Habilitar servicio:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tr069-server
sudo systemctl start tr069-server
```

## Verificación de Instalación

### 1. Verificar Servidor

```bash
# Verificar que el servidor esté ejecutándose
curl http://localhost:7547/status
```

Respuesta esperada:
```json
{
  "server_status": "running",
  "connected_devices": 0,
  "active_sessions": 0,
  "timestamp": "2023-12-07T10:30:00"
}
```

### 2. Verificar Logs

```bash
# Ver logs en tiempo real
tail -f logs/tr069_server.log
```

### 3. Verificar Base de Datos

```bash
# Verificar que las bases de datos se crearon
ls -la data/
# Debería mostrar: tr069_devices.db y tr069_auth.db
```

### 4. Verificar Conectividad

```bash
# Desde otro equipo en la red
telnet <servidor-ip> 7547
```

## Solución de Problemas de Instalación

### Error: Python no encontrado

**Windows:**
1. Instalar Python desde python.org
2. Asegurar que "Add to PATH" esté marcado
3. Reiniciar símbolo del sistema

**Linux:**
```bash
sudo apt install python3 python3-pip
```

### Error: pip no encontrado

```bash
# Windows
python -m ensurepip --upgrade

# Linux
sudo apt install python3-pip
```

### Error: Permisos denegados

**Windows:**
- Ejecutar como administrador

**Linux:**
```bash
sudo chown -R $USER:$USER /path/to/project
chmod +x *.py
```

### Error: Puerto en uso

```bash
# Encontrar proceso usando puerto 7547
# Windows
netstat -ano | findstr :7547

# Linux
lsof -i :7547

# Cambiar puerto en configuración o terminar proceso
```

### Error: Dependencias no se instalan

```bash
# Actualizar pip
python -m pip install --upgrade pip

# Instalar con verbose para ver errores
pip install -r requirements.txt -v

# Instalar dependencias una por una
pip install aiohttp
pip install bcrypt
pip install PyJWT
```

### Error: SSL/TLS

1. Verificar que los archivos de certificado existen
2. Verificar permisos de lectura
3. Usar certificados válidos (no auto-firmados en producción)

### Error: Firewall bloquea conexiones

1. Configurar reglas de firewall
2. Verificar con herramientas de red (telnet, nmap)
3. Temporalmente deshabilitar firewall para probar

## Instalación en Producción

### Consideraciones de Seguridad

1. **Cambiar credenciales por defecto**
2. **Habilitar SSL/HTTPS**
3. **Configurar firewall restrictivo**
4. **Usar base de datos externa (PostgreSQL/MySQL)**
5. **Configurar proxy reverso (nginx/Apache)**
6. **Implementar monitoreo y alertas**
7. **Configurar backups automáticos**

### Proxy Reverso con nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:7547;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Monitoreo

Configurar herramientas de monitoreo:
- **Nagios/Zabbix**: Para monitoreo de servicios
- **Grafana/Prometheus**: Para métricas y dashboards
- **ELK Stack**: Para análisis de logs

---

¡La instalación está completa! El servidor TR-069 debería estar funcionando correctamente.