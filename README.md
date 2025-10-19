# TR069/CWMP ACS Server

Un servidor completo de Auto Configuration Server (ACS) para el protocolo TR069/CWMP, implementado en Python con interfaz de administración web.

## Características

- ✅ **Servidor TR069/CWMP completo** - Implementación del protocolo TR069 con soporte para los principales métodos RPC
- ✅ **Gestión de dispositivos** - Registro y administración automática de dispositivos CPE
- ✅ **Modelo de datos TR-181** - Implementación del modelo de datos estándar
- ✅ **API REST** - API completa para integración y administración
- ✅ **Autenticación y seguridad** - Sistema de autenticación para dispositivos y usuarios
- ✅ **Interfaz de administración** - Panel web para gestión del servidor
- ✅ **Instalador Windows** - Instalación automatizada con archivo .bat
- ✅ **Logs detallados** - Sistema completo de registro de eventos

## Requisitos

- Windows 7/8/10/11 (64-bit)
- Python 3.8 o superior
- 100 MB de espacio en disco
- Privilegios de administrador (para la instalación)

## Instalación Rápida

### Opción 1: Instalador Automático (Recomendado)

1. Descargue o clone este repositorio
2. Ejecute `install.bat` como administrador
3. Siga las instrucciones en pantalla

El instalador realizará automáticamente:
- Verificación de Python
- Instalación de dependencias
- Configuración del servidor
- Creación de reglas de firewall (opcional)
- Instalación como servicio de Windows (opcional)
- Creación de accesos directos

### Opción 2: Instalación Manual

1. Clone el repositorio:
```bash
git clone https://github.com/tuusuario/tr069-server.git
cd tr069-server
```

2. Instale las dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecute el servidor:
```bash
python main.py
```

## Uso

### Iniciar el Servidor

- **Con el instalador**: Usar el acceso directo en el escritorio o ejecutar `start_server.bat`
- **Como servicio**: `net start TR069Server`
- **Manualmente**: `python main.py`

### Acceder a las Interfaces

- **Servidor TR069**: http://localhost:7547
- **API de Administración**: http://localhost:8080
- **Credenciales por defecto**: 
  - Usuario: `admin`
  - Contraseña: `admin`

### Detener el Servidor

- **Con el instalador**: Usar el acceso directo o ejecutar `stop_server.bat`
- **Como servicio**: `net stop TR069Server`
- **Manualmente**: Presionar `Ctrl+C` en la consola

## Configuración de Dispositivos CPE

Configure sus dispositivos CPE con la siguiente información:

- **ACS URL**: `http://<IP-del-servidor>:7547/`
- **Usuario**: (opcional, configure en el panel de administración)
- **Contraseña**: (opcional, configure en el panel de administración)
- **Periodic Inform**: Habilitado (recomendado)
- **Periodic Inform Interval**: 3600 segundos (o según necesidad)

## API REST

El servidor incluye una API REST completa en el puerto 8080:

### Endpoints Principales

- `POST /api/auth/login` - Autenticación
- `GET /api/devices` - Listar dispositivos
- `GET /api/devices/{id}` - Obtener información del dispositivo
- `GET /api/devices/{id}/parameters` - Obtener parámetros del dispositivo
- `POST /api/devices/{id}/parameters` - Configurar parámetros
- `GET /api/datamodel` - Obtener modelo de datos
- `GET /api/status` - Estado del servidor

### Ejemplo de Uso

```python
import requests

# Login
response = requests.post('http://localhost:8080/api/auth/login', 
                         json={'username': 'admin', 'password': 'admin'})
token = response.json()['token']

# Listar dispositivos
headers = {'Authorization': f'Bearer {token}'}
devices = requests.get('http://localhost:8080/api/devices', headers=headers)
print(devices.json())
```

## Métodos RPC Soportados

- ✅ Inform
- ✅ GetRPCMethods
- ✅ GetParameterValues
- ✅ SetParameterValues
- ✅ GetParameterNames
- ✅ SetParameterAttributes
- ✅ GetParameterAttributes
- ✅ AddObject
- ✅ DeleteObject
- ✅ Download
- ✅ Upload
- ✅ Reboot
- ✅ FactoryReset
- ✅ TransferComplete

## Estructura del Proyecto

```
tr069-server/
├── tr069_server/          # Código fuente principal
│   ├── __init__.py
│   ├── server.py         # Servidor TR069/SOAP
│   ├── datamodel.py      # Modelo de datos TR-181
│   ├── auth.py           # Autenticación y seguridad
│   └── api.py            # API REST
├── config/               # Archivos de configuración
├── data/                 # Datos de dispositivos
├── logs/                 # Archivos de log
├── main.py              # Punto de entrada principal
├── requirements.txt     # Dependencias de Python
├── install.bat          # Instalador de Windows
├── start_server.bat     # Script de inicio
├── stop_server.bat      # Script de parada
└── uninstall.bat        # Desinstalador
```

## Configuración Avanzada

### Archivo de Configuración

El servidor utiliza `config/server.json`:

```json
{
  "host": "0.0.0.0",
  "port": 7547,
  "api_port": 8080,
  "log_level": "INFO",
  "session_timeout": 3600
}
```

### Variables de Entorno

- `TR069_HOST` - IP del servidor TR069 (default: 0.0.0.0)
- `TR069_PORT` - Puerto del servidor TR069 (default: 7547)
- `API_PORT` - Puerto de la API (default: 8080)
- `SECRET_KEY` - Clave secreta para sesiones

## Solución de Problemas

### El servidor no inicia

1. Verifique que Python esté instalado: `python --version`
2. Verifique que las dependencias estén instaladas: `pip list`
3. Revise los logs en el directorio `logs/`
4. Verifique que los puertos no estén en uso: `netstat -an | find "7547"`

### Los dispositivos no se conectan

1. Verifique la configuración de firewall
2. Asegúrese de usar la IP correcta del servidor
3. Revise los logs del servidor para mensajes de error
4. Verifique las credenciales de autenticación

### Error de permisos

1. Ejecute el instalador como administrador
2. Verifique los permisos del directorio de instalación
3. Intente instalar en un directorio diferente

## Seguridad

### Recomendaciones

1. **Cambie las credenciales por defecto** inmediatamente después de la instalación
2. **Use HTTPS** en entornos de producción
3. **Configure el firewall** para limitar el acceso
4. **Actualice regularmente** las dependencias
5. **Revise los logs** periódicamente

### Configurar HTTPS

Para habilitar HTTPS, genere certificados SSL y modifique la configuración:

```python
# En main.py, agregue:
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain('cert.pem', 'key.pem')
# Pase context al servidor
```

## Desarrollo

### Ejecutar en modo debug

```bash
python main.py --debug
```

### Ejecutar tests

```bash
pytest tests/
```

### Contribuir

1. Fork el repositorio
2. Cree una rama para su feature (`git checkout -b feature/AmazingFeature`)
3. Commit sus cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abra un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Vea el archivo `LICENSE` para más detalles.

## Soporte

Para reportar bugs o solicitar features, por favor abra un issue en GitHub.

## Créditos

Desarrollado con ❤️ para la comunidad de administradores de red y ISPs.

## Changelog

### v1.0.0 (2024)
- Release inicial
- Implementación completa del protocolo TR069
- API REST
- Instalador Windows
- Autenticación y seguridad básica

## Referencias

- [TR-069 Amendment 6](https://www.broadband-forum.org/technical/download/TR-069_Amendment-6.pdf)
- [TR-181 Device Data Model](https://www.broadband-forum.org/technical/download/TR-181_Issue-2_Amendment-15.pdf)
- [CWMP Protocol](https://en.wikipedia.org/wiki/TR-069)