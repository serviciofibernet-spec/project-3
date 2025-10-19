#!/bin/bash

# TR069 Huawei ONT Management Server Installation Script

echo "=========================================="
echo "TR069 Huawei ONT Management Server Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
check_nodejs() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_status "Node.js is installed: $NODE_VERSION"
        
        # Check if version is >= 16
        MAJOR_VERSION=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
        if [ "$MAJOR_VERSION" -lt 16 ]; then
            print_error "Node.js version 16 or higher is required. Current version: $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js is not installed. Please install Node.js 16 or higher."
        exit 1
    fi
}

# Check if MySQL is installed and running
check_mysql() {
    if command -v mysql &> /dev/null; then
        print_status "MySQL client is installed"
        
        # Try to connect to MySQL
        if mysql -u root -p -e "SELECT VERSION();" &> /dev/null; then
            print_status "MySQL server is accessible"
        else
            print_warning "Cannot connect to MySQL server. Please ensure MySQL is running and accessible."
        fi
    else
        print_error "MySQL is not installed. Please install MySQL server."
        exit 1
    fi
}

# Install Node.js dependencies
install_dependencies() {
    print_status "Installing Node.js dependencies..."
    
    if npm install; then
        print_status "Dependencies installed successfully"
    else
        print_error "Failed to install dependencies"
        exit 1
    fi
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f .env ]; then
        cp .env.example .env
        print_status "Created .env file from template"
        print_warning "Please edit .env file with your configuration before starting the server"
    else
        print_warning ".env file already exists. Please verify your configuration."
    fi
}

# Setup database
setup_database() {
    print_status "Setting up database..."
    
    echo "Please enter your MySQL root password to create the database:"
    read -s MYSQL_ROOT_PASSWORD
    
    # Create database and user
    mysql -u root -p$MYSQL_ROOT_PASSWORD << EOF
CREATE DATABASE IF NOT EXISTS tr069_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'tr069_user'@'localhost' IDENTIFIED BY 'tr069_password';
GRANT ALL PRIVILEGES ON tr069_db.* TO 'tr069_user'@'localhost';
FLUSH PRIVILEGES;
EOF

    if [ $? -eq 0 ]; then
        print_status "Database and user created successfully"
        
        # Run migrations
        print_status "Running database migrations..."
        npm run migrate
        npm run migrate:assignment
        
        if [ $? -eq 0 ]; then
            print_status "Database migrations completed successfully"
        else
            print_error "Database migration failed"
            exit 1
        fi
    else
        print_error "Failed to create database"
        exit 1
    fi
}

# Create systemd service (optional)
create_service() {
    read -p "Do you want to create a systemd service for auto-start? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Creating systemd service..."
        
        CURRENT_DIR=$(pwd)
        USER=$(whoami)
        
        sudo tee /etc/systemd/system/tr069-acs.service > /dev/null << EOF
[Unit]
Description=TR069 ACS Server
After=network.target mysql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/node src/server.js
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

        sudo systemctl daemon-reload
        sudo systemctl enable tr069-acs
        
        print_status "Systemd service created and enabled"
        print_status "You can start the service with: sudo systemctl start tr069-acs"
    fi
}

# Create logs directory
create_logs_dir() {
    print_status "Creating logs directory..."
    mkdir -p logs
    print_status "Logs directory created"
}

# Main installation process
main() {
    print_status "Starting TR069 ACS Server installation..."
    
    # Check prerequisites
    check_nodejs
    check_mysql
    
    # Install and setup
    install_dependencies
    setup_environment
    create_logs_dir
    
    # Database setup
    read -p "Do you want to set up the database now? (y/n): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_database
    else
        print_warning "Database setup skipped. Run 'npm run migrate' and 'npm run migrate:assignment' manually after configuring your database."
    fi
    
    # Optional service creation
    create_service
    
    print_status "Installation completed!"
    echo
    echo "=========================================="
    echo "Next Steps:"
    echo "=========================================="
    echo "1. Edit .env file with your configuration"
    echo "2. If you skipped database setup, run:"
    echo "   npm run migrate"
    echo "   npm run migrate:assignment"
    echo "3. Start the server:"
    echo "   npm start (production)"
    echo "   npm run dev (development)"
    echo
    echo "Default admin credentials:"
    echo "Username: admin"
    echo "Password: admin123"
    echo
    echo "Server will be available at:"
    echo "- ACS Endpoint: http://localhost:7547/acs"
    echo "- Admin Panel: http://localhost:7547/admin"
    echo "- Client Portal: http://localhost:7547/client"
    echo "- API Docs: http://localhost:7547/api/docs"
    echo "=========================================="
}

# Run main function
main