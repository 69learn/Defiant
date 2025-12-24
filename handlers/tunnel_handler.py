from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_connection
import uuid

TUNNEL_TYPE, IRAN_IP, IRAN_PORT, IRAN_USER, IRAN_PASS, FOREIGN_IP, FOREIGN_PORT, FOREIGN_USER, FOREIGN_PASS = range(9)

async def tunnel_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show tunnel installation menu"""
    query = update.callback_query
    
    from handlers.force_join_handler import force_join_check
    if not await force_join_check(update, context):
        return
    
    keyboard = [
        [InlineKeyboardButton("🌐 Backhaul", callback_data='tunnel_backhaul')],
        [InlineKeyboardButton("🔨 Chisel", callback_data='tunnel_chisel')],
        [InlineKeyboardButton("📡 Vxlan", callback_data='tunnel_vxlan')],
        [InlineKeyboardButton("🔄 Mux", callback_data='tunnel_mux')],
        [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text="لطفاً نوع تانل را انتخاب کنید:",
        reply_markup=reply_markup
    )
    await query.answer()

# /** rest of code here **/
async def get_iran_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['iran_ip'] = update.message.text
    await update.message.reply_text("لطفاً PORT سرور ایران را وارد کنید:")
    return IRAN_PORT

async def get_iran_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['iran_port'] = int(update.message.text)
    await update.message.reply_text("لطفاً نام کاربری سرور ایران را وارد کنید:")
    return IRAN_USER

async def get_iran_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['iran_user'] = update.message.text
    await update.message.reply_text("لطفاً رمز عبور سرور ایران را وارد کنید:")
    return IRAN_PASS

async def get_iran_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['iran_pass'] = update.message.text
    await update.message.reply_text("لطفاً IP سرور خارج را وارد کنید:")
    return FOREIGN_IP

async def get_foreign_ip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['foreign_ip'] = update.message.text
    await update.message.reply_text("لطفاً PORT سرور خارج را وارد کنید:")
    return FOREIGN_PORT

async def get_foreign_port(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['foreign_port'] = int(update.message.text)
    await update.message.reply_text("لطفاً نام کاربری سرور خارج را وارد کنید:")
    return FOREIGN_USER

async def get_foreign_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['foreign_user'] = update.message.text
    await update.message.reply_text("لطفاً رمز عبور سرور خارج را وارد کنید:")
    return FOREIGN_PASS

async def get_foreign_pass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['foreign_pass'] = update.message.text
    
    user_id = update.effective_user.id
    tunnel_id = str(uuid.uuid4())[:8]
    tunnel_type = context.user_data['tunnel_type']
    
    connection = get_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute('''
                INSERT INTO tunnels (tunnel_id, user_id, tunnel_type, status)
                VALUES (%s, %s, %s, 'completed')
            ''', (tunnel_id, user_id, tunnel_type))
            
            cursor.execute('''
                INSERT INTO tunnel_configs 
                (tunnel_id, iran_ip, iran_port, iran_username, iran_password, 
                 foreign_ip, foreign_port, foreign_username, foreign_password)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                tunnel_id,
                context.user_data['iran_ip'],
                context.user_data['iran_port'],
                context.user_data['iran_user'],
                context.user_data['iran_pass'],
                context.user_data['foreign_ip'],
                context.user_data['foreign_port'],
                context.user_data['foreign_user'],
                context.user_data['foreign_pass']
            ))
            
            connection.commit()
        except Exception as e:
            print(f"خطا: {e}")
        finally:
            cursor.close()
            connection.close()
    
    message = f"""
✅ تانل با موفقیت ایجاد شد!

🆔 Tunnel ID: {tunnel_id}
📝 نوع: {tunnel_type}
🇮🇷 IP ایران: {context.user_data['iran_ip']}:{context.user_data['iran_port']}
🌍 IP خارج: {context.user_data['foreign_ip']}:{context.user_data['foreign_port']}

این اطلاعات برای مدیریت بعدی ذخیره شده‌اند.
    """
    
    keyboard = [
        [InlineKeyboardButton("◀️ بازگشت", callback_data='main_menu')]
    ]
    
    await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END
