from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_connection, add_vxlan_tunnel
from utils.ssh_manager import SSHManager
from utils.tunnel_utils import generate_tunnel_id
from utils.vxlan_scripts import generate_iran_vxlan_script, generate_kharej_vxlan_script
import tempfile
import os

# Conversation states for Vxlan
VXLAN_IRAN_INFO, VXLAN_FOREIGN_INFO = range(2)

async def vxlan_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Vxlan configuration process"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['tunnel_type'] = 'vxlan'
    
    message = """🇮🇷 کانفیگ سرور ایران - Vxlan

📝 لطفاً اطلاعات زیر را برای کانفیگ سرور ایران وارد کنید:

IPin: (آیپی سرور ایران)
User: (نام کاربری SSH)
Pass: (رمز عبور SSH)
SSH Port: (پورت SSH، معمولاً 22)
Tunneltype: (Direct یا Reverse)
Tunnelname: (نام دلخواه برای تانل، مثال: Ahmad75)
Iptype: (IPv4 یا IPv6)
Tunnelport: (پورت تانل، غیر از پورت‌های سرویس)
Transport: (TCP یا UDP)
Tcpnodelay: (true یا false)
Securitytoken: (رمز امنیتی، باید با سرور خارج یکسان باشد)
Serviceports: (پورت‌های سرویس با کاما جدا شده، مثال: 8090,4830,3333)

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید

💡 نکات:
• IPin میشه آیپی ایران و سرور اول
• Tunneltype: Direct یا Reverse
• Tunnelname: نام دلخواه برای تانل
• Iptype: IPv4 یا IPv6
• Transport: TCP یا UDP
• Tcpnodelay: true یا false
• Securitytoken: باید با سرور خارج یکسان باشد"""
    
    keyboard = [
        [InlineKeyboardButton("◀️ بازگشت به منوی اصلی", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(text=message, reply_markup=InlineKeyboardMarkup(keyboard))
    return VXLAN_IRAN_INFO

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
        required_fields = ['IPin', 'User', 'Pass', 'SSH Port', 'Tunneltype', 'Tunnelname', 
                         'Iptype', 'Tunnelport', 'Transport', 'Tcpnodelay', 'Securitytoken', 'Serviceports']
        missing = [f for f in required_fields if not info.get(f)]
        if missing:
            await update.message.reply_text(f"❌ فیلدهای زیر الزامی هستند:\n{', '.join(missing)}")
            return VXLAN_IRAN_INFO
        
        # Store Iran server info
        context.user_data['iran_ip'] = info.get('IPin', '')
        context.user_data['iran_user'] = info.get('User', '')
        context.user_data['iran_pass'] = info.get('Pass', '')
        context.user_data['iran_ssh_port'] = int(info.get('SSH Port', 22))
        context.user_data['tunneltype'] = info.get('Tunneltype', 'Direct')
        context.user_data['tunnelname'] = info.get('Tunnelname', '')
        context.user_data['iptype'] = info.get('Iptype', 'IPv4')
        context.user_data['tunnelport'] = info.get('Tunnelport', '')
        context.user_data['transport'] = info.get('Transport', 'TCP')
        context.user_data['tcpnodelay'] = info.get('Tcpnodelay', 'true')
        context.user_data['securitytoken'] = info.get('Securitytoken', '')
        context.user_data['serviceports'] = info.get('Serviceports', '')
        
        message = """🌍 کانفیگ سرور خارج - Vxlan

📝 لطفاً اطلاعات زیر را برای کانفیگ سرور خارج وارد کنید:

IPout: (آیپی سرور خارج)
User: (نام کاربری SSH)
Pass: (رمز عبور SSH)
SSH Port: (پورت SSH، معمولاً 22)
Tunneltype: (Direct یا Reverse - باید با ایران یکسان باشد)
Tunnelname: (نام تانل - باید با ایران یکسان باشد)
Iranip: (آیپی سرور ایران - IPv4 یا IPv6)
Tunnelport: (پورت تانل - باید با ایران یکسان باشد)
Transport: (TCP یا UDP - باید با ایران یکسان باشد)
Tcpnodelay: (true یا false)
Securitytoken: (رمز امنیتی - باید با ایران یکسان باشد)
Serviceports: (پورت‌های سرویس با کاما جدا شده، مثال: 8090,4830,3333)

⚠️ تمام اطلاعات را زیر هم و در یک پیام ارسال کنید

💡 نکات:
• IPout میشه آیپی سرور خارج و سرور دوم
• تمام پارامترها باید با سرور ایران یکسان باشند
• Iranip: آیپی سرور ایران"""
        
        keyboard = [
            [InlineKeyboardButton("◀️ بازگشت به منوی اصلی", callback_data='main_menu')]
        ]
        
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
        return VXLAN_FOREIGN_INFO
        
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در پردازش اطلاعات: {str(e)}\n\nلطفاً دوباره سعی کنید")
        return VXLAN_IRAN_INFO

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
        required_fields = ['IPout', 'User', 'Pass', 'SSH Port', 'Tunneltype', 'Tunnelname', 
                         'Iranip', 'Tunnelport', 'Transport', 'Tcpnodelay', 'Securitytoken', 'Serviceports']
        missing = [f for f in required_fields if not info.get(f)]
        if missing:
            await update.message.reply_text(f"❌ فیلدهای زیر الزامی هستند:\n{', '.join(missing)}")
            return VXLAN_FOREIGN_INFO
        
        # Store Foreign server info
        context.user_data['foreign_ip'] = info.get('IPout', '')
        context.user_data['foreign_user'] = info.get('User', '')
        context.user_data['foreign_pass'] = info.get('Pass', '')
        context.user_data['foreign_ssh_port'] = int(info.get('SSH Port', 22))
        context.user_data['foreign_tunneltype'] = info.get('Tunneltype', 'Direct')
        context.user_data['foreign_tunnelname'] = info.get('Tunnelname', '')
        context.user_data['iranip'] = info.get('Iranip', '')
        context.user_data['foreign_tunnelport'] = info.get('Tunnelport', '')
        context.user_data['foreign_transport'] = info.get('Transport', 'TCP')
        context.user_data['foreign_tcpnodelay'] = info.get('Tcpnodelay', 'true')
        context.user_data['foreign_securitytoken'] = info.get('Securitytoken', '')
        context.user_data['foreign_serviceports'] = info.get('Serviceports', '')
        
        await update.message.reply_text("⏳ در حال اتصال به سرورها و نصب Vxlan...\n\nلطفاً صبر کنید...")
        
        # Generate tunnel ID
        tunnel_id = generate_tunnel_id()
        context.user_data['tunnel_id'] = tunnel_id
        
        user_id = update.effective_user.id
        print(f"[v0] Starting Vxlan installation for user {user_id}, tunnel_id: {tunnel_id}")
        
        # Install on Iran server
        iran_script = generate_iran_vxlan_script(
            context.user_data['tunnelname'],
            context.user_data['iptype'],
            context.user_data['tunnelport'],
            context.user_data['transport'].lower(),  # Convert to lowercase for RGT config
            context.user_data['tcpnodelay'],
            context.user_data['securitytoken'],
            context.user_data['serviceports']
        )
        
        iran_success = await install_on_server(
            context.user_data['iran_ip'],
            context.user_data['iran_ssh_port'],
            context.user_data['iran_user'],
            context.user_data['iran_pass'],
            iran_script,
            "Iran",
            update
        )
        
        if not iran_success:
            await update.message.reply_text("❌ خطا در نصب بر روی سرور ایران!\n\nلطفاً اطلاعات سرور و اتصال را چک کنید.")
            return ConversationHandler.END
        
        await update.message.reply_text("✅ نصب بر روی سرور ایران موفق\n\n⏳ در حال نصب بر روی سرور خارج...")
        
        # Install on Foreign server
        foreign_script = generate_kharej_vxlan_script(
            context.user_data['foreign_tunnelname'],
            context.user_data['iranip'],
            context.user_data['foreign_tunnelport'],
            context.user_data['foreign_transport'].lower(),  # Convert to lowercase for RGT config
            context.user_data['foreign_tcpnodelay'],
            context.user_data['foreign_securitytoken'],
            context.user_data['foreign_serviceports']
        )
        
        foreign_success = await install_on_server(
            context.user_data['foreign_ip'],
            context.user_data['foreign_ssh_port'],
            context.user_data['foreign_user'],
            context.user_data['foreign_pass'],
            foreign_script,
            "Foreign",
            update
        )
        
        if not foreign_success:
            await update.message.reply_text("❌ خطا در نصب بر روی سرور خارج!\n\nلطفاً اطلاعات سرور و اتصال را چک کنید.")
            return ConversationHandler.END
        
        print(f"[v0] Saving tunnel to database: {tunnel_id}, user: {user_id}")
        print(f"[v0] IPin: {context.user_data['iran_ip']}, IPout: {context.user_data['foreign_ip']}, Ports: {context.user_data['serviceports']}")
        
        # Save to database
        db_success = add_vxlan_tunnel(
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
            context.user_data['serviceports']
        )
        
        if db_success:
            print(f"[v0] Tunnel saved successfully to database")
        else:
            print(f"[v0] Failed to save tunnel to database")
            await update.message.reply_text("⚠️ هشدار: تانل نصب شد اما ذخیره در دیتابیس با خطا مواجه شد.\n\nلطفاً تنظیمات دیتابیس را بررسی کنید.")
        
        # Send success message
        success_message = f"""✅ تانل Vxlan با موفقیت نصب شد!

🆔 Tunnel ID: `{tunnel_id}`

📋 اطلاعات تانل:
🇮🇷 IPin: {context.user_data['iran_ip']}
🌍 IPout: {context.user_data['foreign_ip']}
🔌 Serviceports: {context.user_data['serviceports']}

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
        print(f"[v0] Exception in get_foreign_info: {str(e)}")
        import traceback
        traceback.print_exc()
        await update.message.reply_text(f"❌ خطا: {str(e)}\n\nلطفاً دوباره سعی کنید.")
        return VXLAN_FOREIGN_INFO

async def install_on_server(ip, port, username, password, script, server_name, update):
    """Install script on remote server via SSH"""
    try:
        ssh = SSHManager()
        
        await update.message.reply_text(f"🔗 در حال اتصال به سرور {server_name} ({ip})...")
        
        if not ssh.connect(ip, port, username, password):
            print(f"[v0] Failed to connect to {server_name} server at {ip}:{port}")
            return False
        
        await update.message.reply_text(f"✅ اتصال به سرور {server_name} برقرار شد\n⬆️ در حال آپلود و اجرای اسکریپت...")
        
        # Save script to temporary file and upload
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as f:
            f.write(script)
            temp_script = f.name
        
        try:
            remote_script = f"/tmp/install_vxlan_{server_name.lower()}.sh"
            
            if not ssh.upload_file(temp_script, remote_script):
                print(f"[v0] Failed to upload script to {server_name}")
                ssh.disconnect()
                return False
            
            # Execute script
            output, error = ssh.execute_command(f"chmod +x {remote_script} && bash {remote_script}")
            
            print(f"[v0] [{server_name}] Output: {output}")
            if error:
                print(f"[v0] [{server_name}] Error: {error}")
            
            if "configured successfully" in output or "Iran server configured successfully" in output or "Kharej server configured successfully" in output:
                ssh.disconnect()
                return True
            else:
                print(f"[v0] Installation might have failed on {server_name}. Output: {output}")
                ssh.disconnect()
                return False
            
        finally:
            if os.path.exists(temp_script):
                os.unlink(temp_script)
            
    except Exception as e:
        print(f"[v0] Error installing on {server_name}: {str(e)}")
        return False
