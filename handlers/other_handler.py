from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    about_text = """
ℹ️ درباره ربات

این ربات برای نصب و مدیریت تانل‌ها و پنل‌های مختلف طراحی شده است.

🔗 پشتیبانی
برای کمک و پشتیبانی، لطفاً با ما تماس بگیرید.

📊 نسخه: 1.0.0
    """
    
    keyboard = [
        [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
    ]
    
    await query.edit_message_text(
        text=about_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()
