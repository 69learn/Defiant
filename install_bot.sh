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
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║   Telegram Tunnel & Panel Bot Setup   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""

    # Step 0: Download and extract bot files from GitHub first
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 0: Downloading Bot Files${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    if ! command -v unzip &> /dev/null; then
        echo -e "${BLUE}→ Installing unzip utility...${NC}"
        apt-get install -y unzip >/dev/null 2>&1
        echo -e "${GREEN}✓ Unzip installed${NC}"
    else
        echo -e "${GREEN}✓ Unzip already available${NC}"
    fi

    if ! command -v wget &> /dev/null; then
        echo -e "${BLUE}→ Installing wget utility...${NC}"
        apt-get install -y wget >/dev/null 2>&1
        echo -e "${GREEN}✓ Wget installed${NC}"
    else
        echo -e "${GREEN}✓ Wget already available${NC}"
    fi

    if [ -d "$INSTALL_DIR" ]; then
        echo -e "${YELLOW}→ Removing old installation...${NC}"
        rm -rf "$INSTALL_DIR"
    fi

    echo -e "${BLUE}→ Creating installation directory...${NC}"
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR" || { echo -e "${RED}❌ Failed to access installation directory!${NC}"; return 1; }

    # Download bot files
    echo -e "${BLUE}→ Downloading bot files from GitHub...${NC}"
    wget -q --show-progress https://github.com/69learn/Defiant/releases/download/defiant/Defiant.zip -O Defiant.zip

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Bot files downloaded successfully${NC}"
    else
        echo -e "${RED}❌ Error downloading bot files!${NC}"
        return 1
    fi

    # Extract files
    echo -e "${BLUE}→ Extracting bot files...${NC}"
    unzip -q -o tunnelpanelbot.zip

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Bot files extracted successfully${NC}"
        rm -f tunnelpanelbot.zip
    else
        echo -e "${RED}❌ Error extracting bot files!${NC}"
        return 1
    fi

    echo ""

    # Step 1: Install prerequisites
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 1: Installing Prerequisites${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    echo -e "${BLUE}→ Updating system...${NC}"
    apt-get update -qq

    # Install Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${BLUE}→ Installing Python3...${NC}"
        apt-get install -y python3 python3-pip python3-venv >/dev/null 2>&1
        echo -e "${GREEN}✓ Python3 installed${NC}"
    else
        echo -e "${GREEN}✓ Python3 already installed${NC}"
    fi

    # Install MySQL
    if ! command -v mysql &> /dev/null; then
        echo -e "${BLUE}→ Installing MySQL Server...${NC}"
        DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server >/dev/null 2>&1
        systemctl start mysql
        systemctl enable mysql >/dev/null 2>&1
        echo -e "${GREEN}✓ MySQL Server installed${NC}"
    else
        echo -e "${GREEN}✓ MySQL Server already installed${NC}"
        # Ensure MySQL is running
        systemctl start mysql 2>/dev/null
    fi

    echo ""

    # Step 2: Database configuration
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 2: Database Configuration${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    read -p "$(echo -e ${BLUE}Enter database name ${GREEN}[default: telegram_bot]${NC}: )" DB_NAME
    DB_NAME=${DB_NAME:-telegram_bot}

    read -p "$(echo -e ${BLUE}Enter database username ${GREEN}[default: bot_user]${NC}: )" DB_USER
    DB_USER=${DB_USER:-bot_user}

    while true; do
        read -s -p "$(echo -e ${BLUE}Enter database password: ${NC})" DB_PASSWORD
        echo ""
        if [ -z "$DB_PASSWORD" ]; then
            echo -e "${RED}❌ Password cannot be empty!${NC}"
        else
            read -s -p "$(echo -e ${BLUE}Confirm database password: ${NC})" DB_PASSWORD_CONFIRM
            echo ""
            if [ "$DB_PASSWORD" = "$DB_PASSWORD_CONFIRM" ]; then
                break
            else
                echo -e "${RED}❌ Passwords do not match! Try again.${NC}"
            fi
        fi
    done

    echo -e "${GREEN}✓ Database information received${NC}"
    echo ""

    # Step 3: Create database and user
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 3: Creating Database${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    echo -e "${BLUE}→ Creating database and user...${NC}"

    mysql -u root << EOF 2>/dev/null
DROP DATABASE IF EXISTS $DB_NAME;
CREATE DATABASE $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
DROP USER IF EXISTS '$DB_USER'@'localhost';
CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Database '$DB_NAME' created successfully${NC}"
        echo -e "${GREEN}✓ User '$DB_USER' created successfully${NC}"
    else
        echo -e "${RED}❌ Error creating database!${NC}"
        return 1
    fi

    echo ""

    # Step 4: Telegram bot configuration (moved before installing dependencies)
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 4: Telegram Bot Configuration${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    while true; do
        read -p "$(echo -e ${BLUE}Enter Telegram bot token: ${NC})" BOT_TOKEN
        if [ -z "$BOT_TOKEN" ]; then
            echo -e "${RED}❌ Bot token cannot be empty!${NC}"
        else
            break
        fi
    done

    while true; do
        read -p "$(echo -e "${BLUE}Enter admin ID ${YELLOW}(optional, press Enter to skip)${NC}: ")" ADMIN_ID
        if [ -z "$ADMIN_ID" ]; then
            ADMIN_ID=0
            echo -e "${YELLOW}⚠ Admin ID skipped, set to 0${NC}"
            break
        elif [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
            break
        else
            echo -e "${RED}❌ Admin ID must be a number!${NC}"
        fi
    done

    echo -e "${GREEN}✓ Bot information received${NC}"
    echo ""

    # Step 5: Create .env file
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 5: Creating Configuration File${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    cat > "$INSTALL_DIR/.env" << EOF
# Telegram Bot Configuration
BOT_TOKEN=$BOT_TOKEN
ADMIN_ID=$ADMIN_ID

# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_USER=$DB_USER
MYSQL_PASSWORD=$DB_PASSWORD
MYSQL_DATABASE=$DB_NAME
MYSQL_PORT=3306

# Flask Configuration
FLASK_PORT=5000
FLASK_HOST=0.0.0.0

# Payment Configuration
CARD_NUMBER=6037997740087599
CARD_HOLDER=مهدی رستگاری
CARD_BANK=بانک ملی
MIN_PAYMENT_AMOUNT=100000

# Crypto Payment Configuration
TRON_WALLET_ADDRESS=TM9PdcVptFWBdb49DRgqru1wYXbVGnnSDh
TRONGRID_API_KEY=
CRYPTO_PAYMENT_TIMEOUT_MINUTES=20
USDT_TO_TOMAN_RATE=72000
EOF

    if [ -f "$INSTALL_DIR/.env" ]; then
        echo -e "${GREEN}✓ .env file created successfully${NC}"
    else
        echo -e "${RED}❌ Failed to create .env file!${NC}"
        return 1
    fi

    echo ""

    # Step 6: Install Python dependencies
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 6: Installing Python Libraries${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    echo -e "${BLUE}→ Installing dependencies from requirements.txt...${NC}"
    
    if [ ! -f "$INSTALL_DIR/requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt not found in $INSTALL_DIR!${NC}"
        echo -e "${YELLOW}   Listing directory contents:${NC}"
        ls -la "$INSTALL_DIR/"
        return 1
    fi

    # Install dependencies with visible progress
    cd "$INSTALL_DIR" || { echo -e "${RED}❌ Cannot change to installation directory${NC}"; return 1; }
    
    echo -e "${BLUE}→ Running: pip3 install -r requirements.txt${NC}"
    pip3 install --upgrade pip setuptools wheel 2>&1 | tail -3
    pip3 install -r requirements.txt 2>&1 | tail -10

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "${GREEN}✓ All Python libraries installed successfully${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies!${NC}"
        echo -e "${YELLOW}   Check the error messages above${NC}"
        return 1
    fi

    echo ""

    # Step 7: Create database tables
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 7: Creating Database Tables${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    echo -e "${BLUE}→ Initializing database structure...${NC}"
    echo -e "${BLUE}   Working directory: $INSTALL_DIR${NC}"

    # Verify database.py exists
    if [ ! -f "$INSTALL_DIR/database.py" ]; then
        echo -e "${RED}❌ database.py not found in $INSTALL_DIR!${NC}"
        return 1
    fi
    
    cd "$INSTALL_DIR" || { echo -e "${RED}❌ Failed to access installation directory!${NC}"; return 1; }
    
    # Run database initialization with detailed output
    python3 << PYEOF
import sys
import os

# Set working directory
os.chdir('$INSTALL_DIR')
sys.path.insert(0, '$INSTALL_DIR')

print('→ Loading database module...')
try:
    from database import init_database
    print('→ Running database initialization...')
    result = init_database()
    if result:
        print('✓ Database tables created successfully')
        sys.exit(0)
    else:
        print('❌ Database initialization returned False')
        sys.exit(1)
except ImportError as e:
    print(f'❌ Import error: {str(e)}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error during initialization: {str(e)}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

    DB_INIT_RESULT=$?
    
    if [ $DB_INIT_RESULT -eq 0 ]; then
        echo -e "${GREEN}✓ Database initialization completed${NC}"
    else
        echo -e "${RED}❌ Failed to initialize database!${NC}"
        echo -e "${YELLOW}   Please check:${NC}"
        echo -e "${YELLOW}   1. Database credentials in .env file${NC}"
        echo -e "${YELLOW}   2. MySQL service is running: systemctl status mysql${NC}"
        echo -e "${YELLOW}   3. Database user has proper permissions${NC}"
        read -p "$(echo -e ${YELLOW}Continue anyway? [y/N]: ${NC})" CONTINUE
        if [[ ! $CONTINUE =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi

    echo ""

    # Step 8: Create systemd service
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"
    echo -e "${YELLOW}Step 8: Setting Up Auto-start Service${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════${NC}"

    if [ ! -f "$INSTALL_DIR/telegram_bot.py" ]; then
        echo -e "${RED}❌ telegram_bot.py not found in $INSTALL_DIR!${NC}"
        echo -e "${YELLOW}   Cannot create systemd service${NC}"
        return 1
    fi

    echo -e "${BLUE}→ Creating systemd service file...${NC}"
    
    cat > /etc/systemd/system/telegram-bot.service << EOF
[Unit]
Description=Telegram Tunnel Panel Bot
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 $INSTALL_DIR/telegram_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=telegram-bot

[Install]
WantedBy=multi-user.target
EOF

    if [ ! -f /etc/systemd/system/telegram-bot.service ]; then
        echo -e "${RED}❌ Failed to create service file!${NC}"
        return 1
    fi

    echo -e "${BLUE}→ Reloading systemd daemon...${NC}"
    systemctl daemon-reload
    
    echo -e "${BLUE}→ Enabling auto-start on boot...${NC}"
    systemctl enable telegram-bot.service >/dev/null 2>&1

    echo -e "${GREEN}✓ Auto-start service configured${NC}"
    echo ""

    # Installation summary
    echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║      Installation Completed! ✨        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${BLUE}📋 Configuration Summary:${NC}"
    echo -e "${YELLOW}  • Installation Path:${NC} $INSTALL_DIR"
    echo -e "${YELLOW}  • Database Name:${NC} $DB_NAME"
    echo -e "${YELLOW}  • Database User:${NC} $DB_USER"
    echo -e "${YELLOW}  • Bot Token:${NC} ${BOT_TOKEN:0:20}..."
    echo -e "${YELLOW}  • Admin ID:${NC} $ADMIN_ID"
    echo ""

    echo -e "${BLUE}🚀 Bot Management Commands:${NC}"
    echo ""
    echo -e "${GREEN}  Start bot:${NC}"
    echo -e "    systemctl start telegram-bot"
    echo ""
    echo -e "${GREEN}  Stop bot:${NC}"
    echo -e "    systemctl stop telegram-bot"
    echo ""
    echo -e "${GREEN}  Restart bot:${NC}"
    echo -e "    systemctl restart telegram-bot"
    echo ""
    echo -e "${GREEN}  Check status:${NC}"
    echo -e "    systemctl status telegram-bot"
    echo ""
    echo -e "${GREEN}  View logs:${NC}"
    echo -e "    journalctl -u telegram-bot -f"
    echo ""

    # Auto-start bot
    read -p "$(echo -e ${BLUE}Do you want to start the bot now? ${GREEN}[Y/n]${NC}: )" START_NOW
    START_NOW=${START_NOW:-Y}

    if [[ $START_NOW =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${BLUE}→ Starting bot...${NC}"
        systemctl start telegram-bot
        
        sleep 3
        
        if systemctl is-active --quiet telegram-bot; then
            echo -e "${GREEN}✓ Bot started successfully!${NC}"
            echo ""
            echo -e "${GREEN}🎉 Your bot is now running!${NC}"
            echo -e "${YELLOW}   You can now chat with your bot on Telegram.${NC}"
        else
            echo -e "${RED}❌ Error starting bot!${NC}"
            echo -e "${YELLOW}   View error details with:${NC}"
            echo -e "   journalctl -u telegram-bot -n 50"
        fi
    else
        echo ""
        echo -e "${YELLOW}To manually start the bot later, use:${NC}"
        echo -e "${GREEN}  systemctl start telegram-bot${NC}"
    fi

    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${GREEN}✨ Installation Complete! Good Luck! ✨${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    
    read -p "Press Enter to return to main menu..."
}

# Function to update bot
update_bot() {
    echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║         Updating Bot                   ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    if [ ! -d "$INSTALL_DIR" ]; then
        echo -e "${RED}❌ Bot is not installed! Please install it first.${NC}"
        sleep 3
        return 1
    fi
    
    cd "$INSTALL_DIR" || { echo -e "${RED}❌ Failed to access installation directory!${NC}"; return 1; }
    
    if systemctl is-active --quiet telegram-bot; then
        echo -e "${YELLOW}→ Stopping bot...${NC}"
        systemctl stop telegram-bot
    fi
    
    echo -e "${BLUE}→ Updating Python dependencies...${NC}"
    pip3 install -r requirements.txt --upgrade --quiet
    
    echo -e "${BLUE}→ Reloading systemd daemon...${NC}"
    systemctl daemon-reload
    
    echo -e "${GREEN}✓ Update completed${NC}"
    echo ""
    
    read -p "$(echo -e ${BLUE}Do you want to start the bot now? ${GREEN}[Y/n]${NC}: )" START_NOW
    START_NOW=${START_NOW:-Y}
    
    if [[ $START_NOW =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}→ Starting bot...${NC}"
        systemctl start telegram-bot
        sleep 2
        
        if systemctl is-active --quiet telegram-bot; then
            echo -e "${GREEN}✓ Bot restarted successfully!${NC}"
        else
            echo -e "${RED}❌ Error starting bot!${NC}"
        fi
    fi
    
    echo ""
    read -p "Press Enter to return to main menu..."
}

# Function to uninstall bot
uninstall_bot() {
    echo -e "${RED}╔════════════════════════════════════════╗${NC}"
    echo -e "${RED}║         Uninstalling Bot               ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════╝${NC}"
    echo ""
    
    read -p "$(echo -e ${RED}Are you sure you want to uninstall? This will remove the service but keep database. ${YELLOW}[y/N]${NC}: )" CONFIRM
    
    if [[ ! $CONFIRM =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Uninstall cancelled.${NC}"
        sleep 2
        return
    fi
    
    echo ""
    echo -e "${YELLOW}→ Stopping bot service...${NC}"
    systemctl stop telegram-bot 2>/dev/null
    
    echo -e "${YELLOW}→ Disabling bot service...${NC}"
    systemctl disable telegram-bot 2>/dev/null
    
    echo -e "${YELLOW}→ Removing service file...${NC}"
    rm -f /etc/systemd/system/telegram-bot.service
    
    echo -e "${YELLOW}→ Reloading systemd...${NC}"
    systemctl daemon-reload
    
    echo ""
    echo -e "${GREEN}✓ Bot service uninstalled${NC}"
    echo -e "${YELLOW}Note: Bot files in $INSTALL_DIR and database were kept.${NC}"
    echo -e "${YELLOW}      To remove completely, delete: $INSTALL_DIR${NC}"
    echo ""
    
    read -p "Press Enter to return to main menu..."
}

# Check root access
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run this script with root access${NC}"
    echo -e "${YELLOW}Usage: sudo bash install_bot.sh${NC}"
    exit 1
fi

# Main loop
while true; do
    show_menu
    read -p "$(echo -e ${CYAN}Enter your choice [0-3]: ${NC})" choice
    
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
            echo ""
            echo -e "${GREEN}Thank you for using DEFIANT Bot Manager!${NC}"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            sleep 2
            ;;
    esac
done
