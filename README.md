# TR069 Huawei ONT Management Server

A comprehensive TR069 ACS (Auto Configuration Server) for managing Huawei ONT devices with advanced features including automatic configuration, monitoring, and client self-service portals.

## Features

### Device Management
- Change SSID and WiFi passwords remotely
- Configure DNS, VLAN, PPPoE settings
- Manage WiFi 2.4/5 GHz parameters
- Remote reboot and firmware updates

### Monitoring & Diagnostics
- Optical power monitoring (dBm)
- Connection status tracking
- Signal level monitoring
- Connected WiFi devices count

### Automation
- Automatic configuration profiles
- Auto-assignment to clients
- Mass configuration deployment
- Profile-based setup on first connection

### Client Portal
- Self-service WiFi management
- Real-time device status
- Configuration history
- User-friendly interface

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Set up MySQL database:
   ```bash
   npm run migrate
   ```

5. Start the server:
   ```bash
   npm run dev  # Development
   npm start    # Production
   ```

## API Endpoints

### TR069 ACS
- `POST /acs` - TR069 CWMP endpoint
- `GET /acs/devices` - List managed devices
- `POST /acs/configure` - Apply configuration

### Client Portal
- `GET /client/:id` - Client dashboard
- `POST /client/:id/wifi` - Update WiFi settings
- `GET /client/:id/status` - Device status

### Admin Panel
- `GET /admin` - Admin dashboard
- `POST /admin/profiles` - Manage profiles
- `GET /admin/monitoring` - System monitoring

## Database Schema

The system uses MySQL with tables for:
- `devices` - ONT device information
- `clients` - Customer information
- `configurations` - Device configurations
- `profiles` - Configuration profiles
- `monitoring` - Device monitoring data
- `users` - System users

## License

MIT License