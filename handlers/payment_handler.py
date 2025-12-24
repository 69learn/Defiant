from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    get_user_wallet, 
    update_wallet_phone, 
    create_transaction, 
    get_transaction,
    update_transaction_status,
    add_balance
)
from config import (
    CARD_NUMBER, 
    CARD_HOLDER, 
    CARD_BANK, 
    MIN_PAYMENT_AMOUNT,
    ADMIN_IDS
)

# Conversation states
SELECTING_PAYMENT_METHOD, ENTERING_AMOUNT, VERIFYING_PHONE, UPLOADING_RECEIPT = range(4)

async def add_credit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    keyboard = [
        [InlineKeyboardButton("💳 کارت به کارت", callback_data='payment_card_to_card')],
        [InlineKeyboardButton("💎 درگاه ارزی", callback_data='payment_crypto_gateway')],
        [InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "💰 روش پرداخت خود را انتخاب کنید:",
        reply_markup=reply_markup
    )
    
    return SELECTING_PAYMENT_METHOD

async def card_to_card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data='main_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"👈🏻 مبلغ مورد نظر خود را به تومان وارد کنید\n\n"
        f"⚠️ حداقل مبلغ قابل شارژ: {MIN_PAYMENT_AMOUNT:,} تومان",
        reply_markup=reply_markup
    )
    
    context.user_data['payment_method'] = 'card_to_card'
    return ENTERING_AMOUNT

async def crypto_gateway_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💎 درگاه ارزی به زودی فعال می‌شود...\n\n"
        "لطفاً از روش کارت به کارت استفاده کنید."
    )
    
    return ConversationHandler.END

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.replace(',', '').replace('،', ''))
        
        if amount < MIN_PAYMENT_AMOUNT:
            await update.message.reply_text(
                f"❌ مبلغ وارد شده کمتر از حداقل مجاز است.\n\n"
                f"حداقل مبلغ: {MIN_PAYMENT_AMOUNT:,} تومان"
            )
            return ENTERING_AMOUNT
        
        context.user_data['payment_amount'] = amount
        
        wallet = get_user_wallet(update.effective_user.id)
        
        if wallet and wallet.get('phone_verified'):
            formatted_card = f"{CARD_NUMBER[:4]} {CARD_NUMBER[4:8]} {CARD_NUMBER[8:12]} {CARD_NUMBER[12:]}"
            
            keyboard = [[InlineKeyboardButton("📤 ارسال رسید", callback_data='send_receipt')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ لطفا مبلغ {amount:,} تومان را از طریق کارت زیر پرداخت کنید\n\n"
                f"💳 {formatted_card}\n"
                f"👤 {CARD_HOLDER} ({CARD_BANK})",
                reply_markup=reply_markup
            )
            return UPLOADING_RECEIPT
        else:
            keyboard = [[InlineKeyboardButton("✅ تایید حساب", callback_data='verify_account')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "🪪 جهت استفاده از قابلیت کارت به کارت باید حساب خود را از دکمه زیر تایید کنید "
                "(این کار برای جلوگیری از افراد سودجو و فیشینگ بوده و اطلاعات شما کاملا محفوظ خواهد ماند)\n\n"
                "‼️ درصورت پرداخت بدون احراز از گزینه *درگاه ارزی* استفاده کنید.",
                reply_markup=reply_markup
            )
            return VERIFYING_PHONE
            
    except ValueError:
        await update.message.reply_text(
            "❌ لطفاً یک عدد معتبر وارد کنید."
        )
        return ENTERING_AMOUNT

async def verify_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    from telegram import KeyboardButton, ReplyKeyboardMarkup
    
    keyboard = [[KeyboardButton("📱 ارسال شماره تماس", request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    
    await query.message.reply_text(
        "📱 لطفاً شماره تماس خود را از دکمه زیر ارسال کنید:",
        reply_markup=reply_markup
    )
    
    return VERIFYING_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    
    if contact and contact.phone_number:
        phone_number = contact.phone_number
        
        if not phone_number.startswith('+98') and not phone_number.startswith('98'):
            from telegram import ReplyKeyboardRemove
            await update.message.reply_text(
                "❌ خرید فقط برای شماره‌های ایران امکان‌پذیر است",
                reply_markup=ReplyKeyboardRemove()
            )
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data='main_menu')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "لطفاً با شماره ایرانی تلاش کنید.",
                reply_markup=reply_markup
            )
            return ConversationHandler.END
        
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        
        update_wallet_phone(update.effective_user.id, phone_number)
        
        amount = context.user_data.get('payment_amount')
        formatted_card = f"{CARD_NUMBER[:4]} {CARD_NUMBER[4:8]} {CARD_NUMBER[8:12]} {CARD_NUMBER[12:]}"
        
        from telegram import ReplyKeyboardRemove
        keyboard = [[InlineKeyboardButton("📤 ارسال رسید", callback_data='send_receipt')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ حساب شما تایید شد!\n\n"
            f"لطفا مبلغ {amount:,} تومان را از طریق کارت زیر پرداخت کنید\n\n"
            f"💳 {formatted_card}\n"
            f"👤 {CARD_HOLDER} ({CARD_BANK})",
            reply_markup=ReplyKeyboardRemove()
        )
        
        await update.message.reply_text(
            "پس از پرداخت، روی دکمه زیر کلیک کنید:",
            reply_markup=reply_markup
        )
        
        return UPLOADING_RECEIPT
    else:
        await update.message.reply_text(
            "❌ شماره تماس دریافت نشد. لطفاً دوباره تلاش کنید."
        )
        return VERIFYING_PHONE

async def send_receipt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🏷 کاربر گرامی: لطفا عکس رسید واریزی ارسال کنید تا حساب شما شارژ شود، از ارسال رسید فیک خودداری کنید.\n\n"
        "✅ زمان تقریبی تایید رسیدها 15 دقیقه الی 4 ساعت می‌باشد."
    )
    
    return UPLOADING_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        amount = context.user_data.get('payment_amount')
        user = update.effective_user
        
        transaction_id = create_transaction(
            user.id, 
            amount, 
            'card_to_card', 
            file_id
        )
        
        if transaction_id:
            keyboard = [
                [
                    InlineKeyboardButton("✅ تایید", callback_data=f'approve_transaction_{transaction_id}'),
                    InlineKeyboardButton("❌ رد", callback_data=f'reject_transaction_{transaction_id}')
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=file_id,
                        caption=f"🆕 درخواست شارژ جدید\n\n"
                                f"👤 کاربر: {user.first_name} (@{user.username})\n"
                                f"🆔 User ID: {user.id}\n"
                                f"💰 مبلغ: {amount:,} تومان\n"
                                f"🔢 شماره تراکنش: {transaction_id}",
                        reply_markup=reply_markup
                    )
                except Exception as e:
                    print(f"Error sending to admin {admin_id}: {e}")
            
            await update.message.reply_text(
                "✅ رسید شما با موفقیت ارسال شد.\n\n"
                "پس از بررسی توسط ادمین، حساب شما شارژ خواهد شد.\n"
                "⏱ زمان تقریبی: 15 دقیقه الی 4 ساعت"
            )
            
            context.user_data.clear()
            return ConversationHandler.END
        else:
            await update.message.reply_text(
                "❌ خطا در ثبت تراکنش. لطفاً دوباره تلاش کنید."
            )
            return UPLOADING_RECEIPT
    else:
        await update.message.reply_text(
            "❌ لطفاً یک عکس ارسال کنید."
        )
        return UPLOADING_RECEIPT

async def approve_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("شما دسترسی ندارید!", show_alert=True)
        return
    
    transaction_id = int(query.data.split('_')[-1])
    transaction = get_transaction(transaction_id)
    
    if not transaction:
        await query.answer("تراکنش یافت نشد!", show_alert=True)
        return
    
    if transaction['status'] != 'pending':
        await query.answer("این تراکنش قبلاً پردازش شده است!", show_alert=True)
        return
    
    update_transaction_status(transaction_id, 'approved')
    add_balance(transaction['user_id'], transaction['amount'])
    
    try:
        await context.bot.send_message(
            chat_id=transaction['user_id'],
            text=f"✅ رسید شما تایید شد!\n\n"
                 f"💰 مبلغ {transaction['amount']:,.0f} تومان به حساب شما اضافه شد."
        )
    except Exception as e:
        print(f"Error notifying user: {e}")
    
    await query.edit_message_caption(
        caption=query.message.caption + "\n\n✅ تایید شده",
        reply_markup=None
    )

async def reject_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.answer("شما دسترسی ندارید!", show_alert=True)
        return
    
    transaction_id = int(query.data.split('_')[-1])
    transaction = get_transaction(transaction_id)
    
    if not transaction:
        await query.answer("تراکنش یافت نشد!", show_alert=True)
        return
    
    if transaction['status'] != 'pending':
        await query.answer("این تراکنش قبلاً پردازش شده است!", show_alert=True)
        return
    
    update_transaction_status(transaction_id, 'rejected', 'رسید معتبر نیست')
    
    try:
        await context.bot.send_message(
            chat_id=transaction['user_id'],
            text=f"❌ رسید شما رد شد!\n\n"
                 f"رسید شما معتبر نیست. لطفاً رسید صحیح را ارسال کنید."
        )
    except Exception as e:
        print(f"Error notifying user: {e}")
    
    await query.edit_message_caption(
        caption=query.message.caption + "\n\n❌ رد شده",
        reply_markup=None
    )

async def cancel_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("عملیات لغو شد.")
    return ConversationHandler.END
