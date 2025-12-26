from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_connection, add_mux_tunnel
from utils.ssh_manager import SSHManager
from utils.mux_scripts import generate_iran_mux_script, generate_foreign_mux_script
from utils.tunnel_utils import generate_tunnel_id
import tempfile
import os

# Conversation states for Mux
MUX_IRAN_INFO, MUX_FOREIGN_INFO = range(2)

async def mux_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Mux configuration process"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['tunnel_type'] = 'mux'
    
    message = """🇮🇷 کانفیگ سرور ایران - Mux
📝 لطفاً اطلاعات زیر را برای کانفیگ سرور ایران وارد کنید:

`IPin:` (آیپی سرور ایران برای اتصال SSH)
`User:` (نام کاربری SSH)
`Pass:` (رمز عبور SSH)
`SSH Port:` (پورت SSH، معمولاً 22)
`IranIP:` (آیپی سرور ایران WAN)
`KharejIP:` (آیپی سرور خارج WAN)
`Ports:` (پورت‌های تانل با فاصله، مثال: 8080 6902 2058 8525)

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید

💡 IranIP: آیپی سرور ایران (WAN)
💡 KharejIP: آیپی سرور خارج (WAN)
💡 Ports: پورت‌های تانل با فاصله"""
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return MUX_IRAN_INFO

async def mux_get_iran_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse Iran server info from user input"""
    try:
        lines = update.message.text.strip().split('\n')
        info = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                # Clean key and value from extra spaces
                clean_key = key.strip()
                clean_value = value.strip()
                info[clean_key] = clean_value
        
        # Check required fields with proper names
        required_fields = {
            'IPin': info.get('IPin'),
            'User': info.get('User'),
            'Pass': info.get('Pass'),
            'IranIP': info.get('IranIP'),
            'KharejIP': info.get('KharejIP'),
            'Ports': info.get('Ports')
        }
        
        missing = [k for k, v in required_fields.items() if not v]
        
        if missing:
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
            ]
            await update.message.reply_text(
                f"❌ فیلدهای زیر الزامی هستند و وارد نشده‌اند:\n{', '.join(missing)}\n\n"
                "لطفاً دوباره تمام اطلاعات را به فرمت زیر ارسال کنید:\n"
                "`IPin:` ...\n`User:` ...\n`Pass:` ...\n`SSH Port:` ...\n`IranIP:` ...\n`KharejIP:` ...\n`Ports:` ...",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return MUX_IRAN_INFO
        
        # Get SSH Port with default value
        ssh_port = info.get('SSH Port', '22')
        if not ssh_port or ssh_port == '':
            ssh_port = '22'
        
        context.user_data['iran_ssh_ip'] = info['IPin']
        context.user_data['iran_user'] = info['User']
        context.user_data['iran_pass'] = info['Pass']
        context.user_data['iran_ssh_port'] = int(ssh_port)
        context.user_data['iran_ip'] = info['IranIP']
        context.user_data['kharej_ip'] = info['KharejIP']
        context.user_data['ports'] = info['Ports']
        
        confirm_msg = f"""🌍 کانفیگ سرور خارج - Mux

📝 حالا لطفاً اطلاعات سرور خارج را وارد کنید:

`IPout:` (آیپی سرور خارج برای اتصال SSH)
`User:` (نام کاربری SSH)
`Pass:` (رمز عبور SSH)
`SSH Port:` (پورت SSH، معمولاً 22)
`IranIP:` {info['IranIP']}
`KharejIP:` {info['KharejIP']}
`Ports:` (پورت‌های تانل با فاصله، مثال: 443 2053 2083)

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید"""
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        
        await update.message.reply_text(confirm_msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return MUX_FOREIGN_INFO
        
    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        await update.message.reply_text(
            f"❌ خطا در پردازش اطلاعات: {str(e)}\n\n"
            "لطفاً اطلاعات را به فرمت زیر ارسال کنید:\n"
            "`IPin:` ...\n`User:` ...\n`Pass:` ...\n`SSH Port:` ...\n`IranIP:` ...\n`KharejIP:` ...\n`Ports:` ...",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return MUX_IRAN_INFO

async def mux_get_foreign_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse Foreign server info and start installation"""
    try:
        lines = update.message.text.strip().split('\n')
        info = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                # Clean key and value from extra spaces
                clean_key = key.strip()
                clean_value = value.strip()
                info[clean_key] = clean_value
        
        # Check required fields with proper names
        required_fields = {
            'IPout': info.get('IPout'),
            'User': info.get('User'),
            'Pass': info.get('Pass'),
            'IranIP': info.get('IranIP'),
            'KharejIP': info.get('KharejIP'),
            'Ports': info.get('Ports')
        }
        
        missing = [k for k, v in required_fields.items() if not v]
        
        if missing:
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
            ]
            await update.message.reply_text(
                f"❌ فیلدهای زیر الزامی هستند و وارد نشده‌اند:\n{', '.join(missing)}\n\n"
                "لطفاً دوباره تمام اطلاعات را به فرمت زیر ارسال کنید:\n"
                "`IPout:` ...\n`User:` ...\n`Pass:` ...\n`SSH Port:` ...\n`IranIP:` ...\n`KharejIP:` ...\n`Ports:` ...",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            return MUX_FOREIGN_INFO
        
        # Get SSH Port with default value
        ssh_port = info.get('SSH Port', '22')
        if not ssh_port or ssh_port == '':
            ssh_port = '22'
        
        context.user_data['foreign_ssh_ip'] = info['IPout']
        context.user_data['foreign_user'] = info['User']
        context.user_data['foreign_pass'] = info['Pass']
        context.user_data['foreign_ssh_port'] = int(ssh_port)
        context.user_data['foreign_iran_ip'] = info['IranIP']
        context.user_data['foreign_kharej_ip'] = info['KharejIP']
        context.user_data['foreign_ports'] = info['Ports']
        
        await update.message.reply_text("⏳ در حال اتصال به سرورها و نصب Mux Tunnel...\n\nلطفاً صبر کنید...")
        
        # Generate tunnel ID
        tunnel_id = generate_tunnel_id()
        context.user_data['tunnel_id'] = tunnel_id
        
        # Install on Iran server
        await update.message.reply_text("🔧 در حال نصب بر روی سرور ایران...")
        
        iran_script = generate_iran_mux_script(
            context.user_data['iran_ip'],
            context.user_data['kharej_ip'],
            context.user_data['ports']
        )
        
        iran_success = await install_on_server(
            context.user_data['iran_ssh_ip'],
            context.user_data['iran_ssh_port'],
            context.user_data['iran_user'],
            context.user_data['iran_pass'],
            iran_script,
            "Iran"
        )
        
        if not iran_success:
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
            ]
            await update.message.reply_text(
                "❌ خطا در نصب بر روی سرور ایران!\n\nلطفاً اطلاعات سرور و دسترسی SSH را چک کنید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ConversationHandler.END
        
        await update.message.reply_text("✅ نصب بر روی سرور ایران موفق\n\n⏳ در حال نصب بر روی سرور خارج...")
        
        # Install on Foreign server
        foreign_script = generate_foreign_mux_script(
            context.user_data['foreign_iran_ip'],
            context.user_data['foreign_kharej_ip']
        )
        
        foreign_success = await install_on_server(
            context.user_data['foreign_ssh_ip'],
            context.user_data['foreign_ssh_port'],
            context.user_data['foreign_user'],
            context.user_data['foreign_pass'],
            foreign_script,
            "Foreign"
        )
        
        if not foreign_success:
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
            ]
            await update.message.reply_text(
                "❌ خطا در نصب بر روی سرور خارج!\n\nلطفاً اطلاعات سرور و دسترسی SSH را چک کنید.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ConversationHandler.END
        
        # Save to database
        user_id = update.effective_user.id
        add_mux_tunnel(
            tunnel_id,
            user_id,
            context.user_data['iran_ssh_ip'],
            context.user_data['iran_ssh_port'],
            context.user_data['iran_user'],
            context.user_data['iran_pass'],
            context.user_data['foreign_ssh_ip'],
            context.user_data['foreign_ssh_port'],
            context.user_data['foreign_user'],
            context.user_data['foreign_pass'],
            context.user_data['ports']
        )
        
        # Send success message
        success_message = f"""✅ تانل Mux با موفقیت نصب شد!

🆔 Tunnel ID: `{tunnel_id}`

📋 اطلاعات تانل:
IPin: `{context.user_data['iran_ssh_ip']}`
IPout: `{context.user_data['foreign_ssh_ip']}`
Ports: `{context.user_data['ports']}`

✨ تمام اطلاعات برای مدیریت بعدی ذخیره شده است."""
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        
        await update.message.reply_text(
            success_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        await update.message.reply_text(
            f"❌ خطا: {str(e)}\n\nلطفاً دوباره سعی کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return MUX_FOREIGN_INFO

async def install_on_server(ip, port, username, password, script, server_name):
    """Install script on remote server via SSH"""
    try:
        ssh = SSHManager()
        
        if not ssh.connect(ip, port, username, password):
            print(f"Failed to connect to {server_name} server at {ip}:{port}")
            return False
        
        # Upload script using upload_string method
        remote_script = f"/tmp/install_mux_{server_name.lower()}.sh"
        
        if not ssh.upload_string(script, remote_script):
            print(f"Failed to upload script to {server_name} server")
            ssh.disconnect()
            return False
        
        # Execute script
        output, error = ssh.execute_command(f"chmod +x {remote_script} && bash {remote_script}")
        
        print(f"[{server_name}] Output: {output}")
        if error:
            print(f"[{server_name}] Error: {error}")
        
        # Check if installation was successful
        if "completed successfully" in output.lower() or "successfully" in output.lower():
            ssh.disconnect()
            return True
        else:
            ssh.disconnect()
            return False
            
    except Exception as e:
        print(f"Error installing on {server_name}: {str(e)}")
        return False
