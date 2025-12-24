from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.ssh_manager import SSHManager
from database import add_user, add_marzban_panel
from utils.tunnel_utils import generate_panel_id
import asyncio
import time

MARZBAN_SERVER_INFO = 0

async def panel_marzban_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Marzban panel installation process"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="🖥 نصب Marzban\n\n"
             "📝 لطفاً اطلاعات سرور را درج کنید:\n\n"
             "IP:\n"
             "User:\n"
             "Pass:\n"
             "SSH Port:\n"
             "Subdomain:\n\n"
             "⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید:",
        reply_markup=reply_markup
    )
    
    return MARZBAN_SERVER_INFO

async def get_marzban_server_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process Marzban server information and install panel"""
    user = update.message.from_user
    add_user(user.id, user.username, user.first_name)
    
    text = update.message.text
    
    # Parse server information
    info = {}
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            info[key] = value
    
    # Validate required fields
    required_fields = ['ip', 'user', 'pass', 'ssh port', 'subdomain']
    missing = [f for f in required_fields if f not in info]
    
    if missing:
        await update.message.reply_text(
            f"❌ فیلدهای زیر موجود نیستند:\n{', '.join(missing)}\n\n"
            "لطفاً دوباره اطلاعات را به صورت صحیح ارسال کنید."
        )
        return MARZBAN_SERVER_INFO
    
    server_ip = info['ip']
    username = info['user']
    password = info['pass']
    ssh_port = int(info.get('ssh port', 22))
    subdomain = info['subdomain']
    
    status_message = await update.message.reply_text(
        f"✅ اطلاعات دریافت شد:\n\n"
        f"🌐 IP: {server_ip}\n"
        f"👤 User: {username}\n"
        f"🔌 SSH Port: {ssh_port}\n"
        f"🌍 Subdomain: {subdomain}\n\n"
        f"⏳ در حال نصب Marzban...\n"
        f"زمان سپری شده: 0:00"
    )
    
    panel_id = generate_panel_id()
    
    # Marzban installation script
    install_script = f"""#!/usr/bin/env bash
set -e

# Configuration
MARZBAN_DB_PASSWORD="modernvarefa43434dsd"
TMP_SCRIPT="/tmp/marzban.sh"
ENV_FILE="/opt/marzban/.env"
SUBDOMAIN="{subdomain}"

echo "Starting automated Marzban installation..."

# Download Marzban installer
echo "Downloading Marzban installer..."
curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh -o "$TMP_SCRIPT"
chmod +x "$TMP_SCRIPT"

# Install expect for automated password entry
if ! command -v expect &>/dev/null; then
    echo "Installing expect..."
    apt-get update -qq
    apt-get install -y expect
fi

# Install Marzban with MySQL
echo "Installing Marzban with MySQL..."
expect << 'EOF'
spawn bash /tmp/marzban.sh install --database mysql
expect "Enter the password for the marzban user*"
send "modernvarefa43434dsd\\r"
expect eof
EOF

# Install certbot
echo "Installing certbot..."
apt-get install -y certbot

# Obtain SSL certificate
echo "Obtaining SSL certificate for $SUBDOMAIN..."
certbot certonly --standalone --agree-tos --register-unsafely-without-email -d "$SUBDOMAIN"

# Copy certificates to Marzban directory
echo "Copying SSL certificates..."
mkdir -p /var/lib/marzban/certs
cp "/etc/letsencrypt/live/$SUBDOMAIN/fullchain.pem" /var/lib/marzban/certs/fullchain.pem
cp "/etc/letsencrypt/live/$SUBDOMAIN/privkey.pem" /var/lib/marzban/certs/privkey.pem

# Update .env file for SSL
echo "Updating .env file for SSL..."
sed -i 's|# UVICORN_SSL_CERTFILE.*|UVICORN_SSL_CERTFILE="/var/lib/marzban/certs/fullchain.pem"|' "$ENV_FILE"
sed -i 's|# UVICORN_SSL_KEYFILE.*|UVICORN_SSL_KEYFILE="/var/lib/marzban/certs/privkey.pem"|' "$ENV_FILE"
sed -i 's|# SUDO_USERNAME.*|SUDO_USERNAME="admin"|' "$ENV_FILE"
sed -i 's|# SUDO_PASSWORD.*|SUDO_PASSWORD="admin"|' "$ENV_FILE"

# Restart Marzban
echo "Restarting Marzban..."
bash "$TMP_SCRIPT" restart &>/dev/null &
sleep 5

# Mark installation as complete
echo "DONE" > /tmp/marzban_install_complete.txt

# Output success message
echo "===================================================="
echo "   Marzban Installation Completed Successfully"
echo "----------------------------------------------------"
echo "   Panel URL: https://$SUBDOMAIN:8000/dashboard/"
echo "   Username: admin"
echo "   Password: admin"
echo "===================================================="
"""
    
    try:
        # Connect to server
        ssh = SSHManager()
        if not ssh.connect(server_ip, ssh_port, username, password):
            await status_message.edit_text("❌ خطا در اتصال به سرور")
            return ConversationHandler.END
        
        ssh.execute_command("rm -f /tmp/marzban_install_complete.txt")
        ssh.upload_string(install_script, "/tmp/install_marzban_auto.sh")
        ssh.execute_command("chmod +x /tmp/install_marzban_auto.sh")
        
        # Execute installation in background
        ssh.execute_command("nohup bash /tmp/install_marzban_auto.sh > /tmp/install_marzban_output.log 2>&1 &")
        
        start_time = time.time()
        max_wait_time = 600  # 10 minutes for Marzban installation
        installation_complete = False
        last_update = 0
        
        while time.time() - start_time < max_wait_time:
            await asyncio.sleep(1)
            elapsed = int(time.time() - start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            
            # Check if installation is complete every second
            check_output, _ = ssh.execute_command("test -f /tmp/marzban_install_complete.txt && echo 'COMPLETE' || echo 'RUNNING'")
            
            if 'COMPLETE' in check_output:
                installation_complete = True
                break
            
            # Update timer display every 5 seconds to avoid rate limiting
            if elapsed - last_update >= 5:
                last_update = elapsed
                try:
                    await status_message.edit_text(
                        f"✅ اطلاعات دریافت شد:\n\n"
                        f"🌐 IP: {server_ip}\n"
                        f"👤 User: {username}\n"
                        f"🔌 SSH Port: {ssh_port}\n"
                        f"🌍 Subdomain: {subdomain}\n\n"
                        f"⏳ در حال نصب Marzban...\n"
                        f"زمان سپری شده: {minutes}:{seconds:02d}"
                    )
                except Exception as e:
                    print(f"[v0] Timer update error: {e}")
        
        if not installation_complete:
            await status_message.edit_text(
                "❌ نصب پنل بیش از حد طول کشید (تایم اوت)\n\n"
                "لطفاً به سرور متصل شوید و وضعیت را بررسی کنید."
            )
            ssh.disconnect()
            return ConversationHandler.END
        
        await asyncio.sleep(2)
        
        # Save panel to database
        panel_username = 'admin'
        panel_password = 'admin'
        panel_port = 8000
        panel_url = f"https://{subdomain}:8000/dashboard/"
        
        add_marzban_panel(
            panel_id=panel_id,
            user_id=user.id,
            server_ip=server_ip,
            server_port=panel_port,
            username=panel_username,
            password=panel_password,
            subdomain=subdomain,
            panel_url=panel_url,
            server_username=username,
            server_password=password,
            ssh_port=ssh_port
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Send success message
        message = (
            "✅ پنل Marzban با موفقیت نصب شد\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Panel ID: `{panel_id}`\n\n"
            "🌐 اطلاعات دسترسی به پنل:\n\n"
            f"آدرس پنل:\n`{panel_url}`\n\n"
            f"👤 نام کاربری: `{panel_username}`\n"
            f"🔑 رمز عبور: `{panel_password}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ نکات مهم:\n"
            "• این اطلاعات را ذخیره کنید\n"
            "• بعد از ورود، حتماً رمز عبور را تغییر دهید\n"
            "• پنل با گواهینامه SSL فعال شده است\n\n"
            "پنل شما آماده استفاده است ✅"
        )
        
        await status_message.edit_text(message, parse_mode='Markdown', reply_markup=reply_markup)
        
        # Disconnect from server
        ssh.disconnect()
        
    except Exception as e:
        await status_message.edit_text(
            f"❌ خطا در نصب پنل:\n{str(e)}\n\n"
            "لطفاً اطلاعات سرور را بررسی کنید."
        )
    
    return ConversationHandler.END
