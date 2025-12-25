#!/bin/bash

# Colors for better output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="/root/telegram-bot"

# Function to display main menu
show_menu() {
    clear
    echo ""
    echo -e "${BOLD}${CYAN}"
    echo "██████╗ ███████╗███████╗██╗ █████╗ ███╗   ██╗████████╗"
    echo "██╔══██╗██╔════╝██╔════╝██║██╔══██╗████╗  ██║╚══██╔══╝"
    echo "██║  ██║█████╗  █████╗  ██║███████║██╔██╗ ██║   ██║   "
    echo "██║  ██║██╔══╝  ██╔══╝  ██║██╔══██║██║╚██╗██║   ██║   "
    echo "██████╔╝███████╗██║     ██║██║  ██║██║ ╚████║   ██║   "
    echo "╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝   "
    echo -e "${NC}"
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}  📱 Telegram Group:${NC}   t.me/sixti9learn"
    echo -e "${GREEN}  📢 Telegram Channel:${NC} t.me/sixtininelearn1"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BOLD}${BLUE}  Please select an option:${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} Install Bot"
    echo -e "  ${YELLOW}2)${NC} Update Bot"
    echo -e "  ${RED}3)${NC} Uninstall Bot"
    echo -e "  ${CYAN}0)${NC} Exit"
    echo ""
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Function to install bot
install_bot() {
    clear
    echo -e "${BOLD}${GREEN}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║     DEFIANT BOT - INSTALLATION WIZARD         ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""

    # Clean previous installation
    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}→ Removing previous installation...${NC}"
        systemctl stop telegram-bot 2>/dev/null
        rm -rf "$INSTALL_DIR"
        echo -e "${GREEN}✓ Previous installation removed${NC}"
        echo ""
    fi

    # Create directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR" || exit 1

    # STEP 1: Install system requirements
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 1: Installing System Requirements${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    apt-get update -qq
    apt-get install -y wget unzip python3 python3-pip mysql-server -qq

    systemctl start mysql
    systemctl enable mysql

    echo -e "${GREEN}✓ System requirements installed${NC}"
    echo ""

    # STEP 2: Download bot files
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 2: Downloading Bot Files${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    wget -q --show-progress https://github.com/69learn/Defiant/releases/download/defiant/defiant.zip
    
    if [ ! -f "defiant.zip" ]; then
        echo -e "${RED}✗ Download failed!${NC}"
        echo -e "${YELLOW}Please check the URL and try again.${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi

    unzip -q defiant.zip
    rm -f defiant.zip

    echo -e "${GREEN}✓ Bot files downloaded and extracted${NC}"
    echo ""

    # STEP 3: Database configuration
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 3: Database Configuration${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    read -p "Database name [telegram_bot]: " DB_NAME
    DB_NAME=${DB_NAME:-telegram_bot}

    read -p "Database user [bot_user]: " DB_USER
    DB_USER=${DB_USER:-bot_user}

    read -sp "Database password: " DB_PASSWORD
    echo ""

    if [ -z "$DB_PASSWORD" ]; then
        echo -e "${RED}✗ Password cannot be empty!${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi

    echo ""
    echo -e "${BLUE}→ Creating database...${NC}"

    mysql -u root <<EOF
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
DROP USER IF EXISTS '$DB_USER'@'localhost';
CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

    echo -e "${GREEN}✓ Database created: $DB_NAME${NC}"
    echo ""

    # STEP 4: Bot configuration
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 4: Bot Configuration${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    read -p "Telegram Bot Token: " BOT_TOKEN

    if [ -z "$BOT_TOKEN" ]; then
        echo -e "${RED}✗ Bot token cannot be empty!${NC}"
        read -p "Press Enter to exit..."
        exit 1
    fi

    read -p "Admin Telegram ID: " ADMIN_ID

    if [ -z "$ADMIN_ID" ]; then
        ADMIN_ID=0
    fi

    echo ""
    echo -e "${BLUE}→ Creating configuration file...${NC}"

    cat > .env <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID

MYSQL_HOST=localhost
MYSQL_USER=$DB_USER
MYSQL_PASSWORD=$DB_PASSWORD
MYSQL_DATABASE=$DB_NAME
MYSQL_PORT=3306

FLASK_PORT=5000
FLASK_HOST=0.0.0.0

CARD_NUMBER=6037997740087599
CARD_HOLDER=مهدی رستگاری
CARD_BANK=بانک ملی
MIN_PAYMENT_AMOUNT=100000

TRON_WALLET_ADDRESS=TM9PdcVptFWBdb49DRgqru1wYXbVGnnSDh
TRONGRID_API_KEY=
CRYPTO_PAYMENT_TIMEOUT_MINUTES=20
USDT_TO_TOMAN_RATE=72000
EOF

    echo -e "${GREEN}✓ Configuration file created${NC}"
    echo ""

    # STEP 5: Install Python dependencies
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 5: Installing Python Dependencies${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    pip3 install --upgrade pip -q
    pip3 install -r requirements.txt -q

    echo -e "${GREEN}✓ Python dependencies installed${NC}"
    echo ""

    # STEP 6: Initialize database
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 6: Initializing Database${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    python3 -c "from database import init_database; init_database()"

    echo -e "${GREEN}✓ Database initialized${NC}"
    echo ""

    # STEP 7: Create systemd service
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 7: Creating System Service${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    cat > /etc/systemd/system/telegram-bot.service <<EOF
[Unit]
Description=Telegram Defiant Bot
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable telegram-bot

    echo -e "${GREEN}✓ System service created${NC}"
    echo ""

    # STEP 8: Start bot
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}STEP 8: Starting Bot${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    systemctl start telegram-bot
    sleep 3

    if systemctl is-active --quiet telegram-bot; then
        echo -e "${GREEN}✓ Bot started successfully!${NC}"
    else
        echo -e "${RED}✗ Bot failed to start${NC}"
        echo -e "${YELLOW}Check logs with: journalctl -u telegram-bot -f${NC}"
    fi

    echo ""
    echo -e "${BOLD}${GREEN}"
    echo "╔═══════════════════════════════════════════════╗"
    echo "║         ✓ INSTALLATION COMPLETED              ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    echo -e "${YELLOW}Useful Commands:${NC}"
    echo -e "  ${GREEN}Start:${NC}   systemctl start telegram-bot"
    echo -e "  ${GREEN}Stop:${NC}    systemctl stop telegram-bot"
    echo -e "  ${GREEN}Restart:${NC} systemctl restart telegram-bot"
    echo -e "  ${GREEN}Status:${NC}  systemctl status telegram-bot"
    echo -e "  ${GREEN}Logs:${NC}    journalctl -u telegram-bot -f"
    echo ""
    
    read -p "Press Enter to return to menu..."
}

# Function to update bot
update_bot() {
    echo -e "${YELLOW}Updating bot...${NC}"
    
    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}Bot is not installed!${NC}"
        sleep 2
        return
    fi
    
    cd "$INSTALL_DIR"
    systemctl stop telegram-bot
    
    pip3 install -r requirements.txt --upgrade -q
    
    systemctl start telegram-bot
    
    echo -e "${GREEN}✓ Bot updated${NC}"
    sleep 2
}

# Function to uninstall bot
uninstall_bot() {
    echo -e "${RED}Uninstalling bot...${NC}"
    
    read -p "Are you sure? [y/N]: " CONFIRM
    
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        return
    fi
    
    systemctl stop telegram-bot 2>/dev/null
    systemctl disable telegram-bot 2>/dev/null
    rm -f /etc/systemd/system/telegram-bot.service
    systemctl daemon-reload
    rm -rf "$INSTALL_DIR"
    
    echo -e "${GREEN}✓ Bot uninstalled${NC}"
    sleep 2
}

# Main loop
while true; do
    show_menu
    read -p "Select option: " choice
    
    case $choice in
        1)
            install_bot
            ;;
        2)
            update_bot
            ;;
        3)
            uninstall_bot
            ;;
        0)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option!${NC}"
            sleep 1
            ;;
    esac
done
