def generate_iran_script(tunnel_port):
    """Generate Chisel server installation script for Iran server"""
    script = f'''#!/bin/bash

# Chisel Tunnel Installation Script for Iran Server
# This script installs and configures Chisel server on Iran server

set -e

echo "=============================================="
echo "    Chisel Server Installation (Iran)"
echo "=============================================="
echo ""

# Colors for output
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m' # No Color

# Function to print colored output
print_success() {{
    echo -e "${{GREEN}}✓ $1${{NC}}"
}}

print_info() {{
    echo -e "${{YELLOW}}ℹ️ $1${{NC}}"
}}

print_error() {{
    echo -e "${{RED}}✗ $1${{NC}}"
}}

# Update system
print_info "Updating system packages..."
apt-get update -qq

# Install required packages
print_info "Installing required packages..."
apt-get install -y wget curl sudo screen > /dev/null 2>&1

# Download Chisel
print_info "Downloading Chisel..."
cd /root
wget -q https://github.com/jpillora/chisel/releases/download/v1.9.1/chisel_1.9.1_linux_amd64.gz
gunzip -f chisel_1.9.1_linux_amd64.gz
mv chisel_1.9.1_linux_amd64 chisel
chmod +x chisel

# Read tunnel port from user input (passed via stdin)
if [ -z "$1" ]; then
    print_error "Tunnel port not provided!"
    exit 1
fi

TUNNEL_PORT="$1"

# Create systemd service
print_info "Creating systemd service..."
cat > /etc/systemd/system/chisel-server.service << EOF
[Unit]
Description=Chisel Tunnel Server
After=network.target

[Service]
Type=simple
User=root
ExecStart=/root/chisel server --port $TUNNEL_PORT --reverse
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start service
print_info "Starting Chisel service..."
systemctl daemon-reload
systemctl enable chisel-server.service > /dev/null 2>&1
systemctl start chisel-server.service

# Wait for service to start
sleep 2

# Check if service is running
if systemctl is-active --quiet chisel-server.service; then
    print_success "Chisel server installed and running!"
    echo ""
    echo "=============================================="
    echo "          Installation Complete"
    echo "=============================================="
    echo "Port: $TUNNEL_PORT"
    echo "Service: chisel-server.service"
    echo "Config: /etc/systemd/system/chisel-server.service"
    echo "=============================================="
else
    print_error "Failed to start Chisel service!"
    exit 1
fi
'''
    return script

def generate_foreign_script(tunnel_port, remote_ip, number_of_config, config_ports):
    """Generate Chisel client installation script for foreign server"""
    script = f'''#!/bin/bash

# Chisel Tunnel Installation Script for Foreign Server
# This script installs and configures Chisel client on foreign server

set -e

echo "=============================================="
echo "   Chisel Client Installation (Foreign)"
echo "=============================================="
echo ""

# Colors for output
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
RED='\\033[0;31m'
NC='\\033[0m' # No Color

# Function to print colored output
print_success() {{
    echo -e "${{GREEN}}✓ $1${{NC}}"
}}

print_info() {{
    echo -e "${{YELLOW}}ℹ️ $1${{NC}}"
}}

print_error() {{
    echo -e "${{RED}}✗ $1${{NC}}"
}}

# Check if required parameters are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
    print_error "Missing required parameters!"
    echo "Usage: $0 <TUNNEL_PORT> <REMOTE_IP> <NUMBER_OF_CONFIG> <CONFIG_PORTS>"
    exit 1
fi

TUNNEL_PORT="$1"
REMOTE_IP="$2"
NUMBER_OF_CONFIG="$3"
CONFIG_PORTS="$4"

# Update system
print_info "Updating system packages..."
apt-get update -qq

# Install required packages
print_info "Installing required packages..."
apt-get install -y wget curl sudo screen > /dev/null 2>&1

# Download Chisel
print_info "Downloading Chisel..."
cd /root
wget -q https://github.com/jpillora/chisel/releases/download/v1.9.1/chisel_1.9.1_linux_amd64.gz
gunzip -f chisel_1.9.1_linux_amd64.gz
mv chisel_1.9.1_linux_amd64 chisel
chmod +x chisel

# Parse config ports (comma separated)
IFS=',' read -ra PORTS <<< "$CONFIG_PORTS"

# Build remote forwarding string
REMOTE_FORWARDS=""
for port in "${{PORTS[@]}}"; do
    port=$(echo $port | xargs) # trim whitespace
    REMOTE_FORWARDS="$REMOTE_FORWARDS R:0.0.0.0:$port:127.0.0.1:$port "
done

# Trim trailing space
REMOTE_FORWARDS=$(echo $REMOTE_FORWARDS | xargs)

print_info "Configuring ports: $CONFIG_PORTS"
print_info "Remote server: $REMOTE_IP:$TUNNEL_PORT"

# Create systemd service
print_info "Creating systemd service..."
cat > /etc/systemd/system/chisel-client.service << EOF
[Unit]
Description=Chisel Tunnel Client
After=network.target

[Service]
Type=simple
User=root
ExecStart=/root/chisel client --keepalive 25s --max-retry-count 10 --max-retry-interval 30s $REMOTE_IP:$TUNNEL_PORT $REMOTE_FORWARDS
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create auto-restart timer (2 hours)
print_info "Creating auto-restart timer..."
cat > /etc/systemd/system/chisel-restart.service << EOF
[Unit]
Description=Chisel Client Restart Service

[Service]
Type=oneshot
ExecStart=/bin/systemctl restart chisel-client.service
EOF

cat > /etc/systemd/system/chisel-restart.timer << EOF
[Unit]
Description=Restart Chisel Client Every 2 Hours

[Timer]
OnBootSec=2h
OnUnitActiveSec=2h
Unit=chisel-restart.service

[Install]
WantedBy=timers.target
EOF

# Reload systemd and start services
print_info "Starting Chisel client..."
systemctl daemon-reload
systemctl enable chisel-client.service > /dev/null 2>&1
systemctl start chisel-client.service
systemctl enable chisel-restart.timer > /dev/null 2>&1
systemctl start chisel-restart.timer

# Wait for service to start
sleep 2

# Check if service is running
if systemctl is-active --quiet chisel-client.service; then
    print_success "Chisel client installed and running!"
    echo ""
    echo "=============================================="
    echo "          Installation Complete"
    echo "=============================================="
    echo "Remote Server: $REMOTE_IP:$TUNNEL_PORT"
    echo "Forwarded Ports: $CONFIG_PORTS"
    echo "Number of Configs: $NUMBER_OF_CONFIG"
    echo "Service: chisel-client.service"
    echo "Auto-Restart: Every 2 hours"
    echo "Config: /etc/systemd/system/chisel-client.service"
    echo "=============================================="
else
    print_error "Failed to start Chisel client!"
    exit 1
fi
'''
    return script
