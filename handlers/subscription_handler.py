from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    has_active_subscription,
    get_user_subscription,
    has_used_trial,
    create_subscription,
    get_user_wallet,
    update_user_wallet
)
from datetime import datetime
import pytz
from persiantools.jdatetime import JalaliDateTime
from config import ADMIN_IDS

SELECTING_PLAN = 1

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

async def buy_subscription_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription purchase menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    used_trial = has_used_trial(user_id)
    
    keyboard = []
    
    # Add trial option if not used
    if not used_trial:
        keyboard.append([InlineKeyboardButton("🧪 اشتراک تست 1 روزه رایگان", callback_data='sub_test')])
    
    keyboard.extend([
        [InlineKeyboardButton("🌑 اشتراک 1 ماهه - 100,000 تومان", callback_data='sub_1_month')],
        [InlineKeyboardButton("🌑 اشتراک 3 ماهه - 250,000 تومان", callback_data='sub_3_month')],
        [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message = "💎 خرید اشتراک\n\n"
    message += "برای استفاده از امکانات ربات نیاز به اشتراک دارید.\n\n"
    
    if not used_trial:
        message += "🎁 شما می‌توانید یک بار از اشتراک تست رایگان استفاده کنید!\n\n"
    
    message += "📋 لیست اشتراک‌ها:\n"
    if not used_trial:
        message += "• تست 1 روزه: رایگان\n"
    message += "• 1 ماهه: 100,000 تومان\n"
    message += "• 3 ماهه: 250,000 تومان\n\n"
    message += "یکی از گزینه‌های زیر را انتخاب کنید:"
    
    await query.edit_message_text(
        text=message,
        reply_markup=reply_markup
    )
    
    return SELECTING_PLAN

async def process_subscription_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process subscription purchase"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    plan_type = query.data.replace('sub_', '')
    
    if plan_type == 'test':
        if has_used_trial(user_id):
            await query.edit_message_text(
                text="❌ شما قبلاً از اشتراک تست استفاده کرده‌اید.\n\n"
                     "جهت تهیه اشتراک می‌توانید از منوی خرید اشتراک اقدام به خرید کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')
                ]])
            )
            return ConversationHandler.END
        
        if create_subscription(user_id, 'test'):
            # Get subscription details to show expiry date
            subscription = get_user_subscription(user_id)
            if subscription:
                tehran_tz = pytz.timezone('Asia/Tehran')
                end_date = subscription['end_date'].replace(tzinfo=pytz.UTC).astimezone(tehran_tz)
                
                # Format date and time in Persian
                end_date_str = end_date.strftime('%Y/%m/%d')
                end_time_str = end_date.strftime('%H:%M')
                
                # Convert to Persian/Jalali date for better UX
                try:
                    jalali_date = JalaliDateTime(end_date)
                    jalali_date_str = jalali_date.strftime('%Y/%m/%d')
                    
                    message = "✅ اشتراک تست 1 روزه شما با موفقیت فعال شد!\n\n"
                    message += "🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید.\n\n"
                    message += f"📅 تاریخ انقضا (شمسی): {jalali_date_str}\n"
                    message += f"🕐 ساعت انقضا: {end_time_str}\n"
                    message += f"📆 تاریخ انقضا (میلادی): {end_date_str}\n\n"
                    message += "💡 پس از اتمام اشتراک تست، می‌توانید اشتراک ماهیانه تهیه کنید."
                except Exception as e:
                    print(f"Error converting to Jalali date: {e}")
                    message = "✅ اشتراک تست 1 روزه شما با موفقیت فعال شد!\n\n"
                    message += "🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید.\n\n"
                    message += f"📅 تاریخ انقضا: {end_date_str}\n"
                    message += f"🕐 ساعت انقضا: {end_time_str}\n\n"
                    message += "💡 پس از اتمام اشتراک تست، می‌توانید اشتراک ماهیانه تهیه کنید."
            else:
                message = "✅ اشتراک تست 1 روزه شما با موفقیت فعال شد!\n\n"
                message += "🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید.\n\n"
                message += "⏱ مدت اعتبار: 1 روز"
            
            keyboard = [
                [
                    InlineKeyboardButton("📦 نصب پنل", callback_data='install_panel'),
                    InlineKeyboardButton("🔐 نصب تانل", callback_data='install_tunnel')
                ],
                [InlineKeyboardButton("⚙️ مدیریت سرویس‌ها", callback_data='manage_services')],
                [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='main_menu')]
            ]
            
            await query.edit_message_text(
                text=message,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text(
                text="❌ خطا در فعال‌سازی اشتراک. لطفاً دوباره تلاش کنید.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')
                ]])
            )
        return ConversationHandler.END
    
    # For paid subscriptions, check wallet balance
    prices = {'1_month': 100000, '3_month': 250000}
    price = prices.get(plan_type, 0)
    
    wallet = get_user_wallet(user_id)
    balance = wallet['balance'] if wallet else 0
    
    if balance < price:
        await query.edit_message_text(
            text=f"❌ موجودی کافی نیست!\n\n"
                 f"💰 موجودی فعلی: {balance:,} تومان\n"
                 f"💵 قیمت اشتراک: {price:,} تومان\n"
                 f"📉 کمبود: {price - balance:,} تومان\n\n"
                 f"لطفاً ابتدا موجودی خود را افزایش دهید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💰 افزایش موجودی", callback_data='add_credit'),
                InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')
            ]])
        )
        return ConversationHandler.END
    
    # Deduct amount and create subscription
    new_balance = balance - price
    if update_user_wallet(user_id, new_balance):
        if create_subscription(user_id, plan_type):
            duration = "1 ماه" if plan_type == '1_month' else "3 ماه"
            
            # Get subscription details
            subscription = get_user_subscription(user_id)
            if subscription:
                tehran_tz = pytz.timezone('Asia/Tehran')
                end_date = subscription['end_date'].replace(tzinfo=pytz.UTC).astimezone(tehran_tz)
                
                # Format date and time in Persian
                end_date_str = end_date.strftime('%Y/%m/%d')
                end_time_str = end_date.strftime('%H:%M')
                
                try:
                    jalali_date = JalaliDateTime(end_date)
                    jalali_date_str = jalali_date.strftime('%Y/%m/%d')
                    
                    await query.edit_message_text(
                        text=f"✅ اشتراک {duration} شما با موفقیت خریداری شد!\n\n"
                             f"💰 مبلغ پرداختی: {price:,} تومان\n"
                             f"💳 موجودی باقیمانده: {new_balance:,} تومان\n"
                             f"📅 تاریخ انقضا (شمسی): {jalali_date_str}\n"
                             f"🕐 ساعت انقضا: {end_time_str}\n"
                             f"📆 تاریخ انقضا (میلادی): {end_date_str}\n\n"
                             f"🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='main_menu')
                        ]])
                    )
                except Exception as e:
                    print(f"Error converting to Jalali: {e}")
                    await query.edit_message_text(
                        text=f"✅ اشتراک {duration} شما با موفقیت خریداری شد!\n\n"
                             f"💰 مبلغ پرداختی: {price:,} تومان\n"
                             f"💳 موجودی باقیمانده: {new_balance:,} تومان\n"
                             f"📅 تاریخ انقضا: {end_date_str}\n"
                             f"🕐 ساعت انقضا: {end_time_str}\n\n"
                             f"🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید.",
                        reply_markup=InlineKeyboardMarkup([[
                            InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='main_menu')
                        ]])
                    )
            else:
                await query.edit_message_text(
                    text=f"✅ اشتراک {duration} شما با موفقیت خریداری شد!\n\n"
                         f"🎉 حالا می‌توانید از تمام امکانات ربات استفاده کنید.",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='main_menu')
                    ]])
                )
        else:
            await query.edit_message_text(
                text="❌ خطا در فعال‌سازی اشتراک. مبلغ به کیف پول شما بازگردانده می‌شود.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')
                ]])
            )
            update_user_wallet(user_id, balance)  # Refund
    else:
        await query.edit_message_text(
            text="❌ خطا در پردازش تراکنش. لطفاً دوباره تلاش کنید.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 منوی اصلی", callback_data='main_menu')
            ]])
        )
    
    return ConversationHandler.END

async def check_subscription_access(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if user has active subscription before allowing access"""
    user_id = update.effective_user.id
    
    if is_admin(user_id):
        return True
    
    if has_active_subscription(user_id):
        return True
    
    used_trial = has_used_trial(user_id)
    
    if not used_trial:
        message = "⚠️ هنوز اشتراکی ندارید!\n\n"
        message += "اگر اشتراک تست را فعال نکرده‌اید، همین الان می‌توانید از منوی خرید اشتراک فعالش کنید."
    else:
        message = "⚠️ اشتراک شما به پایان رسیده است!\n\n"
        message += "جهت تهیه اشتراک می‌توانید از منوی خرید اشتراک اقدام به خرید کنید."
    
    if update.callback_query:
        await update.callback_query.answer(message, show_alert=True)
    
    return False
