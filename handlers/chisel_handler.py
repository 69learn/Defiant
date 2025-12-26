from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import add_chisel_tunnel  # Import add_chisel_tunnel instead of get_connection
from utils.ssh_manager import SSHManager
from utils.tunnel_utils import generate_tunnel_id
from utils.chisel_scripts import generate_iran_script, generate_foreign_script
import tempfile
import os

IRAN_INFO, FOREIGN_INFO = range(2)

async def chisel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Chisel configuration process"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['tunnel_type'] = 'chisel'
    
    message = """📝 لطفاً اطلاعات زیر را برای کانفیگ سرور ایران وارد کنید:

🇮🇷 سرور ایران (سرور اول):

`IPin:`
`User:`
`Pass:`
`SSH Port:`
`TunnelPort:`

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید

💡 IPin: آیپی سرور ایران
💡 TunnelPort: پورتی که برای تانل Chisel استفاده می‌شود (مثال: 8080)"""
    
    keyboard = [
        [InlineKeyboardButton("◀️ بازگشت به منوی اصلی", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return IRAN_INFO

async def get_iran_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse Iran server info from user input"""
    try:
        lines = update.message.text.strip().split('\n')
        info = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        required_fields = ['IPin', 'User', 'Pass', 'SSH Port', 'TunnelPort']
        missing = [f for f in required_fields if not info.get(f)]
        if missing:
            await update.message.reply_text(f"❌ فیلدهای زیر الزامی هستند:\n{', '.join(missing)}")
            return IRAN_INFO
        
        context.user_data['iran_ip'] = info.get('IPin', '')
        context.user_data['iran_user'] = info.get('User', '')
        context.user_data['iran_pass'] = info.get('Pass', '')
        context.user_data['iran_ssh_port'] = int(info.get('SSH Port', 22))
        context.user_data['tunnel_port'] = int(info.get('TunnelPort', 8080))
        
        message = """📝 لطفاً اطلاعات زیر را برای کانفیگ سرور خارج وارد کنید:

🌍 سرور خارج (سرور دوم):

`IPout:`
`User:`
`Pass:`
`SSH Port:`
`TunnelPort:`
`Remoteip:`
`Numberofconfig:`
`Configports:`

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید

💡 IPout: آیپی سرور خارج
💡 TunnelPort: همان پورتی که در سرور ایران استفاده کردید
💡 Remoteip: آیپی سرور ایران (IPin)
💡 Numberofconfig: تعداد کانفیگ‌های مورد نظر
💡 Configports: پورت‌های کانفیگ با کاما جدا شده (مثال: 443,2053,2083)"""
        
        keyboard = [
            [InlineKeyboardButton("◀️ بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return FOREIGN_INFO
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پردازش اطلاعات: {str(e)}\n\nلطفاً دوباره سعی کنید")
        return IRAN_INFO

async def get_foreign_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse Foreign server info and start installation"""
    try:
        lines = update.message.text.strip().split('\n')
        info = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                info[key.strip()] = value.strip()
        
        required_fields = ['IPout', 'User', 'Pass', 'SSH Port', 'TunnelPort', 'Remoteip', 'Numberofconfig', 'Configports']
        missing = [f for f in required_fields if not info.get(f)]
        if missing:
            await update.message.reply_text(f"❌ فیلدهای زیر الزامی هستند:\n{', '.join(missing)}")
            return FOREIGN_INFO
        
        context.user_data['foreign_ip'] = info.get('IPout', '')
        context.user_data['foreign_user'] = info.get('User', '')
        context.user_data['foreign_pass'] = info.get('Pass', '')
        context.user_data['foreign_ssh_port'] = int(info.get('SSH Port', 22))
        foreign_tunnel_port = int(info.get('TunnelPort', 8080))
        context.user_data['remote_ip'] = info.get('Remoteip', '')
        context.user_data['number_of_config'] = int(info.get('Numberofconfig', 1))
        context.user_data['config_ports'] = info.get('Configports', '')
        
        await update.message.reply_text("⏳ در حال اتصال به سرور ایران و نصب Chisel Server...\n\nلطفاً صبر کنید...")
        
        iran_script = generate_iran_script(context.user_data['tunnel_port'])
        
        iran_success = await install_on_server(
            context.user_data['iran_ip'],
            context.user_data['iran_ssh_port'],
            context.user_data['iran_user'],
            context.user_data['iran_pass'],
            iran_script,
            str(context.user_data['tunnel_port']),
            "Iran"
        )
        
        if not iran_success:
            await update.message.reply_text("❌ خطا در نصب بر روی سرور ایران!\n\nلطفاً اطلاعات سرور و آتش‌بندی را چک کنید.")
            return ConversationHandler.END
        
        await update.message.reply_text("✅ نصب بر روی سرور ایران موفق\n\n⏳ در حال نصب بر روی سرور خارج...")
        
        foreign_script = generate_foreign_script(
            foreign_tunnel_port,
            context.user_data['remote_ip'],
            context.user_data['number_of_config'],
            context.user_data['config_ports']
        )
        
        foreign_success = await install_on_server(
            context.user_data['foreign_ip'],
            context.user_data['foreign_ssh_port'],
            context.user_data['foreign_user'],
            context.user_data['foreign_pass'],
            foreign_script,
            f"{foreign_tunnel_port} {context.user_data['remote_ip']} {context.user_data['number_of_config']} {context.user_data['config_ports']}",
            "Foreign"
        )
        
        if not foreign_success:
            await update.message.reply_text("❌ خطا در نصب بر روی سرور خارج!\n\nلطفاً اطلاعات سرور و آتش‌بندی را چک کنید.")
            return ConversationHandler.END
        
        tunnel_id = generate_tunnel_id()
        context.user_data['tunnel_id'] = tunnel_id
        
        user_id = update.effective_user.id
        add_chisel_tunnel(
            tunnel_id,
            user_id,
            context.user_data['iran_ip'],
            context.user_data['iran_ssh_port'],
            context.user_data['iran_user'],
            context.user_data['iran_pass'],
            context.user_data['foreign_ip'],
            context.user_data['foreign_ssh_port'],
            context.user_data['foreign_user'],
            context.user_data['foreign_pass'],
            context.user_data['config_ports']
        )
        
        success_message = f"""✅ تانل Chisel با موفقیت نصب شد!

🆔 Tunnel ID: `{tunnel_id}`

📋 اطلاعات تانل:
🇮🇷 IPin: `{context.user_data['iran_ip']}`
🌍 IPout: `{context.user_data['foreign_ip']}`
🔌 Configports: `{context.user_data['config_ports']}`

✨ تمام اطلاعات برای مدیریت بعدی ذخیره شده است."""
        
        keyboard = [
            [InlineKeyboardButton("◀️ بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        
        await update.message.reply_text(
            success_message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا: {str(e)}\n\nلطفاً دوباره سعی کنید.")
        return FOREIGN_INFO

async def install_on_server(ip, port, username, password, script, script_args, server_name):
    """Install script on remote server via SSH"""
    try:
        ssh = SSHManager()
        
        if not ssh.connect(ip, port, username, password):
            print(f"Failed to connect to {server_name} server at {ip}:{port}")
            return False
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script)
            temp_script = f.name
        
        try:
            remote_script = f"/tmp/install_chisel_{server_name.lower()}.sh"
            
            if not ssh.upload_file(temp_script, remote_script):
                ssh.disconnect()
                return False
            
            output, error = ssh.execute_command(f"chmod +x {remote_script} && bash {remote_script} {script_args}")
            
            print(f"[{server_name}] Output: {output}")
            if error:
                print(f"[{server_name}] Error: {error}")
            
            ssh.disconnect()
            return True
            
        finally:
            if os.path.exists(temp_script):
                os.unlink(temp_script)
            
    except Exception as e:
        print(f"Error installing on {server_name}: {str(e)}")
        return False
