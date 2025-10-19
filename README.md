# 🌐 TR-069 ACS Server

Servidor TR-069 (CWMP - CPE WAN Management Protocol) implementado en Python para la gestión remota de dispositivos CPE (Customer Premises Equipment) como routers, modems y otros dispositivos de red.

## 📋 Características

- ✅ **Protocolo TR-069 completo**: Implementación del estándar CWMP
- 🔐 **Autenticación HTTP Basic**: Acceso seguro al servidor
- 📊 **Panel web de control**: Interfaz web para monitorizar dispositivos
- 💾 **Base de datos JSON**: Almacenamiento simple de dispositivos
- 📝 **Registro detallado**: Logs completos de todas las operaciones
- 🎯 **Fácil instalación**: Instalador .bat para Windows
- 🔧 **Altamente configurable**: Configuración mediante archivo JSON

## 🔧 Requisitos

- **Python 3.7 o superior**
- **Bibliotecas estándar de Python** (incluidas por defecto)

## 📥 Instalación en Windows

### Opción 1: Instalación automática (Recomendado)

1. Descarga todos los archivos del proyecto
2. Ejecuta `install.bat` haciendo doble clic
3. El instalador verificará Python y configurará todo automáticamente
4. Al finalizar, encontrarás `iniciar_servidor.bat` para iniciar el servidor

### Opción 2: Instalación manual

1. Asegúrate de tener Python instalado:
   ```cmd
   python --version
   ```

2. (Opcional) Instala dependencias opcionales:
   ```cmd
   pip install -r requirements.txt
   ```

3. El servidor está listo para ejecutarse

## 🚀 Uso

### Iniciar el servidor

**Opción 1**: Doble clic en `iniciar_servidor.bat`

**Opción 2**: Desde la línea de comandos:
```cmd
python tr069_server.py
```

### Acceder al panel de control

Una vez iniciado el servidor, abre tu navegador en:
```
http://localhost:7547/
```

### Detener el servidor

Presiona `Ctrl+C` en la ventana donde se está ejecutando el servidor.

## ⚙️ Configuración

El servidor se configura mediante el archivo `tr069_config.json`:

```json
{
    "server": {
        "host": "0.0.0.0",       // Escucha en todas las interfaces
        "port": 7547,             // Puerto estándar TR-069
        "ssl_enabled": false      // SSL/TLS (por implementar)
    },
    "auth": {
        "enabled": true,          // Activar autenticación
        "username": "admin",      // Usuario por defecto
        "password": "admin123"    // Contraseña por defecto
    },
    "database": {
        "type": "json",
        "path": "tr069_devices.json"  // Archivo de base de datos
    }
}
```

### Cambiar el puerto

Edita `tr069_config.json` y modifica el valor de `server.port`:
```json
"port": 8080
```

### Cambiar credenciales

Edita `tr069_config.json` y modifica los valores en `auth`:
```json
"auth": {
    "enabled": true,
    "username": "tu_usuario",
    "password": "tu_contraseña_segura"
}
```

## 📡 Protocolo TR-069 / CWMP

### Métodos soportados por el ACS

El servidor soporta los siguientes métodos CWMP:

- ✅ **Inform**: Recepción de información del dispositivo
- ✅ **InformResponse**: Respuesta a Inform
- ✅ **GetRPCMethods**: Consulta de métodos disponibles
- ✅ **GetRPCMethodsResponse**: Respuesta con métodos soportados
- ✅ **TransferComplete**: Confirmación de transferencia
- ✅ **TransferCompleteResponse**: Respuesta a transferencia

### Configurar dispositivo CPE

Para que un dispositivo CPE se conecte a este servidor, configúralo con:

- **URL del ACS**: `http://[IP_DEL_SERVIDOR]:7547`
- **Usuario**: `admin` (o el configurado)
- **Contraseña**: `admin123` (o la configurada)
- **Periodic Inform**: Activado (recomendado cada 60-300 segundos)

## 📁 Estructura de archivos

```
tr069-server/
│
├── tr069_server.py          # Servidor principal
├── tr069_config.json        # Configuración
├── tr069_devices.json       # Base de datos de dispositivos (auto-generado)
├── tr069_server.log         # Registro de eventos (auto-generado)
├── requirements.txt         # Dependencias Python
├── install.bat              # Instalador para Windows
├── iniciar_servidor.bat     # Script de inicio rápido (auto-generado)
├── detener_servidor.bat     # Script de parada (auto-generado)
└── README.md               # Este archivo
```

## 🔍 Registro de eventos (Logs)

El servidor genera logs en dos lugares:

1. **Archivo**: `tr069_server.log` - Registro completo persistente
2. **Consola**: Salida en tiempo real

Niveles de log:
- `INFO`: Operaciones normales
- `WARNING`: Advertencias
- `ERROR`: Errores
- `DEBUG`: Información detallada (para desarrollo)

## 🌐 API Web

### Endpoints disponibles

#### GET `/`
Panel de control web con:
- Estado del servidor
- Lista de dispositivos conectados
- Información de cada dispositivo
- Última conexión

#### POST `/`
Endpoint para mensajes CWMP/SOAP desde dispositivos CPE.

## 🔧 Desarrollo y extensión

### Añadir nuevos métodos RPC

Edita `tr069_server.py` y añade un nuevo método en la clase `TR069RequestHandler`:

```python
def handle_nuevo_metodo(self, root):
    """Maneja mensaje NuevoMetodo"""
    # Tu implementación aquí
    response = self.create_soap_response("NuevoMetodoResponse", contenido)
    return response
```

### Cambiar el almacenamiento

Actualmente usa JSON, pero puedes implementar otros backends:
- SQLite
- MySQL/PostgreSQL
- MongoDB
- Redis

Extiende la clase `DeviceDatabase` con tu implementación.

## 🐛 Solución de problemas

### El servidor no inicia

**Problema**: Puerto ya en uso
```
Error: [Errno 10048] Only one usage of each socket address
```

**Solución**: Cambia el puerto en `tr069_config.json` o cierra la aplicación que esté usando el puerto 7547.

### Los dispositivos no se conectan

1. Verifica que el firewall de Windows permita conexiones en el puerto 7547
2. Verifica la URL del ACS en el dispositivo CPE
3. Verifica las credenciales de autenticación
4. Revisa los logs: `tr069_server.log`

### Python no reconocido

**Problema**: `'python' is not recognized as an internal or external command`

**Solución**: 
1. Reinstala Python desde https://www.python.org/downloads/
2. Marca la opción "Add Python to PATH" durante la instalación
3. Reinicia el símbolo del sistema

## 📊 Base de datos de dispositivos

Los dispositivos se guardan en `tr069_devices.json` con la siguiente estructura:

```json
{
    "SERIAL123456": {
        "Manufacturer": "ACME Corp",
        "OUI": "00B0D0",
        "ProductClass": "Router",
        "SerialNumber": "SERIAL123456",
        "first_seen": "2025-10-19T10:30:00",
        "last_seen": "2025-10-19T12:45:30"
    }
}
```

## 🔒 Seguridad

### Recomendaciones

1. **Cambiar credenciales por defecto**: Modifica `username` y `password` en `tr069_config.json`
2. **Usar contraseñas fuertes**: Mínimo 12 caracteres, combina letras, números y símbolos
3. **Firewall**: Limita el acceso al puerto 7547 solo desde redes confiables
4. **HTTPS**: Para producción, implementa SSL/TLS
5. **Actualizar regularmente**: Mantén Python actualizado

### Implementar SSL/TLS (Futuro)

Para habilitar HTTPS, será necesario:
1. Generar certificados SSL
2. Modificar el servidor para usar `HTTPSServer`
3. Configurar `ssl_enabled: true` en el archivo de configuración

## 📚 Referencias

- [TR-069 Standard (CWMP)](https://www.broadband-forum.org/technical/download/TR-069.pdf)
- [Python http.server](https://docs.python.org/3/library/http.server.html)
- [SOAP Protocol](https://www.w3.org/TR/soap/)

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo licencia MIT.

## 👤 Autor

Desarrollado para la gestión eficiente de dispositivos CPE mediante el protocolo TR-069.

## 🆘 Soporte

Si encuentras problemas o tienes preguntas:

1. Revisa los logs en `tr069_server.log`
2. Consulta la sección de Solución de problemas
3. Verifica la configuración en `tr069_config.json`

---

**¡Gracias por usar TR-069 ACS Server!** 🚀
