"""
Simple Web Interface for TR-069 Server Management
Provides a basic HTML interface for monitoring and managing the server
"""

from aiohttp import web
from aiohttp.web_response import Response
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class WebInterface:
    """Simple web interface for TR-069 server management"""
    
    def __init__(self, server):
        self.server = server
    
    def setup_routes(self, app):
        """Setup web interface routes"""
        app.router.add_get('/admin', self.admin_dashboard)
        app.router.add_get('/admin/devices', self.devices_page)
        app.router.add_get('/admin/logs', self.logs_page)
        app.router.add_get('/admin/config', self.config_page)
        app.router.add_static('/static', 'static', name='static')
    
    async def admin_dashboard(self, request):
        """Main admin dashboard"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>TR-069 Server Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-item { text-align: center; }
        .stat-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .stat-label { color: #666; margin-top: 5px; }
        .nav { margin-bottom: 20px; }
        .nav a { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; }
        .nav a:hover { background-color: #2980b9; }
        .status-online { color: #27ae60; }
        .status-offline { color: #e74c3c; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .refresh-btn { background-color: #27ae60; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .refresh-btn:hover { background-color: #229954; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌐 TR-069 Server Dashboard</h1>
            <p>Auto Configuration Server (ACS) Management Interface</p>
        </div>
        
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/devices">Devices</a>
            <a href="/admin/logs">Logs</a>
            <a href="/admin/config">Configuration</a>
            <a href="/status">API Status</a>
        </div>
        
        <div class="card">
            <h2>Server Status</h2>
            <div class="stats" id="stats">
                <div class="stat-item">
                    <div class="stat-value" id="total-devices">-</div>
                    <div class="stat-label">Total Devices</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value status-online" id="online-devices">-</div>
                    <div class="stat-label">Online</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value status-offline" id="offline-devices">-</div>
                    <div class="stat-label">Offline</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="uptime">-</div>
                    <div class="stat-label">Uptime</div>
                </div>
            </div>
            <button class="refresh-btn" onclick="refreshStats()">🔄 Refresh</button>
        </div>
        
        <div class="card">
            <h2>Recent Devices</h2>
            <table id="recent-devices">
                <thead>
                    <tr>
                        <th>Serial Number</th>
                        <th>Manufacturer</th>
                        <th>Model</th>
                        <th>IP Address</th>
                        <th>Last Contact</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="6">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        async function refreshStats() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                document.getElementById('total-devices').textContent = data.connected_devices || 0;
                document.getElementById('online-devices').textContent = data.online_devices || 0;
                document.getElementById('offline-devices').textContent = data.offline_devices || 0;
                document.getElementById('uptime').textContent = 'Running';
                
                // Load recent devices
                const devicesResponse = await fetch('/devices');
                const devicesData = await devicesResponse.json();
                
                const tbody = document.querySelector('#recent-devices tbody');
                tbody.innerHTML = '';
                
                const devices = Object.values(devicesData).slice(0, 10); // Show last 10
                
                if (devices.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6">No devices found</td></tr>';
                } else {
                    devices.forEach(device => {
                        const row = document.createElement('tr');
                        const statusClass = device.status === 'online' ? 'status-online' : 'status-offline';
                        const lastContact = device.last_contact ? new Date(device.last_contact).toLocaleString() : 'Never';
                        
                        row.innerHTML = `
                            <td>${device.serial_number || 'Unknown'}</td>
                            <td>${device.manufacturer || 'Unknown'}</td>
                            <td>${device.model || 'Unknown'}</td>
                            <td>${device.ip_address || 'Unknown'}</td>
                            <td>${lastContact}</td>
                            <td class="${statusClass}">${device.status || 'Unknown'}</td>
                        `;
                        tbody.appendChild(row);
                    });
                }
            } catch (error) {
                console.error('Error refreshing stats:', error);
            }
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshStats, 30000);
        
        // Initial load
        refreshStats();
    </script>
</body>
</html>
        """
        return Response(text=html, content_type='text/html')
    
    async def devices_page(self, request):
        """Devices management page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>TR-069 Devices</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .nav { margin-bottom: 20px; }
        .nav a { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; }
        .nav a:hover { background-color: #2980b9; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .status-online { color: #27ae60; font-weight: bold; }
        .status-offline { color: #e74c3c; font-weight: bold; }
        .filter { margin-bottom: 20px; }
        .filter input, .filter select { padding: 8px; margin-right: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .device-details { display: none; background-color: #f8f9fa; padding: 10px; margin-top: 10px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 Device Management</h1>
            <p>Connected TR-069 CPE Devices</p>
        </div>
        
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/devices">Devices</a>
            <a href="/admin/logs">Logs</a>
            <a href="/admin/config">Configuration</a>
        </div>
        
        <div class="card">
            <div class="filter">
                <input type="text" id="search" placeholder="Search devices..." onkeyup="filterDevices()">
                <select id="status-filter" onchange="filterDevices()">
                    <option value="">All Status</option>
                    <option value="online">Online</option>
                    <option value="offline">Offline</option>
                </select>
                <button onclick="loadDevices()">🔄 Refresh</button>
            </div>
            
            <table id="devices-table">
                <thead>
                    <tr>
                        <th>Serial Number</th>
                        <th>Manufacturer</th>
                        <th>Model</th>
                        <th>Software Version</th>
                        <th>IP Address</th>
                        <th>Last Contact</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td colspan="8">Loading devices...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let allDevices = {};
        
        async function loadDevices() {
            try {
                const response = await fetch('/devices');
                allDevices = await response.json();
                displayDevices(allDevices);
            } catch (error) {
                console.error('Error loading devices:', error);
            }
        }
        
        function displayDevices(devices) {
            const tbody = document.querySelector('#devices-table tbody');
            tbody.innerHTML = '';
            
            const deviceList = Object.values(devices);
            
            if (deviceList.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8">No devices found</td></tr>';
                return;
            }
            
            deviceList.forEach(device => {
                const row = document.createElement('tr');
                const statusClass = device.status === 'online' ? 'status-online' : 'status-offline';
                const lastContact = device.last_contact ? new Date(device.last_contact).toLocaleString() : 'Never';
                
                row.innerHTML = `
                    <td>${device.serial_number || 'Unknown'}</td>
                    <td>${device.manufacturer || 'Unknown'}</td>
                    <td>${device.model || 'Unknown'}</td>
                    <td>${device.software_version || 'Unknown'}</td>
                    <td>${device.ip_address || 'Unknown'}</td>
                    <td>${lastContact}</td>
                    <td class="${statusClass}">${device.status || 'Unknown'}</td>
                    <td>
                        <button onclick="showDeviceDetails('${device.serial_number}')">Details</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function filterDevices() {
            const search = document.getElementById('search').value.toLowerCase();
            const statusFilter = document.getElementById('status-filter').value;
            
            const filtered = {};
            
            for (const [key, device] of Object.entries(allDevices)) {
                const matchesSearch = !search || 
                    device.serial_number.toLowerCase().includes(search) ||
                    device.manufacturer.toLowerCase().includes(search) ||
                    device.model.toLowerCase().includes(search) ||
                    device.ip_address.toLowerCase().includes(search);
                
                const matchesStatus = !statusFilter || device.status === statusFilter;
                
                if (matchesSearch && matchesStatus) {
                    filtered[key] = device;
                }
            }
            
            displayDevices(filtered);
        }
        
        function showDeviceDetails(serialNumber) {
            const device = allDevices[serialNumber];
            if (device) {
                alert(`Device Details:\\n\\nSerial: ${device.serial_number}\\nManufacturer: ${device.manufacturer}\\nModel: ${device.model}\\nSoftware: ${device.software_version}\\nHardware: ${device.hardware_version}\\nIP: ${device.ip_address}\\nStatus: ${device.status}\\nParameters: ${device.parameter_count}\\nEvents: ${device.events.join(', ')}`);
            }
        }
        
        // Auto-refresh every 60 seconds
        setInterval(loadDevices, 60000);
        
        // Initial load
        loadDevices();
    </script>
</body>
</html>
        """
        return Response(text=html, content_type='text/html')
    
    async def logs_page(self, request):
        """Logs viewing page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>TR-069 Server Logs</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .nav { margin-bottom: 20px; }
        .nav a { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; }
        .nav a:hover { background-color: #2980b9; }
        .log-container { background-color: #2c3e50; color: #ecf0f1; padding: 20px; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 12px; max-height: 600px; overflow-y: auto; }
        .log-line { margin-bottom: 5px; }
        .log-error { color: #e74c3c; }
        .log-warning { color: #f39c12; }
        .log-info { color: #3498db; }
        .log-debug { color: #95a5a6; }
        .controls { margin-bottom: 20px; }
        .controls button, .controls select { padding: 8px 16px; margin-right: 10px; border: none; border-radius: 4px; cursor: pointer; }
        .controls button { background-color: #27ae60; color: white; }
        .controls button:hover { background-color: #229954; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 Server Logs</h1>
            <p>Real-time TR-069 Server Log Monitoring</p>
        </div>
        
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/devices">Devices</a>
            <a href="/admin/logs">Logs</a>
            <a href="/admin/config">Configuration</a>
        </div>
        
        <div class="card">
            <div class="controls">
                <button onclick="refreshLogs()">🔄 Refresh</button>
                <button onclick="clearLogs()">🗑️ Clear Display</button>
                <select id="log-level">
                    <option value="">All Levels</option>
                    <option value="ERROR">Error</option>
                    <option value="WARNING">Warning</option>
                    <option value="INFO">Info</option>
                    <option value="DEBUG">Debug</option>
                </select>
                <button onclick="toggleAutoRefresh()" id="auto-refresh-btn">⏸️ Stop Auto-refresh</button>
            </div>
            
            <div class="log-container" id="log-container">
                <div class="log-line">Loading logs...</div>
            </div>
        </div>
    </div>
    
    <script>
        let autoRefreshInterval;
        let autoRefreshEnabled = true;
        
        function refreshLogs() {
            // Simulate log loading (in real implementation, this would fetch from server)
            const logContainer = document.getElementById('log-container');
            const now = new Date().toISOString();
            
            const sampleLogs = [
                `${now} - tr069_server - INFO - Server started on 0.0.0.0:7547`,
                `${now} - tr069_server - INFO - Device registered: CPE_001234`,
                `${now} - device_manager - INFO - Inform received from device: CPE_001234`,
                `${now} - cwmp_handlers - DEBUG - Processing GetParameterValues request`,
                `${now} - auth_security - WARNING - Failed login attempt from 192.168.1.100`,
                `${now} - tr069_server - ERROR - Connection timeout for device CPE_005678`
            ];
            
            logContainer.innerHTML = '';
            
            sampleLogs.forEach(log => {
                const div = document.createElement('div');
                div.className = 'log-line';
                
                if (log.includes('ERROR')) {
                    div.className += ' log-error';
                } else if (log.includes('WARNING')) {
                    div.className += ' log-warning';
                } else if (log.includes('INFO')) {
                    div.className += ' log-info';
                } else if (log.includes('DEBUG')) {
                    div.className += ' log-debug';
                }
                
                div.textContent = log;
                logContainer.appendChild(div);
            });
            
            // Scroll to bottom
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        function clearLogs() {
            document.getElementById('log-container').innerHTML = '<div class="log-line">Logs cleared</div>';
        }
        
        function toggleAutoRefresh() {
            const btn = document.getElementById('auto-refresh-btn');
            
            if (autoRefreshEnabled) {
                clearInterval(autoRefreshInterval);
                btn.textContent = '▶️ Start Auto-refresh';
                autoRefreshEnabled = false;
            } else {
                autoRefreshInterval = setInterval(refreshLogs, 5000);
                btn.textContent = '⏸️ Stop Auto-refresh';
                autoRefreshEnabled = true;
            }
        }
        
        // Start auto-refresh
        autoRefreshInterval = setInterval(refreshLogs, 5000);
        
        // Initial load
        refreshLogs();
    </script>
</body>
</html>
        """
        return Response(text=html, content_type='text/html')
    
    async def config_page(self, request):
        """Configuration page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>TR-069 Configuration</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .nav { margin-bottom: 20px; }
        .nav a { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 4px; margin-right: 10px; }
        .nav a:hover { background-color: #2980b9; }
        .config-section { margin-bottom: 30px; }
        .config-section h3 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        .form-group input[type="checkbox"] { width: auto; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        .btn-primary { background-color: #3498db; color: white; }
        .btn-success { background-color: #27ae60; color: white; }
        .btn-danger { background-color: #e74c3c; color: white; }
        .btn:hover { opacity: 0.9; }
        .alert { padding: 15px; margin-bottom: 20px; border-radius: 4px; }
        .alert-success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-danger { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚙️ Server Configuration</h1>
            <p>TR-069 Server Settings and Configuration</p>
        </div>
        
        <div class="nav">
            <a href="/admin">Dashboard</a>
            <a href="/admin/devices">Devices</a>
            <a href="/admin/logs">Logs</a>
            <a href="/admin/config">Configuration</a>
        </div>
        
        <div id="alert-container"></div>
        
        <div class="card">
            <div class="config-section">
                <h3>Server Settings</h3>
                <div class="form-group">
                    <label>Host Address:</label>
                    <input type="text" id="host" value="0.0.0.0" placeholder="0.0.0.0">
                </div>
                <div class="form-group">
                    <label>Port:</label>
                    <input type="number" id="port" value="7547" min="1" max="65535">
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="ssl-enabled"> Enable SSL/HTTPS
                    </label>
                </div>
                <div class="form-group">
                    <label>SSL Certificate Path:</label>
                    <input type="text" id="ssl-cert" placeholder="/path/to/certificate.pem">
                </div>
                <div class="form-group">
                    <label>SSL Key Path:</label>
                    <input type="text" id="ssl-key" placeholder="/path/to/private_key.pem">
                </div>
            </div>
            
            <div class="config-section">
                <h3>Logging Settings</h3>
                <div class="form-group">
                    <label>Log Level:</label>
                    <select id="log-level">
                        <option value="DEBUG">Debug</option>
                        <option value="INFO" selected>Info</option>
                        <option value="WARNING">Warning</option>
                        <option value="ERROR">Error</option>
                        <option value="CRITICAL">Critical</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Log File Path:</label>
                    <input type="text" id="log-file" value="logs/tr069_server.log">
                </div>
                <div class="form-group">
                    <label>Max Log File Size:</label>
                    <input type="text" id="log-max-size" value="10MB" placeholder="10MB">
                </div>
            </div>
            
            <div class="config-section">
                <h3>Security Settings</h3>
                <div class="form-group">
                    <label>Max Failed Login Attempts:</label>
                    <input type="number" id="max-failed-attempts" value="5" min="1" max="100">
                </div>
                <div class="form-group">
                    <label>IP Block Duration (minutes):</label>
                    <input type="number" id="block-duration" value="15" min="1" max="1440">
                </div>
                <div class="form-group">
                    <label>Session Timeout (hours):</label>
                    <input type="number" id="session-timeout" value="24" min="1" max="168">
                </div>
            </div>
            
            <div class="config-section">
                <button class="btn btn-success" onclick="saveConfig()">💾 Save Configuration</button>
                <button class="btn btn-primary" onclick="loadConfig()">🔄 Reload</button>
                <button class="btn btn-danger" onclick="resetConfig()">🔄 Reset to Defaults</button>
            </div>
        </div>
    </div>
    
    <script>
        function showAlert(message, type = 'success') {
            const alertContainer = document.getElementById('alert-container');
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            
            alertContainer.innerHTML = '';
            alertContainer.appendChild(alert);
            
            setTimeout(() => {
                alertContainer.innerHTML = '';
            }, 5000);
        }
        
        function loadConfig() {
            // In a real implementation, this would fetch from the server
            showAlert('Configuration loaded successfully');
        }
        
        function saveConfig() {
            // Validate inputs
            const port = document.getElementById('port').value;
            if (port < 1 || port > 65535) {
                showAlert('Invalid port number. Must be between 1 and 65535.', 'danger');
                return;
            }
            
            const maxAttempts = document.getElementById('max-failed-attempts').value;
            if (maxAttempts < 1) {
                showAlert('Max failed attempts must be at least 1.', 'danger');
                return;
            }
            
            // Simulate saving configuration
            showAlert('Configuration saved successfully! Restart the server to apply changes.');
        }
        
        function resetConfig() {
            if (confirm('Are you sure you want to reset all settings to defaults?')) {
                document.getElementById('host').value = '0.0.0.0';
                document.getElementById('port').value = '7547';
                document.getElementById('ssl-enabled').checked = false;
                document.getElementById('ssl-cert').value = '';
                document.getElementById('ssl-key').value = '';
                document.getElementById('log-level').value = 'INFO';
                document.getElementById('log-file').value = 'logs/tr069_server.log';
                document.getElementById('log-max-size').value = '10MB';
                document.getElementById('max-failed-attempts').value = '5';
                document.getElementById('block-duration').value = '15';
                document.getElementById('session-timeout').value = '24';
                
                showAlert('Configuration reset to defaults');
            }
        }
        
        // Initial load
        loadConfig();
    </script>
</body>
</html>
        """
        return Response(text=html, content_type='text/html')