from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from telegram.error import BadRequest, Forbidden
from database import (
    get_force_join_status, 
    set_force_join_status,
    add_force_join_channel,
    remove_force_join_channel,
    get_all_force_join_channels
)
from config import ADMIN_IDS

# Conversation states
WAITING_CHANNEL_ID = 1

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def check_user_membership(bot, user_id, channels):
    """Check if user is member of all required channels"""
    if not channels:
        return True, []
    
    not_joined = []
    
    for channel in channels:
        channel_id = channel[0]
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ['left', 'kicked']:
                not_joined.append(channel)
        except (BadRequest, Forbidden) as e:
            print(f"Error checking membership for channel {channel_id}: {e}")
            not_joined.append(channel)
    
    return len(not_joined) == 0, not_joined

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has joined all required channels"""
    user_id = update.effective_user.id
    
    # Admin bypass
    if is_admin(user_id):
        return True
    
    # Check if force join is enabled
    if not get_force_join_status():
        return True
    
    channels = get_all_force_join_channels()
    if not channels:
        return True
    
    is_member, not_joined = await check_user_membership(context.bot, user_id, channels)
    
    if not is_member:
        # Show force join message
        text = "برای استفاده از ربات ابتدا باید در کانال‌های زیر عضو شوید:\n\n"
        
        keyboard = []
        for channel in not_joined:
            channel_id, channel_username, channel_title = channel
            button_text = channel_title if channel_title else (channel_username if channel_username else channel_id)
            
            if channel_username:
                keyboard.append([InlineKeyboardButton(f"📢 {button_text}", url=f"https://t.me/{channel_username}")])
            else:
                # Try to create invite link
                try:
                    invite_link = await context.bot.create_chat_invite_link(chat_id=channel_id)
                    keyboard.append([InlineKeyboardButton(f"📢 {button_text}", url=invite_link.invite_link)])
                except Exception as e:
                    print(f"Error creating invite link for {channel_id}: {e}")
        
        keyboard.append([InlineKeyboardButton("✅ عضو شدم", callback_data='check_membership')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.answer("ابتدا در کانال‌ها عضو شوید", show_alert=True)
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup
            )
        
        return False
    
    return True

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'I joined' button click"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user = query.from_user
    channels = get_all_force_join_channels()
    
    is_member, not_joined = await check_user_membership(context.bot, user_id, channels)
    
    if is_member:
        await query.answer("✅ عضویت شما تایید شد!", show_alert=True)
        
        if user_id in ADMIN_IDS:
            keyboard = [
                [InlineKeyboardButton("🎛️ پنل مدیریت", callback_data='admin_panel')],
                [
                    InlineKeyboardButton("📦 نصب پنل", callback_data='install_panel'),
                    InlineKeyboardButton("🔐 نصب تانل", callback_data='install_tunnel')
                ],
                [InlineKeyboardButton("💰 افزایش موجودی", callback_data='add_credit')],
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
                [InlineKeyboardButton("💰 افزایش موجودی", callback_data='add_credit')],
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
            f"سلام {user.first_name}!\n\nخوش‌آمدید به ربات تانل و پنل.\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
    else:
        text = "❌ هنوز در تمام کانال‌ها عضو نشده‌اید!\n\nلطفاً در کانال‌های زیر عضو شوید:\n\n"
        
        keyboard = []
        for channel in not_joined:
            channel_id, channel_username, channel_title = channel
            button_text = channel_title if channel_title else (channel_username if channel_username else channel_id)
            
            if channel_username:
                keyboard.append([InlineKeyboardButton(f"📢 {button_text}", url=f"https://t.me/{channel_username}")])
            else:
                try:
                    invite_link = await context.bot.create_chat_invite_link(chat_id=channel_id)
                    keyboard.append([InlineKeyboardButton(f"📢 {button_text}", url=invite_link.invite_link)])
                except Exception:
                    pass
        
        keyboard.append([InlineKeyboardButton("✅ عضو شدم", callback_data='check_membership')])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text=text, reply_markup=reply_markup)

# Admin panel handlers

async def force_join_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show force join management menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("شما دسترسی به این بخش را ندارید.")
        return
    
    is_enabled = get_force_join_status()
    channels = get_all_force_join_channels()
    
    status_text = "✅ فعال" if is_enabled else "❌ غیرفعال"
    
    text = "🔐 مدیریت عضویت اجباری\n\n"
    text += f"وضعیت: {status_text}\n"
    text += f"تعداد کانال‌ها: {len(channels)}\n\n"
    text += "⚠️ توجه: ربات باید در تمام کانال‌ها ادمین باشد تا بتواند عضویت کاربران را بررسی کند.\n\n"
    
    if channels:
        text += "📢 کانال‌های ثبت شده:\n"
        for channel in channels:
            channel_id, channel_username, channel_title = channel
            display_name = channel_title if channel_title else (channel_username if channel_username else channel_id)
            text += f"• {display_name}\n"
    
    keyboard = [
        [InlineKeyboardButton(
            "✅ غیرفعال کردن" if is_enabled else "❌ فعال کردن",
            callback_data='toggle_force_join'
        )],
        [InlineKeyboardButton("➕ افزودن کانال", callback_data='add_force_join_channel')],
        [InlineKeyboardButton("🗑 حذف کانال", callback_data='remove_force_join_channel')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='admin_panel')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def toggle_force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle force join on/off"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    current_status = get_force_join_status()
    new_status = not current_status
    
    if set_force_join_status(new_status):
        status_text = "فعال" if new_status else "غیرفعال"
        await query.answer(f"عضویت اجباری {status_text} شد.", show_alert=True)
    else:
        await query.answer("خطا در تغییر وضعیت!", show_alert=True)
    
    await force_join_management(update, context)

async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding a new channel"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("شما دسترسی به این بخش را ندارید.")
        return ConversationHandler.END
    
    text = "➕ افزودن کانال جدید\n\n"
    text += "لطفاً یکی از موارد زیر را ارسال کنید:\n\n"
    text += "1️⃣ آیدی عددی کانال (مثال: -1001234567890)\n"
    text += "2️⃣ یوزرنیم کانال (مثال: @channelname)\n\n"
    text += "⚠️ توجه: ربات باید در کانال ادمین باشد!\n\n"
    text += "برای لغو /cancel را ارسال کنید."
    
    keyboard = [[InlineKeyboardButton("❌ لغو", callback_data='force_join_management')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=text, reply_markup=reply_markup)
    
    return WAITING_CHANNEL_ID

async def receive_channel_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive channel ID from user"""
    message = update.message
    channel_input = message.text.strip()
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply_text("شما دسترسی به این بخش را ندارید.")
        return ConversationHandler.END
    
    try:
        # Check if input is username or numeric ID
        if channel_input.startswith('@'):
            channel_username = channel_input[1:]
            chat = await context.bot.get_chat(chat_id=channel_input)
            channel_id = str(chat.id)
            channel_title = chat.title
        else:
            # Try to parse as numeric ID
            channel_id = channel_input
            if not channel_id.startswith('-'):
                channel_id = '-' + channel_id
            
            chat = await context.bot.get_chat(chat_id=channel_id)
            channel_username = chat.username
            channel_title = chat.title
        
        # Check if bot is admin in the channel
        bot_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            await message.reply_text(
                "❌ خطا: ربات در این کانال ادمین نیست!\n\n"
                "لطفاً ابتدا ربات را در کانال ادمین کنید و دوباره تلاش کنید."
            )
            return ConversationHandler.END
        
        # Add channel to database
        if add_force_join_channel(channel_id, channel_username, channel_title):
            await message.reply_text(
                f"✅ کانال با موفقیت اضافه شد!\n\n"
                f"📢 نام: {channel_title}\n"
                f"🆔 آیدی: {channel_id}\n"
                f"👤 یوزرنیم: @{channel_username if channel_username else 'ندارد'}"
            )
        else:
            await message.reply_text("❌ خطا در افزودن کانال به دیتابیس!")
        
        return ConversationHandler.END
        
    except BadRequest as e:
        await message.reply_text(
            f"❌ خطا: کانال یافت نشد یا ربات دسترسی ندارد.\n\n"
            f"جزئیات: {str(e)}\n\n"
            f"لطفاً مطمئن شوید که:\n"
            f"1. آیدی یا یوزرنیم صحیح است\n"
            f"2. ربات در کانال ادمین است"
        )
        return ConversationHandler.END
    except Exception as e:
        await message.reply_text(f"❌ خطا: {str(e)}")
        return ConversationHandler.END

async def remove_channel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of channels to remove"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text("شما دسترسی به این بخش را ندارید.")
        return
    
    channels = get_all_force_join_channels()
    
    if not channels:
        await query.answer("هیچ کانالی ثبت نشده است.", show_alert=True)
        await force_join_management(update, context)
        return
    
    text = "🗑 حذف کانال\n\nکانال مورد نظر را انتخاب کنید:\n\n"
    
    keyboard = []
    for channel in channels:
        channel_id, channel_username, channel_title = channel
        display_name = channel_title if channel_title else (channel_username if channel_username else channel_id)
        keyboard.append([InlineKeyboardButton(
            f"❌ {display_name}",
            callback_data=f'confirm_remove_channel_{channel_id}'
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data='force_join_management')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text=text, reply_markup=reply_markup)

async def confirm_remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and remove channel"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.answer("شما دسترسی به این بخش را ندارید.", show_alert=True)
        return
    
    # Extract channel_id from callback data
    channel_id = query.data.replace('confirm_remove_channel_', '')
    
    if remove_force_join_channel(channel_id):
        await query.answer("✅ کانال با موفقیت حذف شد.", show_alert=True)
    else:
        await query.answer("❌ خطا در حذف کانال!", show_alert=True)
    
    await force_join_management(update, context)

async def cancel_add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel adding channel"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ افزودن کانال لغو شد.")
    
    return ConversationHandler.END
