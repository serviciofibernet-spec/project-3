# 🌐 Servidor TR-069 ACS

Servidor TR-069 (CWMP - CPE WAN Management Protocol) implementado en Python para la gestión remota de dispositivos CPE (Customer Premises Equipment) como routers, módems y otros dispositivos de red.

## 🚀 Inicio Rápido

### 1️⃣ Instalación

Ejecuta el instalador para Windows:
```
install.bat
```

### 2️⃣ Iniciar el Servidor

Ejecuta:
```
iniciar_servidor.bat
```

O manualmente:
```
python tr069_server.py
```

### 3️⃣ Acceder al Panel Web

Abre tu navegador en:
```
http://localhost:7547/
```

### 4️⃣ Credenciales por Defecto

- **Usuario**: admin
- **Contraseña**: admin123

## 📋 Características Principales

- ✅ Servidor TR-069/CWMP completo
- 🔐 Autenticación HTTP Basic
- 📊 Panel web de monitorización
- 💾 Base de datos JSON de dispositivos
- 📝 Registro detallado de eventos
- 🎯 Instalación automática con .bat
- 🔧 Configuración flexible mediante JSON

## ⚙️ Configuración Rápida

Edita el archivo `tr069_config.json`:

```json
{
    "server": {
        "host": "0.0.0.0",
        "port": 7547
    },
    "auth": {
        "enabled": true,
        "username": "admin",
        "password": "admin123"
    }
}
```

## 🔌 Conectar Dispositivos CPE

Configura tus dispositivos con:

- **URL del ACS**: `http://[TU_IP]:7547`
- **Usuario**: `admin`
- **Contraseña**: `admin123`
- **Inform periódico**: 60-300 segundos

## 📁 Archivos Importantes

- `tr069_server.py` - Servidor principal
- `tr069_config.json` - Configuración
- `tr069_devices.json` - Base de datos (auto-creado)
- `tr069_server.log` - Registro de eventos (auto-creado)
- `install.bat` - Instalador para Windows
- `README.md` - Documentación completa en inglés

## 🛠️ Requisitos

- Python 3.7 o superior
- Windows (el instalador .bat es específico para Windows)
- Para Linux/Mac: ejecutar directamente `python3 tr069_server.py`

## 🐛 Solución de Problemas

### Puerto en uso
Si el puerto 7547 está ocupado, cambia el puerto en `tr069_config.json`:
```json
"port": 8080
```

### Python no encontrado
1. Descarga Python desde: https://www.python.org/downloads/
2. Durante la instalación, marca "Add Python to PATH"
3. Reinicia el símbolo del sistema

### Firewall bloqueando conexiones
Permite el puerto 7547 en el Firewall de Windows:
1. Panel de Control → Sistema y Seguridad → Firewall de Windows
2. Configuración avanzada → Reglas de entrada
3. Nueva regla → Puerto → TCP → 7547 → Permitir conexión

## 📊 Ver Dispositivos Conectados

Los dispositivos se almacenan en `tr069_devices.json` y se pueden ver en:
1. El panel web: http://localhost:7547/
2. Directamente en el archivo JSON
3. Los logs: `tr069_server.log`

## 🔒 Seguridad

**⚠️ IMPORTANTE**: Cambia las credenciales por defecto antes de usar en producción.

Edita `tr069_config.json`:
```json
"auth": {
    "enabled": true,
    "username": "tu_nuevo_usuario",
    "password": "contraseña_segura_aqui"
}
```

## 📚 Documentación Completa

Para documentación detallada en inglés, consulta `README.md`

## 🆘 Ayuda

Si tienes problemas:
1. Revisa `tr069_server.log` para ver errores
2. Verifica la configuración en `tr069_config.json`
3. Asegúrate de que Python esté correctamente instalado
4. Verifica que el firewall no esté bloqueando el puerto

## 📄 Licencia

Código abierto bajo licencia MIT.

---

**¡Disfruta gestionando tus dispositivos CPE!** 🎉
