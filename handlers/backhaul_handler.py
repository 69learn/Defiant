from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_connection, add_backhaul_tunnel
from utils.ssh_manager import SSHManager
from utils.tunnel_utils import generate_tunnel_id, generate_iran_script, generate_foreign_script
import tempfile
import os

# Conversation states for Backhaul
IRAN_INFO, FOREIGN_INFO = range(2)

async def backhaul_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Backhaul configuration process"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['tunnel_type'] = 'backhaul'
    
    message = """📝 لطفاً اطلاعات زیر را برای کانفیگ سرور ایران وارد کنید:

🇮🇷 سرور ایران:
`IPin:` (آیپی سرور ایران)
`User:` (نام کاربری SSH)
`Pass:` (رمز عبور SSH)
`SSH Port:` (پورت SSH، معمولاً 22)
`TunnelPorts:` (پورت‌های تانل را با فاصله وارد کنید، مثال: 443 2083 8084)
`Transport:` (tcp, tcpmux, udp, ws, wss, wsmux, wssmux - پیش‌فرض: tcp)
`Subdomain:` (فقط برای wss و wssmux، مثال: sub.example.com)

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید"""
    
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
        
        # Validate required fields
        required_fields = ['IPin', 'User', 'Pass', 'TunnelPorts']
        missing = [f for f in required_fields if not info.get(f)]
        if missing:
            await update.message.reply_text(f"❌ فیلدهای زیر الزامی هستند:\n{', '.join(missing)}")
            return IRAN_INFO
        
        context.user_data['iran_ip'] = info.get('IPin', '')
        context.user_data['iran_user'] = info.get('User', '')
        context.user_data['iran_pass'] = info.get('Pass', '')
        context.user_data['iran_ssh_port'] = int(info.get('SSH Port', 22))
        context.user_data['tunnel_ports'] = info.get('TunnelPorts', '443 2083 8084')
        context.user_data['transport_iran'] = info.get('Transport', 'tcp').lower()
        context.user_data['subdomain'] = info.get('Subdomain', '')
        
        message = """📝 لطفاً اطلاعات زیر را برای کانفیگ سرور خارج وارد کنید:

🌍 سرور خارج:
`IPout:` (آیپی سرور خارج)
`User:` (نام کاربری SSH)
`Pass:` (رمز عبور SSH)
`SSH Port:` (پورت SSH، معمولاً 22)
`Transport:` (tcp, tcpmux, udp, ws, wss, wsmux, wssmux - باید با سرور ایران یکی باشد)
`RemoteIPorSubdomain:` (آیپی یا سابدامین سرور ایران)

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید"""
        
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
        
        # Validate required fields
        required_fields = ['IPout', 'User', 'Pass', 'RemoteIPorSubdomain']
        missing = [f for f in required_fields if not info.get(f)]
        if missing:
            await update.message.reply_text(f"❌ فیلدهای زیر الزامی هستند:\n{', '.join(missing)}")
            return FOREIGN_INFO
        
        context.user_data['foreign_ip'] = info.get('IPout', '')
        context.user_data['foreign_user'] = info.get('User', '')
        context.user_data['foreign_pass'] = info.get('Pass', '')
        context.user_data['foreign_ssh_port'] = int(info.get('SSH Port', 22))
        context.user_data['transport_foreign'] = info.get('Transport', 'tcp').lower()
        context.user_data['remote_ip_subdomain'] = info.get('RemoteIPorSubdomain', '')
        
        await update.message.reply_text("⏳ در حال اتصال به سرورها و نصب Backhaul...\n\nلطفاً صبر کنید...")
        
        # Generate tunnel ID
        tunnel_id = generate_tunnel_id()
        context.user_data['tunnel_id'] = tunnel_id
        
        # Install on Iran server
        iran_script = generate_iran_script(
            context.user_data['transport_iran'],
            context.user_data['tunnel_ports'],
            context.user_data['subdomain']
        )
        
        iran_success = await install_on_server(
            context.user_data['iran_ip'],
            context.user_data['iran_ssh_port'],
            context.user_data['iran_user'],
            context.user_data['iran_pass'],
            iran_script,
            "Iran"
        )
        
        if not iran_success:
            await update.message.reply_text("❌ خطا در نصب بر روی سرور ایران!\n\nلطفاً اطلاعات سرور و آتش‌بندی را چک کنید.")
            return ConversationHandler.END
        
        await update.message.reply_text("✅ نصب بر روی سرور ایران موفق\n\n⏳ در حال نصب بر روی سرور خارج...")
        
        # Install on Foreign server
        foreign_script = generate_foreign_script(
            context.user_data['transport_foreign'],
            context.user_data['remote_ip_subdomain']
        )
        
        foreign_success = await install_on_server(
            context.user_data['foreign_ip'],
            context.user_data['foreign_ssh_port'],
            context.user_data['foreign_user'],
            context.user_data['foreign_pass'],
            foreign_script,
            "Foreign"
        )
        
        if not foreign_success:
            await update.message.reply_text("❌ خطا در نصب بر روی سرور خارج!\n\nلطفاً اطلاعات سرور و آتش‌بندی را چک کنید.")
            return ConversationHandler.END
        
        # Save to database
        user_id = update.effective_user.id
        add_backhaul_tunnel(
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
            context.user_data['transport_iran'],
            context.user_data['subdomain'],
            context.user_data['tunnel_ports']
        )
        
        success_message = f"""✅ تانل Backhaul با موفقیت نصب شد!

🆔 Tunnel ID: `{tunnel_id}`

📋 اطلاعات تانل:
🇮🇷 سرور ایران: `{context.user_data['iran_ip']}`
🌍 سرور خارج: `{context.user_data['foreign_ip']}`
📡 Transport: `{context.user_data['transport_iran']}`
🔌 پورت‌ها: `{context.user_data['tunnel_ports']}`

✨ تمام اطلاعات برای مدیریت بعدی ذخیره شده است."""
        
        keyboard = [
            [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
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

async def install_on_server(ip, port, username, password, script, server_name):
    """Install script on remote server via SSH"""
    try:
        ssh = SSHManager()
        
        if not ssh.connect(ip, port, username, password):
            print(f"Failed to connect to {server_name} server at {ip}:{port}")
            return False
        
        # Save script to temporary file and upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script)
            temp_script = f.name
        
        try:
            remote_script = f"/tmp/install_backhaul_{server_name.lower()}.sh"
            
            if not ssh.upload_file(temp_script, remote_script):
                ssh.disconnect()
                return False
            
            # Execute script
            output, error = ssh.execute_command(f"chmod +x {remote_script} && bash {remote_script}")
            
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

def backhaul_conversation_handler():
    """Create conversation handler for Backhaul setup"""
    return ConversationHandler(
        entry_points=[],
        states={
            IRAN_INFO: [],
            FOREIGN_INFO: []
        },
        fallbacks=[]
    )
