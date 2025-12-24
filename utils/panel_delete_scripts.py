"""
Panel deletion scripts for different panel types
"""

MARZBAN_DELETE_SCRIPT = """#!/usr/bin/env bash
set -e

echo "============================================"
echo "   Removing Marzban Completely..."
echo "============================================"

# Stop and remove containers
echo "[1] Stopping & Removing Docker containers..."
docker ps -a --format "{{.Names}}" | grep -i marzban && \\
docker stop $(docker ps -a --format "{{.Names}}" | grep -i marzban) || true

docker ps -a --format "{{.Names}}" | grep -i marzban && \\
docker rm $(docker ps -a --format "{{.Names}}" | grep -i marzban) || true

# Remove Marzban Docker images
echo "[2] Removing Docker images..."
docker images --format "{{.Repository}}" | grep -i marzban && \\
docker rmi $(docker images --format "{{.Repository}}" | grep -i marzban) || true

# Remove Docker network and volumes
echo "[3] Removing Docker networks & volumes..."
docker network ls --format "{{.Name}}" | grep -i marzban && \\
docker network rm $(docker network ls --format "{{.Name}}" | grep -i marzban) || true

docker volume ls --format "{{.Name}}" | grep -i marzban && \\
docker volume rm $(docker volume ls --format "{{.Name}}" | grep -i marzban) || true

# Remove installation folders
echo "[4] Removing folders..."
rm -rf /opt/marzban || true
rm -rf /var/lib/marzban || true
rm -rf /etc/marzban || true

# Remove SSL certificates related to domain
echo "[5] Removing SSL (Let's Encrypt) for Marzban..."
rm -rf /etc/letsencrypt/live/* || true
rm -rf /etc/letsencrypt/archive/* || true
rm -rf /etc/letsencrypt/renewal/* || true

# Remove MySQL database & user
echo "[6] Removing MySQL database..."
if [ -f /opt/marzban/.env ]; then
    MYSQL_ROOT_PWD="$(grep MYSQL_ROOT_PASSWORD /opt/marzban/.env | cut -d= -f2 | tr -d '"')"
    
    if [ -n "$MYSQL_ROOT_PWD" ]; then
        mysql -u root -p"$MYSQL_ROOT_PWD" -e "DROP DATABASE IF EXISTS marzban;" 2>/dev/null || true
        mysql -u root -p"$MYSQL_ROOT_PWD" -e "DROP USER IF EXISTS 'marzban'@'localhost';" 2>/dev/null || true
    fi
fi

# Remove systemd service if exists
echo "[7] Removing systemd service..."
systemctl stop marzban 2>/dev/null || true
systemctl disable marzban 2>/dev/null || true
rm -f /etc/systemd/system/marzban.service
systemctl daemon-reload

# Clean logs
echo "[8] Cleaning logs..."
rm -rf /var/log/marzban 2>/dev/null || true

echo "============================================"
echo "   ✔ Marzban has been COMPLETELY removed!"
echo "============================================"
"""

MARZNESHIN_DELETE_SCRIPT = """#!/usr/bin/env bash
set -e

echo "============================================"
echo "   Removing Marzneshin Completely..."
echo "============================================"

# Stop and remove containers
echo "[1] Stopping & Removing Docker containers..."
docker ps -a --format "{{.Names}}" | grep -i marzneshin && \\
docker stop $(docker ps -a --format "{{.Names}}" | grep -i marzneshin) || true

docker ps -a --format "{{.Names}}" | grep -i marzneshin && \\
docker rm $(docker ps -a --format "{{.Names}}" | grep -i marzneshin) || true

# Remove Marzneshin Docker images
echo "[2] Removing Docker images..."
docker images --format "{{.Repository}}" | grep -i marzneshin && \\
docker rmi $(docker images --format "{{.Repository}}" | grep -i marzneshin) || true

# Remove Docker networks and volumes
echo "[3] Removing Docker networks & volumes..."
docker network ls --format "{{.Name}}" | grep -i marzneshin && \\
docker network rm $(docker network ls --format "{{.Name}}" | grep -i marzneshin) || true

docker volume ls --format "{{.Name}}" | grep -i marzneshin && \\
docker volume rm $(docker volume ls --format "{{.Name}}" | grep -i marzneshin) || true

# Remove installation folders
echo "[4] Removing folders..."
rm -rf /opt/marzneshin || true
rm -rf /var/lib/marzneshin || true
rm -rf /etc/opt/marzneshin || true
rm -rf /usr/lib/marzneshin || true

# Remove SSL certificates
echo "[5] Removing SSL (Let's Encrypt) for Marzneshin..."
rm -rf /etc/letsencrypt/live/* || true
rm -rf /etc/letsencrypt/archive/* || true
rm -rf /etc/letsencrypt/renewal/* || true

# Remove MySQL database & user
echo "[6] Removing MySQL database..."
if [ -f /etc/opt/marzneshin/.env ]; then
    DB_PASSWORD="$(grep SQLALCHEMY_DATABASE_URL /etc/opt/marzneshin/.env | grep -oP 'mysql://marzneshin:\\K[^@]+' || echo '')"
    
    if [ -n "$DB_PASSWORD" ]; then
        mysql -u root -p"$DB_PASSWORD" -e "DROP DATABASE IF EXISTS marzneshin;" 2>/dev/null || true
        mysql -u root -p"$DB_PASSWORD" -e "DROP USER IF EXISTS 'marzneshin'@'%';" 2>/dev/null || true
        mysql -u root -p"$DB_PASSWORD" -e "FLUSH PRIVILEGES;" 2>/dev/null || true
    fi
fi

# Remove systemd services
echo "[7] Removing systemd services..."
systemctl stop marzneshin 2>/dev/null || true
systemctl disable marzneshin 2>/dev/null || true
rm -f /etc/systemd/system/marzneshin.service || true

systemctl stop marzneshin-node 2>/dev/null || true
systemctl disable marzneshin-node 2>/dev/null || true
rm -f /etc/systemd/system/marzneshin-node.service || true

systemctl daemon-reload

# Remove CLI command
echo "[8] Removing Marzneshin CLI..."
rm -f /usr/bin/marzneshin || true
rm -f /usr/local/bin/marzneshin || true

# Clean logs
echo "[9] Cleaning logs..."
rm -rf /var/log/marzneshin 2>/dev/null || true

# Remove installation script
rm -f /tmp/marzneshin.sh || true
rm -f /tmp/install_marzneshin_*.sh || true

echo "============================================"
echo "   ✔ Marzneshin has been COMPLETELY removed!"
echo "============================================"
"""

XUI_DELETE_SCRIPT = """#!/bin/bash
# اجرای دستور uninstall با پاسخ خودکار y
echo "y" | x-ui uninstall
"""

PASARGUARD_DELETE_SCRIPT = """#!/usr/bin/env bash
set -e

# ------------------------------
# اسکریپت حذف کامل PasarGuard
# ------------------------------

echo "===================================================="
echo "   PasarGuard Complete Uninstallation Script"
echo "===================================================="
echo ""
echo "Starting automatic uninstallation process..."
echo ""

# ------------------------------
# [1/6] متوقف و حذف کانتینرهای Docker
# ------------------------------
echo "[1/6] Stopping and removing Docker containers..."
if [ -d "/opt/pasarguard" ]; then
    cd /opt/pasarguard
    if [ -f "docker-compose.yml" ] || [ -f "compose.yml" ]; then
        docker compose down -v 2>/dev/null || docker-compose down -v 2>/dev/null || true
        echo "✓ Docker containers stopped and removed"
    else
        echo "⚠ docker-compose.yml not found, skipping..."
    fi
else
    echo "⚠ /opt/pasarguard directory not found, skipping Docker cleanup..."
fi

# ------------------------------
# [2/6] حذف Images مربوط به PasarGuard
# ------------------------------
echo "[2/6] Removing PasarGuard Docker images..."
docker images | grep -i pasarguard | awk '{print $3}' | xargs -r docker rmi -f 2>/dev/null || true
echo "✓ Docker images removed"

# ------------------------------
# [3/6] حذف فایل‌های نصب شده
# ------------------------------
echo "[3/6] Removing installation files..."

if [ -d "/opt/pasarguard" ]; then
    rm -rf /opt/pasarguard
    echo "✓ Removed /opt/pasarguard"
fi

if [ -d "/opt/pg-node" ]; then
    rm -rf /opt/pg-node
    echo "✓ Removed /opt/pg-node"
fi

if [ -d "/var/lib/pasarguard" ]; then
    rm -rf /var/lib/pasarguard
    echo "✓ Removed /var/lib/pasarguard"
fi

if [ -d "/var/lib/pg-node/certs" ]; then
    rm -rf /var/lib/pg-node/certs
    echo "✓ Removed /var/lib/pg-node/certs"
fi

if [ -d "/var/lib/pg-node" ]; then
    rm -rf /var/lib/pg-node
    echo "✓ Removed /var/lib/pg-node"
fi

# حذف فایل‌های موقت
if [ -f "/tmp/pasarguard.sh" ]; then
    rm -f /tmp/pasarguard.sh
    echo "✓ Removed temporary files"
fi

# ------------------------------
# [4/6] حذف گواهی‌های SSL
# ------------------------------
echo "[4/6] Removing SSL certificates..."

if [ -d "/etc/letsencrypt/live" ]; then
    for cert_dir in /etc/letsencrypt/live/*/; do
        if [ -d "$cert_dir" ]; then
            cert_name=$(basename "$cert_dir")
            certbot delete --cert-name "$cert_name" --non-interactive 2>/dev/null || true
            echo "✓ SSL certificate for $cert_name removed"
        fi
    done
else
    echo "⚠ No SSL certificates found"
fi

# ------------------------------
# [5/6] حذف دستورات CLI
# ------------------------------
echo "[5/6] Removing PasarGuard CLI commands..."
if [ -f "/usr/local/bin/pasarguard" ]; then
    rm -f /usr/local/bin/pasarguard
    echo "✓ Removed pasarguard CLI"
fi

if [ -f "/usr/local/bin/pg-node" ]; then
    rm -f /usr/local/bin/pg-node
    echo "✓ Removed pg-node CLI"
fi

if [ -f "/usr/local/bin/pg-node-service.sh" ]; then
    rm -f /usr/local/bin/pg-node-service.sh
    echo "✓ Removed pg-node-service.sh"
fi

# حذف در مسیرهای دیگر احتمالی
if [ -f "/opt/pg-node/pg-node-service.sh" ]; then
    rm -f /opt/pg-node/pg-node-service.sh
    echo "✓ Removed pg-node-service.sh from /opt"
fi

# حذف سرویس systemd (اگر وجود دارد)
if systemctl list-units --full -all | grep -q "pasarguard"; then
    systemctl stop pasarguard 2>/dev/null || true
    systemctl disable pasarguard 2>/dev/null || true
    rm -f /etc/systemd/system/pasarguard.service
    systemctl daemon-reload
    echo "✓ Removed systemd service"
fi

if systemctl list-units --full -all | grep -q "pg-node"; then
    systemctl stop pg-node 2>/dev/null || true
    systemctl disable pg-node 2>/dev/null || true
    rm -f /etc/systemd/system/pg-node.service
    systemctl daemon-reload
    echo "✓ Removed pg-node systemd service"
fi

# ------------------------------
# [6/6] پاکسازی نهایی
# ------------------------------
echo "[6/6] Final cleanup..."

apt-get remove -y expect certbot python3-pexpect 2>/dev/null || true
apt-get autoremove -y 2>/dev/null || true
echo "✓ Packages removed"

# پاکسازی volumes یتیم Docker
docker volume prune -f 2>/dev/null || true

echo ""
echo "===================================================="
echo "   PasarGuard Uninstallation Completed!"
echo "===================================================="
echo ""
echo "✓ All PasarGuard components have been removed"
echo "✓ All pg-node components have been removed"
echo "✓ Server is now clean"
echo ""
echo "Note: You may need to manually remove any firewall"
echo "      rules or DNS records that were configured."
echo ""
echo "===================================================="
"""

def get_panel_delete_script(panel_type):
    """Return the appropriate delete script based on panel type"""
    scripts = {
        'marzban': MARZBAN_DELETE_SCRIPT,
        'marzneshin': MARZNESHIN_DELETE_SCRIPT,
        '3x-ui': XUI_DELETE_SCRIPT,
        'pasarguard': PASARGUARD_DELETE_SCRIPT
    }
    return scripts.get(panel_type.lower(), "")
