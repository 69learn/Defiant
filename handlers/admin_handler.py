from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_all_users, get_user_info, get_user_tunnels, get_user_panels, get_all_users_basic
from config import ADMIN_IDS
import math

# States for conversation handler
BROADCAST_MESSAGE, USER_ID_INPUT, AMOUNT_INPUT = range(3)

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel main menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(
            text="شما دسترسی به این بخش را ندارید."
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 لیست کاربران", callback_data='admin_users_list')],
        [InlineKeyboardButton("💰 امور مالی", callback_data='admin_financial')],
        [InlineKeyboardButton("📢 پیام همگانی", callback_data='admin_broadcast')],
        [InlineKeyboardButton("🔐 عضویت اجباری", callback_data='force_join_management')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="👑 پنل مدیریت\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show paginated list of users"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(text="شما دسترسی به این بخش را ندارید.")
        return
    
    # Get page number from callback data
    page = 1
    if '_page_' in query.data:
        page = int(query.data.split('_page_')[1])
    
    users = get_all_users()
    
    if not users or len(users) == 0:
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text="هیچ کاربری یافت نشد.",
            reply_markup=reply_markup
        )
        return
    
    # Pagination
    per_page = 5
    total_pages = math.ceil(len(users) / per_page)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_users = users[start_idx:end_idx]
    
    text = f"👥 لیست کاربران (صفحه {page}/{total_pages})\n"
    text += f"تعداد کل: {len(users)} کاربر\n\n"
    
    keyboard = []
    
    for user in page_users:
        user_id_db, username, first_name, created_at, tunnel_count, panel_count = user
        username_display = f"@{username}" if username else "بدون یوزرنیم"
        text += f"━━━━━━━━━━━━━━━━━━━\n"
        text += f"👤 {first_name}\n"
        text += f"🆔 {username_display}\n"
        text += f"🔢 ID: `{user_id_db}`\n"
        text += f"🔐 تانل‌ها: {tunnel_count}\n"
        text += f"🎛️ پنل‌ها: {panel_count}\n"
    
    text += "━━━━━━━━━━━━━━━━━━━\n"
    
    # Pagination buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ قبلی", callback_data=f'admin_users_list_page_{page-1}'))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("➡️ بعدی", callback_data=f'admin_users_list_page_{page+1}'))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_financial(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show financial management menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(text="شما دسترسی به این بخش را ندارید.")
        return
    
    # در حال حاضر جدول مالی نداریم، پس فقط یک پیام ساده نمایش میدیم
    text = "💰 امور مالی\n\n"
    text += "این بخش در حال توسعه است.\n\n"
    text += "قابلیت‌های آینده:\n"
    text += "• مشاهده شارژ‌های انجام شده\n"
    text += "• مدیریت درخواست‌های شارژ\n"
    text += "• افزودن/کاهش موجودی کاربران\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )

async def admin_broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start broadcast message flow"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(text="شما دسترسی به این بخش را ندارید.")
        return ConversationHandler.END
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='admin_panel')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        text="📢 پیام همگانی\n\nپیام خود را برای ارسال به تمام کاربران وارد کنید:\n\n(برای لغو از دکمه زیر استفاده کنید)",
        reply_markup=reply_markup
    )
    
    return BROADCAST_MESSAGE

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send broadcast message to all users"""
    message = update.message
    broadcast_text = message.text
    
    users = get_all_users_basic()
    
    if not users:
        await message.reply_text("خطا در دریافت لیست کاربران.")
        return ConversationHandler.END
    
    success_count = 0
    fail_count = 0
    
    status_message = await message.reply_text(
        f"در حال ارسال پیام...\n\n✅ موفق: {success_count}\n❌ ناموفق: {fail_count}\n📊 کل: {len(users)}"
    )
    
    for idx, user in enumerate(users):
        user_id = user[0]
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 پیام از مدیریت:\n\n{broadcast_text}"
            )
            success_count += 1
        except Exception as e:
            fail_count += 1
            print(f"خطا در ارسال به {user_id}: {e}")
        
        # Update status every 10 messages
        if (idx + 1) % 10 == 0:
            await status_message.edit_text(
                f"در حال ارسال پیام...\n\n✅ موفق: {success_count}\n❌ ناموفق: {fail_count}\n📊 کل: {len(users)}"
            )
    
    await status_message.edit_text(
        f"✅ ارسال پیام همگانی تکمیل شد!\n\n✅ موفق: {success_count}\n❌ ناموفق: {fail_count}\n📊 کل: {len(users)}"
    )
    
    return ConversationHandler.END

async def admin_broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel broadcast"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ ارسال پیام همگانی لغو شد.")
    
    return ConversationHandler.END

# New function for force join management
async def force_join_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show force join management menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(text="شما دسترسی به این بخش را ندارید.")
        return
    
    # Placeholder for force join management functionality
    text = "🔐 عضویت اجباری\n\n"
    text += "این بخش در حال توسعه است.\n\n"
    text += "قابلیت‌های آینده:\n"
    text += "• مدیریت اجبار ورود به گروه\n"
    text += "• تنظیم گروه‌های اجباری\n"
    
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=text,
        reply_markup=reply_markup
    )
