// Admin Panel JavaScript
class AdminPanel {
    constructor() {
        this.token = localStorage.getItem('adminToken');
        this.currentUser = null;
        this.init();
    }

    init() {
        // Check if user is logged in
        if (this.token) {
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

        // Navigation
        document.querySelectorAll('.nav-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.showSection(e.target.dataset.section);
                this.updateActiveNav(e.target);
            });
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
                this.loadDashboard();
            } else {
                this.showLogin();
            }
        } catch (error) {
            console.error('Token verification failed:', error);
            this.showLogin();
        }
    }

    async handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });

            const data = await response.json();

            if (data.success) {
                this.token = data.data.token;
                this.currentUser = data.data.user;
                localStorage.setItem('adminToken', this.token);
                this.showMainApp();
                this.loadDashboard();
            } else {
                this.showError(data.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showError('Network error. Please try again.');
        }
    }

    handleLogout() {
        localStorage.removeItem('adminToken');
        this.token = null;
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
        document.getElementById('currentUser').textContent = this.currentUser.username;
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.add('d-none');
        });

        // Show selected section
        const section = document.getElementById(`${sectionName}Section`);
        if (section) {
            section.classList.remove('d-none');
        }

        // Update page title
        const titles = {
            dashboard: 'Dashboard',
            devices: 'Dispositivos',
            clients: 'Clientes',
            profiles: 'Perfiles',
            monitoring: 'Monitoreo',
            logs: 'Logs'
        };
        document.getElementById('pageTitle').textContent = titles[sectionName] || sectionName;

        // Load section data
        switch (sectionName) {
            case 'dashboard':
                this.loadDashboard();
                break;
            case 'devices':
                this.loadDevices();
                break;
            case 'clients':
                this.loadClients();
                break;
            case 'profiles':
                this.loadProfiles();
                break;
            case 'monitoring':
                this.loadMonitoring();
                break;
            case 'logs':
                this.loadLogs();
                break;
        }
    }

    updateActiveNav(activeLink) {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }

    async loadDashboard() {
        try {
            // Load dashboard stats
            const [devicesResponse, clientsResponse] = await Promise.all([
                fetch('/api/devices', { headers: { 'Authorization': `Bearer ${this.token}` } }),
                fetch('/api/clients', { headers: { 'Authorization': `Bearer ${this.token}` } })
            ]);

            if (devicesResponse.ok && clientsResponse.ok) {
                const devicesData = await devicesResponse.json();
                const clientsData = await clientsResponse.json();

                const devices = devicesData.data || [];
                const clients = clientsData.data || [];

                // Update stats
                document.getElementById('totalDevices').textContent = devices.length;
                document.getElementById('onlineDevices').textContent = 
                    devices.filter(d => d.status === 'online').length;
                document.getElementById('totalClients').textContent = clients.length;
                document.getElementById('pendingTasks').textContent = '0'; // TODO: Implement

                // Update recent devices table
                this.updateRecentDevicesTable(devices.slice(0, 5));
            }
        } catch (error) {
            console.error('Error loading dashboard:', error);
        }
    }

    updateRecentDevicesTable(devices) {
        const tbody = document.getElementById('recentDevicesTable');
        
        if (devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay dispositivos</td></tr>';
            return;
        }

        tbody.innerHTML = devices.map(device => `
            <tr>
                <td>${device.serial_number}</td>
                <td>${device.model || 'N/A'}</td>
                <td>
                    <span class="badge ${this.getStatusBadgeClass(device.status)}">
                        ${this.getStatusText(device.status)}
                    </span>
                </td>
                <td>${this.formatDate(device.last_inform)}</td>
            </tr>
        `).join('');
    }

    async loadDevices() {
        try {
            const response = await fetch('/api/devices', {
                headers: { 'Authorization': `Bearer ${this.token}` }
            });

            if (response.ok) {
                const data = await response.json();
                this.updateDevicesTable(data.data || []);
            }
        } catch (error) {
            console.error('Error loading devices:', error);
        }
    }

    updateDevicesTable(devices) {
        const tbody = document.getElementById('devicesTable');
        
        if (devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">No hay dispositivos registrados</td></tr>';
            return;
        }

        tbody.innerHTML = devices.map(device => `
            <tr>
                <td>${device.serial_number}</td>
                <td>${device.model || 'N/A'}</td>
                <td>${device.client_name || 'Sin asignar'}</td>
                <td>
                    <span class="badge ${this.getStatusBadgeClass(device.status)}">
                        ${this.getStatusText(device.status)}
                    </span>
                </td>
                <td>${device.ip_address || 'N/A'}</td>
                <td>${this.formatDate(device.last_inform)}</td>
                <td>
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary" onclick="adminPanel.viewDevice(${device.id})">
                            <i class="bi bi-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-warning" onclick="adminPanel.rebootDevice(${device.id})">
                            <i class="bi bi-arrow-clockwise"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-info" onclick="adminPanel.configureDevice(${device.id})">
                            <i class="bi bi-gear"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }

    async loadClients() {
        // TODO: Implement clients loading
        console.log('Loading clients...');
    }

    async loadProfiles() {
        // TODO: Implement profiles loading
        console.log('Loading profiles...');
    }

    async loadMonitoring() {
        // TODO: Implement monitoring loading
        console.log('Loading monitoring...');
    }

    async loadLogs() {
        // TODO: Implement logs loading
        console.log('Loading logs...');
    }

    // Device actions
    async viewDevice(deviceId) {
        // TODO: Implement device view modal
        console.log('Viewing device:', deviceId);
    }

    async rebootDevice(deviceId) {
        if (confirm('¿Está seguro de que desea reiniciar este dispositivo?')) {
            try {
                const response = await fetch(`/api/devices/${deviceId}/reboot`, {
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${this.token}` }
                });

                const data = await response.json();
                if (data.success) {
                    this.showSuccess('Reinicio programado correctamente');
                } else {
                    this.showError(data.error || 'Error al programar reinicio');
                }
            } catch (error) {
                console.error('Error rebooting device:', error);
                this.showError('Error de red');
            }
        }
    }

    async configureDevice(deviceId) {
        // TODO: Implement device configuration modal
        console.log('Configuring device:', deviceId);
    }

    // Utility methods
    getStatusBadgeClass(status) {
        const classes = {
            online: 'bg-success',
            offline: 'bg-danger',
            configuring: 'bg-warning',
            error: 'bg-danger'
        };
        return classes[status] || 'bg-secondary';
    }

    getStatusText(status) {
        const texts = {
            online: 'En línea',
            offline: 'Desconectado',
            configuring: 'Configurando',
            error: 'Error'
        };
        return texts[status] || status;
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString('es-ES');
    }

    showError(message) {
        // TODO: Implement proper error display
        alert('Error: ' + message);
    }

    showSuccess(message) {
        // TODO: Implement proper success display
        alert('Éxito: ' + message);
    }
}

// Global functions
function refreshDevices() {
    adminPanel.loadDevices();
}

// Initialize admin panel
const adminPanel = new AdminPanel();