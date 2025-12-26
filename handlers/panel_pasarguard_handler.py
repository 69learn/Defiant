import paramiko
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import add_pasarguard_panel
from utils.tunnel_utils import generate_panel_id
import time

PASARGUARD_SERVER_INFO = 0

async def panel_pasarguard_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = (
        "🖥 نصب PasarGuard\n\n"
        "📝 لطفاً اطلاعات سرور را درج کنید:\n\n"
        "`IP:`\n"
        "`User:`\n"
        "`Pass:`\n"
        "`SSH Port:`\n"
        "`Subdomain:`\n\n"
        "⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید:"
    )
    
    await query.edit_message_text(text=message, reply_markup=reply_markup, parse_mode='Markdown')
    return PASARGUARD_SERVER_INFO

async def get_pasarguard_server_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    try:
        lines = update.message.text.strip().split('\n')
        
        if len(lines) < 5:
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "❌ فرمت اطلاعات اشتباه است. لطفاً دوباره تلاش کنید:\n\n"
                "`IP:`\n"
                "`User:`\n"
                "`Pass:`\n"
                "`SSH Port:`\n"
                "`Subdomain:`",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return PASARGUARD_SERVER_INFO
        
        def extract_value(line):
            """Extract value from line, handling both 'IP:value' and 'value' formats"""
            if ':' in line and not line.startswith('http'):
                parts = line.split(':', 1)
                return parts[1].strip()
            return line.strip()
        
        server_ip = extract_value(lines[0])
        server_user = extract_value(lines[1])
        server_pass = extract_value(lines[2])
        ssh_port = extract_value(lines[3])
        subdomain = extract_value(lines[4])
        
        context.user_data['pasarguard_server'] = {
            'ip': server_ip,
            'user': server_user,
            'pass': server_pass,
            'ssh_port': ssh_port,
            'subdomain': subdomain
        }
        
        status_message = await update.message.reply_text("⏳ در حال اتصال به سرور و نصب PasarGuard...")
        
        db_password = "modernvarefa43434dsd"
        
        # SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            ssh.connect(server_ip, port=int(ssh_port), username=server_user, password=server_pass, timeout=30)
            
            rand = random.randint(100, 999)
            admin_username = f"beshkanuser140m{rand}"
            admin_password = "BeshKan223355@DD"
            
            install_script = f'''#!/usr/bin/env bash
set -e

# ------------------------------
# تنظیمات
# ------------------------------
PASARGUARD_DB_PASSWORD="modernvarefa43434dsd"
MY_SUBDOMAIN="{subdomain}"
ADMIN_USER="{admin_username}"
ADMIN_PASS="{admin_password}"

# ------------------------------
# نصب expect و python3-pexpect
# ------------------------------
echo "[1/7] Installing expect and pexpect..."
apt-get update -qq
apt-get install -y expect python3-pexpect &>/dev/null

# ------------------------------
# دانلود اسکریپت Pasarguard
# ------------------------------
echo "[2/7] Downloading Pasarguard installation script..."
TMP_SCRIPT="/tmp/pasarguard.sh"
curl -sL https://github.com/PasarGuard/scripts/raw/main/pasarguard.sh -o $TMP_SCRIPT
chmod +x $TMP_SCRIPT

# ------------------------------
# اجرای نصب Pasarguard با پاسخ خودکار به تمام سوالات
# ------------------------------
echo "[3/7] Running Pasarguard installation (this may take a few minutes)..."

expect << 'EOF'
set timeout 240
spawn bash /tmp/pasarguard.sh install --database mysql

expect {{
    -re "Do you want to override the previous installation\\\\?" {{
        send "y\\r"
        exp_continue
    }}
    -re "Delete volumes\\\\?" {{
        send "y\\r"
        exp_continue
    }}
    -re "Enter the password for the database" {{
        send "modernvarefa43434dsd\\r"
        exp_continue
    }}
    -re "Do you want to install PasarGuard node\\\\?" {{
        send "y\\r"
        exp_continue
    }}
    -re "Do you want to use your own public certificate instead\\\\?" {{
        send "n\\r"
        exp_continue
    }}
    -re "Enter additional SAN entries.*press ENTER" {{
        send "\\r"
        exp_continue
    }}
    -re "Enter your API Key.*leave blank" {{
        send "\\r"
        exp_continue
    }}
    -re "Do you want to use REST protocol instead\\\\?" {{
        send "n\\r"
        exp_continue
    }}
    -re "Enter the SERVICE_PORT.*default" {{
        send "39022\\r"
        exp_continue
    }}
    -re "Do you want to install and start the systemd service" {{
        send "y\\r"
        exp_continue
    }}
    -re "Enter the API_PORT for node service.*default" {{
        send "39032\\r"
        exp_continue
    }}
    -re "Node installation completed successfully!" {{
        exit 0
    }}
    timeout {{
        exit 0
    }}
    eof {{
        exit 0
    }}
}}
wait
EOF

sleep 8

# ------------------------------
# بررسی وضعیت کانتینرها
# ------------------------------
echo "[4/7] Checking Docker containers status..."

if ! docker ps | grep -q pasarguard; then
    echo "Error: Pasarguard containers are not running"
    exit 1
fi

# ------------------------------
# نصب certbot و گرفتن سرتیفیکیت
# ------------------------------
echo "[5/7] Installing certbot and obtaining SSL certificate..."

cd /opt/pasarguard
docker compose stop

apt-get install -y certbot &>/dev/null

certbot certonly --standalone --agree-tos --register-unsafely-without-email -d $MY_SUBDOMAIN &>/dev/null

if [ ! -d "/etc/letsencrypt/live/$MY_SUBDOMAIN" ]; then
    echo "Error: SSL certificate not obtained"
    docker compose start
    exit 1
fi

# کپی سرتیفیکیت‌ها
mkdir -p /var/lib/pasarguard/certs
cp /etc/letsencrypt/live/$MY_SUBDOMAIN/fullchain.pem /var/lib/pasarguard/certs/fullchain.pem
cp /etc/letsencrypt/live/$MY_SUBDOMAIN/privkey.pem /var/lib/pasarguard/certs/privkey.pem
chmod 644 /var/lib/pasarguard/certs/*.pem

# ------------------------------
# تغییر فایل .env برای SSL
# ------------------------------
echo "[6/7] Configuring SSL in .env file..."
ENV_FILE="/opt/pasarguard/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found"
    exit 1
fi

sed -i '/UVICORN_SSL_CERTFILE/d' "$ENV_FILE"
sed -i '/UVICORN_SSL_KEYFILE/d' "$ENV_FILE"
sed -i '/# UVICORN_SSL_CERTFILE/d' "$ENV_FILE"
sed -i '/# UVICORN_SSL_KEYFILE/d' "$ENV_FILE"

echo "" >> "$ENV_FILE"
echo "# SSL Configuration" >> "$ENV_FILE"
echo "UVICORN_SSL_CERTFILE=/var/lib/pasarguard/certs/fullchain.pem" >> "$ENV_FILE"
echo "UVICORN_SSL_KEYFILE=/var/lib/pasarguard/certs/privkey.pem" >> "$ENV_FILE"

# راه‌اندازی مجدد Pasarguard
docker compose start

sleep 12

# ------------------------------
# ایجاد ادمین
# ------------------------------
echo "[7/7] Creating admin user..."

python3 << PYTHON_EOF
import pexpect
import sys

try:
    child = pexpect.spawn("pasarguard cli admins --create $ADMIN_USER")
    child.logfile = sys.stderr.buffer
    
    child.expect("Make this admin a sudo admin\\\\? \\\\[y/N\\\\]:", timeout=30)
    child.sendline("y")
    
    child.expect("Password:", timeout=30)
    child.sendline("$ADMIN_PASS")
    
    child.expect("Confirm Password:", timeout=30)
    child.sendline("$ADMIN_PASS")
    
    child.expect("Enable user notifications for this admin\\\\? \\\\[y/N\\\\]:", timeout=30)
    child.sendline("n")
    
    child.expect(pexpect.EOF, timeout=10)
    
    print("Admin user created successfully", file=sys.stderr)
    
except Exception as e:
    print(f"ERROR creating admin: {{str(e)}}", file=sys.stderr)
    sys.exit(1)
PYTHON_EOF

# ------------------------------
# ریستارت نهایی Pasarguard
# ------------------------------
nohup bash -c "cd /opt/pasarguard && pasarguard restart" > /dev/null 2>&1 &

sleep 5

# ------------------------------
# ذخیره اطلاعات نهایی
# ------------------------------
cat > /tmp/pasarguard_final_info_{user_id}.txt << FINAL_INFO_EOF
URL:https://$MY_SUBDOMAIN:8000/dashboard/
USERNAME:$ADMIN_USER
PASSWORD:$ADMIN_PASS
DB_PASSWORD:$PASARGUARD_DB_PASSWORD
PHPMYADMIN:http://$MY_SUBDOMAIN:8010
SSL_CERT:/var/lib/pasarguard/certs/fullchain.pem
SSL_KEY:/var/lib/pasarguard/certs/privkey.pem
SUBDOMAIN:$MY_SUBDOMAIN
FINAL_INFO_EOF

echo "PASARGUARD_INSTALL_COMPLETE"
'''
            
            # Upload script
            sftp = ssh.open_sftp()
            script_path = f'/tmp/install_pasarguard_{user_id}.sh'
            
            with sftp.open(script_path, 'w') as f:
                f.write(install_script)
            
            sftp.chmod(script_path, 0o755)
            sftp.close()
            
            stdin, stdout, stderr = ssh.exec_command(f'nohup bash {script_path} > /tmp/pasarguard_install.log 2>&1 & echo $!')
            pid = stdout.read().decode().strip()
            
            start_time = time.time()
            max_wait_time = 180
            last_update = 0
            dot_count = 0
            
            while time.time() - start_time < max_wait_time:
                stdin, stdout, stderr = ssh.exec_command(f'grep "PASARGUARD_INSTALL_COMPLETE" /tmp/pasarguard_install.log 2>/dev/null')
                completion_check = stdout.read().decode().strip()
                
                if completion_check:
                    break
                
                elapsed = int(time.time() - start_time)
                if elapsed - last_update >= 5:
                    dot_count = (dot_count + 1) % 4
                    dots = "." * dot_count
                    try:
                        await status_message.edit_text(
                            f"⏳ در حال نصب PasarGuard{dots}\n"
                            f"زمان سپری شده: {elapsed // 60}:{elapsed % 60:02d}\n"
                            f"لطفا صبر کنید..."
                        )
                    except:
                        pass
                    last_update = elapsed
                
                time.sleep(1)
            
            stdin, stdout, stderr = ssh.exec_command(f'cat /tmp/pasarguard_final_info_{user_id}.txt 2>/dev/null')
            final_info = stdout.read().decode('utf-8').strip()
            
            if not final_info:
                stdin, stdout, stderr = ssh.exec_command('tail -50 /tmp/pasarguard_install.log')
                install_log = stdout.read().decode('utf-8').strip()
                ssh.close()
                
                keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await status_message.edit_text(
                    f"⚠️ نصب با خطا مواجه شد\n\n"
                    f"آخرین خطوط لاگ:\n```\n{install_log[-1000:]}\n```",
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                return ConversationHandler.END
            
            ssh.close()
            
            info_dict = {}
            for line in final_info.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info_dict[key] = value
            
            panel_url = info_dict.get('URL', f"https://{subdomain}:8000/dashboard/")
            final_username = info_dict.get('USERNAME', admin_username)
            final_password = info_dict.get('PASSWORD', admin_password)
            db_pass = info_dict.get('DB_PASSWORD', db_password)
            phpmyadmin = info_dict.get('PHPMYADMIN', f"http://{subdomain}:8010")
            ssl_cert = info_dict.get('SSL_CERT', '/var/lib/pasarguard/certs/fullchain.pem')
            ssl_key = info_dict.get('SSL_KEY', '/var/lib/pasarguard/certs/privkey.pem')
            final_subdomain = info_dict.get('SUBDOMAIN', subdomain)
            
            panel_id = generate_panel_id()
            
            add_pasarguard_panel(
                panel_id=panel_id,
                user_id=user_id,
                server_ip=server_ip,
                server_port=8000,
                username=final_username,
                password=final_password,
                subdomain=final_subdomain,
                panel_url=panel_url,
                server_username=server_user,
                server_password=server_pass,
                ssh_port=int(ssh_port),
                db_password=db_pass
            )
            
            keyboard = [[InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            success_message = (
                "✅ پنل Pasarguard با موفقیت نصب شد\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Panel ID: `{panel_id}`\n\n"
                "🌐 اطلاعات دسترسی به پنل:\n\n"
                f"آدرس پنل:\n`{panel_url}`\n\n"
                f"👤 نام کاربری: `{final_username}`\n"
                f"🔑 رمز عبور: `{final_password}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "💾 اطلاعات دیتابیس:\n"
                f"🔐 Password: `{db_pass}`\n"
                f"📊 phpMyAdmin: `{phpmyadmin}`\n\n"
                "🔒 SSL Certificate:\n"
                "✓ Let's Encrypt certificate installed\n"
                f"📜 Certificate: `{ssl_cert}`\n"
                f"🔑 Private Key: `{ssl_key}`\n\n"
                "━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ نکات مهم:\n"
                "• این اطلاعات را ذخیره کنید\n"
                "• بعد از ورود، حتماً رمز عبور را تغییر دهید\n"
                "• پنل با گواهینامه SSL فعال شده است\n\n"
                "پنل شما آماده استفاده است ✅\n\n"
                "برای بازگشت به منو: /start"
            )
            
            await status_message.edit_text(success_message, reply_markup=reply_markup, parse_mode='Markdown')

        except paramiko.AuthenticationException:
            await update.message.reply_text("❌ خطا در احراز هویت! نام کاربری یا رمز عبور اشتباه است.")
        except paramiko.SSHException as e:
            await update.message.reply_text(f"❌ خطا در اتصال SSH: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در نصب: {str(e)}")
        finally:
            if ssh:
                ssh.close()
        
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطای سیستم: {str(e)}")
        return ConversationHandler.END
