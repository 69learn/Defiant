"""
Scripts for deleting different types of tunnels
"""

def get_delete_script(tunnel_type):
    """Return appropriate delete script based on tunnel type"""
    
    scripts = {
        'mux': MUX_DELETE_SCRIPT,
        'vxlan': VXLAN_DELETE_SCRIPT,
        'chisel': CHISEL_DELETE_SCRIPT,
        'backhaul': BACKHAUL_DELETE_SCRIPT
    }
    
    return scripts.get(tunnel_type.lower(), MUX_DELETE_SCRIPT)

# Mux (Waterwall) delete script
MUX_DELETE_SCRIPT = """#!/bin/bash
set -e

echo "Stopping services..."
systemctl stop waterwall-ir 2>/dev/null || true
systemctl stop waterwall-kharej 2>/dev/null || true

echo "Disabling services..."
systemctl disable waterwall-ir 2>/dev/null || true
systemctl disable waterwall-kharej 2>/dev/null || true

echo "Removing service files..."
rm -f /etc/systemd/system/waterwall-ir.service
rm -f /etc/systemd/system/waterwall-kharej.service

echo "Reloading systemd..."
systemctl daemon-reload

echo "Removing Waterwall directory..."
rm -rf /root/Waterwall

echo "Cleanup finished!"
echo "Both Iran & Foreign configurations fully removed."
"""

# Vxlan (RGT) delete script
VXLAN_DELETE_SCRIPT = """#!/bin/bash
set -e

echo "Stopping services..."
systemctl stop RGT-iran-* 2>/dev/null || true
systemctl stop RGT-kharej-* 2>/dev/null || true

echo "Disabling services..."
systemctl disable RGT-iran-* 2>/dev/null || true
systemctl disable RGT-kharej-* 2>/dev/null || true

echo "Removing service files..."
rm -f /etc/systemd/system/RGT-iran-*.service
rm -f /etc/systemd/system/RGT-kharej-*.service

echo "Reloading systemd..."
systemctl daemon-reload

echo "Removing RGT core directory..."
rm -rf /root/rgt-core

echo "Cleanup finished!"
echo "✔ All RGT Iran & Kharej configs, binaries, and services removed."
"""

# Chisel delete script
CHISEL_DELETE_SCRIPT = """#!/bin/bash

echo "=============================================="
echo "          Chisel Full Removal Script"
echo "=============================================="

# Stop and disable services if they exist
systemctl stop chisel-server.service 2>/dev/null
systemctl disable chisel-server.service 2>/dev/null

systemctl stop chisel-client.service 2>/dev/null
systemctl disable chisel-client.service 2>/dev/null

systemctl stop chisel-restart.timer 2>/dev/null
systemctl disable chisel-restart.timer 2>/dev/null

systemctl stop chisel-restart.service 2>/dev/null

# Remove systemd files
rm -f /etc/systemd/system/chisel-server.service
rm -f /etc/systemd/system/chisel-client.service
rm -f /etc/systemd/system/chisel-restart.service
rm -f /etc/systemd/system/chisel-restart.timer

# Reload daemon
systemctl daemon-reload

# Remove binary if exists
rm -f /root/chisel

# Remove logs
rm -f /var/log/chisel*.log

echo "Chisel server, client, timers, services, binary, and logs removed successfully."
echo "=============================================="
"""

# Backhaul delete script
BACKHAUL_DELETE_SCRIPT = """#!/bin/bash
set -e

echo "======================================"
echo "   Backhaul Full Removal Script"
echo "======================================"

SERVICE_FILE="/etc/systemd/system/backhaul.service"
INSTALL_DIR="/root"
CONF_FILE="$INSTALL_DIR/conf.toml"
BACKHAUL_BIN="$INSTALL_DIR/backhaul"
TLS_CERT="$INSTALL_DIR/server.crt"
TLS_KEY="$INSTALL_DIR/server.key"
TAR_FILE="$INSTALL_DIR/backhaul_linux_amd64.tar.gz"

echo "[1] Stopping service..."
systemctl stop backhaul.service 2>/dev/null || true

echo "[2] Disabling service..."
systemctl disable backhaul.service 2>/dev/null || true

echo "[3] Removing service file..."
rm -f "$SERVICE_FILE"

echo "[4] Deleting Backhaul binary..."
rm -f "$BACKHAUL_BIN"

echo "[5] Deleting config file..."
rm -f "$CONF_FILE"

echo "[6] Removing downloaded archive..."
rm -f "$TAR_FILE"

echo "[7] Removing TLS certificate and key if exist..."
rm -f "$TLS_CERT" "$TLS_KEY"

echo "[8] Reloading systemd..."
systemctl daemon-reload

echo "======================================"
echo "   Backhaul Removed Completely"
echo "======================================"
"""
