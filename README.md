# TR-069 ACS Server para ONTs Huawei

Sistema completo de gestión automatizada para ONTs Huawei utilizando el protocolo TR-069/CWMP.

## 🚀 Características

### Gestión de Dispositivos
- ✅ Auto-descubrimiento y registro automático de ONTs
- ✅ Configuración automática según modelo del equipo
- ✅ Gestión de SSID y contraseñas WiFi (2.4/5 GHz)
- ✅ Configuración de DNS, VLAN, PPPoE
- ✅ Reinicios remotos
- ✅ Actualizaciones de firmware

### Monitoreo y Diagnóstico
- 📊 Potencia óptica (RX/TX) en dBm
- 📊 Estado de conexión WAN
- 📊 Temperatura del dispositivo
- 📊 Dispositivos conectados al WiFi
- 📊 Nivel de señal y calidad
- 📊 Tiempo de actividad (uptime)

### Automatización
- 🤖 Perfiles de configuración automática
- 🤖 Asignación automática de clientes
- 🤖 Recolección automática de diagnósticos
- 🤖 Detección de dispositivos con problemas

### Interfaces
- 🎨 Panel web para administradores
- 🎨 Portal de autogestión para clientes
- 🎨 API REST completa
- 🎨 Base de datos MySQL

## 📋 Requisitos

- Python 3.8+
- MySQL 5.7+ / MariaDB 10.3+
- Redis (opcional, para caché)

## 🔧 Instalación

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd tr069-acs-server
```

### 2. Crear entorno virtual

```bash
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar base de datos

```bash
# Crear base de datos MySQL
mysql -u root -p < database/schema.sql

# O manualmente:
mysql -u root -p
CREATE DATABASE tr069_acs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tr069_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON tr069_acs.* TO 'tr069_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

Editar `.env`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=tr069_user
DB_PASSWORD=tu_contraseña_segura
DB_NAME=tr069_acs

ACS_URL=http://tu-servidor.com:7547
ACS_USERNAME=admin
ACS_PASSWORD=admin123
SECRET_KEY=tu-clave-secreta-aqui

PORT=7547
```

### 6. Inicializar base de datos

```bash
mysql -u tr069_user -p tr069_acs < database/schema.sql
```

### 7. Ejecutar servidor

```bash
python app.py
```

El servidor estará disponible en:
- CWMP Endpoint: `http://localhost:7547/cwmp`
- Admin API: `http://localhost:7547/api/admin`
- Client API: `http://localhost:7547/api/client`
- Monitoring API: `http://localhost:7547/api/monitoring`

## 🔐 Configuración de ONTs

Para que las ONTs se conecten al ACS, debes configurar los siguientes parámetros en cada dispositivo:

### Parámetros TR-069 en la ONT

```
InternetGatewayDevice.ManagementServer.URL = http://tu-servidor.com:7547/cwmp
InternetGatewayDevice.ManagementServer.Username = admin
InternetGatewayDevice.ManagementServer.Password = admin123
InternetGatewayDevice.ManagementServer.PeriodicInformEnable = 1
InternetGatewayDevice.ManagementServer.PeriodicInformInterval = 300
```

### Ejemplo de configuración vía CLI (Huawei)

```bash
# Conectarse a la ONT vía telnet/SSH
telnet 192.168.1.1

# Configurar ACS
WAP> enable
WAP# config
WAP(config)# cwmp
WAP(config-cwmp)# acs-url http://tu-servidor.com:7547/cwmp
WAP(config-cwmp)# acs-username admin
WAP(config-cwmp)# acs-password admin123
WAP(config-cwmp)# periodic-inform enable
WAP(config-cwmp)# periodic-inform-interval 300
WAP(config-cwmp)# end
WAP# save
```

## 📚 API Documentation

### Admin API

#### Obtener lista de dispositivos
```bash
GET /api/admin/devices
Authorization: Bearer <token>

# Filtrar por estado
GET /api/admin/devices?status=online

# Filtrar por cliente
GET /api/admin/devices?client_id=1
```

#### Obtener detalles de dispositivo
```bash
GET /api/admin/devices/{device_id}
Authorization: Bearer <token>
```

#### Cambiar WiFi de un dispositivo
```bash
PUT /api/admin/devices/{device_id}/wifi
Authorization: Bearer <token>
Content-Type: application/json

{
  "wifi_24": {
    "ssid": "MiWiFi-2.4G",
    "password": "contraseña123",
    "enabled": true
  },
  "wifi_5": {
    "ssid": "MiWiFi-5G",
    "password": "contraseña123",
    "enabled": true
  }
}
```

#### Configurar dispositivo completo
```bash
POST /api/admin/devices/{device_id}/configure
Authorization: Bearer <token>
Content-Type: application/json

{
  "wifi_24": {
    "ssid": "MiWiFi",
    "password": "pass123456"
  },
  "dns": {
    "primary": "8.8.8.8",
    "secondary": "8.8.4.4"
  },
  "vlan": 100,
  "pppoe": {
    "username": "usuario@isp",
    "password": "contraseña"
  }
}
```

#### Reiniciar dispositivo
```bash
POST /api/admin/devices/{device_id}/reboot
Authorization: Bearer <token>
```

#### Actualizar firmware
```bash
POST /api/admin/devices/{device_id}/firmware
Authorization: Bearer <token>
Content-Type: application/json

{
  "firmware_url": "http://servidor.com/firmware/HG8245H_V3R017C10S115.bin",
  "file_size": 15728640
}
```

#### Asignar dispositivo a cliente
```bash
POST /api/admin/devices/{device_id}/assign
Authorization: Bearer <token>
Content-Type: application/json

{
  "client_id": 1
}
```

### Client API

#### Login
```bash
POST /api/client/login
Content-Type: application/json

{
  "username": "cliente123",
  "password": "contraseña"
}
```

#### Ver mis dispositivos
```bash
GET /api/client/devices
Authorization: Bearer <token>
```

#### Cambiar WiFi de mi dispositivo
```bash
PUT /api/client/devices/{device_id}/wifi
Authorization: Bearer <token>
Content-Type: application/json

{
  "wifi_24": {
    "ssid": "MiCasa-WiFi",
    "password": "nuevacontraseña123"
  }
}
```

### Monitoring API

#### Obtener diagnósticos
```bash
GET /api/monitoring/devices/{device_id}/diagnostics/latest

# Historial (últimas 24 horas)
GET /api/monitoring/devices/{device_id}/diagnostics?hours=24
```

#### Obtener potencia óptica
```bash
GET /api/monitoring/devices/{device_id}/optical-power?hours=24
```

#### Ver dispositivos conectados
```bash
GET /api/monitoring/devices/{device_id}/connected
```

#### Obtener calidad de señal
```bash
GET /api/monitoring/devices/{device_id}/signal-quality
```

## 🎯 Perfiles de Configuración

Los perfiles permiten automatizar la configuración de nuevas ONTs según su modelo.

### Crear perfil de configuración

```bash
POST /api/admin/profiles
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Perfil Huawei HG8245H",
  "description": "Configuración estándar para HG8245H",
  "model_filter": "HG8245H",
  "priority": 10,
  "is_active": true,
  "configuration": {
    "wifi_24": {
      "ssid": "WIFI-{serial}",
      "enabled": true
    },
    "wifi_5": {
      "ssid": "WIFI-{serial}-5G",
      "enabled": true
    },
    "dns": {
      "primary": "8.8.8.8",
      "secondary": "8.8.4.4"
    }
  }
}
```

## 🔄 Scheduler (Tareas Automatizadas)

El servidor incluye un scheduler que ejecuta tareas periódicas:

### Ejecutar scheduler

```bash
python utils/scheduler.py
```

### Tareas programadas:
- **Cada 5 minutos**: Verificar estado de dispositivos
- **Cada 15 minutos**: Recolectar diagnósticos
- **Cada 30 minutos**: Reintentar tareas fallidas
- **Diariamente (3:00 AM)**: Limpiar datos antiguos

## 🐳 Despliegue con Docker

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7547

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:7547", "app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: tr069_acs
      MYSQL_USER: tr069_user
      MYSQL_PASSWORD: tr069pass
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "3306:3306"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  tr069-acs:
    build: .
    environment:
      DB_HOST: mysql
      DB_USER: tr069_user
      DB_PASSWORD: tr069pass
      DB_NAME: tr069_acs
      REDIS_HOST: redis
      ACS_URL: http://localhost:7547
    ports:
      - "7547:7547"
    depends_on:
      - mysql
      - redis
    volumes:
      - ./logs:/app/logs

volumes:
  mysql_data:
```

## 📊 Estructura del Proyecto

```
tr069-acs-server/
├── app.py                      # Aplicación principal
├── config.py                   # Configuración
├── requirements.txt            # Dependencias Python
├── .env.example               # Variables de entorno ejemplo
├── database/
│   ├── schema.sql             # Schema de base de datos
│   └── models.py              # Modelos SQLAlchemy
├── tr069/
│   ├── cwmp_server.py         # Servidor CWMP/TR-069
│   ├── soap_handler.py        # Manejo de mensajes SOAP
│   └── device_manager.py      # Gestión de dispositivos
├── api/
│   ├── admin_api.py           # API de administración
│   ├── client_api.py          # API de clientes
│   └── monitoring_api.py      # API de monitoreo
├── utils/
│   ├── scheduler.py           # Tareas programadas
│   └── connection_request.py  # Connection Request
└── web/
    └── templates/
        ├── admin.html         # Panel admin
        └── client.html        # Panel cliente
```

## 🔒 Seguridad

### Recomendaciones:

1. **Cambiar credenciales por defecto**
   ```bash
   # En .env
   ACS_USERNAME=tu_usuario_seguro
   ACS_PASSWORD=contraseña_muy_segura_aqui
   SECRET_KEY=clave-secreta-aleatoria-muy-larga
   ```

2. **Usar HTTPS en producción**
   - Configurar certificado SSL/TLS
   - Usar reverse proxy (nginx/Apache)

3. **Implementar autenticación JWT**
   - El código incluye placeholders para JWT
   - Instalar: `pip install PyJWT`

4. **Firewall**
   - Permitir solo IPs de ONTs en puerto 7547
   - Usar VPN para acceso administrativo

## 🐛 Solución de Problemas

### ONT no se conecta

1. Verificar que la ONT tenga acceso de red al servidor ACS
2. Revisar configuración TR-069 en la ONT
3. Verificar logs del servidor: `tail -f logs/app.log`
4. Verificar que el puerto 7547 esté accesible

### Tareas no se ejecutan

1. Verificar que la ONT esté online
2. Revisar tabla `configuration_tasks` en la BD
3. Esperar al próximo Inform (default 5 minutos)
4. Usar Connection Request para forzar conexión inmediata

### Diagnósticos no se recolectan

1. Verificar que el scheduler esté ejecutándose
2. Revisar rutas de parámetros para tu modelo específico de ONT
3. Algunos parámetros pueden variar según firmware

## 📝 Modelos Huawei Soportados

Este sistema ha sido probado con:
- HG8245H
- HG8245Q
- HG8240H
- HG8310M
- EG8145V5

Otros modelos Huawei con TR-069 deberían funcionar, pero pueden requerir ajustes en las rutas de parámetros.

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT.

## 📧 Soporte

Para reportar bugs o solicitar features, abre un issue en GitHub.

## 🙏 Agradecimientos

Desarrollado para facilitar la gestión de redes FTTH con ONTs Huawei.
