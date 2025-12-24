def generate_iran_vxlan_script(tunnel_name, ip_type, tunnel_port, transport, tcp_nodelay, security_token, service_ports):
    """Generate Vxlan installation script for Iran server"""
    
    script = f'''#!/bin/bash

# Check if the script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Define colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[0;33m'
CYAN='\\033[0;36m'
NC='\\033[0m'

# Define paths
CONFIG_DIR="/root/rgt-core"
SERVICE_DIR="/etc/systemd/system"
RGT_BIN="${{CONFIG_DIR}}/rgt"

# Function to colorize text
colorize() {{
    local color="$1"
    local text="$2"
    local color_code
    case $color in
        red) color_code=$RED ;;
        green) color_code=$GREEN ;;
        yellow) color_code=$YELLOW ;;
        cyan) color_code=$CYAN ;;
        *) color_code=$NC ;;
    esac
    echo -e "${{color_code}}${{text}}${{NC}}"
}}

# Function to install dependencies
install_dependencies() {{
    colorize yellow "Installing dependencies..."
    apt-get update -qq
    apt-get install -y unzip curl jq iproute2 >/dev/null 2>&1 || {{
        colorize red "Failed to install dependencies"
        exit 1
    }}
    colorize green "Dependencies installed successfully"
}}

# Function to download and install RGT core
download_and_extract_rgt() {{
    if [[ -f "${{RGT_BIN}}" ]] && [[ -x "${{RGT_BIN}}" ]]; then
        colorize green "RGT is already installed"
        return 0
    fi

    colorize yellow "Downloading RGT core..."
    DOWNLOAD_URL="https://github.com/black-sec/RGT/raw/main/core/RGT-x86-64-linux.zip"
    DOWNLOAD_DIR=$(mktemp -d)
    ZIP_FILE="$DOWNLOAD_DIR/rgt.zip"

    if ! curl -sSL -o "$ZIP_FILE" "$DOWNLOAD_URL"; then
        colorize red "Failed to download RGT core"
        rm -rf "$DOWNLOAD_DIR"
        exit 1
    fi

    colorize yellow "Extracting RGT..."
    mkdir -p "$CONFIG_DIR"
    if ! unzip -q "$ZIP_FILE" -d "$CONFIG_DIR"; then
        colorize red "Failed to extract RGT"
        rm -rf "$DOWNLOAD_DIR"
        exit 1
    fi

    mv "${{CONFIG_DIR}}/rgt" "${{RGT_BIN}}" 2>/dev/null
    chmod +x "${{RGT_BIN}}"
    rm -rf "$DOWNLOAD_DIR"

    if [[ ! -x "${{RGT_BIN}}" ]]; then
        colorize red "RGT binary is not executable"
        exit 1
    fi

    colorize green "RGT installed successfully"
}}

# Get parameters from command line
TUNNEL_NAME="{tunnel_name}"
IP_TYPE="{ip_type}"
TUNNEL_PORT="{tunnel_port}"
TRANSPORT="{transport}"
TCP_NODELAY={tcp_nodelay}
SECURITY_TOKEN="{security_token}"
SERVICE_PORTS="{service_ports}"

# Auto-install dependencies and RGT core
install_dependencies
download_and_extract_rgt

# Set local IP based on IP type
if [[ "$IP_TYPE" == "IPv6" ]]; then
    LOCAL_IP="[::]"
else
    LOCAL_IP="0.0.0.0"
fi

# Create configuration file
CONFIG_FILE="${{CONFIG_DIR}}/iran-${{TUNNEL_NAME}}.toml"

cat << EOF > "$CONFIG_FILE"
[server]
bind_addr = "${{LOCAL_IP}}:${{TUNNEL_PORT}}"
default_token = "$SECURITY_TOKEN"
heartbeat_interval = 0

[server.transport]
type = "$TRANSPORT"

[server.transport.${{TRANSPORT}}]
nodelay = ${{TCP_NODELAY}}
keepalive_secs = 20
keepalive_interval = 8

EOF

# Parse service ports and add them to config
IFS=',' read -r -a ports <<< "$SERVICE_PORTS"
for port in "${{ports[@]}}"; do
    port=$(echo "$port" | tr -d ' ')
    cat << EOF >> "$CONFIG_FILE"
[server.services.service${{port}}]
type = "$TRANSPORT"
token = "$SECURITY_TOKEN"
bind_addr = "${{LOCAL_IP}}:${{port}}"
nodelay = ${{TCP_NODELAY}}

EOF
done

# Create systemd service
SERVICE_FILE="${{SERVICE_DIR}}/RGT-iran-${{TUNNEL_NAME}}.service"
cat << EOF > "$SERVICE_FILE"
[Unit]
Description=RGT Iran Reverse Tunnel - $TUNNEL_NAME
After=network.target

[Service]
Type=simple
ExecStart=${{RGT_BIN}} ${{CONFIG_FILE}}
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable --now "RGT-iran-${{TUNNEL_NAME}}.service"

if systemctl is-active --quiet "RGT-iran-${{TUNNEL_NAME}}.service"; then
    colorize green "✓ Iran server configured successfully"
    echo "Tunnel Name: $TUNNEL_NAME"
    echo "Tunnel Port: $TUNNEL_PORT"
    echo "Transport: $TRANSPORT"
    echo "Service Ports: $SERVICE_PORTS"
    exit 0
else
    colorize red "Failed to start service"
    exit 1
fi
'''
    
    return script

def generate_kharej_vxlan_script(tunnel_name, iran_ip, tunnel_port, transport, tcp_nodelay, security_token, service_ports):
    """Generate Vxlan installation script for Foreign (Kharej) server"""
    
    script = f'''#!/bin/bash

# Check if the script is run as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

# Define colors
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[0;33m'
CYAN='\\033[0;36m'
NC='\\033[0m'

# Define paths
CONFIG_DIR="/root/rgt-core"
SERVICE_DIR="/etc/systemd/system"
RGT_BIN="${{CONFIG_DIR}}/rgt"

# Function to colorize text
colorize() {{
    local color="$1"
    local text="$2"
    local color_code
    case $color in
        red) color_code=$RED ;;
        green) color_code=$GREEN ;;
        yellow) color_code=$YELLOW ;;
        cyan) color_code=$CYAN ;;
        *) color_code=$NC ;;
    esac
    echo -e "${{color_code}}${{text}}${{NC}}"
}}

# Function to install dependencies
install_dependencies() {{
    colorize yellow "Installing dependencies..."
    apt-get update -qq
    apt-get install -y unzip curl jq iproute2 >/dev/null 2>&1 || {{
        colorize red "Failed to install dependencies"
        exit 1
    }}
    colorize green "Dependencies installed successfully"
}}

# Function to download and install RGT core
download_and_extract_rgt() {{
    if [[ -f "${{RGT_BIN}}" ]] && [[ -x "${{RGT_BIN}}" ]]; then
        colorize green "RGT is already installed"
        return 0
    fi

    colorize yellow "Downloading RGT core..."
    DOWNLOAD_URL="https://github.com/black-sec/RGT/raw/main/core/RGT-x86-64-linux.zip"
    DOWNLOAD_DIR=$(mktemp -d)
    ZIP_FILE="$DOWNLOAD_DIR/rgt.zip"

    if ! curl -sSL -o "$ZIP_FILE" "$DOWNLOAD_URL"; then
        colorize red "Failed to download RGT core"
        rm -rf "$DOWNLOAD_DIR"
        exit 1
    fi

    colorize yellow "Extracting RGT..."
    mkdir -p "$CONFIG_DIR"
    if ! unzip -q "$ZIP_FILE" -d "$CONFIG_DIR"; then
        colorize red "Failed to extract RGT"
        rm -rf "$DOWNLOAD_DIR"
        exit 1
    fi

    mv "${{CONFIG_DIR}}/rgt" "${{RGT_BIN}}" 2>/dev/null
    chmod +x "${{RGT_BIN}}"
    rm -rf "$DOWNLOAD_DIR"

    if [[ ! -x "${{RGT_BIN}}" ]]; then
        colorize red "RGT binary is not executable"
        exit 1
    fi

    colorize green "RGT installed successfully"
}}

# Function to validate IPv4 address
check_ipv4() {{
    local ip=$1
    ipv4_pattern="^([0-9]{{1,3}}\\.?){{3}}[0-9]{{1,3}}$"
    if [[ $ip =~ $ipv4_pattern ]]; then
        IFS='.' read -r -a octets <<< "$ip"
        for octet in "${{octets[@]}}"; do
            [[ $octet -gt 255 ]] && return 1
        done
        return 0
    fi
    return 1
}}

# Function to validate IPv6 address
check_ipv6() {{
    local ip=$1
    ip="${{ip#[}}"
    ip="${{ip%]}}"
    ipv6_pattern="^(([0-9a-fA-F]{{1,4}}:){{7}}[0-9a-fA-F]{{1,4}}|([0-9a-fA-F]{{1,4}}:){{1,7}}:|([0-9a-fA-F]{{1,4}}:){{1,6}}:[0-9a-fA-F]{{1,4}}|([0-9a-fA-F]{{1,4}}:){{1,5}}(:[0-9a-fA-F]{{1,4}}){{1,2}}|([0-9a-fA-F]{{1,4}}:){{1,4}}(:[0-9a-fA-F]{{1,4}}){{1,3}}|([0-9a-fA-F]{{1,4}}:){{1,3}}(:[0-9a-fA-F]{{1,4}}){{1,4}}|([0-9a-fA-F]{{1,4}}:){{1,2}}(:[0-9a-fA-F]{{1,4}}){{1,5}}|[0-9a-fA-F]{{1,4}}:(:[0-9a-fA-F]{{1,4}}){{1,6}}|:((:[0-9a-fA-F]{{1,4}}){{1,7}}|:))$"
    [[ $ip =~ $ipv6_pattern ]] && return 0 || return 1
}}

# Get parameters from command line
TUNNEL_NAME="{tunnel_name}"
IRAN_IP="{iran_ip}"
TUNNEL_PORT="{tunnel_port}"
TRANSPORT="{transport}"
TCP_NODELAY={tcp_nodelay}
SECURITY_TOKEN="{security_token}"
SERVICE_PORTS="{service_ports}"

# Auto-install dependencies and RGT core
install_dependencies
download_and_extract_rgt

# Remove brackets from IPv6 if present
if check_ipv6 "$IRAN_IP"; then
    IRAN_IP="${{IRAN_IP#[}}"
    IRAN_IP="${{IRAN_IP%]}}"
fi

# Create configuration file
CONFIG_FILE="${{CONFIG_DIR}}/kharej-${{TUNNEL_NAME}}.toml"

cat << EOF > "$CONFIG_FILE"
[client]
remote_addr = "${{IRAN_IP}}:${{TUNNEL_PORT}}"
default_token = "$SECURITY_TOKEN"
heartbeat_timeout = 0

[client.transport]
type = "$TRANSPORT"

[client.transport.${{TRANSPORT}}]
nodelay = ${{TCP_NODELAY}}
keepalive_secs = 20
keepalive_interval = 8

EOF

# Parse service ports and add them to config
IFS=',' read -r -a ports <<< "$SERVICE_PORTS"
for port in "${{ports[@]}}"; do
    port=$(echo "$port" | tr -d ' ')
    cat << EOF >> "$CONFIG_FILE"
[client.services.service${{port}}]
type = "$TRANSPORT"
token = "$SECURITY_TOKEN"
local_addr = "127.0.0.1:${{port}}"
nodelay = ${{TCP_NODELAY}}

EOF
done

# Create systemd service
SERVICE_FILE="${{SERVICE_DIR}}/RGT-kharej-${{TUNNEL_NAME}}.service"
cat << EOF > "$SERVICE_FILE"
[Unit]
Description=RGT Kharej Reverse Tunnel - $TUNNEL_NAME
After=network.target

[Service]
Type=simple
ExecStart=${{RGT_BIN}} ${{CONFIG_FILE}}
Restart=always
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable --now "RGT-kharej-${{TUNNEL_NAME}}.service"

if systemctl is-active --quiet "RGT-kharej-${{TUNNEL_NAME}}.service"; then
    colorize green "✓ Kharej server configured successfully"
    echo "Tunnel Name: $TUNNEL_NAME"
    echo "Iran Server: ${{IRAN_IP}}:${{TUNNEL_PORT}}"
    echo "Transport: $TRANSPORT"
    echo "Service Ports: $SERVICE_PORTS"
    exit 0
else
    colorize red "Failed to start service"
    exit 1
fi
'''
    
    return script
