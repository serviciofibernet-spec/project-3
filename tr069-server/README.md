# 📡 Servidor TR-069/CWMP en PHP

Un servidor TR-069 (CPE WAN Management Protocol) completo desarrollado en PHP para gestionar dispositivos CPE (Customer Premises Equipment) como routers, módems y dispositivos IoT.

## 🚀 Características

- ✅ **Servidor ACS completo** - Implementación del protocolo TR-069/CWMP
- ✅ **Panel de administración web** - Interfaz moderna y responsive
- ✅ **Gestión de dispositivos** - Monitoreo y control de CPEs
- ✅ **Manejo de tareas** - Ejecución de comandos RPC en dispositivos
- ✅ **Gestión de firmware** - Actualización remota de firmware
- ✅ **Sistema de logs** - Registro detallado de todas las operaciones
- ✅ **Autenticación HTTP** - Seguridad para las comunicaciones
- ✅ **Base de datos MySQL** - Almacenamiento persistente
- ✅ **Instalador web** - Configuración fácil paso a paso

## 📋 Requisitos del Sistema

### Requisitos mínimos:
- **PHP** >= 7.4
- **MySQL** >= 5.7 o MariaDB >= 10.2
- **Apache** 2.4+ con mod_rewrite habilitado
- **Extensiones PHP requeridas:**
  - PDO y PDO_MySQL
  - SOAP
  - JSON
  - DOM
  - SimpleXML
  - mbstring

### Requisitos recomendados:
- PHP 8.0 o superior
- MySQL 8.0 o MariaDB 10.5
- 2GB RAM mínimo
- 10GB espacio en disco

## 🛠️ Instalación

### 1. Clonar o descargar el proyecto

```bash
# Si tienes Git instalado
git clone https://github.com/tu-usuario/tr069-server.git
cd tr069-server

# O descarga y descomprime el archivo ZIP
```

### 2. Configurar el servidor web

#### Apache (recomendado):
```apache
<VirtualHost *:80>
    ServerName tr069.local
    DocumentRoot /ruta/a/tr069-server
    
    <Directory /ruta/a/tr069-server>
        AllowOverride All
        Require all granted
    </Directory>
    
    # Configuración para el endpoint ACS en puerto 8080
    Listen 8080
    <VirtualHost *:8080>
        DocumentRoot /ruta/a/tr069-server/public
        <Directory /ruta/a/tr069-server/public>
            AllowOverride All
            Require all granted
        </Directory>
    </VirtualHost>
</VirtualHost>
```

#### Nginx:
```nginx
server {
    listen 80;
    server_name tr069.local;
    root /ruta/a/tr069-server/public;
    index index.php;
    
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
    
    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }
    
    location ~ /\.(config|src|database|logs|vendor) {
        deny all;
    }
}

# Endpoint ACS en puerto 8080
server {
    listen 8080;
    root /ruta/a/tr069-server/public;
    
    location /acs {
        fastcgi_pass unix:/var/run/php/php7.4-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root/acs.php;
        include fastcgi_params;
    }
}
```

### 3. Instalar dependencias (opcional)

Si tienes Composer instalado:
```bash
composer install
```

### 4. Configurar permisos

```bash
# Linux/Mac
chmod -R 755 tr069-server
chmod -R 777 tr069-server/logs
chmod -R 777 tr069-server/config
chmod 777 tr069-server/install.php

# Crear carpeta de logs si no existe
mkdir -p tr069-server/logs
```

### 5. Ejecutar el instalador web

1. Abre tu navegador y ve a: `http://tu-servidor/tr069-server/install.php`
2. Sigue el asistente de instalación:
   - **Paso 1:** Configuración de base de datos
   - **Paso 2:** Configuración del servidor TR-069
   - **Paso 3:** Crear cuenta de administrador
   - **Paso 4:** Finalizar instalación

### 6. Eliminar el instalador (IMPORTANTE)

Por seguridad, después de completar la instalación:
```bash
rm tr069-server/install.php
```

## 🔧 Configuración

### Configuración de Base de Datos

Durante la instalación necesitarás:
- **Host:** Generalmente `localhost`
- **Puerto:** Generalmente `3306`
- **Nombre de BD:** Por ejemplo `tr069_server`
- **Usuario:** Tu usuario de MySQL
- **Contraseña:** Tu contraseña de MySQL

### Configuración del Servidor TR-069

- **URL del Servidor:** La dirección IP o dominio de tu servidor
- **Puerto:** Puerto para el endpoint ACS (por defecto 8080)
- **Ruta ACS:** Path del endpoint (por defecto `/acs`)
- **Autenticación HTTP:** Usuario y contraseña para los CPEs

### Configurar dispositivos CPE

En tu router/modem/dispositivo CPE, configura:

1. **ACS URL:** `http://tu-servidor:8080/acs`
2. **ACS Username:** El usuario configurado (por defecto: `acs`)
3. **ACS Password:** La contraseña configurada (por defecto: `acs123`)
4. **Periodic Inform:** Habilitar y configurar intervalo (ej: 300 segundos)

## 📱 Uso del Sistema

### Acceder al panel de administración

1. Ve a: `http://tu-servidor/tr069-server/public/`
2. Inicia sesión con las credenciales creadas durante la instalación

### Funcionalidades principales

#### Dashboard
- Vista general del sistema
- Estadísticas en tiempo real
- Dispositivos recientes
- Logs importantes

#### Gestión de Dispositivos
- Lista de todos los CPEs registrados
- Estado de conexión
- Información detallada
- Parámetros del dispositivo

#### Tareas
- Crear tareas para dispositivos
- Tipos de tareas soportadas:
  - GetParameterValues
  - SetParameterValues
  - Reboot
  - FactoryReset
  - Download (actualización de firmware)
  - Upload

#### Firmware
- Gestión de archivos de firmware
- Asignación a modelos específicos
- Programación de actualizaciones

#### Logs
- Registro de todas las operaciones
- Filtrado por nivel (DEBUG, INFO, WARNING, ERROR)
- Búsqueda y exportación

## 🔌 Métodos RPC Soportados

El servidor implementa los siguientes métodos TR-069:

### Métodos del CPE al ACS:
- ✅ Inform
- ✅ GetRPCMethods
- ✅ TransferComplete
- ✅ RequestDownload
- ✅ Kicked
- ✅ DUStateChangeComplete
- ✅ AutonomousTransferComplete

### Métodos del ACS al CPE:
- ✅ GetRPCMethods
- ✅ SetParameterValues
- ✅ GetParameterValues
- ✅ GetParameterNames
- ✅ SetParameterAttributes
- ✅ GetParameterAttributes
- ✅ AddObject
- ✅ DeleteObject
- ✅ Reboot
- ✅ FactoryReset
- ✅ Download
- ✅ Upload
- ✅ ScheduleInform

## 🐛 Solución de Problemas

### El instalador no funciona
- Verifica que tengas PHP 7.4 o superior
- Asegúrate de que las extensiones requeridas estén instaladas
- Verifica los permisos de escritura en las carpetas

### Los dispositivos no se conectan
- Verifica la configuración del ACS URL en el dispositivo
- Revisa los logs en `tr069-server/logs/`
- Asegúrate de que el puerto 8080 esté abierto
- Verifica las credenciales de autenticación

### Error de base de datos
- Verifica las credenciales en `config/config.php`
- Asegúrate de que MySQL esté ejecutándose
- Verifica que la base de datos exista

### Página en blanco
- Revisa los logs de PHP: `tail -f /var/log/apache2/error.log`
- Habilita el modo debug editando `config/config.php`
- Verifica que mod_rewrite esté habilitado

## 🔒 Seguridad

### Recomendaciones importantes:

1. **Elimina install.php** después de la instalación
2. **Cambia las credenciales por defecto**
3. **Usa HTTPS** en producción
4. **Configura un firewall** para limitar acceso
5. **Actualiza regularmente** PHP y las dependencias
6. **Realiza backups** de la base de datos regularmente
7. **Revisa los logs** periódicamente

### Configuración de HTTPS (recomendado)

```apache
<VirtualHost *:443>
    ServerName tr069.local
    DocumentRoot /ruta/a/tr069-server
    
    SSLEngine on
    SSLCertificateFile /ruta/a/certificado.crt
    SSLCertificateKeyFile /ruta/a/private.key
    
    # Resto de la configuración...
</VirtualHost>
```

## 📊 Estructura del Proyecto

```
tr069-server/
├── config/              # Archivos de configuración
├── database/            # Esquemas y migraciones SQL
├── logs/               # Archivos de log
├── public/             # Archivos públicos (web root)
│   ├── css/           # Estilos
│   ├── js/            # JavaScript
│   ├── acs.php        # Endpoint TR-069
│   ├── index.php      # Panel de administración
│   └── login.php      # Página de login
├── src/                # Código fuente PHP
│   ├── Controllers/    # Controladores
│   ├── Models/        # Modelos
│   ├── Services/      # Servicios
│   └── TR069Server.php # Clase principal del servidor
├── templates/          # Plantillas HTML
├── vendor/            # Dependencias (si usa Composer)
├── .htaccess          # Configuración Apache
├── composer.json      # Dependencias PHP
├── install.php        # Instalador web
└── README.md          # Este archivo
```

## 🧪 Testing

Para verificar que todo funciona correctamente:

1. **Test de conexión ACS:**
```bash
curl -X POST http://tu-servidor:8080/acs \
  -H "Content-Type: text/xml" \
  -H "SOAPAction: " \
  -u acs:acs123
```

2. **Verificar requisitos del sistema:**
```bash
composer run check-requirements
```

3. **Simulador de CPE:**
Puedes usar herramientas como [GenieACS Simulator](https://github.com/genieacs/genieacs-sim) para pruebas.

## 📚 Recursos Adicionales

- [Especificación TR-069 (Broadband Forum)](https://www.broadband-forum.org/technical/download/TR-069.pdf)
- [Documentación de CWMP](https://cwmp-data-models.broadband-forum.org/)
- [Modelos de datos TR-181](https://www.broadband-forum.org/technical/download/TR-181_Issue-2.pdf)

## 🤝 Soporte

Si encuentras problemas o tienes preguntas:

1. Revisa la sección de [Solución de Problemas](#-solución-de-problemas)
2. Revisa los logs del sistema en `logs/`
3. Contacta al administrador del sistema

## 📄 Licencia

Este proyecto es software propietario. Todos los derechos reservados.

## 🎯 Roadmap

Funcionalidades planeadas para futuras versiones:

- [ ] API REST para integración con sistemas externos
- [ ] Soporte para TR-369 (USP)
- [ ] Dashboard con gráficas en tiempo real
- [ ] Sistema de alertas y notificaciones
- [ ] Backup automático de configuraciones
- [ ] Soporte multi-tenant
- [ ] Aplicación móvil de monitoreo

---

**Desarrollado con ❤️ para la gestión eficiente de dispositivos CPE**