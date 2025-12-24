from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    add_shared_access, remove_shared_access, toggle_shared_access,
    get_shared_admins, get_accessible_accounts, get_user_by_id
)

# Conversation states
WAITING_ADMIN_ID = 1

async def access_management_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show access management main menu"""
    query = update.callback_query
    user_id = query.from_user.id
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    # Get admins with access to this account
    admins = get_shared_admins(user_id)
    
    # Get accounts this user has access to
    accessible = get_accessible_accounts(user_id)
    
    message = "مدیریت دسترسی\n\n"
    message += f"تعداد ادمین‌های با دسترسی: {len(admins)}\n"
    message += f"تعداد اکانت‌های قابل دسترسی: {len(accessible)}\n\n"
    message += "از منوی زیر گزینه مورد نظر را انتخاب کنید:"
    
    keyboard = [
        [InlineKeyboardButton("➕ افزودن ادمین جدید", callback_data='add_admin')],
        [InlineKeyboardButton("📋 لیست ادمین‌های من", callback_data='list_my_admins')],
        [InlineKeyboardButton("🔑 اکانت‌های قابل دسترسی", callback_data='list_accessible_accounts')],
        [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def add_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start process of adding new admin"""
    query = update.callback_query
    
    message = "افزودن ادمین جدید\n\n"
    message += "لطفاً User ID عددی کاربری که می‌خواهید به او دسترسی مدیریت بدهید را ارسال کنید.\n\n"
    message += "مثال: 1234567890\n\n"
    message += "برای لغو، /cancel را ارسال کنید."
    
    keyboard = [
        [InlineKeyboardButton("لغو", callback_data='access_management')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()
    
    return WAITING_ADMIN_ID

async def receive_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive admin ID and add access"""
    user_id = update.message.from_user.id
    admin_id_text = update.message.text.strip()
    
    # Validate input
    try:
        admin_id = int(admin_id_text)
    except ValueError:
        await update.message.reply_text(
            "❌ User ID باید یک عدد باشد.\n\nلطفاً دوباره تلاش کنید یا /cancel برای لغو ارسال کنید."
        )
        return WAITING_ADMIN_ID
    
    # Check if trying to add themselves
    if admin_id == user_id:
        await update.message.reply_text(
            "❌ شما نمی‌توانید خودتان را به عنوان ادمین اضافه کنید!\n\nلطفاً User ID دیگری وارد کنید یا /cancel برای لغو ارسال کنید."
        )
        return WAITING_ADMIN_ID
    
    # Check if user exists
    admin_user = get_user_by_id(admin_id)
    if not admin_user:
        await update.message.reply_text(
            f"❌ کاربری با User ID {admin_id} در سیستم یافت نشد.\n\nاین کاربر باید حداقل یکبار ربات را استارت زده باشد.\n\nلطفاً دوباره تلاش کنید یا /cancel برای لغو ارسال کنید."
        )
        return WAITING_ADMIN_ID
    
    # Add access
    if add_shared_access(user_id, admin_id):
        admin_username = admin_user[1] if admin_user[1] else "بدون یوزرنیم"
        admin_name = admin_user[2] if admin_user[2] else "بدون نام"
        
        message = f"✅ دسترسی با موفقیت اضافه شد!\n\n"
        message += f"👤 کاربر: {admin_name}\n"
        message += f"🆔 User ID: `{admin_id}`\n"
        message += f"📱 Username: @{admin_username}\n\n"
        message += "این کاربر حالا می‌تواند تانل‌ها و پنل‌های شما را مدیریت کند."
        
        keyboard = [
            [InlineKeyboardButton("بازگشت به مدیریت دسترسی", callback_data='access_management')]
        ]
        
        await update.message.reply_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ خطا در افزودن دسترسی. لطفاً دوباره تلاش کنید."
        )
    
    return ConversationHandler.END

async def cancel_add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel adding admin"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        return await access_management_callback(update, context)
    else:
        keyboard = [
            [InlineKeyboardButton("بازگشت به مدیریت دسترسی", callback_data='access_management')]
        ]
        await update.message.reply_text(
            "عملیات لغو شد.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return ConversationHandler.END

async def list_my_admins_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of admins who have access to this account"""
    query = update.callback_query
    user_id = query.from_user.id
    
    admins = get_shared_admins(user_id)
    
    if not admins:
        message = "شما هیچ ادمینی اضافه نکرده‌اید.\n\nبرای افزودن ادمین جدید از دکمه زیر استفاده کنید."
        keyboard = [
            [InlineKeyboardButton("➕ افزودن ادمین جدید", callback_data='add_admin')],
            [InlineKeyboardButton("◀️ بازگشت", callback_data='access_management')]
        ]
    else:
        message = f"لیست ادمین‌های شما ({len(admins)} نفر):\n\n"
        
        keyboard = []
        for access_id, admin_id, username, first_name, is_active, created_at in admins:
            status_emoji = "✅" if is_active else "❌"
            display_name = first_name if first_name else "بدون نام"
            if username:
                display_name += f" (@{username})"
            
            button_text = f"{status_emoji} {display_name}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f'admin_detail_{admin_id}')])
        
        keyboard.append([InlineKeyboardButton("➕ افزودن ادمین جدید", callback_data='add_admin')])
        keyboard.append([InlineKeyboardButton("◀️ بازگشت", callback_data='access_management')])
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def admin_detail_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin details with management options"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_id = int(query.data.split('_')[-1])
    
    admins = get_shared_admins(user_id)
    admin = next((a for a in admins if a[1] == admin_id), None)
    
    if not admin:
        await query.answer("ادمین پیدا نشد!", show_alert=True)
        return
    
    access_id, admin_id, username, first_name, is_active, created_at = admin
    
    status_text = "فعال ✅" if is_active else "غیرفعال ❌"
    status_emoji = "✅" if is_active else "❌"
    toggle_text = "غیرفعال کردن ❌" if is_active else "فعال کردن ✅"
    
    display_name = first_name if first_name else "بدون نام"
    username_text = f"@{username}" if username else "بدون یوزرنیم"
    
    message = f"جزئیات ادمین\n\n"
    message += f"👤 نام: {display_name}\n"
    message += f"🆔 User ID: `{admin_id}`\n"
    message += f"📱 Username: {username_text}\n"
    message += f"📅 تاریخ افزودن: {created_at}\n"
    message += f"📊 وضعیت: {status_text}\n\n"
    
    if is_active:
        message += "این ادمین می‌تواند تانل‌ها و پنل‌های شما را مدیریت کند."
    else:
        message += "دسترسی این ادمین غیرفعال شده است."
    
    keyboard = [
        [InlineKeyboardButton(toggle_text, callback_data=f'toggle_admin_{admin_id}')],
        [InlineKeyboardButton("🗑 حذف ادمین", callback_data=f'remove_admin_{admin_id}')],
        [InlineKeyboardButton("◀️ بازگشت", callback_data='list_my_admins')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    await query.answer()

async def toggle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle admin access status"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_id = int(query.data.split('_')[-1])
    
    if toggle_shared_access(user_id, admin_id):
        await query.answer("وضعیت دسترسی تغییر کرد ✅", show_alert=True)
        # Refresh the admin detail page
        context.user_data['callback_query_data'] = f'admin_detail_{admin_id}'
        new_query = query
        new_query.data = f'admin_detail_{admin_id}'
        await admin_detail_callback(update, context)
    else:
        await query.answer("خطا در تغییر وضعیت!", show_alert=True)

async def remove_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove admin access"""
    query = update.callback_query
    user_id = query.from_user.id
    admin_id = int(query.data.split('_')[-1])
    
    if remove_shared_access(user_id, admin_id):
        message = "✅ دسترسی ادمین با موفقیت حذف شد.\n\nاین کاربر دیگر نمی‌تواند سرویس‌های شما را مدیریت کند."
        
        keyboard = [
            [InlineKeyboardButton("◀️ بازگشت به لیست", callback_data='list_my_admins')]
        ]
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await query.answer("ادمین حذف شد ✅")
    else:
        await query.answer("خطا در حذف ادمین!", show_alert=True)

async def list_accessible_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of accounts that user has access to"""
    query = update.callback_query
    user_id = query.from_user.id
    
    accounts = get_accessible_accounts(user_id)
    
    if not accounts:
        message = "شما به هیچ اکانت دیگری دسترسی ندارید.\n\nاگر صاحب اکانتی شما را به عنوان ادمین اضافه کند، در اینجا نمایش داده می‌شود."
        keyboard = [
            [InlineKeyboardButton("◀️ بازگشت", callback_data='access_management')]
        ]
    else:
        message = f"اکانت‌هایی که به آن‌ها دسترسی دارید ({len(accounts)} اکانت):\n\n"
        
        keyboard = []
        for access_id, owner_id, username, first_name, is_active, created_at in accounts:
            display_name = first_name if first_name else "بدون نام"
            if username:
                display_name += f" (@{username})"
            
            keyboard.append([InlineKeyboardButton(f"🔑 {display_name}", callback_data=f'switch_account_{owner_id}')])
        
        keyboard.append([InlineKeyboardButton("◀️ بازگشت", callback_data='access_management')])
        
        message += "توجه: شما می‌توانید تانل‌ها و پنل‌های این اکانت‌ها را مدیریت کنید."
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def switch_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch to managing another account"""
    query = update.callback_query
    owner_id = int(query.data.split('_')[-1])
    
    # Store the active account in context
    context.user_data['active_account'] = owner_id
    
    owner_user = get_user_by_id(owner_id)
    owner_name = owner_user[2] if owner_user and owner_user[2] else "کاربر"
    
    message = f"شما در حال مدیریت اکانت {owner_name} هستید.\n\n"
    message += "حالا می‌توانید تانل‌ها و پنل‌های این اکانت را مشاهده و مدیریت کنید."
    
    keyboard = [
        [InlineKeyboardButton("🔧 مدیریت سرویس‌ها", callback_data='manage_services')],
        [InlineKeyboardButton("🔄 بازگشت به اکانت خودم", callback_data='reset_account')],
        [InlineKeyboardButton("◀️ بازگشت", callback_data='access_management')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer(f"در حال مدیریت اکانت {owner_name}", show_alert=False)

async def reset_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset to user's own account"""
    query = update.callback_query
    
    # Clear active account from context
    if 'active_account' in context.user_data:
        del context.user_data['active_account']
    
    message = "شما به اکانت خودتان بازگشتید.\n\nحالا سرویس‌های خودتان را مدیریت می‌کنید."
    
    keyboard = [
        [InlineKeyboardButton("🔧 مدیریت سرویس‌ها", callback_data='manage_services')],
        [InlineKeyboardButton("◀️ بازگشت", callback_data='access_management')]
    ]
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer("بازگشت به اکانت خودتان", show_alert=False)
