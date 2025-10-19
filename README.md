# Servidor TR-069 (CWMP) en Python

Un servidor ACS (Auto Configuration Server) TR-069 completo implementado en Python con instalador automático para Windows.

## Características

- ✅ **Protocolo TR-069 completo**: Implementación completa del protocolo CWMP
- ✅ **Gestión de dispositivos**: Registro, monitoreo y configuración de dispositivos CPE
- ✅ **Autenticación y seguridad**: Sistema de usuarios, sesiones y protección contra ataques
- ✅ **Base de datos SQLite**: Almacenamiento persistente de dispositivos y configuraciones
- ✅ **Interfaz web**: API REST para gestión y monitoreo
- ✅ **Instalador Windows**: Script .bat para instalación automática
- ✅ **Configuración flexible**: Archivo JSON de configuración
- ✅ **Logging avanzado**: Sistema de logs con rotación automática

## Instalación Rápida (Windows)

1. **Descargar** todos los archivos del proyecto
2. **Ejecutar como Administrador** el archivo `install_tr069_server.bat`
3. **Seguir** las instrucciones del instalador
4. **¡Listo!** El servidor estará instalado y configurado

### Requisitos Previos

- Windows 7/8/10/11
- Python 3.8 o superior
- Permisos de administrador

## Instalación Manual

### 1. Clonar o descargar el proyecto

```bash
git clone <repository-url>
cd tr069-server
```

### 2. Crear entorno virtual

```bash
python -m venv venv
```

### 3. Activar entorno virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 5. Ejecutar el servidor

```bash
python tr069_server.py
```

## Configuración

El servidor se configura mediante el archivo `config/server_config.json`:

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 7547,
    "ssl_enabled": false,
    "ssl_cert_path": "",
    "ssl_key_path": ""
  },
  "database": {
    "devices_db": "data/tr069_devices.db",
    "auth_db": "data/tr069_auth.db"
  },
  "logging": {
    "level": "INFO",
    "file": "logs/tr069_server.log",
    "max_size": "10MB",
    "backup_count": 5
  },
  "security": {
    "max_failed_attempts": 5,
    "block_duration_minutes": 15,
    "session_timeout_hours": 24
  }
}
```

### Parámetros de Configuración

#### Servidor
- `host`: Dirección IP para bind (0.0.0.0 para todas las interfaces)
- `port`: Puerto del servidor (por defecto 7547)
- `ssl_enabled`: Habilitar HTTPS/SSL
- `ssl_cert_path`: Ruta al certificado SSL
- `ssl_key_path`: Ruta a la clave privada SSL

#### Base de Datos
- `devices_db`: Ruta a la base de datos de dispositivos
- `auth_db`: Ruta a la base de datos de autenticación

#### Logging
- `level`: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `file`: Archivo de log
- `max_size`: Tamaño máximo del archivo de log
- `backup_count`: Número de archivos de backup

#### Seguridad
- `max_failed_attempts`: Intentos fallidos antes de bloquear IP
- `block_duration_minutes`: Duración del bloqueo en minutos
- `session_timeout_hours`: Tiempo de expiración de sesión

## Uso del Servidor

### Iniciar el Servidor

**Opción 1: Script de inicio (Windows)**
```bash
start_server.bat
```

**Opción 2: Comando directo**
```bash
python tr069_server.py
```

**Opción 3: Con parámetros**
```bash
python tr069_server.py --host 0.0.0.0 --port 7547 --debug
```

### Detener el Servidor

**Windows:**
```bash
stop_server.bat
```

**Manual:**
Presionar `Ctrl+C` en la consola del servidor

### Acceso Web

Una vez iniciado, el servidor estará disponible en:

- **Servidor principal**: http://localhost:7547
- **Estado del servidor**: http://localhost:7547/status
- **Lista de dispositivos**: http://localhost:7547/devices
- **Información del servidor**: http://localhost:7547 (GET)

## API REST

### Endpoints Disponibles

#### GET /
Información general del servidor
```json
{
  "server": "TR-069 ACS Server",
  "version": "1.0",
  "status": "running",
  "connected_devices": 5
}
```

#### GET /status
Estado detallado del servidor
```json
{
  "server_status": "running",
  "connected_devices": 5,
  "active_sessions": 2,
  "timestamp": "2023-12-07T10:30:00"
}
```

#### GET /devices
Lista de dispositivos conectados
```json
{
  "device_001": {
    "last_contact": "2023-12-07T10:29:45",
    "ip_address": "192.168.1.100",
    "parameter_count": 25,
    "events": ["1 BOOT", "2 PERIODIC"]
  }
}
```

#### POST /
Endpoint principal para comunicación CWMP con dispositivos CPE

## Protocolo TR-069 Soportado

### Métodos RPC Implementados

#### Del ACS al CPE:
- `GetRPCMethods`: Obtener métodos RPC soportados
- `GetParameterValues`: Obtener valores de parámetros
- `SetParameterValues`: Establecer valores de parámetros
- `AddObject`: Añadir objeto
- `DeleteObject`: Eliminar objeto
- `Reboot`: Reiniciar dispositivo
- `FactoryReset`: Reset de fábrica
- `Download`: Descargar firmware/configuración
- `Upload`: Subir logs/configuración

#### Del CPE al ACS:
- `Inform`: Notificación de eventos
- `TransferComplete`: Confirmación de transferencia
- `GetRPCMethodsResponse`: Respuesta a GetRPCMethods
- `GetParameterValuesResponse`: Respuesta a GetParameterValues
- `SetParameterValuesResponse`: Respuesta a SetParameterValues

### Eventos Soportados

- `0 BOOTSTRAP`: Arranque inicial
- `1 BOOT`: Reinicio
- `2 PERIODIC`: Contacto periódico
- `3 SCHEDULED`: Contacto programado
- `4 VALUE CHANGE`: Cambio de valor
- `6 CONNECTION REQUEST`: Solicitud de conexión
- `7 TRANSFER COMPLETE`: Transferencia completada
- `8 DIAGNOSTICS COMPLETE`: Diagnóstico completado

## Gestión de Dispositivos

### Registro Automático

Los dispositivos se registran automáticamente cuando envían su primer mensaje `Inform`. El servidor extrae:

- Número de serie
- Fabricante y modelo
- Versión de software/hardware
- Dirección IP
- URL de Connection Request
- Parámetros del dispositivo

### Monitoreo

El servidor monitorea continuamente:

- Estado de conexión (online/offline)
- Último contacto
- Eventos recibidos
- Parámetros actualizados

### Base de Datos

Toda la información se almacena en bases de datos SQLite:

- `tr069_devices.db`: Dispositivos y configuraciones
- `tr069_auth.db`: Usuarios y sesiones

## Seguridad

### Autenticación

- Sistema de usuarios con roles (admin, user, readonly)
- Sesiones con tokens JWT
- Protección contra ataques de fuerza bruta
- Bloqueo automático de IPs maliciosas

### Credenciales por Defecto

```
Usuario: admin
Contraseña: admin123
```

**⚠️ IMPORTANTE: Cambiar estas credenciales inmediatamente después de la instalación**

### Protecciones Implementadas

- Validación de entrada
- Protección CSRF
- Rate limiting
- Logging de accesos
- Timeouts de sesión

## Logs y Monitoreo

### Archivos de Log

- `logs/tr069_server.log`: Log principal del servidor
- Rotación automática cuando alcanza el tamaño máximo
- Múltiples niveles de log (DEBUG, INFO, WARNING, ERROR)

### Información Registrada

- Conexiones de dispositivos
- Mensajes CWMP enviados/recibidos
- Intentos de autenticación
- Errores y excepciones
- Cambios de configuración

## Solución de Problemas

### El servidor no inicia

1. Verificar que Python 3.8+ esté instalado
2. Verificar que todas las dependencias estén instaladas
3. Verificar que el puerto 7547 no esté en uso
4. Revisar los logs para errores específicos

### Los dispositivos no se conectan

1. Verificar la configuración de red del dispositivo
2. Verificar que el firewall permita el puerto 7547
3. Revisar los logs del servidor para mensajes de error
4. Verificar la URL del ACS en el dispositivo

### Problemas de autenticación

1. Verificar credenciales de usuario
2. Revisar logs de acceso
3. Verificar que la IP no esté bloqueada
4. Comprobar la configuración de seguridad

### Errores de base de datos

1. Verificar permisos de escritura en el directorio `data/`
2. Verificar que SQLite esté disponible
3. Revisar logs para errores específicos de BD

## Desarrollo y Personalización

### Estructura del Proyecto

```
tr069-server/
├── tr069_server.py          # Servidor principal
├── cwmp_handlers.py         # Manejadores del protocolo CWMP
├── device_manager.py        # Gestión de dispositivos
├── auth_security.py         # Autenticación y seguridad
├── config.py               # Gestión de configuración
├── requirements.txt        # Dependencias de Python
├── install_tr069_server.bat # Instalador para Windows
├── config/
│   └── server_config.json  # Configuración del servidor
├── data/                   # Bases de datos
├── logs/                   # Archivos de log
└── README.md              # Esta documentación
```

### Añadir Nuevos Métodos RPC

1. Implementar el método en `cwmp_handlers.py`
2. Añadir el manejador en `tr069_server.py`
3. Actualizar la documentación

### Personalizar la Autenticación

Modificar `auth_security.py` para:
- Integrar con LDAP/Active Directory
- Añadir autenticación de dos factores
- Implementar SSO

### Añadir Nuevas Funcionalidades

El servidor está diseñado para ser extensible:
- Módulos independientes
- Configuración flexible
- API REST para integraciones

## Licencia

Este proyecto está bajo licencia MIT. Ver archivo LICENSE para más detalles.

## Soporte

Para soporte técnico o reportar problemas:

1. Revisar esta documentación
2. Consultar los logs del servidor
3. Crear un issue en el repositorio del proyecto

## Contribuciones

Las contribuciones son bienvenidas:

1. Fork del repositorio
2. Crear rama para la funcionalidad
3. Realizar cambios y tests
4. Enviar pull request

---

**¡Gracias por usar el Servidor TR-069 en Python!** 🚀