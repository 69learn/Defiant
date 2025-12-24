def generate_iran_mux_script(iran_ip, kharej_ip, ports):
    """Generate Mux installation script for Iran server"""
    
    script = f'''#!/bin/bash
set -e

install_unzip() {{
    if ! command -v unzip &> /dev/null; then
        echo "Installing unzip..."
        apt update && apt install -y unzip
    fi
}}

setup_waterwall() {{
    WW_DIR="/root/Waterwall"
    mkdir -p "$WW_DIR"
    cd "$WW_DIR" || exit

    WW_ZIP="Waterwall-linux-gcc-x64.zip"
    if [ ! -f "$WW_ZIP" ]; then
        echo "Downloading Waterwall..."
        wget -O "$WW_ZIP" "https://github.com/radkesvat/WaterWall/releases/download/v1.40/Waterwall-linux-gcc-x64.zip"
    fi

    if [ ! -f "Waterwall" ]; then
        echo "Extracting Waterwall..."
        unzip -o "$WW_ZIP"
        chmod +x Waterwall
    fi

    echo "Waterwall is ready in $WW_DIR"
}}

config_iran() {{
    local IRAN_IP="$1"
    local FOREIGN_IP="$2"
    local PORTS="$3"

    echo "Configuring IRAN server..."
    
    CONFIG_FILE="/root/Waterwall/config_ir.json"
    CORE_FILE="/root/Waterwall/core.json"

cat > "$CONFIG_FILE" <<EOF
{{
    "name": "iran",
    "nodes": [
        {{
            "name": "mytun",
            "type": "TunDevice",
            "settings": {{
                "device-name": "wtun0",
                "device-ip": "10.10.0.1/24"
            }},
            "next": "ipovsrc"
        }},
        {{
            "name": "ipovsrc",
            "type": "IpOverrider",
            "settings": {{
                "direction": "up",
                "mode": "source-ip",
                "ipv4": "$IRAN_IP"
            }},
            "next": "ipovdest"
        }},
        {{
            "name": "ipovdest",
            "type": "IpOverrider",
            "settings": {{
                "direction": "up",
                "mode": "dest-ip",
                "ipv4": "$FOREIGN_IP"
            }},
            "next": "manip"
        }},
        {{
            "name": "manip",
            "type": "IpManipulator",
            "settings": {{
                "protoswap": 18
            }},
            "next": "ipovsrc2"
        }},
        {{
            "name": "ipovsrc2",
            "type": "IpOverrider",
            "settings": {{
                "direction": "down",
                "mode": "source-ip",
                "ipv4": "10.10.0.2"
            }},
            "next": "ipovdest2"
        }},
        {{
            "name": "ipovdest2",
            "type": "IpOverrider",
            "settings": {{
                "direction": "down",
                "mode": "dest-ip",
                "ipv4": "10.10.0.1"
            }},
            "next": "rd"
        }},
        {{
            "name": "rd",
            "type": "RawSocket",
            "settings": {{
                "capture-filter-mode": "source-ip",
                "capture-ip": "$FOREIGN_IP"
            }}
        }}
EOF

    # Add port configurations
    IFS=' ' read -ra PORT_ARRAY <<< "$PORTS"
    for PORT in "${{PORT_ARRAY[@]}}"; do
cat >> "$CONFIG_FILE" <<EOF
        ,
        {{
            "name": "input$PORT",
            "type": "TcpListener",
            "settings": {{
                "address": "0.0.0.0",
                "port": $PORT,
                "nodelay": true
            }},
            "next": "output$PORT"
        }},
        {{
            "name": "output$PORT",
            "type": "TcpConnector",
            "settings": {{
                "address": "10.10.0.2",
                "port": $PORT,
                "nodelay": true
            }}
        }}
EOF
    done

    echo "    ]
}}" >> "$CONFIG_FILE"

    create_core "$CONFIG_FILE" "$CORE_FILE"
    create_service "ir"
    
    echo "Iran server configured successfully!"
}}

create_core() {{
    local CONFIG_FILE="$1"
    local CORE_FILE="$2"
cat > "$CORE_FILE" <<EOF
{{
    "log": {{
        "path": "log/",
        "internal": {{
            "loglevel": "DEBUG",
            "file": "internal.log",
            "console": true
        }},
        "core": {{
            "loglevel": "DEBUG",
            "file": "core.log",
            "console": true
        }},
        "network": {{
            "loglevel": "DEBUG",
            "file": "network.log",
            "console": true
        }},
        "dns": {{
            "loglevel": "SILENT",
            "file": "dns.log",
            "console": false
        }}
    }},
    "dns": {{}},
    "misc": {{
        "workers": 1,
        "ram-profile": "client",
        "libs-path": "libs/"
    }},
    "configs": [
        "$CONFIG_FILE"
    ]
}}
EOF
}}

create_service() {{
    local NAME="$1"
    SERVICE_FILE="/etc/systemd/system/waterwall-$NAME.service"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Waterwall $NAME
After=network.target

[Service]
WorkingDirectory=/root/Waterwall
ExecStart=/root/Waterwall/Waterwall
Restart=always
User=root
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

    chmod +x /root/Waterwall/Waterwall
    systemctl daemon-reload
    systemctl restart waterwall-$NAME
    systemctl enable waterwall-$NAME
    
    echo "Service waterwall-$NAME started and enabled"
}}

# Main execution
IRAN_IP="{iran_ip}"
FOREIGN_IP="{kharej_ip}"
PORTS="{ports}"

if [ -z "$IRAN_IP" ] || [ -z "$FOREIGN_IP" ] || [ -z "$PORTS" ]; then
    echo "Usage: $0 <IRAN_IP> <FOREIGN_IP> <PORTS>"
    exit 1
fi

install_unzip
setup_waterwall
config_iran "$IRAN_IP" "$FOREIGN_IP" "$PORTS"

echo "Mux Iran installation completed successfully!"
'''
    
    return script

def generate_foreign_mux_script(iran_ip, kharej_ip):
    """Generate Mux installation script for Foreign server"""
    
    script = f'''#!/bin/bash
set -e

install_unzip() {{
    if ! command -v unzip &> /dev/null; then
        echo "Installing unzip..."
        apt update && apt install -y unzip
    fi
}}

setup_waterwall() {{
    WW_DIR="/root/Waterwall"
    mkdir -p "$WW_DIR"
    cd "$WW_DIR" || exit

    WW_ZIP="Waterwall-linux-gcc-x64.zip"
    if [ ! -f "$WW_ZIP" ]; then
        echo "Downloading Waterwall..."
        wget -O "$WW_ZIP" "https://github.com/radkesvat/WaterWall/releases/download/v1.40/Waterwall-linux-gcc-x64.zip"
    fi

    if [ ! -f "Waterwall" ]; then
        echo "Extracting Waterwall..."
        unzip -o "$WW_ZIP"
        chmod +x Waterwall
    fi

    echo "Waterwall is ready in $WW_DIR"
}}

config_foreign() {{
    local IRAN_IP="$1"
    local FOREIGN_IP="$2"

    echo "Configuring FOREIGN server..."
    
    CONFIG_FILE="/root/Waterwall/config_kharej.json"
    CORE_FILE="/root/Waterwall/core.json"

cat > "$CONFIG_FILE" <<EOF
{{
    "name": "kharej",
    "nodes": [
        {{
            "name": "mytun",
            "type": "TunDevice",
            "settings": {{
                "device-name": "wtun0",
                "device-ip": "10.10.0.1/24"
            }},
            "next": "ipovsrc"
        }},
        {{
            "name": "ipovsrc",
            "type": "IpOverrider",
            "settings": {{
                "direction": "up",
                "mode": "source-ip",
                "ipv4": "$FOREIGN_IP"
            }},
            "next": "ipovdest"
        }},
        {{
            "name": "ipovdest",
            "type": "IpOverrider",
            "settings": {{
                "direction": "up",
                "mode": "dest-ip",
                "ipv4": "$IRAN_IP"
            }},
            "next": "manip"
        }},
        {{
            "name": "manip",
            "type": "IpManipulator",
            "settings": {{
                "protoswap": 18
            }},
            "next": "ipovsrc2"
        }},
        {{
            "name": "ipovsrc2",
            "type": "IpOverrider",
            "settings": {{
                "direction": "down",
                "mode": "source-ip",
                "ipv4": "10.10.0.2"
            }},
            "next": "ipovdest2"
        }},
        {{
            "name": "ipovdest2",
            "type": "IpOverrider",
            "settings": {{
                "direction": "down",
                "mode": "dest-ip",
                "ipv4": "10.10.0.1"
            }},
            "next": "rd"
        }},
        {{
            "name": "rd",
            "type": "RawSocket",
            "settings": {{
                "capture-filter-mode": "source-ip",
                "capture-ip": "$IRAN_IP"
            }}
        }}
    ]
}}
EOF

    create_core "$CONFIG_FILE" "$CORE_FILE"
    create_service "kharej"
    
    echo "Foreign server configured successfully!"
}}

create_core() {{
    local CONFIG_FILE="$1"
    local CORE_FILE="$2"
cat > "$CORE_FILE" <<EOF
{{
    "log": {{
        "path": "log/",
        "internal": {{
            "loglevel": "DEBUG",
            "file": "internal.log",
            "console": true
        }},
        "core": {{
            "loglevel": "DEBUG",
            "file": "core.log",
            "console": true
        }},
        "network": {{
            "loglevel": "DEBUG",
            "file": "network.log",
            "console": true
        }},
        "dns": {{
            "loglevel": "SILENT",
            "file": "dns.log",
            "console": false
        }}
    }},
    "dns": {{}},
    "misc": {{
        "workers": 1,
        "ram-profile": "client",
        "libs-path": "libs/"
    }},
    "configs": [
        "$CONFIG_FILE"
    ]
}}
EOF
}}

create_service() {{
    local NAME="$1"
    SERVICE_FILE="/etc/systemd/system/waterwall-$NAME.service"

cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Waterwall $NAME
After=network.target

[Service]
WorkingDirectory=/root/Waterwall
ExecStart=/root/Waterwall/Waterwall
Restart=always
User=root
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
EOF

    chmod +x /root/Waterwall/Waterwall
    systemctl daemon-reload
    systemctl restart waterwall-$NAME
    systemctl enable waterwall-$NAME
    
    echo "Service waterwall-$NAME started and enabled"
}}

# Main execution
IRAN_IP="{iran_ip}"
FOREIGN_IP="{kharej_ip}"

if [ -z "$IRAN_IP" ] || [ -z "$FOREIGN_IP" ]; then
    echo "Usage: $0 <IRAN_IP> <FOREIGN_IP>"
    exit 1
fi

install_unzip
setup_waterwall
config_foreign "$IRAN_IP" "$FOREIGN_IP"

echo "Mux Foreign installation completed successfully!"
'''
    
    return script
