from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def panel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    keyboard = [
        [InlineKeyboardButton("📦 3x-ui", callback_data='panel_3xui')],
        [InlineKeyboardButton("🎯 Marzban", callback_data='panel_marzban')],
        [InlineKeyboardButton("🔷 Marzneshin", callback_data='panel_marzneshin')],
        [InlineKeyboardButton("🔒 Pasarguard", callback_data='panel_pasarguard')],
        [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="لطفاً نوع پنل را انتخاب کنید:",
        reply_markup=reply_markup
    )
    await query.answer()
