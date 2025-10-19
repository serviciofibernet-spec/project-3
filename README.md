# TR-069 Server en Python

Un servidor TR-069 (CWMP) completo implementado en Python con interfaz web y API REST para la gestión de dispositivos.

## Características

- ✅ Servidor TR-069 completo con soporte SOAP/HTTP
- ✅ Interfaz web para gestión de dispositivos
- ✅ API REST para integración
- ✅ Base de datos SQLite para persistencia
- ✅ Limpieza automática de dispositivos antiguos
- ✅ Instalador automático para Windows (.bat)
- ✅ Logging completo
- ✅ Soporte CORS para desarrollo web

## Instalación Rápida (Windows)

1. **Descargar e instalar Python 3.8+** desde [python.org](https://python.org)
   - Asegúrate de marcar "Add Python to PATH" durante la instalación

2. **Ejecutar el instalador automático:**
   ```batch
   install_tr069_server.bat
   ```

3. **Iniciar el servidor:**
   ```batch
   start_tr069_server.bat
   ```

## Instalación Manual

### Requisitos
- Python 3.8 o superior
- pip (incluido con Python)

### Pasos

1. **Clonar o descargar el proyecto**

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar el servidor (opcional):**
   Edita `config.ini` para personalizar la configuración:
   ```ini
   [server]
   host = 0.0.0.0
   port = 8080
   
   [logging]
   level = INFO
   file = tr069_server.log
   ```

4. **Iniciar el servidor:**
   ```bash
   python tr069_server.py
   ```

## Uso

### Endpoints del Servidor

- **Interfaz Web:** http://localhost:8080/
- **Endpoint TR-069:** http://localhost:8080/tr069
- **API REST:** http://localhost:8080/devices

### Métodos TR-069 Soportados

- `Inform` - Registro de dispositivos
- `GetParameterValues` - Obtener valores de parámetros
- `SetParameterValues` - Establecer valores de parámetros
- `GetParameterNames` - Obtener nombres de parámetros disponibles

### API REST

#### Obtener todos los dispositivos
```bash
GET /devices
```

#### Obtener dispositivo específico
```bash
GET /devices/{device_id}
```

#### Obtener parámetros de un dispositivo
```bash
GET /devices/{device_id}/parameters
```

#### Establecer parámetros de un dispositivo
```bash
POST /devices/{device_id}/parameters
Content-Type: application/json

{
    "Device.WiFi.Radio.1.Enable": "true",
    "Device.WiFi.Radio.1.SSID": "MiWiFi",
    "Device.WiFi.Radio.1.Password": "mipassword123"
}
```

## Pruebas

Ejecuta el cliente de prueba para verificar que el servidor funciona:

```bash
python test_client.py
```

Este script enviará mensajes TR-069 de prueba al servidor.

## Configuración

### Archivo config.ini

```ini
[server]
host = 0.0.0.0          # Dirección IP del servidor
port = 8080             # Puerto HTTP
ssl_port = 8443         # Puerto HTTPS (no implementado aún)

[logging]
level = INFO            # Nivel de logging (DEBUG, INFO, WARNING, ERROR)
file = tr069_server.log # Archivo de log

[database]
file = tr069_devices.db # Archivo de base de datos SQLite

[security]
enable_ssl = false      # Habilitar HTTPS
cert_file = server.crt  # Certificado SSL
key_file = server.key   # Clave privada SSL

[device_management]
cleanup_hours = 24      # Horas antes de limpiar dispositivos inactivos
max_devices = 1000      # Máximo número de dispositivos
```

## Parámetros de Dispositivo Soportados

### Información del Dispositivo
- `Device.DeviceInfo.Manufacturer`
- `Device.DeviceInfo.ModelName`
- `Device.DeviceInfo.SoftwareVersion`
- `Device.DeviceInfo.HardwareVersion`
- `Device.DeviceInfo.SerialNumber`

### Servidor de Gestión
- `Device.ManagementServer.URL`
- `Device.ManagementServer.Username`
- `Device.ManagementServer.Password`
- `Device.ManagementServer.PeriodicInformInterval`

### WiFi (Radio 1)
- `Device.WiFi.Radio.1.Enable`
- `Device.WiFi.Radio.1.SSID`
- `Device.WiFi.Radio.1.Password`
- `Device.WiFi.Radio.1.Channel`
- `Device.WiFi.Radio.1.ChannelWidth`
- `Device.WiFi.Radio.1.SecurityMode`

## Estructura del Proyecto

```
tr069-server/
├── tr069_server.py          # Servidor principal
├── test_client.py           # Cliente de prueba
├── requirements.txt         # Dependencias Python
├── config.ini              # Configuración
├── install_tr069_server.bat # Instalador Windows
├── start_tr069_server.bat  # Script de inicio Windows
├── README.md               # Este archivo
└── tr069_devices.db        # Base de datos (se crea automáticamente)
```

## Logs

Los logs se guardan en `tr069_server.log` e incluyen:
- Registro de dispositivos
- Operaciones de parámetros
- Errores y advertencias
- Actividad del servidor

## Desarrollo

### Agregar Nuevos Parámetros

Para agregar nuevos parámetros de dispositivo, modifica el método `generate_parameter_names()` en `tr069_server.py`:

```python
def generate_parameter_names(self, path: str, next_level: bool) -> List[Dict[str, Any]]:
    parameters = []
    
    if path == "." or path == "":
        parameters.extend([
            {"Name": "Device.NuevoParametro.Valor", "Writable": "true"},
            # ... más parámetros
        ])
    
    return parameters
```

### Agregar Nuevos Métodos TR-069

1. Crea un método `handle_nuevometodo()` en la clase `TR069Server`
2. Implementa la lógica del método
3. Retorna una respuesta SOAP usando `create_soap_response()`

## Solución de Problemas

### El servidor no inicia
- Verifica que Python esté instalado: `python --version`
- Verifica que las dependencias estén instaladas: `pip list`
- Revisa el archivo de log: `tr069_server.log`

### Los dispositivos no se registran
- Verifica que el firewall permita conexiones en el puerto 8080
- Revisa los logs para errores de parsing XML
- Verifica que el dispositivo esté enviando mensajes SOAP válidos

### Error de permisos en Windows
- Ejecuta el instalador como administrador
- Verifica que Python esté en el PATH del sistema

## Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo LICENSE para más detalles.

## Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## Soporte

Para soporte y preguntas:
- Abre un issue en GitHub
- Revisa los logs del servidor
- Consulta la documentación TR-069 oficial