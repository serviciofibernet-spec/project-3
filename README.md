# 🚀 TR-069 ACS Server en PHP

Servidor TR-069 (Technical Report 069) Auto Configuration Server (ACS) completo desarrollado en PHP para la gestión remota de dispositivos CPE (Customer Premises Equipment) como routers, ONTs, y otros dispositivos de red.

## 📋 Características

- ✅ Servidor TR-069 ACS completo compatible con el protocolo CWMP
- ✅ Soporte para mensajes SOAP estándar (Inform, GetParameterValues, SetParameterValues, Reboot, etc.)
- ✅ Instalador web con interfaz moderna
- ✅ Panel de administración intuitivo
- ✅ Gestión de dispositivos CPE
- ✅ Historial de comunicaciones (Inform logs)
- ✅ Sistema de tareas pendientes para dispositivos
- ✅ Almacenamiento de parámetros de dispositivos
- ✅ Autenticación HTTP Basic para dispositivos
- ✅ Sistema de logging completo
- ✅ Interfaz responsive y moderna

## 🔧 Requisitos del Sistema

### Requisitos Mínimos

- **PHP**: 7.4 o superior (recomendado PHP 8.0+)
- **Extensiones PHP requeridas**:
  - `pdo`
  - `pdo_mysql`
  - `soap`
  - `simplexml`
  - `json`
  - `mbstring`
- **MySQL**: 5.7+ o **MariaDB**: 10.2+
- **Servidor Web**: Apache 2.4+ o Nginx
  - Apache: con `mod_rewrite` habilitado
  - Nginx: con configuración de reescritura apropiada
- **Permisos**: Permisos de escritura en el directorio de instalación

### Verificar Extensiones PHP

```bash
php -m | grep -E 'pdo|mysql|soap|simplexml|json|mbstring'
```

## 📦 Instalación

### 1. Clonar o Descargar el Proyecto

```bash
# Clonar el repositorio
git clone <repository-url> tr069-acs
cd tr069-acs

# O descargar y extraer el ZIP
wget <download-url>
unzip tr069-acs.zip
cd tr069-acs
```

### 2. Configurar Permisos

```bash
# Dar permisos de escritura al directorio
chmod 755 .
chmod 644 *.php
chmod 644 schema.sql

# Crear y dar permisos al directorio de logs
mkdir -p logs
chmod 755 logs
```

### 3. Configurar Servidor Web

#### Para Apache

El archivo `.htaccess` ya está incluido. Solo asegúrate de que `mod_rewrite` esté habilitado:

```bash
sudo a2enmod rewrite
sudo systemctl restart apache2
```

Configuración del VirtualHost (ejemplo):

```apache
<VirtualHost *:80>
    ServerName acs.tudominio.com
    DocumentRoot /var/www/tr069-acs
    
    <Directory /var/www/tr069-acs>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    
    ErrorLog ${APACHE_LOG_DIR}/tr069-acs-error.log
    CustomLog ${APACHE_LOG_DIR}/tr069-acs-access.log combined
</VirtualHost>
```

#### Para Nginx

Configuración del sitio (ejemplo):

```nginx
server {
    listen 80;
    server_name acs.tudominio.com;
    root /var/www/tr069-acs;
    index index.php;
    
    # Logs
    access_log /var/log/nginx/tr069-acs-access.log;
    error_log /var/log/nginx/tr069-acs-error.log;
    
    # Proteger archivos sensibles
    location ~ ^/(config\.php|schema\.sql|\.env)$ {
        deny all;
    }
    
    location ~ /logs/ {
        deny all;
    }
    
    # PHP-FPM
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
    
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
}
```

### 4. Crear Base de Datos (Opcional)

Puedes crear la base de datos manualmente antes de la instalación:

```bash
mysql -u root -p
```

```sql
CREATE DATABASE tr069_acs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'tr069user'@'localhost' IDENTIFIED BY 'tu_password_segura';
GRANT ALL PRIVILEGES ON tr069_acs.* TO 'tr069user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 5. Ejecutar el Instalador Web

1. Abre tu navegador y accede a: `http://tu-servidor/install.php`
2. Completa el formulario con los siguientes datos:

#### Configuración de Base de Datos
- **Host**: localhost (o la IP de tu servidor MySQL)
- **Puerto**: 3306 (por defecto)
- **Nombre de BD**: tr069_acs (o el que hayas creado)
- **Usuario**: root (o el usuario que creaste)
- **Contraseña**: Tu contraseña de MySQL

#### Configuración del ACS
- **URL del ACS**: `http://tu-servidor/acs.php` (URL completa donde los dispositivos se conectarán)
- **Usuario ACS**: `acs_user` (usuario para autenticación de dispositivos CPE)
- **Contraseña ACS**: Elige una contraseña segura (los dispositivos usarán esto)

#### Usuario Administrador
- **Usuario**: admin (o el que prefieras)
- **Email**: tu@email.com
- **Contraseña**: Contraseña para acceder al panel de administración

3. Haz clic en "🚀 Instalar TR-069 ACS"
4. Una vez completada la instalación, serás redirigido al panel de control

### 6. Seguridad Post-Instalación

```bash
# Opcional: Eliminar o proteger el instalador
rm install.php
# O protegerlo
chmod 000 install.php

# Proteger el archivo de configuración
chmod 600 config.php
```

## 🔐 Primer Acceso

### Panel de Administración

1. Accede a: `http://tu-servidor/index.php`
2. Inicia sesión con las credenciales de administrador que configuraste
3. Verás el dashboard con estadísticas y dispositivos

**Credenciales por defecto** (si no las cambiaste):
- Usuario: `admin`
- Contraseña: La que configuraste en el instalador

## 📱 Configurar Dispositivos CPE

Para que tus dispositivos CPE se conecten al ACS, configúralos con:

### Parámetros TR-069

```
ACS URL: http://tu-servidor/acs.php
ACS Username: acs_user (o el que configuraste)
ACS Password: *** (la que configuraste)
Periodic Inform Enable: Yes
Periodic Inform Interval: 300 (segundos)
Connection Request Username: admin (opcional)
Connection Request Password: *** (opcional)
```

### Ejemplo de Configuración en Router

La mayoría de routers tienen una sección TR-069 o CWMP en la configuración:

1. Accede a la interfaz web del router
2. Busca la sección **TR-069**, **CWMP** o **Gestión Remota**
3. Habilita TR-069
4. Introduce los parámetros del ACS mencionados arriba
5. Guarda y aplica

## 📊 Uso del Sistema

### Dashboard Principal

El dashboard muestra:
- 📱 **Dispositivos Totales**: Número total de dispositivos registrados
- ✅ **Dispositivos Online**: Dispositivos activos en los últimos 10 minutos
- ⏳ **Tareas Pendientes**: Comandos esperando ser ejecutados
- 📊 **Informs Hoy**: Número de comunicaciones recibidas hoy

### Gestión de Dispositivos

1. Haz clic en **"Dispositivos"** en el menú
2. Verás la lista de todos los dispositivos conectados
3. Haz clic en **"Ver Detalles"** para ver información completa de un dispositivo
4. Desde el detalle puedes:
   - 🔄 **Reiniciar** el dispositivo
   - 📥 **Obtener Parámetros** actualizados
   - Ver todos los parámetros almacenados

### Crear Tareas Manualmente

Puedes insertar tareas directamente en la base de datos:

```sql
-- Reiniciar un dispositivo
INSERT INTO tasks (device_id, task_type, status)
VALUES (1, 'Reboot', 'pending');

-- Obtener parámetros específicos
INSERT INTO tasks (device_id, task_type, parameters, status)
VALUES (1, 'GetParameterValues', 
'{"parameters":["InternetGatewayDevice.DeviceInfo.","InternetGatewayDevice.WANDevice."]}',
'pending');

-- Establecer parámetros
INSERT INTO tasks (device_id, task_type, parameters, status)
VALUES (1, 'SetParameterValues',
'{"parameters":{"InternetGatewayDevice.ManagementServer.PeriodicInformInterval":"300"}}',
'pending');
```

## 🗂️ Estructura del Proyecto

```
tr069-acs/
├── acs.php                 # Servidor TR-069 principal (endpoint SOAP)
├── index.php               # Dashboard / Panel de administración
├── install.php             # Instalador web
├── devices.php             # Gestión de dispositivos
├── config.php              # Configuración (generado por instalador)
├── config.sample.php       # Ejemplo de configuración
├── schema.sql              # Esquema de base de datos
├── .htaccess              # Configuración Apache
├── logs/                   # Directorio de logs (auto-creado)
│   ├── .htaccess          # Protección del directorio
│   └── acs_YYYY-MM-DD.log # Logs por día
└── README.md              # Este archivo
```

## 🔍 Logs y Debugging

### Ver Logs

Los logs se guardan en el directorio `logs/`:

```bash
# Ver logs de hoy
tail -f logs/acs_$(date +%Y-%m-%d).log

# Ver todos los logs
tail -f logs/*.log

# Buscar errores
grep -i error logs/*.log
```

### Habilitar Debug

Edita `config.php`:

```php
'app' => [
    'debug' => true  // Cambiar a true
],
'logging' => [
    'log_level' => 'debug',  // Cambiar a debug
    'log_requests' => true   // Registrar todas las peticiones
]
```

### Formato de Logs

```
[2025-10-19 10:30:45] [info] Received request from CPE {"ip":"192.168.1.100","method":"POST"}
[2025-10-19 10:30:45] [info] Received Inform {"serial":"ABC123456","oui":"00259E","events":["2 PERIODIC"]}
[2025-10-19 10:30:45] [debug] Request body {"body":"<?xml version=..."}
```

## 🗄️ Estructura de Base de Datos

### Tablas Principales

- **devices**: Información de dispositivos CPE
- **parameters**: Parámetros de cada dispositivo
- **tasks**: Tareas pendientes para dispositivos
- **inform_log**: Historial de comunicaciones
- **users**: Usuarios del panel de administración
- **config**: Configuración del sistema

## 🔒 Seguridad

### Recomendaciones

1. **Cambiar contraseñas por defecto**
2. **Usar HTTPS en producción**:
   ```php
   'security' => [
       'enable_https' => true
   ]
   ```
3. **Firewall**: Restringir acceso al ACS solo a IPs conocidas
4. **Eliminar install.php** después de la instalación
5. **Proteger logs**: El directorio `logs/` ya está protegido por `.htaccess`
6. **Actualizar regularmente** PHP y MySQL
7. **Backups**: Hacer copias de seguridad de la base de datos regularmente

### Habilitar HTTPS

```bash
# Instalar Certbot (Let's Encrypt)
sudo apt install certbot python3-certbot-apache

# Obtener certificado
sudo certbot --apache -d acs.tudominio.com

# Renovación automática
sudo certbot renew --dry-run
```

## 🐛 Solución de Problemas

### Los dispositivos no se conectan

1. Verifica que la URL del ACS sea accesible desde el dispositivo
2. Verifica las credenciales (usuario/contraseña del ACS)
3. Revisa los logs: `tail -f logs/*.log`
4. Verifica que el puerto 80/443 esté abierto en el firewall

### Error de conexión a la base de datos

1. Verifica que MySQL esté corriendo: `sudo systemctl status mysql`
2. Verifica las credenciales en `config.php`
3. Verifica que el usuario tenga permisos: `GRANT ALL PRIVILEGES ON tr069_acs.* TO 'user'@'localhost';`

### No aparecen dispositivos en el panel

1. Verifica que los dispositivos estén enviando Inform
2. Revisa los logs del ACS
3. Verifica autenticación HTTP Basic
4. Comprueba la tabla `inform_log` en la base de datos:
   ```sql
   SELECT * FROM inform_log ORDER BY created_at DESC LIMIT 10;
   ```

### Permisos de escritura en logs

```bash
chmod 755 logs
chown www-data:www-data logs  # En Ubuntu/Debian
```

## 📝 API y Extensiones

### Agregar Nuevos RPC Methods

Para agregar soporte a nuevos métodos RPC, edita `acs.php`:

```php
// En la clase TR069Handler, agregar nuevo método
private function handleNuevoMetodo($xml) {
    // Tu lógica aquí
    return $this->generateNuevaRespuesta();
}

// En handleRequest(), agregar detección
$nuevo = $xml->xpath('//cwmp:NuevoMetodo');
if (!empty($nuevo)) {
    return $this->handleNuevoMetodo($xml);
}
```

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🙏 Créditos

- Basado en el estándar **TR-069** de Broadband Forum
- Protocolo **CWMP** (CPE WAN Management Protocol)

## 📞 Soporte

Para soporte y preguntas:
- 📧 Email: soporte@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/usuario/tr069-acs/issues)
- 📖 Documentación: [Wiki del Proyecto](https://github.com/usuario/tr069-acs/wiki)

## 🔄 Actualizaciones

### Versión 1.0.0 (Actual)
- ✅ Servidor TR-069 ACS completo
- ✅ Instalador web
- ✅ Panel de administración
- ✅ Soporte para Inform, GetParameterValues, SetParameterValues, Reboot
- ✅ Sistema de tareas
- ✅ Logging completo

### Roadmap
- 🔜 Soporte para Download (firmware updates)
- 🔜 API REST para integración externa
- 🔜 Notificaciones por email/webhook
- 🔜 Gráficas y estadísticas avanzadas
- 🔜 Soporte para múltiples tenants

---

**¡Gracias por usar TR-069 ACS!** 🚀
