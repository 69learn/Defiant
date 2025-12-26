from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import add_user
import paramiko
import time
import uuid
from utils.tunnel_utils import generate_panel_id
import asyncio

MARZNESHIN_SERVER_INFO = 0

async def panel_marzneshin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="🖥 نصب Marzneshin\n\n"
             "📝 لطفاً اطلاعات سرور را درج کنید:\n\n"
             "IP:\n"
             "User:\n"
             "Pass:\n"
             "SSH Port:\n"
             "Subdomain:\n\n"
             "⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید:",
        reply_markup=reply_markup
    )
    
    return MARZNESHIN_SERVER_INFO

def extract_value(line):
    """Extract value after colon if exists, otherwise return the line"""
    if ':' in line:
        return line.split(':', 1)[1].strip()
    return line.strip()

async def get_marzneshin_server_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    add_user(user.id, user.username, user.first_name)
    
    text = update.message.text.strip()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    if len(lines) < 5:
        await update.message.reply_text(
            "⚠️ اطلاعات ناقص است. لطفاً تمام موارد را وارد کنید:\n"
            "IP:\n"
            "User:\n"
            "Pass:\n"
            "SSH Port:\n"
            "Subdomain:"
        )
        return MARZNESHIN_SERVER_INFO
    
    try:
        server_ip = extract_value(lines[0])
        server_username = extract_value(lines[1])
        server_password = extract_value(lines[2])
        ssh_port = int(extract_value(lines[3]))
        subdomain = extract_value(lines[4])
        
        panel_id = generate_panel_id()
        
        status_message = await update.message.reply_text(
            "⏳ در حال نصب Marzneshin...\n"
            "زمان سپری شده: 0:00\n"
            "این فرآیند ممکن است چند دقیقه طول بکشد."
        )
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(server_ip, port=ssh_port, username=server_username, password=server_password, timeout=30)
            
            sftp = ssh.open_sftp()
            
            marzneshin_db_password = "beshkan223355@!DDnm"
            
            install_script = f'''#!/usr/bin/env bash
set -e

# ============================================================
# Initial Configuration
# ============================================================
MARZNESHIN_DB_PASSWORD="{marzneshin_db_password}"
TMP_SCRIPT="/tmp/marzneshin.sh"
ENV_FILE="/etc/opt/marzneshin/.env"
SUBDOMAIN="{subdomain}"

echo "Starting automated Marzneshin installation..."

# ============================================================
# Function to check and install prerequisites
# ============================================================
install_if_missing() {{
    local pkg="$1"
    if ! command -v "$pkg" &>/dev/null; then
        echo "$pkg not found. Installing..."
        apt-get update -qq
        apt-get install -y "$pkg"
    else
        echo "$pkg already installed."
    fi
}}

echo "Checking prerequisites..."
install_if_missing curl
install_if_missing expect
install_if_missing python3
install_if_missing certbot

# ============================================================
# Download main Marzneshin script
# ============================================================
echo "Downloading Marzneshin installer..."
curl -sL https://github.com/marzneshin/Marzneshin/raw/master/script.sh -o "$TMP_SCRIPT"
chmod +x "$TMP_SCRIPT"

# ============================================================
# Install Marzneshin with fixed database password
# ============================================================
echo "Installing Marzneshin..."
expect << EOF
spawn bash $TMP_SCRIPT install --database mysql
expect "Enter the password for the marzneshin user*"
send "$MARZNESHIN_DB_PASSWORD\\r"
expect eof
EOF

# Wait for installation to complete
sleep 10

# ============================================================
# Obtain SSL certificate for domain
# ============================================================
echo "Obtaining SSL certificate for $SUBDOMAIN..."
certbot certonly --standalone --agree-tos --register-unsafely-without-email -d "$SUBDOMAIN"

# ============================================================
# Copy certificates to Marzneshin directory
# ============================================================
echo "Copying SSL certificates..."
mkdir -p /var/lib/marzneshin/certs
cp "/etc/letsencrypt/live/$SUBDOMAIN/fullchain.pem" /var/lib/marzneshin/certs/fullchain.pem
cp "/etc/letsencrypt/live/$SUBDOMAIN/privkey.pem" /var/lib/marzneshin/certs/privkey.pem

# ============================================================
# Configure .env file for SSL activation
# ============================================================
echo "Updating .env file for SSL..."
sed -i 's|# UVICORN_SSL_CERTFILE.*|UVICORN_SSL_CERTFILE="/var/lib/marzneshin/certs/fullchain.pem"|' "$ENV_FILE"
sed -i 's|# UVICORN_SSL_KEYFILE.*|UVICORN_SSL_KEYFILE="/var/lib/marzneshin/certs/privkey.pem"|' "$ENV_FILE"

# ============================================================
# Restart Marzneshin
# ============================================================
echo "Restarting Marzneshin..."
bash "$TMP_SCRIPT" restart &>/dev/null &
sleep 5

# ============================================================
# Install pexpect for Python admin user creation
# ============================================================
echo "Installing pexpect..."
pip3 install pexpect &>/dev/null || true

# ============================================================
# Execute Python to create admin user
# ============================================================
echo "Creating admin user..."
python3 << 'PYEOF'
import pexpect
import random

rand = random.randint(100, 999)
username = f"beshkanuser140m{{rand}}"
password = "beshkan223355@ddnm"

print(username)
print(password)

child = pexpect.spawn("marzneshin cli admin create --sudo")
child.expect("Username")
child.sendline(username)
child.expect("Password")
child.sendline(password)
child.expect("Repeat")
child.sendline(password)
child.expect(pexpect.EOF)
PYEOF

# ============================================================
# Display final result
# ============================================================
echo "===================================================="
echo "   Marzneshin Installation Completed Successfully"
echo "----------------------------------------------------"
echo "   Panel Management Address:"
echo "   https://$SUBDOMAIN:8000/dashboard/"
echo "===================================================="
echo "MARZNESHIN_INSTALL_COMPLETE"
'''
            
            script_path = '/tmp/install_marzneshin_full.sh'
            with sftp.file(script_path, 'w') as f:
                f.write(install_script)
            sftp.close()
            
            ssh.exec_command(f'chmod +x {script_path}')
            
            stdin, stdout, stderr = ssh.exec_command(f'nohup bash {script_path} > /tmp/marzneshin_install.log 2>&1 & echo $!')
            pid = stdout.read().decode().strip()
            
            start_time = time.time()
            max_wait_time = 600  # 10 minutes timeout
            installation_complete = False
            last_update = 0
            
            while time.time() - start_time < max_wait_time:
                await asyncio.sleep(1)
                elapsed = int(time.time() - start_time)
                minutes = elapsed // 60
                seconds = elapsed % 60
                
                # Check if process is still running
                try:
                    stdin_check, stdout_check, stderr_check = ssh.exec_command(f'ps -p {pid} > /dev/null && echo "running" || echo "done"')
                    status = stdout_check.read().decode().strip()
                    if status == "done":
                        installation_complete = True
                        break
                except:
                    pass
                
                # Update message every 5 seconds to avoid rate limiting
                if elapsed - last_update >= 5:
                    last_update = elapsed
                    try:
                        await status_message.edit_text(
                            f"⏳ در حال نصب Marzneshin...\n"
                            f"زمان سپری شده: {minutes}:{seconds:02d}\n"
                            f"لطفا صبر کنید..."
                        )
                    except:
                        pass
            
            if not installation_complete:
                await status_message.edit_text(
                    "❌ خطا: زمان نصب به پایان رسید\n"
                    "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
                )
                ssh.close()
                return ConversationHandler.END
            
            stdin, stdout, stderr = ssh.exec_command('cat /tmp/marzneshin_install.log')
            output = stdout.read().decode()
            
            admin_user = None
            admin_pass = None
            lines = output.split('\n')
            
            # Look for the two lines printed by Python (username then password)
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('beshkanuser140m'):
                    admin_user = line
                    # Password should be on next line
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line.startswith('beshkan223355'):
                            admin_pass = next_line
                    break
            
            if not admin_user or not admin_pass:
                import random
                rand = random.randint(100, 999)
                admin_user = f"beshkanuser140m{rand}"
                admin_pass = "beshkan223355@ddnm"
            
            panel_url = f"https://{subdomain}:8000/dashboard/"
            
            from database import add_marzneshin_panel
            add_marzneshin_panel(
                panel_id=panel_id,
                user_id=user.id,
                server_ip=server_ip,
                server_port=8000,
                username=admin_user,
                password=admin_pass,
                subdomain=subdomain,
                panel_url=panel_url,
                server_username=server_username,
                server_password=server_password,
                ssh_port=ssh_port
            )
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_message.edit_text(
                "✅ پنل Marzneshin با موفقیت نصب شد\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Panel ID: `{panel_id}`\n\n"
                "🌐 اطلاعات دسترسی به پنل:\n\n"
                "آدرس پنل:\n"
                f"`{panel_url}`\n\n"
                f"👤 نام کاربری: `{admin_user}`\n\n"
                f"🔑 رمز عبور: `{admin_pass}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ نکات مهم:\n"
                "• این اطلاعات را ذخیره کنید\n"
                "• بعد از ورود، حتماً رمز عبور را تغییر دهید\n"
                "• پنل با گواهینامه SSL فعال شده است\n\n"
                "پنل شما آماده استفاده است ✅",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            await status_message.edit_text(f"❌ خطا در نصب پنل: {str(e)}")
        finally:
            ssh.close()
        
        return ConversationHandler.END

    except ValueError as e:
        await update.message.reply_text(
            f"⚠️ خطا در پردازش اطلاعات: {str(e)}\n"
            "لطفاً SSH Port را به صورت عدد وارد کنید."
        )
        return MARZNESHIN_SERVER_INFO
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}")
        return ConversationHandler.END
