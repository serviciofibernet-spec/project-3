# Guía Rápida de Inicio

## 🚀 Inicio Rápido (5 minutos)

### Opción 1: Docker (Recomendado)

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd tr069-acs-server

# 2. Iniciar con Docker Compose
docker-compose up -d

# 3. Esperar a que los servicios estén listos (30 segundos)
docker-compose logs -f tr069-acs

# 4. Agregar datos de ejemplo
docker-compose exec tr069-acs python scripts/add_sample_data.py

# 5. ¡Listo! El servidor está corriendo
# Accede a: http://localhost:7547
```

### Opción 2: Instalación Manual

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd tr069-acs-server

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar base de datos MySQL
mysql -u root -p < database/schema.sql

# 5. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con tus credenciales

# 6. Agregar datos de ejemplo
python scripts/add_sample_data.py

# 7. Iniciar servidor
python app.py
```

## 📱 Primer Uso

### 1. Verificar instalación

```bash
# Con Docker
docker-compose exec tr069-acs python scripts/test_connection.py

# Sin Docker
python scripts/test_connection.py
```

### 2. Acceder a los paneles

- **Panel Admin**: http://localhost:7547/admin
  - Usuario: `admin`
  - Contraseña: `admin123`

- **Panel Cliente**: http://localhost:7547/client
  - Usuario: `cliente1`
  - Contraseña: `cliente123`

### 3. Configurar tu primera ONT

#### En la ONT Huawei (vía CLI o Web):

```
URL del ACS: http://tu-ip-servidor:7547/cwmp
Usuario: admin
Contraseña: admin123
Periodic Inform: Activado
Intervalo: 300 segundos
```

#### Vía Web de la ONT:
1. Acceder a http://192.168.100.1 (IP ONT)
2. Login: admin/admin (o credenciales del fabricante)
3. Ir a: Management → Device Management → TR-069 Configuration
4. Configurar:
   - ACS URL: `http://tu-servidor:7547/cwmp`
   - ACS Username: `admin`
   - ACS Password: `admin123`
   - Periodic Inform Enable: ☑️
   - Inform Interval: `300`
5. Guardar y aplicar

### 4. Verificar conexión

Después de 5 minutos (o reiniciar ONT), verifica:

```bash
# API
curl http://localhost:7547/api/admin/devices \
  -H "Authorization: Bearer admin-token"

# MySQL
mysql -u tr069_user -p tr069_acs
SELECT serial_number, status, last_inform FROM devices;
```

## 🎯 Operaciones Comunes

### Cambiar WiFi de una ONT

```bash
curl -X PUT http://localhost:7547/api/admin/devices/1/wifi \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "wifi_24": {
      "ssid": "MiWiFi-Nuevo",
      "password": "nuevapass123"
    }
  }'
```

### Reiniciar ONT remotamente

```bash
curl -X POST http://localhost:7547/api/admin/devices/1/reboot \
  -H "Authorization: Bearer admin-token"
```

### Ver diagnósticos

```bash
curl http://localhost:7547/api/monitoring/devices/1/diagnostics/latest
```

### Crear perfil de configuración

```bash
curl -X POST http://localhost:7547/api/admin/profiles \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Perfil Residencial",
    "model_filter": "HG8245H",
    "is_active": true,
    "configuration": {
      "wifi_24": {"enabled": true},
      "wifi_5": {"enabled": true},
      "dns": {"primary": "8.8.8.8", "secondary": "8.8.4.4"}
    }
  }'
```

## 🔧 Comandos Útiles

### Docker

```bash
# Ver logs
docker-compose logs -f tr069-acs

# Reiniciar servicio
docker-compose restart tr069-acs

# Ejecutar comando en contenedor
docker-compose exec tr069-acs python scripts/create_admin.py

# Acceder a MySQL
docker-compose exec mysql mysql -u tr069_user -ptr069pass tr069_acs

# Ver estado de servicios
docker-compose ps
```

### Base de Datos

```bash
# Backup
docker-compose exec mysql mysqldump -u tr069_user -ptr069pass tr069_acs > backup.sql

# Restore
docker-compose exec -T mysql mysql -u tr069_user -ptr069pass tr069_acs < backup.sql

# Ver dispositivos
docker-compose exec mysql mysql -u tr069_user -ptr069pass tr069_acs -e "SELECT serial_number, model, status FROM devices;"
```

## 🐛 Solución de Problemas

### ONT no aparece en el sistema

1. **Verificar conectividad**:
   ```bash
   # Desde el servidor
   telnet IP_ONT 7547
   ```

2. **Ver logs del servidor**:
   ```bash
   docker-compose logs -f tr069-acs | grep CWMP
   ```

3. **Verificar configuración TR-069 en ONT**:
   - URL correcta con http:// y puerto
   - Credenciales correctas
   - Periodic Inform activado

### Cambios no se aplican

1. **Verificar tareas pendientes**:
   ```bash
   curl http://localhost:7547/api/admin/tasks?status=pending \
     -H "Authorization: Bearer admin-token"
   ```

2. **Forzar conexión inmediata** (próxima versión):
   ```bash
   # Connection Request to device
   curl -X POST http://localhost:7547/api/admin/devices/1/connect
   ```

3. **Esperar próximo Inform** (5 minutos por defecto)

### Error de base de datos

```bash
# Verificar conexión
docker-compose exec tr069-acs python scripts/test_connection.py

# Recrear tablas
docker-compose exec mysql mysql -u tr069_user -ptr069pass tr069_acs < database/schema.sql
```

## 📈 Próximos Pasos

1. **Configurar SSL/TLS** para producción
2. **Implementar autenticación JWT** completa
3. **Configurar firewall** para limitar acceso
4. **Hacer backup automático** de base de datos
5. **Monitorear logs** con herramientas como ELK
6. **Escalar** con múltiples workers de Gunicorn

## 📚 Más Información

- [README.md](README.md) - Documentación completa
- [API Documentation](README.md#-api-documentation) - Referencia API
- [TR-069 Spec](https://www.broadband-forum.org/technical/download/TR-069.pdf) - Especificación oficial

## 💡 Consejos

- Mantén actualizado el firmware de las ONTs
- Usa contraseñas fuertes en producción
- Haz backups regulares de la base de datos
- Monitorea el uso de recursos del servidor
- Documenta las configuraciones personalizadas por cliente

---

**¿Necesitas ayuda?** Abre un issue en GitHub o consulta la documentación completa.
