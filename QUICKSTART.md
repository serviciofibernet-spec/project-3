# 🚀 Guía Rápida de Inicio - TR-069 ACS

Esta guía te ayudará a tener tu servidor TR-069 funcionando en menos de 5 minutos.

## ⚡ Instalación Rápida

### Paso 1: Verificar Requisitos

```bash
php check_requirements.php
```

O accede desde el navegador: `http://tu-servidor/check_requirements.php`

### Paso 2: Ejecutar el Instalador

1. Abre tu navegador
2. Ve a: `http://tu-servidor/install.php`
3. Completa el formulario con tus datos:

```
Base de Datos:
  Host: localhost
  Puerto: 3306
  Nombre: tr069_acs
  Usuario: root
  Contraseña: (tu password de MySQL)

Configuración ACS:
  URL ACS: http://tu-servidor/acs.php
  Usuario ACS: acs_user
  Contraseña ACS: (elige una contraseña segura)

Usuario Admin:
  Usuario: admin
  Email: tu@email.com
  Contraseña: (tu contraseña de admin)
```

4. Clic en "🚀 Instalar TR-069 ACS"

### Paso 3: Acceder al Panel

1. Ve a: `http://tu-servidor/index.php`
2. Inicia sesión con tu usuario admin
3. ¡Listo! Ya puedes gestionar dispositivos

## 📱 Configurar Dispositivos CPE

En tu router/dispositivo TR-069, configura:

```
ACS URL: http://tu-servidor/acs.php
ACS Username: acs_user
ACS Password: (la que configuraste)
Periodic Inform: Habilitado
Inform Interval: 300 segundos
```

## 📊 ¿Qué Esperar?

Después de configurar un dispositivo:

1. **Primer Inform**: El dispositivo enviará su información automáticamente
2. **Registro**: Aparecerá en el panel de control
3. **Gestión**: Podrás ver sus parámetros, reiniciarlo, etc.

## 🔒 Post-Instalación (Recomendado)

```bash
# Proteger el instalador
chmod 000 install.php

# O eliminarlo
rm install.php

# Proteger la configuración
chmod 600 config.php
```

## 🐛 Problemas Comunes

### El dispositivo no aparece
- Verifica que la URL del ACS sea accesible
- Revisa logs: `tail -f logs/acs_*.log`
- Verifica credenciales del ACS

### Error de base de datos
- Verifica MySQL: `sudo systemctl status mysql`
- Verifica permisos del usuario MySQL

### No puedo escribir logs
```bash
chmod 755 logs
chown www-data:www-data logs
```

## 📖 Más Información

- **README completo**: Ver `README.md`
- **Soporte**: Revisar logs en `logs/`
- **Base de datos**: Acceder con cualquier cliente MySQL

## 🎯 URLs Importantes

- **Dashboard**: `http://tu-servidor/index.php`
- **Dispositivos**: `http://tu-servidor/devices.php`
- **ACS Endpoint**: `http://tu-servidor/acs.php` (para dispositivos)
- **Verificación**: `http://tu-servidor/check_requirements.php`

---

¡Disfruta de tu servidor TR-069! 🎉
