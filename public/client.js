// Client Portal JavaScript
class ClientPortal {
    constructor() {
        this.token = localStorage.getItem('clientToken');
        this.clientId = localStorage.getItem('clientId');
        this.currentClient = null;
        this.devices = [];
        this.init();
    }

    init() {
        // Check if user is logged in
        if (this.token && this.clientId) {
            this.verifyToken();
        } else {
            this.showLogin();
        }

        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Logout button
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.handleLogout();
        });

        // WiFi form
        document.getElementById('wifiForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleWiFiUpdate();
        });
    }

    async verifyToken() {
        try {
            const response = await fetch('/api/auth/verify', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.data.user;
                this.showMainApp();
                this.loadClientData();
            } else {
                this.showLogin();
            }
        } catch (error) {
            console.error('Token verification failed:', error);
            this.showLogin();
        }
    }

    async handleLogin() {
        const clientCode = document.getElementById('clientCode').value;
        const password = document.getElementById('password').value;

        try {
            // First, authenticate with the system
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    username: clientCode, // Using client code as username
                    password 
                })
            });

            const data = await response.json();

            if (data.success) {
                this.token = data.data.token;
                this.currentUser = data.data.user;
                
                // Get client ID from user data
                const profileResponse = await fetch('/api/auth/profile', {
                    headers: {
                        'Authorization': `Bearer ${this.token}`
                    }
                });

                if (profileResponse.ok) {
                    const profileData = await profileResponse.json();
                    this.clientId = profileData.data.client_id;
                    
                    if (this.clientId) {
                        localStorage.setItem('clientToken', this.token);
                        localStorage.setItem('clientId', this.clientId);
                        this.showMainApp();
                        this.loadClientData();
                    } else {
                        this.showError('No se encontró información de cliente asociada');
                    }
                } else {
                    this.showError('Error al obtener información del perfil');
                }
            } else {
                this.showError(data.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Error de red. Por favor intente nuevamente.');
        }
    }

    handleLogout() {
        localStorage.removeItem('clientToken');
        localStorage.removeItem('clientId');
        this.token = null;
        this.clientId = null;
        this.currentUser = null;
        this.showLogin();
    }

    showLogin() {
        document.getElementById('loginScreen').classList.remove('d-none');
        document.getElementById('mainApp').classList.add('d-none');
    }

    showMainApp() {
        document.getElementById('loginScreen').classList.add('d-none');
        document.getElementById('mainApp').classList.remove('d-none');
    }

    async loadClientData() {
        try {
            const response = await fetch(`/api/clients/${this.clientId}/dashboard`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentClient = data.data.client;
                this.devices = data.data.devices || [];
                
                this.updateClientInfo();
                this.updateDevicesDisplay();
            } else {
                this.showError('Error al cargar datos del cliente');
            }
        } catch (error) {
            console.error('Error loading client data:', error);
            this.showError('Error de conexión');
        }
    }

    updateClientInfo() {
        if (this.currentClient) {
            document.getElementById('currentClient').textContent = this.currentClient.name;
            document.getElementById('clientName').textContent = this.currentClient.name;
            document.getElementById('clientInfo').textContent = 
                `Código: ${this.currentClient.client_code} | Plan: ${this.currentClient.service_plan || 'N/A'}`;
        }
    }

    updateDevicesDisplay() {
        const container = document.getElementById('devicesContainer');
        
        if (this.devices.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center">
                    <div class="card">
                        <div class="card-body py-5">
                            <i class="bi bi-router text-muted" style="font-size: 3rem;"></i>
                            <h5 class="mt-3">No hay dispositivos asignados</h5>
                            <p class="text-muted">Contacta a soporte técnico para asignar dispositivos a tu cuenta.</p>
                        </div>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = this.devices.map(device => this.createDeviceCard(device)).join('');
    }

    createDeviceCard(device) {
        const monitoring = device.monitoring || {};
        const isOnline = device.status === 'online';
        
        return `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card device-card h-100">
                    <div class="card-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <h6 class="mb-0">
                                <i class="bi bi-router me-2"></i>${device.model || 'ONT'}
                            </h6>
                            <span class="badge ${isOnline ? 'bg-success' : 'bg-danger'}">
                                ${isOnline ? 'En línea' : 'Desconectado'}
                            </span>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="row g-3">
                            <div class="col-6">
                                <div class="metric-card p-3 rounded">
                                    <div class="d-flex align-items-center">
                                        <i class="bi bi-wifi text-primary me-2"></i>
                                        <div>
                                            <small class="text-muted">Dispositivos WiFi</small>
                                            <div class="fw-bold">${monitoring.total_wifi_clients || 0}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="metric-card p-3 rounded">
                                    <div class="d-flex align-items-center">
                                        <i class="bi bi-speedometer2 text-info me-2"></i>
                                        <div>
                                            <small class="text-muted">Señal Óptica</small>
                                            <div class="fw-bold">${monitoring.optical_power || 'N/A'} dBm</div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                <i class="bi bi-clock me-1"></i>
                                Última conexión: ${this.formatDate(device.last_inform)}
                            </small>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <div class="d-grid gap-2 d-md-flex">
                            <button class="btn btn-primary btn-sm flex-fill" 
                                    onclick="clientPortal.showWiFiModal(${device.id})"
                                    ${!isOnline ? 'disabled' : ''}>
                                <i class="bi bi-wifi me-1"></i>Configurar WiFi
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" 
                                    onclick="clientPortal.showDeviceDetails(${device.id})">
                                <i class="bi bi-info-circle me-1"></i>Detalles
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    async showWiFiModal(deviceId) {
        const device = this.devices.find(d => d.id === deviceId);
        if (!device) return;

        // Load current WiFi configuration
        try {
            const response = await fetch(`/api/clients/${this.clientId}/devices/${deviceId}/status`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                const wifiConfig = data.data.wifiConfig || {};
                
                // Populate form
                document.getElementById('ssid24').value = wifiConfig.ssid_2_4ghz || '';
                document.getElementById('password24').value = wifiConfig.password_2_4ghz || '';
                document.getElementById('ssid5').value = wifiConfig.ssid_5ghz || '';
                document.getElementById('password5').value = wifiConfig.password_5ghz || '';
                
                // Store device ID for form submission
                document.getElementById('wifiForm').dataset.deviceId = deviceId;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('wifiModal'));
                modal.show();
            }
        } catch (error) {
            console.error('Error loading WiFi config:', error);
            this.showError('Error al cargar configuración WiFi');
        }
    }

    async handleWiFiUpdate() {
        const deviceId = document.getElementById('wifiForm').dataset.deviceId;
        const wifiSettings = {
            ssid_2_4ghz: document.getElementById('ssid24').value,
            password_2_4ghz: document.getElementById('password24').value,
            ssid_5ghz: document.getElementById('ssid5').value,
            password_5ghz: document.getElementById('password5').value
        };

        try {
            const response = await fetch(`/api/clients/${this.clientId}/wifi`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    deviceId: parseInt(deviceId),
                    wifiSettings
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Configuración WiFi actualizada. Los cambios se aplicarán en unos momentos.');
                
                // Hide modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('wifiModal'));
                modal.hide();
                
                // Refresh data
                setTimeout(() => {
                    this.refreshData();
                }, 2000);
            } else {
                this.showError(data.error || 'Error al actualizar configuración WiFi');
            }
        } catch (error) {
            console.error('Error updating WiFi:', error);
            this.showError('Error de conexión');
        }
    }

    async showDeviceDetails(deviceId) {
        const device = this.devices.find(d => d.id === deviceId);
        if (!device) return;

        try {
            const response = await fetch(`/api/clients/${this.clientId}/devices/${deviceId}/status`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.displayDeviceDetails(data.data);
                
                const modal = new bootstrap.Modal(document.getElementById('deviceModal'));
                modal.show();
            }
        } catch (error) {
            console.error('Error loading device details:', error);
            this.showError('Error al cargar detalles del dispositivo');
        }
    }

    displayDeviceDetails(deviceData) {
        const device = deviceData.device;
        const monitoring = deviceData.monitoring || {};
        const connectedDevices = deviceData.connectedDevices || [];

        const detailsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Información del Dispositivo</h6>
                    <table class="table table-sm">
                        <tr><td>Número de Serie:</td><td>${device.serial_number}</td></tr>
                        <tr><td>Modelo:</td><td>${device.model || 'N/A'}</td></tr>
                        <tr><td>Estado:</td><td>
                            <span class="badge ${device.status === 'online' ? 'bg-success' : 'bg-danger'}">
                                ${device.status === 'online' ? 'En línea' : 'Desconectado'}
                            </span>
                        </td></tr>
                        <tr><td>Última Conexión:</td><td>${this.formatDate(device.last_inform)}</td></tr>
                    </table>
                </div>
                <div class="col-md-6">
                    <h6>Monitoreo</h6>
                    <table class="table table-sm">
                        <tr><td>Potencia Óptica:</td><td>${monitoring.optical_power || 'N/A'} dBm</td></tr>
                        <tr><td>Temperatura:</td><td>${monitoring.temperature || 'N/A'}°C</td></tr>
                        <tr><td>Uso de CPU:</td><td>${monitoring.cpu_usage || 'N/A'}%</td></tr>
                        <tr><td>Uso de Memoria:</td><td>${monitoring.memory_usage || 'N/A'}%</td></tr>
                    </table>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <h6>Dispositivos Conectados (${connectedDevices.length})</h6>
                    ${connectedDevices.length > 0 ? `
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Dispositivo</th>
                                        <th>IP</th>
                                        <th>Conexión</th>
                                        <th>Conectado desde</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${connectedDevices.map(dev => `
                                        <tr>
                                            <td>${dev.hostname || dev.mac_address}</td>
                                            <td>${dev.ip_address || 'N/A'}</td>
                                            <td>
                                                <span class="badge bg-info">
                                                    ${dev.connection_type.replace('_', ' ').toUpperCase()}
                                                </span>
                                            </td>
                                            <td>${this.formatDate(dev.connected_at)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    ` : '<p class="text-muted">No hay dispositivos conectados</p>'}
                </div>
            </div>
        `;

        document.getElementById('deviceDetails').innerHTML = detailsHtml;
    }

    async refreshData() {
        await this.loadClientData();
        this.showSuccess('Datos actualizados');
    }

    // Utility methods
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('es-ES');
    }

    showError(message) {
        // Create toast notification
        this.showToast(message, 'danger');
    }

    showSuccess(message) {
        // Create toast notification
        this.showToast(message, 'success');
    }

    showToast(message, type) {
        // Simple toast implementation
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        // Add toast container if it doesn't exist
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Add toast
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        toastContainer.appendChild(toastElement.firstElementChild);
        
        // Show toast
        const toast = new bootstrap.Toast(toastContainer.lastElementChild);
        toast.show();
        
        // Remove toast element after hiding
        toastContainer.lastElementChild.addEventListener('hidden.bs.toast', () => {
            toastContainer.removeChild(toastContainer.lastElementChild);
        });
    }
}

// Global functions
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const button = input.nextElementSibling;
    const icon = button.querySelector('i');
    
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

// Initialize client portal
const clientPortal = new ClientPortal();