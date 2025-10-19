# TR-069 ACS Server

Un servidor TR-069 ACS (Auto Configuration Server) completo implementado en PHP para la gestión remota de dispositivos CPE (Customer Premises Equipment).

## Características

- ✅ **Servidor TR-069 completo** - Implementación del protocolo CWMP (CPE WAN Management Protocol)
- ✅ **Interfaz web de administración** - Panel de control intuitivo para gestionar dispositivos
- ✅ **Gestión de dispositivos** - Monitoreo en tiempo real del estado de conexión
- ✅ **Sistema de tareas** - Programación y ejecución de comandos remotos
- ✅ **Presets de configuración** - Plantillas reutilizables para configurar múltiples dispositivos
- ✅ **Registro de eventos** - Logging completo de actividades y errores
- ✅ **Autenticación segura** - Sistema de login para el panel de administración
- ✅ **Instalador automático** - Script de instalación paso a paso

## Requisitos del Sistema

- **PHP 7.4+** con extensiones:
  - PDO MySQL
  - SimpleXML
  - cURL
- **MySQL 5.7+** o **MariaDB 10.2+**
- **Servidor web** (Apache, Nginx, etc.)

## Instalación

### 1. Descargar e instalar archivos

```bash
# Clonar o descargar los archivos del proyecto
git clone <repository-url> tr069-acs
cd tr069-acs

# Configurar permisos
chmod 755 logs/
chmod 644 *.php
```

### 2. Configurar servidor web

#### Apache
```apache
<VirtualHost *:80>
    DocumentRoot /path/to/tr069-acs
    ServerName tr069.example.com
    
    <Directory /path/to/tr069-acs>
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

#### Nginx
```nginx
server {
    listen 80;
    server_name tr069.example.com;
    root /path/to/tr069-acs;
    index index.php;
    
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
    
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_index index.php;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

### 3. Ejecutar instalador

1. Accede a `http://tu-dominio.com/install.php`
2. Sigue los pasos del instalador:
   - **Paso 1**: Configuración de base de datos
   - **Paso 2**: Configuración del ACS
   - **Paso 3**: Finalización

### 4. Configurar dispositivos CPE

Configura tus dispositivos TR-069 con:
- **ACS URL**: `http://tu-dominio.com/acs.php`
- **Username/Password**: (si se configuró autenticación)

## Estructura del Proyecto

```
tr069-acs/
├── acs.php                 # Endpoint principal del servidor TR-069
├── index.php              # Dashboard principal
├── install.php            # Script de instalación
├── devices.php            # Gestión de dispositivos
├── device.php             # Vista individual de dispositivo
├── tasks.php              # Gestión de tareas
├── events.php             # Registro de eventos
├── presets.php            # Presets de configuración
├── classes/               # Clases PHP
│   ├── Database.php       # Conexión a base de datos
│   ├── TR069Server.php    # Lógica del servidor TR-069
│   └── Logger.php         # Sistema de logging
├── config/                # Archivos de configuración (generados)
│   ├── database.php       # Configuración de BD
│   └── acs.php           # Configuración del ACS
├── templates/             # Plantillas HTML
│   ├── header.php        # Cabecera común
│   ├── footer.php        # Pie común
│   └── login.php         # Página de login
├── sql/                  # Esquemas de base de datos
│   └── schema.sql        # Estructura de tablas
└── logs/                 # Archivos de log
    └── acs.log           # Log principal
```

## Funcionalidades del ACS

### Métodos TR-069 Soportados

- **Inform** - Recepción de información de dispositivos
- **GetParameterValues** - Obtener valores de parámetros
- **SetParameterValues** - Establecer valores de parámetros
- **Reboot** - Reiniciar dispositivo
- **GetRPCMethods** - Obtener métodos disponibles

### Gestión de Dispositivos

- **Monitoreo en tiempo real** - Estado online/offline
- **Información detallada** - Fabricante, modelo, versión, etc.
- **Historial de conexiones** - Registro de última actividad
- **Parámetros del dispositivo** - Visualización y edición

### Sistema de Tareas

- **Programación de comandos** - Ejecución diferida de operaciones
- **Prioridades** - Control de orden de ejecución
- **Estado de tareas** - Seguimiento de progreso
- **Resultados** - Registro de éxito/error

### Presets de Configuración

- **Plantillas reutilizables** - Configuraciones predefinidas
- **Aplicación masiva** - Configurar múltiples dispositivos
- **Parámetros personalizables** - Flexibilidad total

## Configuración Avanzada

### Variables de Entorno

Puedes configurar variables adicionales en `config/acs.php`:

```php
// Timeout para conexiones
define('CONNECTION_TIMEOUT', 30);

// Intervalo de inform esperado (segundos)
define('INFORM_INTERVAL', 300);

// Habilitar debug
define('DEBUG_MODE', false);
```

### Autenticación HTTP

Para habilitar autenticación HTTP básica para dispositivos:

```php
// En config/acs.php
define('ACS_USERNAME', 'tu_usuario');
define('ACS_PASSWORD', 'tu_contraseña');
```

### Logging Personalizado

Modifica el nivel de logging en `classes/Logger.php`:

```php
// Niveles: DEBUG, INFO, WARNING, ERROR
$logger->setLevel('INFO');
```

## Seguridad

### Recomendaciones

1. **HTTPS**: Usar siempre HTTPS en producción
2. **Firewall**: Restringir acceso al puerto del ACS
3. **Autenticación**: Configurar credenciales fuertes
4. **Actualizaciones**: Mantener PHP y MySQL actualizados

### Configuración HTTPS

```apache
<VirtualHost *:443>
    DocumentRoot /path/to/tr069-acs
    ServerName tr069.example.com
    
    SSLEngine on
    SSLCertificateFile /path/to/certificate.crt
    SSLCertificateKeyFile /path/to/private.key
</VirtualHost>
```

## Troubleshooting

### Problemas Comunes

1. **Dispositivos no se conectan**
   - Verificar URL del ACS
   - Revisar logs en `logs/acs.log`
   - Comprobar conectividad de red

2. **Error de base de datos**
   - Verificar credenciales en `config/database.php`
   - Comprobar que MySQL esté ejecutándose
   - Revisar permisos de usuario de BD

3. **Tareas no se ejecutan**
   - Verificar que el dispositivo esté online
   - Revisar prioridades de tareas
   - Comprobar logs de errores

### Logs Importantes

```bash
# Log principal del ACS
tail -f logs/acs.log

# Logs del servidor web
tail -f /var/log/apache2/error.log
tail -f /var/log/nginx/error.log

# Logs de PHP
tail -f /var/log/php7.4-fpm.log
```

## API y Extensiones

### Estructura de Base de Datos

Las principales tablas son:

- `devices` - Información de dispositivos
- `sessions` - Sesiones TR-069 activas
- `parameters` - Parámetros de dispositivos
- `tasks` - Cola de tareas pendientes
- `events` - Registro de eventos
- `presets` - Plantillas de configuración

### Extensión del Código

Para añadir nuevos métodos TR-069:

1. Modificar `classes/TR069Server.php`
2. Añadir handler en `handleSOAPRequest()`
3. Implementar lógica específica del método

## Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

## Soporte

Para soporte técnico:
- Revisar logs del sistema
- Consultar documentación TR-069
- Verificar configuración de red

---

**Nota**: Este servidor ACS es compatible con la mayoría de dispositivos TR-069 estándar. Para funcionalidades específicas del fabricante, pueden requerirse modificaciones adicionales.