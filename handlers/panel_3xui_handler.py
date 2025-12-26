from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from utils.ssh_manager import SSHManager
from database import add_user, add_3xui_panel
from utils.tunnel_utils import generate_panel_id
import re
import asyncio
import time

SERVER_INFO = 0

async def panel_3xui_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="🖥 نصب پنل 3x-ui\n\n"
             "📝 لطفاً اطلاعات سرور را درج کنید:\n\n"
             "`IP:`\n"
             "`User:`\n"
             "`Pass:`\n"
             "`SSH Port:`\n\n"
             "⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SERVER_INFO

async def get_server_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    print(f"[v0] User requesting panel install: user_id={user.id}, username={user.username}")
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
    required_fields = ['ip', 'user', 'pass', 'ssh port']
    missing = [f for f in required_fields if f not in info]
    
    if missing:
        await update.message.reply_text(
            f"❌ فیلدهای زیر موجود نیستند:\n{', '.join(missing)}\n\n"
            "لطفاً دوباره اطلاعات را به صورت صحیح ارسال کنید."
        )
        return SERVER_INFO
    
    server_ip = info['ip']
    username = info['user']
    password = info['pass']
    ssh_port = int(info.get('ssh port', 22))
    
    print(f"[v0] Server info parsed: IP={server_ip}, User={username}, SSH_Port={ssh_port}")
    
    # Confirm details
    status_message = await update.message.reply_text(
        f"✅ اطلاعات دریافت شد:\n\n"
        f"🌐 IP: {server_ip}\n"
        f"👤 User: {username}\n"
        f"🔌 SSH Port: {ssh_port}\n\n"
        f"⏳ در حال نصب پنل 3x-ui...\n"
        f"زمان سپری شده: 0:00"
    )
    
    panel_id = generate_panel_id()
    print(f"[v0] Generated panel_id: {panel_id}")
    
    install_script = """#!/usr/bin/env bash

# نصب expect اگر نصب نیست
if ! command -v expect >/dev/null 2>&1; then
    apt update -y >/dev/null 2>&1
    apt install expect -y >/dev/null 2>&1
fi

curl -Ls https://raw.githubusercontent.com/mhsanaei/3x-ui/master/install.sh -o /tmp/install_3xui.sh >/dev/null 2>&1
chmod +x /tmp/install_3xui.sh

# اجرای نصب با expect
expect << 'EOF' 2>&1 | tee /tmp/install_3xui_log.txt
set timeout -1
spawn bash /tmp/install_3xui.sh

expect {
    "customize the Panel Port" {
        send "y\\r"
    }
}

expect {
    "Please set up the panel port" {
        send "2087\\r"
    }
}

expect eof
EOF

# Mark installation as complete
echo "DONE" > /tmp/3xui_install_complete.txt
"""
    
    try:
        # Connect to server
        ssh = SSHManager()
        if not ssh.connect(server_ip, ssh_port, username, password):
            print(f"[v0] SSH connection failed to {server_ip}:{ssh_port}")
            await status_message.edit_text("❌ خطا در اتصال به سرور")
            return ConversationHandler.END
        
        print(f"[v0] SSH connection successful to {server_ip}:{ssh_port}")
        
        ssh.execute_command("rm -f /tmp/3xui_install_complete.txt /tmp/install_3xui_log.txt /tmp/install_3xui_output.log")
        ssh.upload_string(install_script, "/tmp/install_3xui_auto.sh")
        ssh.execute_command("chmod +x /tmp/install_3xui_auto.sh")
        
        # Execute installation in background
        print(f"[v0] Starting 3x-ui installation script...")
        ssh.execute_command("nohup bash /tmp/install_3xui_auto.sh > /tmp/install_3xui_output.log 2>&1 &")
        
        start_time = time.time()
        max_wait_time = 300  # Reduced to 5 minutes since install takes ~30 seconds
        installation_complete = False
        last_update = 0
        
        while time.time() - start_time < max_wait_time:
            await asyncio.sleep(1)
            elapsed = int(time.time() - start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            
            # Check if installation is complete every second
            check_output, _ = ssh.execute_command("test -f /tmp/3xui_install_complete.txt && echo 'COMPLETE' || echo 'RUNNING'")
            
            if 'COMPLETE' in check_output:
                print(f"[v0] Installation completed after {elapsed} seconds")
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
                        f"🔌 SSH Port: {ssh_port}\n\n"
                        f"⏳ در حال نصب پنل 3x-ui...\n"
                        f"زمان سپری شده: {minutes}:{seconds:02d}"
                    )
                except Exception as e:
                    print(f"[v0] Timer update error: {e}")
        
        if not installation_complete:
            print(f"[v0] Installation timed out after {max_wait_time} seconds")
            await status_message.edit_text(
                "❌ نصب پنل بیش از حد طول کشید (تایم اوت)\n\n"
                "لطفاً به سرور متصل شوید و وضعیت را بررسی کنید:\n"
                "`x-ui`"
            )
            ssh.disconnect()
            return ConversationHandler.END
        
        await asyncio.sleep(2)
        
        print(f"[v0] Reading installation output...")
        output, _ = ssh.execute_command("cat /tmp/install_3xui_log.txt 2>/dev/null || cat /tmp/install_3xui_output.log")
        print(f"[v0] Installation output length: {len(output)} characters")
        
        if output:
            print(f"[v0] Output preview: {output[:500]}")
        
        panel_info = extract_panel_info(output)
        print(f"[v0] Extracted panel info: {panel_info}")
        
        panel_username = panel_info['username'] if panel_info and panel_info['username'] != 'N/A' else 'admin'
        panel_password = panel_info['password'] if panel_info and panel_info['password'] != 'N/A' else 'admin'
        panel_port = int(panel_info['port']) if panel_info and panel_info['port'] != 'N/A' else 2087
        web_path = panel_info['web_path'] if panel_info and panel_info['web_path'] != 'N/A' else '/'
        
        print(f"[v0] Saving panel to database: panel_id={panel_id}")
        
        save_result = add_3xui_panel(
            panel_id=panel_id,
            user_id=user.id,
            server_ip=server_ip,
            server_port=panel_port,
            username=panel_username,
            password=panel_password,
            web_path=web_path,
            server_username=username,
            server_password=password,
            ssh_port=ssh_port
        )
        
        if save_result:
            print(f"[v0] Panel saved successfully")
        else:
            print(f"[v0] Failed to save panel")
        
        if panel_info and panel_info['url'] != 'N/A':
            panel_url = panel_info['url']
        else:
            panel_url = f"http://{server_ip}:{panel_port}{web_path}"
        
        keyboard = [[InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='main_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            "✅ پنل 3x-UI با موفقیت نصب شد\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🆔 Panel ID: `{panel_id}`\n\n"
            "📋 اطلاعات دسترسی به پنل:\n\n"
            f"🌐 آدرس پنل:\n`{panel_url}`\n\n"
            f"👤 نام کاربری: `{panel_username}`\n"
            f"🔑 رمز عبور: `{panel_password}`\n"
            f"🔌 پورت پنل: `{panel_port}`\n"
            f"📁 مسیر پایه وب: `{web_path}`\n\n"
            "━━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ نکات مهم:\n"
            "• این اطلاعات را ذخیره کنید\n"
            "• بعد از ورود، حتماً رمز عبور را تغییر دهید\n"
            "• برای مدیریت پنل در سرور: `x-ui`\n\n"
            "✅ پنل شما آماده استفاده است\n\n"
            "🏠 برای بازگشت به منو: /start"
        )
        
        print(f"[v0] Sending final message to user...")
        await status_message.edit_text(message, reply_markup=reply_markup, parse_mode='Markdown')
        print(f"[v0] Installation completed successfully")
        
        # Disconnect from server
        ssh.disconnect()
        
    except Exception as e:
        print(f"[v0] Exception during installation: {type(e).__name__}: {str(e)}")
        import traceback
        print(f"[v0] Traceback: {traceback.format_exc()}")
        
        await status_message.edit_text(
            f"❌ خطا در نصب پنل:\n{str(e)}\n\n"
            "لطفاً اطلاعات سرور را بررسی کنید."
        )
    
    return ConversationHandler.END

def extract_panel_info(output):
    """Extract panel information from installation output"""
    try:
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        output = ansi_escape.sub('', output)
        
        url_match = re.search(r'http://[\d\.]+:\d+(/[A-Za-z0-9]+)?', output)
        username_match = re.search(r'username:\s*(\S+)', output, re.IGNORECASE)
        password_match = re.search(r'password:\s*(\S+)', output, re.IGNORECASE)
        port_match = re.search(r'port:\s*(\d+)', output, re.IGNORECASE)
        web_path_match = re.search(r'web base path:\s*(/\S+)', output, re.IGNORECASE)
        
        if url_match:
            full_url = url_match.group(0)
            web_path = url_match.group(1) if url_match.group(1) else '/'
            
            # If web_path_match found explicitly, use that instead
            if web_path_match:
                web_path = web_path_match.group(1)
            
            return {
                'url': full_url,
                'username': username_match.group(1) if username_match else 'N/A',
                'password': password_match.group(1) if password_match else 'N/A',
                'port': port_match.group(1) if port_match else '2087',
                'web_path': web_path
            }
        
        return None
    except Exception as e:
        print(f"[v0] Error extracting panel info: {e}")
        return None
