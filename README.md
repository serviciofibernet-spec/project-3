# Servidor TR-069 en PHP

Un servidor TR-069 completo implementado en PHP para la gestión remota de dispositivos CPE (Customer Premises Equipment).

## 🚀 Características

- **Servidor SOAP TR-069** completo con todos los métodos estándar
- **Base de datos SQLite** para almacenamiento de dispositivos y parámetros
- **Panel de administración web** intuitivo
- **Sistema de autenticación** seguro
- **Logging completo** de todas las operaciones
- **Instalador automático** con configuración paso a paso
- **Gestión de sesiones** y dispositivos
- **Interfaz responsive** y moderna

## 📋 Requisitos del Sistema

- PHP 7.4 o superior
- Extensión SOAP de PHP
- Extensión PDO SQLite
- Servidor web (Apache/Nginx)
- Permisos de escritura en el directorio del proyecto

## 🛠️ Instalación

1. **Clonar o descargar** el proyecto en tu servidor web
2. **Configurar permisos** de escritura para los directorios `data/` y `logs/`
3. **Acceder** a `http://tu-servidor/install.php`
4. **Seguir** el asistente de instalación paso a paso
5. **Configurar** los datos básicos del servidor

### Instalación Rápida

```bash
# Clonar el repositorio
git clone <repository-url> tr069-server
cd tr069-server

# Configurar permisos
chmod 755 data/ logs/
chmod 644 *.php includes/*.php

# Acceder al instalador
# http://localhost/tr069-server/install.php
```

## 🔧 Configuración

### Paso 1: Configuración Básica
- **Nombre del Servidor**: Identificador del servidor TR-069
- **URL del Servidor**: URL completa donde estará disponible el servidor
- **Usuario Administrador**: Usuario para acceder al panel de administración
- **Contraseña Administrador**: Contraseña segura para el administrador

### Paso 2: Base de Datos
- **SQLite**: Base de datos ligera (recomendado)
- Se crea automáticamente en `data/tr069.db`

### Paso 3: Autenticación
- **Habilitar autenticación**: Control de acceso al servidor
- **Timeout de sesión**: Duración de las sesiones en segundos

## 📱 Uso del Servidor

### Endpoint SOAP
El servidor TR-069 está disponible en:
```
http://tu-servidor/index.php
```

### Panel de Administración
Accede al panel de administración en:
```
http://tu-servidor/admin.php
```

### Métodos TR-069 Implementados

- **Inform**: Registro e información de dispositivos
- **GetParameterNames**: Obtener nombres de parámetros
- **GetParameterValues**: Obtener valores de parámetros
- **SetParameterValues**: Establecer valores de parámetros
- **Download**: Descargar archivos al dispositivo
- **Reboot**: Reiniciar dispositivo
- **FactoryReset**: Restaurar configuración de fábrica

## 🗂️ Estructura del Proyecto

```
tr069-server/
├── index.php              # Servidor principal TR-069
├── install.php            # Instalador del sistema
├── admin.php              # Panel de administración
├── config.php             # Configuración del servidor
├── includes/
│   ├── database.php       # Clase de base de datos
│   └── tr069_server.php   # Servidor SOAP TR-069
├── data/
│   ├── tr069.db          # Base de datos SQLite
│   ├── config.json       # Configuración del sistema
│   └── .db_initialized   # Flag de inicialización
├── logs/
│   └── tr069.log         # Log del servidor
└── README.md             # Este archivo
```

## 🔐 Seguridad

- **Autenticación**: Sistema de login seguro con hash de contraseñas
- **Sesiones**: Gestión segura de sesiones con timeout
- **Validación**: Validación de entrada en todos los formularios
- **Logging**: Registro de todas las operaciones para auditoría

## 📊 Monitoreo

### Dashboard Principal
- Total de dispositivos registrados
- Dispositivos activos
- Eventos recientes
- Estado del servidor

### Gestión de Dispositivos
- Lista completa de dispositivos
- Información detallada de cada dispositivo
- Parámetros del dispositivo
- Historial de actividad

### Logs del Sistema
- Registro de todas las operaciones
- Filtrado por dispositivo
- Limpieza de logs antiguos

## 🔧 Configuración Avanzada

### Variables de Configuración

```php
// config.php
define('SERVER_NAME', 'TR069-PHP-Server');
define('SERVER_VERSION', '1.0.0');
define('AUTH_ENABLED', true);
define('SESSION_TIMEOUT', 3600);
define('LOG_LEVEL', 'INFO');
```

### Base de Datos

El servidor utiliza SQLite con las siguientes tablas:
- **devices**: Información de dispositivos CPE
- **sessions**: Sesiones activas
- **parameters**: Parámetros de dispositivos
- **logs**: Registro de actividades

## 🐛 Solución de Problemas

### Error de Conexión a Base de Datos
```bash
# Verificar permisos
chmod 755 data/
chmod 644 data/tr069.db
```

### Error SOAP
```bash
# Verificar extensión SOAP
php -m | grep soap
```

### Logs del Servidor
```bash
# Ver logs en tiempo real
tail -f logs/tr069.log
```

## 📝 Logs y Debugging

### Niveles de Log
- **DEBUG**: Información detallada de depuración
- **INFO**: Información general del sistema
- **WARNING**: Advertencias del sistema
- **ERROR**: Errores del sistema

### Ubicación de Logs
- **Log del servidor**: `logs/tr069.log`
- **Logs de base de datos**: Tabla `logs` en SQLite
- **Logs de PHP**: Configurado en `php.ini`

## 🤝 Contribuciones

1. Fork del proyecto
2. Crear rama para nueva funcionalidad
3. Commit de cambios
4. Push a la rama
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🆘 Soporte

Para soporte técnico o preguntas:
- Crear un issue en el repositorio
- Revisar la documentación
- Verificar los logs del sistema

## 🔄 Actualizaciones

### Versión 1.0.0
- Implementación inicial del servidor TR-069
- Panel de administración web
- Base de datos SQLite
- Sistema de autenticación
- Logging completo

---

**¡Disfruta gestionando tus dispositivos CPE con este servidor TR-069!** 🚀