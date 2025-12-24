from telegram import Update, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

async def cancel_operation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation and return to main menu"""
    context.user_data.clear()
    
    keyboard = [
        [InlineKeyboardButton("🏠 بازگشت به منوی اصلی", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ عملیات لغو شد.\n\nبرای بازگشت به منوی اصلی، دکمه زیر را بزنید:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "❌ عملیات لغو شد.\n\nبرای بازگشت به منوی اصلی، دکمه زیر را بزنید:",
            reply_markup=ReplyKeyboardRemove()
        )
        await update.message.reply_text(
            "برای بازگشت به منوی اصلی:",
            reply_markup=reply_markup
        )
    
    return ConversationHandler.END
