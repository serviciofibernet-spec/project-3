# Servidor TR-069 para Gestión Automatizada de ONTs Huawei

Un servidor ACS (Auto Configuration Server) completo para la gestión automatizada de ONTs Huawei con funcionalidades avanzadas de configuración, monitoreo y automatización.

## 🚀 Características Principales

### Configuración Automática
- **Cambio de SSID y contraseña WiFi** (2.4GHz y 5GHz)
- **Configuración de parámetros de red**: DNS, VLAN, PPPoE, puertos
- **Perfiles automáticos** por modelo de ONT
- **Configuración automática** al conectar nuevas ONTs

### Monitoreo y Diagnóstico
- **Potencia óptica** (dBm) en tiempo real
- **Estado de conexión** y nivel de señal
- **Dispositivos conectados** al WiFi
- **Estadísticas de tráfico** y rendimiento

### Automatización Masiva
- **Detección automática** de ONTs conectadas
- **Asignación automática** al cliente correcto
- **Configuración automática** según perfil del modelo
- **Gestión centralizada** de múltiples ONTs

### Interfaces Web
- **Panel de administración** completo
- **Panel de cliente** para autogestión
- **API REST** para integraciones
- **Interfaz responsive** y moderna

## 📋 Requisitos del Sistema

- Python 3.8+
- MySQL 5.7+ o MariaDB 10.3+
- Linux (recomendado Ubuntu 20.04+)
- Mínimo 2GB RAM
- 10GB espacio en disco

## 🛠️ Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd tr069-server
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar base de datos MySQL
```bash
# Instalar MySQL (Ubuntu/Debian)
sudo apt update
sudo apt install mysql-server

# Crear usuario y base de datos
sudo mysql -u root -p
```

En MySQL:
```sql
CREATE DATABASE tr069_onts CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tr069'@'localhost' IDENTIFIED BY 'tr069pass';
GRANT ALL PRIVILEGES ON tr069_onts.* TO 'tr069'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 5. Inicializar base de datos
```bash
python setup_database.py
```

### 6. Iniciar servidor
```bash
python app.py
```

## 🌐 Acceso Web

- **Panel de administración**: http://localhost:5000
- **Credenciales por defecto**: admin / admin123
- **Servidor TR-069 ACS**: Puerto 7547

## 📱 Modelos de ONT Soportados

- Huawei HG8240H
- Huawei HG8245H
- Huawei HG8245H5
- Huawei HG8245Q
- Huawei HG8245W
- Huawei HG8247H
- Huawei HG8247W
- Huawei HG8240X
- Huawei HG8240Q

## 🔧 Configuración de ONTs

### Configuración WiFi
- SSID personalizado para 2.4GHz y 5GHz
- Contraseñas seguras
- Canales optimizados
- Seguridad WPA2-PSK

### Configuración de Red
- Modo IP: DHCP, Estático, PPPoE
- Configuración VLAN
- Servidores DNS personalizados
- Gestión de puertos

### Monitoreo
- Potencia óptica (TX/RX)
- Temperatura del módulo óptico
- Dispositivos WiFi conectados
- Estadísticas de tráfico

## 🔄 Automatización

### Perfiles de Configuración
Cada modelo de ONT tiene un perfil de configuración que se aplica automáticamente:

```python
# Ejemplo de perfil
profile = {
    'wifi_2_4_ssid': 'WiFi-{customer_name}-2.4G',
    'wifi_2_4_password': '{customer_name}2024',
    'wifi_5_ssid': 'WiFi-{customer_name}-5G',
    'wifi_5_password': '{customer_name}2024',
    'vlan_id': 100,
    'dns_primary': '8.8.8.8'
}
```

### Variables Disponibles
- `{customer_name}`: Nombre del cliente
- `{serial}`: Últimos 4 dígitos del serial
- `{model}`: Modelo de la ONT

## 📊 API REST

### Endpoints Principales

#### ONTs
- `GET /api/onts` - Listar ONTs
- `GET /api/onts/{id}` - Detalles de ONT
- `PUT /api/onts/{id}/wifi` - Configurar WiFi
- `PUT /api/onts/{id}/network` - Configurar red
- `POST /api/onts/{id}/reboot` - Reiniciar ONT

#### Monitoreo
- `GET /api/onts/{id}/monitoring` - Datos de monitoreo
- `GET /api/stats` - Estadísticas generales

### Ejemplo de uso
```bash
# Obtener lista de ONTs
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/onts

# Configurar WiFi
curl -X PUT -H "Content-Type: application/json" \
  -d '{"wifi_2_4_ssid": "MiWiFi", "wifi_2_4_password": "mi123456"}' \
  http://localhost:5000/api/onts/1/wifi
```

## 🔒 Seguridad

- Autenticación por sesiones
- Contraseñas hasheadas con Werkzeug
- Validación de entrada
- Protección CSRF
- Logs de auditoría

## 📈 Monitoreo y Alertas

### Métricas Monitoreadas
- Potencia óptica (umbral: -25 dBm)
- Estado de conexión
- Dispositivos WiFi conectados
- Tráfico de red
- Uptime de la ONT

### Alertas Automáticas
- ONT offline por más de 1 hora
- Potencia óptica baja
- Alto número de dispositivos conectados
- Errores de configuración

## 🚀 Despliegue en Producción

### Usando Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Usando Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000 7547
CMD ["python", "app.py"]
```

### Configuración Nginx
```nginx
server {
    listen 80;
    server_name tr069.yourdomain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Mantenimiento

### Backup de Base de Datos
```bash
mysqldump -u tr069 -p tr069_onts > backup_$(date +%Y%m%d).sql
```

### Logs
- Logs de aplicación: `logs/tr069_server.log`
- Logs de acceso: `logs/access.log`
- Logs de errores: `logs/error.log`

### Actualización
```bash
git pull
pip install -r requirements.txt
python setup_database.py
```

## 📞 Soporte

Para soporte técnico o reportar problemas:
- Crear un issue en el repositorio
- Documentar el modelo de ONT y versión de firmware
- Incluir logs relevantes

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo LICENSE para más detalles.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📚 Documentación Adicional

- [Especificación TR-069](https://www.broadband-forum.org/technical/download/TR-069.pdf)
- [Documentación Huawei ONT](https://support.huawei.com/enterprise/)
- [Guía de configuración avanzada](docs/advanced-config.md)