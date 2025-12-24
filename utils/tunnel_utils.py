import uuid
import random
import string

def generate_tunnel_id():
    """Generate unique tunnel ID"""
    return f"BH-{uuid.uuid4().hex[:12].upper()}"

def generate_iran_script(transport, tunnel_ports, subdomain=None):
    """Generate installation script for Iran server (advanced)"""
    
    ports_list = tunnel_ports.split()
    
    # Build ports array with proper TOML formatting
    ports_toml = ""
    for i, port in enumerate(ports_list):
        if i == len(ports_list) - 1:
            ports_toml += f'    "{port}={port}"\n'
        else:
            ports_toml += f'    "{port}={port}",\n'
    
    # Determine TLS settings
    tls_section = ""
    if transport in ["wss", "wssmux"]:
        domain = subdomain or "example.com"
        tls_section = f"""
# Generate TLS certificates
openssl genpkey -algorithm RSA -out /root/server.key -pkeyopt rsa_keygen_bits:2048 2>/dev/null || true
openssl req -new -key /root/server.key -out /root/server.csr -subj "/CN={domain}" 2>/dev/null || true
openssl x509 -req -in /root/server.csr -signkey /root/server.key -out /root/server.crt -days 365 2>/dev/null || true
"""
    
    script = f'''#!/bin/bash
set -euo pipefail

# Backhaul Iran Server Installation Script - v0.6.5
err() {{
    echo "خطا: $*" >&2
    exit 1
}}

INSTALL_DIR="/root"
SERVICE_USER="root"
TOKEN="mehdi"
CONF_FILE="$INSTALL_DIR/conf.toml"
SERVICE_FILE="/etc/systemd/system/backhaul.service"
BACKHAUL_URL="https://github.com/Musixal/Backhaul/releases/download/v0.6.5/backhaul_linux_amd64.tar.gz"
TRANSPORT="{transport}"
BIND_ADDR="0.0.0.0:3080"

echo "Starting Backhaul installation for Iran..."

# Update package manager
apt-get update -y 2>/dev/null || yum update -y 2>/dev/null || true
apt-get install -y wget tar openssl 2>/dev/null || yum install -y wget tar openssl 2>/dev/null || true

# Download and extract Backhaul
echo "Downloading Backhaul v0.6.5..."
cd "$INSTALL_DIR"
wget -q -O backhaul_linux_amd64.tar.gz "$BACKHAUL_URL" 2>/dev/null || err "Failed to download Backhaul"
tar -xzf backhaul_linux_amd64.tar.gz || err "Failed to extract Backhaul"
chmod +x "$INSTALL_DIR/backhaul" || err "Failed to set permissions"
rm -f backhaul_linux_amd64.tar.gz

{tls_section}

# Create conf.toml based on transport type
echo "Creating configuration for transport: $TRANSPORT"
cat > "$CONF_FILE" <<'CONFEOF'
[server]
bind_addr = "0.0.0.0:3080"
transport = "{transport}"
token = "mehdi"
keepalive_period = 10
nodelay = true
heartbeat = 40
channel_size = 2048
sniffer = false
web_port = 2525
sniffer_log = "/root/backhaul.json"
log_level = "info"
ports = [
{ports_toml}]
CONFEOF

# Create systemd service file
echo "Creating systemd service..."
cat > "$SERVICE_FILE" <<'SERVICEEOF'
[Unit]
Description=Backhaul Reverse Tunnel Service
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/conf.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576
User=root

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Enable and start service
systemctl daemon-reload || true
systemctl enable backhaul.service || true
systemctl restart backhaul.service || true

# Verify service is running
sleep 2
if systemctl is-active --quiet backhaul.service; then
    echo "✅ Backhaul service started successfully"
else
    echo "⚠️ Warning: Backhaul service may not have started correctly"
fi

echo "=== BACKHAUL IRAN INSTALLATION COMPLETE ==="
echo "Transport: $TRANSPORT"
echo "Bind Address: 0.0.0.0:3080"
echo "Status: Service configured"
'''
    
    return script

def generate_foreign_script(transport, remote_ip_or_domain):
    """Generate installation script for Foreign server (advanced)"""
    
    script = f'''#!/bin/bash
set -euo pipefail

# Backhaul Foreign Server Installation Script - v0.6.5
INSTALL_DIR="/root"
SERVICE_USER="root"
TOKEN="mehdi"
CONF_FILE="$INSTALL_DIR/conf.toml"
SERVICE_FILE="/etc/systemd/system/backhaul.service"
BACKHAUL_URL="https://github.com/Musixal/Backhaul/releases/download/v0.6.5/backhaul_linux_amd64.tar.gz"
REMOTE="{remote_ip_or_domain}"
TRANSPORT="{transport}"
PORT="3080"

echo "Starting Backhaul installation for Foreign server..."

# Update package manager
apt-get update -y 2>/dev/null || yum update -y 2>/dev/null || true
apt-get install -y wget tar 2>/dev/null || yum install -y wget tar 2>/dev/null || true

# Download and extract Backhaul
echo "Downloading Backhaul v0.6.5..."
cd "$INSTALL_DIR"
wget -q -O backhaul_linux_amd64.tar.gz "$BACKHAUL_URL" 2>/dev/null || exit 1
tar -xzf backhaul_linux_amd64.tar.gz || exit 1
chmod +x "$INSTALL_DIR/backhaul" || exit 1
rm -f backhaul_linux_amd64.tar.gz

# Create conf.toml for client mode
echo "Creating configuration for transport: $TRANSPORT"
cat > "$CONF_FILE" <<'CONFEOF'
[client]
remote_addr = "{remote_ip_or_domain}:3080"
transport = "{transport}"
token = "mehdi"
connection_pool = 128
aggressive_pool = false
keepalive_period = 10
dial_timeout = 10
retry_interval = 3
nodelay = true
sniffer = false
web_port = 2525
sniffer_log = "/root/backhaul.json"
log_level = "info"
CONFEOF

# Create systemd service file
echo "Creating systemd service..."
cat > "$SERVICE_FILE" <<'SERVICEEOF'
[Unit]
Description=Backhaul Reverse Tunnel Service
After=network.target

[Service]
Type=simple
ExecStart=/root/backhaul -c /root/conf.toml
Restart=always
RestartSec=3
LimitNOFILE=1048576
User=root

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Enable and start service
systemctl daemon-reload || true
systemctl enable backhaul.service || true
systemctl restart backhaul.service || true

# Verify service is running
sleep 2
if systemctl is-active --quiet backhaul.service; then
    echo "✅ Backhaul service started successfully"
else
    echo "⚠️ Warning: Backhaul service may not have started correctly"
fi

echo "=== BACKHAUL FOREIGN INSTALLATION COMPLETE ==="
echo "Remote Address: {remote_ip_or_domain}:3080"
echo "Transport: $TRANSPORT"
echo "Status: Service configured"
'''
    
    return script

def generate_panel_id():
    """Generate unique panel ID"""
    return f"PNL-{uuid.uuid4().hex[:12].upper()}"
