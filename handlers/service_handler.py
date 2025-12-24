from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_user_tunnels_with_access, get_user_panels_with_access, 
    get_tunnel_config, delete_tunnel, get_panel_config, delete_panel,
    get_user_by_id
)
from utils.ssh_manager import SSHManager
from utils.tunnel_delete_scripts import get_delete_script
from utils.panel_delete_scripts import get_panel_delete_script

async def manage_services_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show service management main menu"""
    query = update.callback_query
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    active_account = context.user_data.get('active_account', query.from_user.id)
    
    if active_account != query.from_user.id:
        owner_user = get_user_by_id(active_account)
        owner_name = owner_user[2] if owner_user and owner_user[2] else "کاربر"
        account_text = f"\n\n🔑 در حال مدیریت اکانت: {owner_name}"
    else:
        account_text = ""
    
    keyboard = [
        [InlineKeyboardButton("تانل من", callback_data='my_tunnels')],
        [InlineKeyboardButton("پنل من", callback_data='my_panels')],
        [InlineKeyboardButton("بازگشت", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text=f"مدیریت سرویس‌ها{account_text}\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def my_tunnels_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's tunnels as inline buttons"""
    query = update.callback_query
    user_id = query.from_user.id
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    active_account = context.user_data.get('active_account', user_id)
    
    tunnels = get_user_tunnels_with_access(active_account)
    
    if not tunnels or len(tunnels) == 0:
        keyboard = [
            [InlineKeyboardButton("بازگشت", callback_data='manage_services')]
        ]
        await query.edit_message_text(
            text="شما هیچ تانلی ندارید.\n\nبرای ایجاد تانل جدید به منوی اصلی بروید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.answer()
        return
    
    keyboard = []
    
    for tunnel in tunnels:
        tunnel_id, tunnel_type, status, iran_ip, foreign_ip, transport_type, tunnel_ports, created_at, owner_id = tunnel
        
        owner_indicator = " 🔑" if owner_id != user_id else ""
        button_text = f"{tunnel_type.upper()} | {tunnel_id[:8]}...{owner_indicator}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'tunnel_info_{tunnel_id}')])
    
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='manage_services')])
    
    await query.edit_message_text(
        text="تانل‌های شما:\n\n🔑 = دسترسی مشترک\n\nروی هر تانل کلیک کنید تا جزئیات و گزینه حذف را ببینید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def tunnel_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed tunnel info with delete button"""
    query = update.callback_query
    tunnel_id = query.data.split('_')[-1]
    
    tunnels = get_user_tunnels_with_access(query.from_user.id)
    tunnel = next((t for t in tunnels if t[0] == tunnel_id), None)
    
    if not tunnel:
        await query.answer("تانل پیدا نشد!", show_alert=True)
        return
    
    tunnel_id, tunnel_type, status, iran_ip, foreign_ip, transport_type, tunnel_ports, created_at, owner_id = tunnel
    
    message = f"اطلاعات تانل:\n\n"
    message += f"Tunnel ID: `{tunnel_id}`\n"
    message += f"Service: {tunnel_type.upper()}\n"
    message += f"IPin: {iran_ip or 'N/A'}\n"
    message += f"IPout: {foreign_ip or 'N/A'}\n"
    message += f"Ports: {tunnel_ports or 'N/A'}\n"
    
    keyboard = [
        [InlineKeyboardButton("حذف تانل", callback_data=f'delete_tunnel_{tunnel_id}')],
        [InlineKeyboardButton("بازگشت", callback_data='my_tunnels')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    await query.answer()

async def delete_tunnel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete tunnel from both servers and database"""
    query = update.callback_query
    tunnel_id = query.data.split('_')[-1]
    user_id = query.from_user.id
    
    # Get tunnel details
    config = get_tunnel_config(tunnel_id)
    
    if not config:
        await query.answer("تانل پیدا نشد!", show_alert=True)
        return
    
    await query.edit_message_text("در حال حذف تانل...")
    
    tunnel_type = config['tunnel_type']
    iran_ip = config['iran_ip']
    iran_port = config.get('iran_port', 22)
    iran_username = config.get('iran_username', 'root')
    iran_password = config.get('iran_password', '')
    foreign_ip = config['foreign_ip']
    foreign_port = config.get('foreign_port', 22)
    foreign_username = config.get('foreign_username', 'root')
    foreign_password = config.get('foreign_password', '')
    
    delete_script = get_delete_script(tunnel_type)
    
    success = True
    error_messages = []
    
    # Delete from Iran server
    if iran_ip and iran_password:
        try:
            ssh_iran = SSHManager()
            if ssh_iran.connect(iran_ip, iran_port, iran_username, iran_password):
                ssh_iran.upload_string(delete_script, f'/tmp/delete_{tunnel_type}.sh')
                output, error = ssh_iran.execute_command(f'chmod +x /tmp/delete_{tunnel_type}.sh && bash /tmp/delete_{tunnel_type}.sh')
                ssh_iran.disconnect()
            else:
                error_messages.append("خطا در اتصال به سرور ایران")
                success = False
        except Exception as e:
            error_messages.append(f"خطا در حذف از سرور ایران: {str(e)}")
            success = False
    
    # Delete from Foreign server
    if foreign_ip and foreign_password:
        try:
            ssh_foreign = SSHManager()
            if ssh_foreign.connect(foreign_ip, foreign_port, foreign_username, foreign_password):
                ssh_foreign.upload_string(delete_script, f'/tmp/delete_{tunnel_type}.sh')
                output, error = ssh_foreign.execute_command(f'chmod +x /tmp/delete_{tunnel_type}.sh && bash /tmp/delete_{tunnel_type}.sh')
                ssh_foreign.disconnect()
            else:
                error_messages.append("خطا در اتصال به سرور خارج")
                success = False
        except Exception as e:
            error_messages.append(f"خطا در حذف از سرور خارج: {str(e)}")
            success = False
    
    # Delete from database
    if delete_tunnel(tunnel_id):
        if success:
            message = f"تانل {tunnel_id} با موفقیت از هر دو سرور و دیتابیس حذف شد."
        else:
            message = f"تانل از دیتابیس حذف شد اما مشکلاتی در حذف از سرورها وجود داشت:\n\n"
            message += "\n".join(error_messages)
    else:
        message = "خطا در حذف تانل از دیتابیس"
    
    keyboard = [
        [InlineKeyboardButton("بازگشت", callback_data='my_tunnels')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def my_panels_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's panels as inline buttons"""
    query = update.callback_query
    user_id = query.from_user.id
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    active_account = context.user_data.get('active_account', user_id)
    
    panels = get_user_panels_with_access(active_account)
    
    if not panels or len(panels) == 0:
        keyboard = [
            [InlineKeyboardButton("بازگشت", callback_data='manage_services')]
        ]
        await query.edit_message_text(
            text="شما هیچ پنلی ندارید.\n\nبرای نصب پنل جدید به منوی اصلی بروید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.answer()
        return
    
    keyboard = []
    
    for panel in panels:
        panel_id, panel_type, server_ip, server_port, username, password, web_path, status, created_at, subdomain, db_password, owner_id = panel
        
        short_id = panel_id[:12] if len(panel_id) > 12 else panel_id
        owner_indicator = " 🔑" if owner_id != user_id else ""
        button_text = f"{panel_type.upper()} | {short_id}{owner_indicator}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f'panel_info_{panel_id}')])
    
    keyboard.append([InlineKeyboardButton("بازگشت", callback_data='manage_services')])
    
    await query.edit_message_text(
        text="پنل‌های شما:\n\n🔑 = دسترسی مشترک\n\nروی هر پنل کلیک کنید تا جزئیات و گزینه حذف را ببینید:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def panel_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed panel info with delete button"""
    query = update.callback_query
    panel_id = query.data.split('_', 2)[-1]  # Use split with limit to handle panel IDs with underscores
    
    panels = get_user_panels_with_access(query.from_user.id)
    panel = next((p for p in panels if p[0] == panel_id), None)
    
    if not panel:
        keyboard = [
            [InlineKeyboardButton("🗑 حذف از ربات (Force Delete)", callback_data=f'force_delete_panel_{panel_id}')],
            [InlineKeyboardButton("🔙 بازگشت", callback_data='my_panels')]
        ]
        await query.edit_message_text(
            text=f"⚠️ پنل پیدا نشد!\n\nPanel ID: `{panel_id}`\n\nاگر می‌خواهید این پنل را از لیست ربات حذف کنید، روی دکمه زیر کلیک کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        await query.answer()
        return
    
    panel_id, panel_type, server_ip, server_port, username, password, web_path, status, created_at, subdomain, db_password, owner_id = panel
    
    if subdomain and panel_type in ['pasarguard', 'marzban', 'marzneshin']:
        panel_url = f"https://{subdomain}:{server_port}/dashboard/"
    elif web_path:
        panel_url = f"http://{server_ip}:{server_port}{web_path}"
    else:
        panel_url = f"http://{server_ip}:{server_port}"
    
    message = f"✅ پنل {panel_type.upper()} با موفقیت نصب شد\n"
    message += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    message += f"🆔 Panel ID: `{panel_id}`\n\n"
    message += "🌐 اطلاعات دسترسی به پنل:\n\n"
    message += f"آدرس پنل:\n`{panel_url}`\n\n"
    message += f"👤 نام کاربری: `{username}`\n"
    message += f"🔑 رمز عبور: `{password}`\n"
    
    if panel_type == '3x-ui':
        message += f"📡 پورت پنل: `{server_port}`\n"
        if web_path:
            message += f"🌐 مسیر پایه وب: `{web_path}`\n"
    
    message += "\n━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if panel_type == 'pasarguard' and db_password:
        phpmyadmin = f"http://{subdomain}:8010" if subdomain else f"http://{server_ip}:8010"
        message += "💾 اطلاعات دیتابیس:\n"
        message += f"🔐 Password: `{db_password}`\n"
        message += f"📊 phpMyAdmin: `{phpmyadmin}`\n\n"
        message += "━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    message += "⚠️ نکات مهم:\n"
    message += "• این اطلاعات را ذخیره کنید\n"
    message += "• بعد از ورود، حتماً رمز عبور را تغییر دهید\n"
    
    if panel_type in ['pasarguard', 'marzban', 'marzneshin']:
        message += "• پنل با گواهینامه SSL فعال شده است\n"
    elif panel_type == '3x-ui':
        message += "• برای مدیریت پنل در سرور: x-ui\n"
    
    message += "\n✅ پنل شما آماده استفاده است"
    
    keyboard = []
    
    # Show backup button only for 3x-ui and marzban
    if panel_type in ['3x-ui', 'marzban', 'marzneshin', 'pasarguard']:
        keyboard.append([InlineKeyboardButton("💾 بکاپ", callback_data=f'backup_panel_{panel_id}')])
    
    keyboard.append([InlineKeyboardButton("🗑 حذف پنل", callback_data=f'delete_panel_{panel_id}')])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='my_panels')])
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    await query.answer()

async def delete_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete panel from server and database"""
    query = update.callback_query
    panel_id = query.data.split('_', 2)[-1]  # Handle panel IDs with underscores
    
    config = get_panel_config(panel_id)
    
    if not config:
        await query.answer("پنل پیدا نشد!", show_alert=True)
        return
    
    await query.edit_message_text("در حال حذف پنل...")
    
    panel_type = config['panel_type']
    server_ip = config['server_ip']
    ssh_port = config.get('ssh_port', 22)
    server_username = config.get('server_username', 'root')
    server_password = config.get('server_password', '')
    
    delete_script = get_panel_delete_script(panel_type)
    
    if not delete_script:
        error_message = f"اسکریپت حذف برای پنل نوع {panel_type} پیدا نشد"
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data='my_panels')]]
        await query.edit_message_text(
            text=error_message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.answer()
        return
    
    success = True
    error_message = ""
    
    # Delete from server
    if server_ip and server_password:
        try:
            ssh = SSHManager()
            if ssh.connect(server_ip, ssh_port, server_username, server_password):
                script_name = f'/tmp/delete_{panel_type}.sh'
                ssh.upload_string(delete_script, script_name)
                output, error = ssh.execute_command(f'chmod +x {script_name} && bash {script_name}')
                ssh.disconnect()
            else:
                error_message = "خطا در اتصال به سرور"
                success = False
        except Exception as e:
            error_message = f"خطا در حذف از سرور: {str(e)}"
            success = False
    
    # Delete from database
    db_delete_success = delete_panel(panel_id)
    
    if db_delete_success:
        if success:
            message = f"پنل {panel_type.upper()} با شناسه {panel_id} با موفقیت از سرور و دیتابیس حذف شد."
        else:
            message = f"پنل از دیتابیس حذف شد اما مشکل در حذف از سرور:\n\n{error_message}"
    else:
        message = "خطا در حذف پنل از دیتابیس"
    
    keyboard = [
        [InlineKeyboardButton("بازگشت", callback_data='my_panels')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def force_delete_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Force delete panel from database only without server cleanup"""
    query = update.callback_query
    panel_id = query.data.split('_', 3)[-1]  # Handle panel IDs with underscores in force delete
    
    await query.edit_message_text("در حال حذف پنل از ربات...")
    
    # Delete from database only
    db_delete_success = delete_panel(panel_id)
    
    if db_delete_success:
        message = f"پنل با شناسه {panel_id} با موفقیت از ربات حذف شد.\n\n"
        message += "توجه: این پنل فقط از لیست ربات حذف شد و ممکن است همچنان روی سرور نصب باشد."
        
        await query.edit_message_text(message)
        await query.answer()
        
        # Wait a moment then show updated panel list
        import asyncio
        await asyncio.sleep(1.5)
        
        # Refresh the panel list by calling my_panels_callback
        await my_panels_callback(update, context)
    else:
        message = "خطا در حذف پنل از دیتابیس"
        
        keyboard = [
            [InlineKeyboardButton("بازگشت", callback_data='my_panels')]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.answer()
