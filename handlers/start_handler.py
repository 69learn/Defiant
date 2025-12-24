from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import add_user, get_user_wallet
from config import ADMIN_IDS

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    if user.id in ADMIN_IDS:
        keyboard = [
            [InlineKeyboardButton("🎛️ پنل مدیریت", callback_data='admin_panel')],
            [
                InlineKeyboardButton("📦 نصب پنل", callback_data='install_panel'),
                InlineKeyboardButton("🔐 نصب تانل", callback_data='install_tunnel')
            ],
            [
                InlineKeyboardButton("👤 حساب من", callback_data='my_account'),
                InlineKeyboardButton("⚙️ مدیریت سرویس‌ها", callback_data='manage_services')
            ],
            [
                InlineKeyboardButton("🔑 مدیریت دسترسی", callback_data='access_management'),
                InlineKeyboardButton("ℹ️ درباره", callback_data='about')
            ]
        ]
    else:
        keyboard = [
            [
                InlineKeyboardButton("📦 نصب پنل", callback_data='install_panel'),
                InlineKeyboardButton("🔐 نصب تانل", callback_data='install_tunnel')
            ],
            [
                InlineKeyboardButton("👤 حساب من", callback_data='my_account'),
                InlineKeyboardButton("⚙️ مدیریت سرویس‌ها", callback_data='manage_services')
            ],
            [
                InlineKeyboardButton("🔑 مدیریت دسترسی", callback_data='access_management'),
                InlineKeyboardButton("ℹ️ درباره", callback_data='about')
            ]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"سلام {user.first_name}!\n\nخوش‌آمدید به ربات تانل و پنل.\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    if 'active_account' in context.user_data:
        del context.user_data['active_account']
    
    if query.data == 'main_menu':
        if user.id in ADMIN_IDS:
            keyboard = [
                [InlineKeyboardButton("🎛️ پنل مدیریت", callback_data='admin_panel')],
                [
                    InlineKeyboardButton("📦 نصب پنل", callback_data='install_panel'),
                    InlineKeyboardButton("🔐 نصب تانل", callback_data='install_tunnel')
                ],
                [
                    InlineKeyboardButton("👤 حساب من", callback_data='my_account'),
                    InlineKeyboardButton("⚙️ مدیریت سرویس‌ها", callback_data='manage_services')
                ],
                [
                    InlineKeyboardButton("🔑 مدیریت دسترسی", callback_data='access_management'),
                    InlineKeyboardButton("ℹ️ درباره", callback_data='about')
                ]
            ]
        else:
            keyboard = [
                [
                    InlineKeyboardButton("📦 نصب پنل", callback_data='install_panel'),
                    InlineKeyboardButton("🔐 نصب تانل", callback_data='install_tunnel')
                ],
                [
                    InlineKeyboardButton("👤 حساب من", callback_data='my_account'),
                    InlineKeyboardButton("⚙️ مدیریت سرویس‌ها", callback_data='manage_services')
                ],
                [
                    InlineKeyboardButton("🔑 مدیریت دسترسی", callback_data='access_management'),
                    InlineKeyboardButton("ℹ️ درباره", callback_data='about')
                ]
            ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="منوی اصلی:",
            reply_markup=reply_markup
        )
        await query.answer()

async def my_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user account information and balance"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    from database import get_user_wallet, get_user_tunnels, get_user_panels
    
    # Get user wallet info
    wallet = get_user_wallet(user.id)
    balance = wallet['balance'] if wallet else 0
    
    # Get user's tunnels and panels count
    tunnels = get_user_tunnels(user.id)
    panels = get_user_panels(user.id)
    
    # Get backup channels for each panel
    from database import get_connection
    backup_channels = []
    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute('''
                SELECT DISTINCT backup_channel_id 
                FROM panel_backups 
                WHERE user_id = %s AND backup_channel_id IS NOT NULL
            ''', (user.id,))
            backup_channels = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting backup channels: {e}")
        finally:
            cursor.close()
            connection.close()
    
    message = f"👤 حساب کاربری شما\n\n"
    message += f"🆔 نام: {user.first_name}\n"
    message += f"🔢 User ID: `{user.id}`\n"
    if user.username:
        message += f"📱 Username: @{user.username}\n"
    message += f"📊 آمار:\n"
    message += f"   🔐 تانل‌های فعال: {len(tunnels)}\n"
    message += f"   📦 پنل‌های فعال: {len(panels)}\n"
    
    if backup_channels:
        message += f"\n📢 کانال‌های بکاپ:\n"
        for channel_id in backup_channels:
            message += f"   • {channel_id}\n"
    else:
        message += f"\n📢 کانال بکاپ: تنظیم نشده\n"
    
    keyboard = [
        [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
