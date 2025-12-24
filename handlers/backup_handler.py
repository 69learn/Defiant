from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import get_panel_config
from utils.ssh_manager import SSHManager
import io
from datetime import datetime
import re
import os

# Conversation states
WAITING_CHANNEL, WAITING_CRON_SCHEDULE = range(2)

async def backup_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show backup options for panel"""
    query = update.callback_query
    panel_id = query.data.split('_', 2)[-1]
    
    # Store panel_id in context
    context.user_data['backup_panel_id'] = panel_id
    
    # Get panel config to determine panel type
    config = get_panel_config(panel_id)
    
    if not config:
        await query.answer("پنل پیدا نشد!", show_alert=True)
        return
    
    panel_type = config['panel_type']
    context.user_data['backup_panel_type'] = panel_type
    
    keyboard = [
        [InlineKeyboardButton("1️⃣ بکاپ دائمی + ارسال به کانال", callback_data=f'backup_cron_{panel_id}')],
        [InlineKeyboardButton("2️⃣ بکاپ موقت + ارسال به ربات", callback_data=f'backup_instant_{panel_id}')],
        [InlineKeyboardButton("بازگشت", callback_data=f'panel_info_{panel_id}')]
    ]
    
    message = f"چه نوع بکاپی از سرور پنل {panel_type.upper()} میخواهید؟\n\n"
    message += "1️⃣ بکاپ لحظه‌ای ارسال به کانال به صورت دائم (با کرونجاب)\n"
    message += "2️⃣ بکاپ و ارسال فقط داخل ربات به صورت موقت\n\n"
    message += "گزینه مورد نظر خود را انتخاب کنید:"
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()

async def backup_instant_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Instant backup and send to bot"""
    query = update.callback_query
    panel_id = query.data.split('_', 2)[-1]
    
    config = get_panel_config(panel_id)
    
    if not config:
        await query.answer("پنل پیدا نشد!", show_alert=True)
        return
    
    await query.edit_message_text("در حال تهیه بکاپ... لطفاً صبر کنید.")
    
    panel_type = config['panel_type']
    server_ip = config['server_ip']
    ssh_port = config.get('ssh_port', 22)
    server_username = config.get('server_username', 'root')
    server_password = config.get('server_password', '')
    
    try:
        ssh = SSHManager()
        if not ssh.connect(server_ip, ssh_port, server_username, server_password):
            await query.edit_message_text("خطا در اتصال به سرور!")
            await query.answer()
            return
        
        # Get current date and time
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        if panel_type == '3x-ui':
            # Backup 3x-ui database
            backup_filename = f"3xui_backup_{date_str}.tar.gz" # Changed from zip to tar.gz
            remote_backup_path = f"/root/{backup_filename}"
            
            # Create tar.gz backup of x-ui.db # Changed from zip to tar.gz
            command = f"cd /etc/x-ui && tar -czf {remote_backup_path} x-ui.db" # Changed from zip to tar.gz
            output, error = ssh.execute_command(command)
            
            if error and "warning" not in error.lower():
                await query.edit_message_text(f"خطا در ایجاد بکاپ:\n{error}")
                ssh.disconnect()
                return
            
            # Download the backup file
            sftp = ssh.ssh.open_sftp()
            file_data = io.BytesIO()
            sftp.getfo(remote_backup_path, file_data)
            file_data.seek(0)
            sftp.close()
            
            # Delete remote backup file
            ssh.execute_command(f"rm -f {remote_backup_path}")
            ssh.disconnect()
            
            # Send backup file to user
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=file_data,
                filename=backup_filename,
                caption=f"بکاپ پنل 3X-UI\n\nPanel ID: `{panel_id}`\n\nتاریخ: {date_str.replace('_', ' ')}",
                parse_mode='Markdown'
            )
            
            keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'panel_info_{panel_id}')]]
            await query.edit_message_text(
                text="بکاپ با موفقیت ارسال شد!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif panel_type == 'marzban':
            # Backup Marzban
            backup_filename = f"marzban_backup_{date_str}.tar.gz"
            remote_backup_path = f"/root/{backup_filename}"
            
            # Get Marzban backup script logic
            backup_script = f"""#!/bin/bash
# Marzban Backup Script
BACKUP_FILE="{remote_backup_path}"
REMARK="marzban"
DATABASE_SUFFIX="_database.sql"
LOGS_SUFFIX="_logs.txt"

# Check environment file
ENV_FILE="/opt/marzban/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Environment file not found: $ENV_FILE"
    exit 1
fi

# Extract SQLALCHEMY_DATABASE_URL
SQLALCHEMY_DATABASE_URL=$(grep -v '^#' "$ENV_FILE" | grep 'SQLALCHEMY_DATABASE_URL' | awk -F '=' '{{print $2}}' | tr -d ' ' | tr -d '"' | tr -d "'")

BACKUP_DIRS="/opt/marzban /var/lib/marzban"
TEMP_FILES=""

# Check if MySQL/MariaDB
if [[ ! -z "$SQLALCHEMY_DATABASE_URL" && "$SQLALCHEMY_DATABASE_URL" != *"sqlite3"* ]]; then
    if [[ "$SQLALCHEMY_DATABASE_URL" =~ ^(mysql\\+pymysql|mariadb\\+pymysql)://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_USER="${{BASH_REMATCH[2]}}"
        DB_PASSWORD="${{BASH_REMATCH[3]}}"
        DB_HOST="${{BASH_REMATCH[4]}}"
        DB_PORT="${{BASH_REMATCH[5]}}"
        DB_NAME="${{BASH_REMATCH[6]}}"
        
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        mysqldump --column-statistics=0 -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
        
        if [[ -f "$DB_BACKUP_FILE" ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
            TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
        fi
    fi
fi

# Get Marzban logs
if command -v marzban &> /dev/null; then
    LOGS_FILE="/root/_${{REMARK}}${{LOGS_SUFFIX}}"
    marzban logs --no-follow > "$LOGS_FILE" 2>/dev/null
    
    if [[ -f "$LOGS_FILE" ]]; then
        BACKUP_DIRS="$BACKUP_DIRS $LOGS_FILE"
        TEMP_FILES="$TEMP_FILES $LOGS_FILE"
    fi
fi

# Create tar.gz backup
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null

# Clean up temp files
if [[ ! -z "$TEMP_FILES" ]]; then
    rm -f $TEMP_FILES
fi

echo "Backup created: $BACKUP_FILE"
"""
            
            # Upload and execute backup script
            ssh.upload_string(backup_script, '/tmp/marzban_backup.sh')
            output, error = ssh.execute_command('chmod +x /tmp/marzban_backup.sh && bash /tmp/marzban_backup.sh')
            
            if "Backup created" not in output and error:
                await query.edit_message_text(f"خطا در ایجاد بکاپ:\n{error}")
                ssh.disconnect()
                return
            
            # Download the backup file
            sftp = ssh.ssh.open_sftp()
            file_data = io.BytesIO()
            
            try:
                sftp.getfo(remote_backup_path, file_data)
                file_data.seek(0)
            except Exception as e:
                await query.edit_message_text(f"خطا در دانلود بکاپ:\n{str(e)}")
                sftp.close()
                ssh.disconnect()
                return
            
            sftp.close()
            
            # Delete remote backup file and temp script
            ssh.execute_command(f"rm -f {remote_backup_path} /tmp/marzban_backup.sh")
            ssh.disconnect()
            
            # Send backup file to user
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=file_data,
                filename=backup_filename,
                caption=f"بکاپ پنل Marzban\n\nPanel ID: `{panel_id}`\n\nتاریخ: {date_str.replace('_', ' ')}",
                parse_mode='Markdown'
            )
            
            keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'panel_info_{panel_id}')]]
            await query.edit_message_text(
                text="بکاپ با موفقیت ارسال شد!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif panel_type == 'marzneshin':
            # Backup Marzneshin
            backup_filename = f"marzneshin_backup_{date_str}.tar.gz"
            remote_backup_path = f"/root/{backup_filename}"
            
            # Get Marzneshin backup script logic
            backup_script = f"""#!/bin/bash
# Marzneshin Backup Script
BACKUP_FILE="{remote_backup_path}"
REMARK="marzneshin"
DATABASE_SUFFIX="_database.sql"
LOGS_SUFFIX="_logs.txt"

# Check docker-compose file
DOCKER_COMPOSE_FILE="/etc/opt/marzneshin/docker-compose.yml"
if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    echo "Docker compose file not found: $DOCKER_COMPOSE_FILE"
    exit 1
fi

# Extract database configuration
DB_TYPE=$(yq eval '.services.db.image' "$DOCKER_COMPOSE_FILE" 2>/dev/null || echo "")
DB_NAME=$(yq eval '.services.db.environment.MARIADB_DATABASE // .services.db.environment.MYSQL_DATABASE' "$DOCKER_COMPOSE_FILE" 2>/dev/null || echo "")
DB_PASSWORD=$(yq eval '.services.db.environment.MARIADB_ROOT_PASSWORD // .services.db.environment.MYSQL_ROOT_PASSWORD' "$DOCKER_COMPOSE_FILE" 2>/dev/null || echo "")
DB_PORT=$(yq eval '.services.db.ports[0]' "$DOCKER_COMPOSE_FILE" 2>/dev/null | cut -d':' -f2 || echo "3306")

# Determine database type
if [[ "$DB_TYPE" == *"mariadb"* ]]; then
    DB_TYPE="mariadb"
elif [[ "$DB_TYPE" == *"mysql"* ]]; then
    DB_TYPE="mysql"
else
    DB_TYPE="sqlite"
fi

# Setup backup directories
BACKUP_DIRS="/etc/opt/marzneshin"
TEMP_FILES=""

# Scan and add volumes from docker-compose
for service in $(yq eval '.services | keys | .[]' "$DOCKER_COMPOSE_FILE" 2>/dev/null); do
    for volume in $(yq eval ".services.$service.volumes | .[]" "$DOCKER_COMPOSE_FILE" 2>/dev/null | awk -F ':' '{{print $1}}'); do
        if [[ -d "$volume" && ! "$volume" =~ /(mysql|mariadb)$ ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $volume"
        fi
    done
done

# Backup MySQL/MariaDB if used
if [[ "$DB_TYPE" != "sqlite" && ! -z "$DB_PASSWORD" && ! -z "$DB_NAME" ]]; then
    DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
    mysqldump -h 127.0.0.1 --column-statistics=0 -P $DB_PORT -u root -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
    
    if [[ -f "$DB_BACKUP_FILE" ]]; then
        BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
        TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
    fi
fi

# Get Marzneshin logs
if command -v marzneshin &> /dev/null; then
    LOGS_FILE="/root/_${{REMARK}}${{LOGS_SUFFIX}}"
    marzneshin logs --no-follow > "$LOGS_FILE" 2>/dev/null
    
    if [[ -f "$LOGS_FILE" ]]; then
        BACKUP_DIRS="$BACKUP_DIRS $LOGS_FILE"
        TEMP_FILES="$TEMP_FILES $LOGS_FILE"
    fi
fi

# Create tar.gz backup
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null

# Clean up temp files
if [[ ! -z "$TEMP_FILES" ]]; then
    rm -f $TEMP_FILES
fi

echo "Backup created: $BACKUP_FILE"
"""
            
            # Upload and execute backup script
            ssh.upload_string(backup_script, '/tmp/marzneshin_backup.sh')
            output, error = ssh.execute_command('chmod +x /tmp/marzneshin_backup.sh && bash /tmp/marzneshin_backup.sh')
            
            if "Backup created" not in output and error:
                await query.edit_message_text(f"خطا در ایجاد بکاپ:\n{error}")
                ssh.disconnect()
                return
            
            # Download the backup file
            sftp = ssh.ssh.open_sftp()
            file_data = io.BytesIO()
            
            try:
                sftp.getfo(remote_backup_path, file_data)
                file_data.seek(0)
            except Exception as e:
                await query.edit_message_text(f"خطا در دانلود بکاپ:\n{str(e)}")
                sftp.close()
                ssh.disconnect()
                return
            
            sftp.close()
            
            # Delete remote backup file and temp script
            ssh.execute_command(f"rm -f {remote_backup_path} /tmp/marzneshin_backup.sh")
            ssh.disconnect()
            
            # Send backup file to user
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=file_data,
                filename=backup_filename,
                caption=f"بکاپ پنل Marzneshin\n\nPanel ID: `{panel_id}`\n\nتاریخ: {date_str.replace('_', ' ')}",
                parse_mode='Markdown'
            )
            
            keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'panel_info_{panel_id}')]]
            await query.edit_message_text(
                text="بکاپ با موفقیت ارسال شد!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        elif panel_type == 'pasarguard':
            # Backup Pasarguard
            backup_filename = f"pasarguard_backup_{date_str}.tar.gz"
            remote_backup_path = f"/root/{backup_filename}"
            
            # Get Pasarguard backup script logic
            backup_script = f"""#!/bin/bash
# Pasarguard Backup Script
BACKUP_FILE="{remote_backup_path}"
REMARK="pasarguard"
DATABASE_SUFFIX="_database.sql"

# Check environment file
ENV_FILE="/opt/pasarguard/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    echo "Environment file not found: $ENV_FILE"
    exit 1
fi

# Extract DATABASE_URL
DATABASE_URL=$(grep -v '^#' "$ENV_FILE" | grep 'SQLALCHEMY_DATABASE_URL' | awk -F '=' '{{print $2}}' | tr -d ' ' | tr -d '"' | tr -d "'")

# Initialize backup directories
BACKUP_DIRS="/opt/pasarguard /var/lib/pasarguard"
TEMP_FILES=""

# Determine database type and backup accordingly
if [[ -z "$DATABASE_URL" || "$DATABASE_URL" == *"sqlite"* ]]; then
    # SQLite - no separate backup needed, included in directories
    DB_TYPE="sqlite"
else
    # Extract database details from URL
    if [[ "$DATABASE_URL" =~ ^(postgresql|postgres|timescaledb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_TYPE="postgresql"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="${{BASH_REMATCH[6]}}"
        DB_NAME="${{BASH_REMATCH[7]}}"
        
        # Backup PostgreSQL database
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        
        # Find PostgreSQL container
        PG_CONTAINER=$(docker ps --filter "ancestor=postgres" --filter "ancestor=timescaledb/timescaledb" --format "{{{{.Names}}}}" | head -n 1)
        if [[ -z "$PG_CONTAINER" ]]; then
            PG_CONTAINER=$(docker ps --filter "publish=$DB_PORT" --format "{{{{.Names}}}}" | head -n 1)
        fi
        
        if [[ ! -z "$PG_CONTAINER" ]]; then
            docker exec -e PGPASSWORD="$DB_PASSWORD" $PG_CONTAINER pg_dump -U $DB_USER -d "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
            
            if [[ -f "$DB_BACKUP_FILE" ]]; then
                BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
                TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
            fi
        fi
        
    elif [[ "$DATABASE_URL" =~ ^(postgresql|postgres|timescaledb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^/]+)/(.+)$ ]]; then
        DB_TYPE="postgresql"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="5432"
        DB_NAME="${{BASH_REMATCH[6]}}"
        
        # Backup PostgreSQL database
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        PG_CONTAINER=$(docker ps --filter "ancestor=postgres" --filter "ancestor=timescaledb/timescaledb" --format "{{{{.Names}}}}" | head -n 1)
        if [[ ! -z "$PG_CONTAINER" ]]; then
            docker exec -e PGPASSWORD="$DB_PASSWORD" $PG_CONTAINER pg_dump -U $DB_USER -d "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
            if [[ -f "$DB_BACKUP_FILE" ]]; then
                BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
                TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
            fi
        fi
        
    elif [[ "$DATABASE_URL" =~ ^(mysql|mariadb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_TYPE="${{BASH_REMATCH[1]}}"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="${{BASH_REMATCH[6]}}"
        DB_NAME="${{BASH_REMATCH[7]}}"
        
        # Backup MySQL/MariaDB database
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        mysqldump --column-statistics=0 -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
        
        if [[ -f "$DB_BACKUP_FILE" ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
            TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
        fi
        
    elif [[ "$DATABASE_URL" =~ ^(mysql|mariadb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^/]+)/(.+)$ ]]; then
        DB_TYPE="${{BASH_REMATCH[1]}}"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="3306"
        DB_NAME="${{BASH_REMATCH[6]}}"
        
        # Backup MySQL/MariaDB database
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        mysqldump --column-statistics=0 -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
        
        if [[ -f "$DB_BACKUP_FILE" ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
            TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
        fi
    fi
fi

# Create tar.gz backup
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null

# Clean up temp files
if [[ ! -z "$TEMP_FILES" ]]; then
    rm -f $TEMP_FILES
fi

echo "Backup created: $BACKUP_FILE"
"""
            
            # Upload and execute backup script
            ssh.upload_string(backup_script, '/tmp/pasarguard_backup.sh')
            output, error = ssh.execute_command('chmod +x /tmp/pasarguard_backup.sh && bash /tmp/pasarguard_backup.sh')
            
            if "Backup created" not in output and error:
                await query.edit_message_text(f"خطا در ایجاد بکاپ:\n{error}")
                ssh.disconnect()
                return
            
            # Download the backup file
            sftp = ssh.ssh.open_sftp()
            file_data = io.BytesIO()
            
            try:
                sftp.getfo(remote_backup_path, file_data)
                file_data.seek(0)
            except Exception as e:
                await query.edit_message_text(f"خطا در دانلود بکاپ:\n{str(e)}")
                sftp.close()
                ssh.disconnect()
                return
            
            sftp.close()
            
            # Delete remote backup file and temp script
            ssh.execute_command(f"rm -f {remote_backup_path} /tmp/pasarguard_backup.sh")
            ssh.disconnect()
            
            # Send backup file to user
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=file_data,
                filename=backup_filename,
                caption=f"بکاپ پنل Pasarguard\n\nPanel ID: `{panel_id}`\n\nتاریخ: {date_str.replace('_', ' ')}",
                parse_mode='Markdown'
            )
            
            keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'panel_info_{panel_id}')]]
            await query.edit_message_text(
                text="بکاپ با موفقیت ارسال شد!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        
        else:
            await query.edit_message_text(f"بکاپ برای پنل نوع {panel_type} هنوز پشتیبانی نمی‌شود.")
            
    except Exception as e:
        await query.edit_message_text(f"خطا در تهیه بکاپ:\n{str(e)}")
    
    await query.answer()

async def backup_cron_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start cron backup process - ask for channel"""
    query = update.callback_query
    panel_id = query.data.split('_', 2)[-1]
    
    context.user_data['backup_panel_id'] = panel_id
    
    keyboard = [[InlineKeyboardButton("انصراف", callback_data=f'backup_panel_{panel_id}')]]
    
    message = "لطفاً آیدی کانال تلگرام خود را وارد کنید:\n\n"
    message += "فرمت 1: @channelname\n"
    message += "فرمت 2: -1001234567890 (آیدی عددی)\n\n"
    message += "⚠️ نکته مهم: حتماً ربات را به عنوان ادمین به کانال خود اضافه کنید تا بتواند بکاپ‌ها را ارسال کند."
    
    await query.edit_message_text(
        text=message,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()
    
    return WAITING_CHANNEL

async def backup_receive_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive channel name and ask for cron schedule"""
    message = update.message
    channel_input = message.text.strip()
    
    # Validate channel format
    if not (channel_input.startswith('@') or (channel_input.startswith('-') and channel_input[1:].isdigit())):
        await message.reply_text(
            "❌ فرمت کانال صحیح نیست!\n\n"
            "لطفاً یکی از این فرمت‌ها را وارد کنید:\n"
            "- @channelname\n"
            "- -1001234567890 (آیدی عددی)"
        )
        return WAITING_CHANNEL
    
    channel_id = channel_input
    
    if channel_input.startswith('@'):
        # Try to get chat info to convert username to numeric ID
        try:
            chat = await context.bot.get_chat(channel_input)
            channel_id = str(chat.id)
            
            # Verify bot is admin in the channel
            try:
                bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
                if bot_member.status not in ['administrator', 'creator']:
                    await message.reply_text(
                        "⚠️ ربات در کانال شما ادمین نیست!\n\n"
                        "لطفاً ابتدا ربات را به عنوان ادمین به کانال اضافه کنید و دوباره تلاش کنید."
                    )
                    return WAITING_CHANNEL
            except Exception:
                await message.reply_text(
                    "⚠️ ربات به کانال شما دسترسی ندارد!\n\n"
                    "لطفاً مطمئن شوید:\n"
                    "1. ربات را به کانال اضافه کرده‌اید\n"
                    "2. ربات ادمین کانال است\n"
                    "3. نام کانال را صحیح وارد کرده‌اید"
                )
                return WAITING_CHANNEL
                
        except Exception as e:
            await message.reply_text(
                f"❌ خطا در دسترسی به کانال!\n\n"
                f"لطفاً بررسی کنید:\n"
                f"- نام کانال صحیح است؟\n"
                f"- کانال عمومی (Public) است؟\n"
                f"- ربات به کانال اضافه شده؟\n\n"
                f"⚠️ اگر کانال خصوصی است، از آیدی عددی کانال استفاده کنید."
            )
            return WAITING_CHANNEL
    else:
        # Numeric ID provided directly - verify bot has access
        try:
            chat = await context.bot.get_chat(channel_input)
            bot_member = await context.bot.get_chat_member(chat.id, context.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                await message.reply_text(
                    "⚠️ ربات در کانال شما ادمین نیست!\n\n"
                    "لطفاً ابتدا ربات را به عنوان ادمین به کانال اضافه کنید و دوباره تلاش کنید."
                )
                return WAITING_CHANNEL
        except Exception as e:
            await message.reply_text(
                f"❌ خطا در دسترسی به کانال با آیدی {channel_input}\n\n"
                f"لطفاً مطمئن شوید:\n"
                f"- آیدی کانال صحیح است\n"
                f"- ربات به کانال اضافه شده و ادمین است"
            )
            return WAITING_CHANNEL
    
    # Store numeric channel ID in context
    context.user_data['backup_channel'] = channel_id
    
    panel_id = context.user_data.get('backup_panel_id')
    
    keyboard = [
        [InlineKeyboardButton("🧪 تست ارسال بکاپ به کانال", callback_data=f'test_backup_channel_{panel_id}')],
        [InlineKeyboardButton("هر 1 ساعت", callback_data=f'cron_schedule_1h_{panel_id}')],
        [InlineKeyboardButton("هر 4 ساعت", callback_data=f'cron_schedule_4h_{panel_id}')],
        [InlineKeyboardButton("هر 12 ساعت", callback_data=f'cron_schedule_12h_{panel_id}')],
        [InlineKeyboardButton("انصراف", callback_data=f'backup_panel_{panel_id}')]
    ]
    
    await message.reply_text(
        text=f"✅ کانال تنظیم شد!\n\nChannel ID: `{channel_id}`\n\n"
        f"🧪 توصیه می‌شود ابتدا بکاپ تستی به کانال ارسال کنید تا از صحت عملکرد مطمئن شوید.\n\n"
        f"سپس زمان‌بندی کرونجاب را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return WAITING_CRON_SCHEDULE

async def test_backup_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a test backup to the channel"""
    query = update.callback_query
    await query.answer()
    
    panel_id = context.user_data.get('backup_panel_id')
    channel_id = context.user_data.get('backup_channel')
    
    if not channel_id:
        await query.edit_message_text("خطا: کانال تنظیم نشده است!")
        return ConversationHandler.END
    
    config = get_panel_config(panel_id)
    
    if not config:
        await query.edit_message_text("پنل پیدا نشد!")
        return ConversationHandler.END
    
    await query.edit_message_text("🧪 در حال ارسال بکاپ تستی به کانال... لطفاً صبر کنید.")
    
    panel_type = config['panel_type']
    server_ip = config['server_ip']
    ssh_port = config.get('ssh_port', 22)
    server_username = config.get('server_username', 'root')
    server_password = config.get('server_password', '')
    
    try:
        ssh = SSHManager()
        if not ssh.connect(server_ip, ssh_port, server_username, server_password):
            await query.edit_message_text("خطا در اتصال به سرور!")
            return WAITING_CRON_SCHEDULE
        
        # Get current date and time
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d_%H-%M-%S")
        
        backup_file_io = None
        backup_filename = None
        caption = f"🧪 بکاپ تستی {panel_type.upper()}\nPanel ID: {panel_id}\nتاریخ: {date_str.replace('_', ' ')}"
        
        if panel_type == '3x-ui':
            backup_filename = f"3xui_test_backup_{date_str}.tar.gz" # Changed from zip to tar.gz
            remote_backup_path = f"/tmp/{backup_filename}"
            
            # Create tar.gz backup # Changed from zip to tar.gz
            command = f"cd /etc/x-ui && tar -czf {remote_backup_path} x-ui.db 2>/dev/null" # Changed from zip to tar.gz
            output, error = ssh.execute_command(command)
            
            if not error or "warning" in error.lower():
                # Download the backup file
                sftp = ssh.ssh.open_sftp()
                backup_file_io = io.BytesIO()
                try:
                    sftp.getfo(remote_backup_path, backup_file_io)
                    backup_file_io.seek(0)
                except Exception:
                    backup_file_io = None
                finally:
                    sftp.close()
                    ssh.execute_command(f"rm -f {remote_backup_path}")
        
        elif panel_type in ['marzban', 'marzneshin', 'pasarguard']:
            backup_filename = f"{panel_type}_test_backup_{date_str}.tar.gz"
            remote_backup_path = f"/tmp/{backup_filename}"
            
            # Create backup script based on panel type
            if panel_type == 'marzban':
                backup_script = f"""#!/bin/bash
BACKUP_FILE="{remote_backup_path}"
BACKUP_DIRS="/opt/marzban /var/lib/marzban"
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null
echo "Backup created"
"""
            elif panel_type == 'marzneshin':
                backup_script = f"""#!/bin/bash
BACKUP_FILE="{remote_backup_path}"
BACKUP_DIRS="/etc/opt/marzneshin"
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null
echo "Backup created"
"""
            elif panel_type == 'pasarguard':
                backup_script = f"""#!/bin/bash
BACKUP_FILE="{remote_backup_path}"
BACKUP_DIRS="/opt/pasarguard /var/lib/pasarguard"
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null
echo "Backup created"
"""
            
            # Upload and execute backup script
            ssh.upload_string(backup_script, f'/tmp/test_backup_{panel_type}.sh')
            output, error = ssh.execute_command(f'chmod +x /tmp/test_backup_{panel_type}.sh && bash /tmp/test_backup_{panel_type}.sh')
            
            if "Backup created" in output:
                # Download the backup file
                sftp = ssh.ssh.open_sftp()
                backup_file_io = io.BytesIO()
                try:
                    sftp.getfo(remote_backup_path, backup_file_io)
                    backup_file_io.seek(0)
                except Exception:
                    backup_file_io = None
                finally:
                    sftp.close()
                    ssh.execute_command(f"rm -f {remote_backup_path} /tmp/test_backup_{panel_type}.sh")
        
        ssh.disconnect()
        
        if not backup_file_io:
            keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'backup_panel_{panel_id}')]]
            await query.edit_message_text(
                text="❌ خطا در ایجاد فایل بکاپ!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_CRON_SCHEDULE
        
        try:
            await context.bot.send_document(
                chat_id=channel_id,
                document=backup_file_io,
                filename=backup_filename,
                caption=caption
            )
            
            # Show success message with options to setup cron
            keyboard = [
                [InlineKeyboardButton("هر 1 ساعت", callback_data=f'cron_schedule_1h_{panel_id}')],
                [InlineKeyboardButton("هر 4 ساعت", callback_data=f'cron_schedule_4h_{panel_id}')],
                [InlineKeyboardButton("هر 12 ساعت", callback_data=f'cron_schedule_12h_{panel_id}')],
                [InlineKeyboardButton("انصراف", callback_data=f'backup_panel_{panel_id}')]
            ]
            
            await query.edit_message_text(
                text=f"✅ بکاپ تستی با موفقیت به کانال ارسال شد!\n\n"
                f"📢 کانال: `{channel_id}`\n\n"
                f"حالا می‌توانید زمان‌بندی کرونجاب را برای بکاپ خودکار انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'backup_panel_{panel_id}')]]
            await query.edit_message_text(
                text=f"❌ خطا در ارسال بکاپ به کانال!\n\n"
                f"خطا: {str(e)}\n\n"
                f"لطفاً مطمئن شوید:\n"
                f"- ربات در کانال ادمین است\n"
                f"- آیدی کانال صحیح است",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return WAITING_CRON_SCHEDULE
        
    except Exception as e:
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'backup_panel_{panel_id}')]]
        await query.edit_message_text(
            text=f"❌ خطا: {str(e)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    return WAITING_CRON_SCHEDULE


async def backup_setup_cron(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Setup cron job on server"""
    query = update.callback_query
    
    # Parse schedule from callback data
    schedule_match = re.search(r'cron_schedule_(\d+)h', query.data)
    if not schedule_match:
        await query.answer("خطا در تشخیص زمان‌بندی!", show_alert=True)
        return ConversationHandler.END
    
    hours = int(schedule_match.group(1))
    panel_id = context.user_data.get('backup_panel_id')
    channel = context.user_data.get('backup_channel')
    
    config = get_panel_config(panel_id)
    
    if not config:
        await query.answer("پنل پیدا نشد!", show_alert=True)
        return ConversationHandler.END
    
    await query.edit_message_text("در حال تنظیم بکاپ خودکار... لطفاً صبر کنید.")
    
    panel_type = config['panel_type']
    server_ip = config['server_ip']
    ssh_port = config.get('ssh_port', 22)
    server_username = config.get('server_username', 'root')
    server_password = config.get('server_password', '')
    
    try:
        ssh = SSHManager()
        if not ssh.connect(server_ip, ssh_port, server_username, server_password):
            await query.edit_message_text("خطا در اتصال به سرور!")
            return ConversationHandler.END
        
        # Get bot token from config
        from config import BOT_TOKEN
        
        if panel_type == '3x-ui':
            # Create 3x-ui backup script
            backup_script = f"""#!/bin/bash
# 3X-UI Backup Script
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="/tmp/3xui_backup_$DATE.tar.gz" # Changed from zip to tar.gz
PANEL_ID="{panel_id}"
CHANNEL_ID="{channel}"
BOT_TOKEN="{BOT_TOKEN}"

# Create tar.gz backup # Changed from zip to tar.gz
cd /etc/x-ui && tar -czf $BACKUP_FILE x-ui.db 2>/dev/null # Changed from zip to tar.gz

# Send to Telegram channel
if [[ -f "$BACKUP_FILE" ]]; then
    curl -F "chat_id=$CHANNEL_ID" \\
         -F "document=@$BACKUP_FILE" \\
         -F "caption=بکاپ خودکار 3X-UI%0APanel ID: $PANEL_ID%0Aتاریخ: $DATE" \\
         "https://api.telegram.org/bot$BOT_TOKEN/sendDocument" >/dev/null 2>&1
    
    rm -f $BACKUP_FILE
fi
"""
            
        elif panel_type == 'marzban':
            # Create Marzban backup script
            backup_script = f"""#!/bin/bash
# Marzban Backup Script
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="/tmp/marzban_backup_$DATE.tar.gz"
PANEL_ID="{panel_id}"
CHANNEL_ID="{channel}"
BOT_TOKEN="{BOT_TOKEN}"
REMARK="marzban"
DATABASE_SUFFIX="_database.sql"
LOGS_SUFFIX="_logs.txt"

# Check environment file
ENV_FILE="/opt/marzban/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    exit 1
fi

# Extract database URL
SQLALCHEMY_DATABASE_URL=$(grep -v '^#' "$ENV_FILE" | grep 'SQLALCHEMY_DATABASE_URL' | awk -F '=' '{{print $2}}' | tr -d ' ' | tr -d '"' | tr -d "'")

BACKUP_DIRS="/opt/marzban /var/lib/marzban"
TEMP_FILES=""

# Backup MySQL/MariaDB if used
if [[ ! -z "$SQLALCHEMY_DATABASE_URL" && "$SQLALCHEMY_DATABASE_URL" != *"sqlite3"* ]]; then
    if [[ "$SQLALCHEMY_DATABASE_URL" =~ ^(mysql\\+pymysql|mariadb\\+pymysql)://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_USER="${{BASH_REMATCH[2]}}"
        DB_PASSWORD="${{BASH_REMATCH[3]}}"
        DB_HOST="${{BASH_REMATCH[4]}}"
        DB_PORT="${{BASH_REMATCH[5]}}"
        DB_NAME="${{BASH_REMATCH[6]}}"
        
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        mysqldump --column-statistics=0 -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
        
        if [[ -f "$DB_BACKUP_FILE" ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
            TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
        fi
    fi
fi

# Get Marzban logs
if command -v marzban &> /dev/null; then
    LOGS_FILE="/root/_${{REMARK}}${{LOGS_SUFFIX}}"
    marzban logs --no-follow > "$LOGS_FILE" 2>/dev/null
    
    if [[ -f "$LOGS_FILE" ]]; then
        BACKUP_DIRS="$BACKUP_DIRS $LOGS_FILE"
        TEMP_FILES="$TEMP_FILES $LOGS_FILE"
    fi
fi

# Create tar.gz backup
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null

# Clean up temp files
if [[ ! -z "$TEMP_FILES" ]]; then
    rm -f $TEMP_FILES
fi

# Send to Telegram channel
if [[ -f "$BACKUP_FILE" ]]; then
    curl -F "chat_id=$CHANNEL_ID" \\
         -F "document=@$BACKUP_FILE" \\
         -F "caption=بکاپ خودکار Marzban%0APanel ID: $PANEL_ID%0Aتاریخ: $DATE" \\
         "https://api.telegram.org/bot$BOT_TOKEN/sendDocument" >/dev/null 2>&1
    
    rm -f $BACKUP_FILE
fi
"""
        
        elif panel_type == 'marzneshin':
            # Create Marzneshin backup script
            backup_script = f"""#!/bin/bash
# Marzneshin Backup Script
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="/tmp/marzneshin_backup_$DATE.tar.gz"
PANEL_ID="{panel_id}"
CHANNEL_ID="{channel}"
BOT_TOKEN="{BOT_TOKEN}"
REMARK="marzneshin"
DATABASE_SUFFIX="_database.sql"
LOGS_SUFFIX="_logs.txt"

# Check docker-compose file
DOCKER_COMPOSE_FILE="/etc/opt/marzneshin/docker-compose.yml"
if [[ ! -f "$DOCKER_COMPOSE_FILE" ]]; then
    exit 1
fi

# Extract database configuration
DB_TYPE=$(yq eval '.services.db.image' "$DOCKER_COMPOSE_FILE" 2>/dev/null || echo "")
DB_NAME=$(yq eval '.services.db.environment.MARIADB_DATABASE // .services.db.environment.MYSQL_DATABASE' "$DOCKER_COMPOSE_FILE" 2>/dev/null || echo "")
DB_PASSWORD=$(yq eval '.services.db.environment.MARIADB_ROOT_PASSWORD // .services.db.environment.MYSQL_ROOT_PASSWORD' "$DOCKER_COMPOSE_FILE" 2>/dev/null || echo "")
DB_PORT=$(yq eval '.services.db.ports[0]' "$DOCKER_COMPOSE_FILE" 2>/dev/null | cut -d':' -f2 || echo "3306")

# Determine database type
if [[ "$DB_TYPE" == *"mariadb"* ]]; then
    DB_TYPE="mariadb"
elif [[ "$DB_TYPE" == *"mysql"* ]]; then
    DB_TYPE="mysql"
else
    DB_TYPE="sqlite"
fi

# Setup backup directories
BACKUP_DIRS="/etc/opt/marzneshin"
TEMP_FILES=""

# Scan and add volumes from docker-compose
for service in $(yq eval '.services | keys | .[]' "$DOCKER_COMPOSE_FILE" 2>/dev/null); do
    for volume in $(yq eval ".services.$service.volumes | .[]" "$DOCKER_COMPOSE_FILE" 2>/dev/null | awk -F ':' '{{print $1}}'); do
        if [[ -d "$volume" && ! "$volume" =~ /(mysql|mariadb)$ ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $volume"
        fi
    done
done

# Backup MySQL/MariaDB if used
if [[ "$DB_TYPE" != "sqlite" && ! -z "$DB_PASSWORD" && ! -z "$DB_NAME" ]]; then
    DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
    mysqldump -h 127.0.0.1 --column-statistics=0 -P $DB_PORT -u root -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
    
    if [[ -f "$DB_BACKUP_FILE" ]]; then
        BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
        TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
    fi
fi

# Get Marzneshin logs
if command -v marzneshin &> /dev/null; then
    LOGS_FILE="/root/_${{REMARK}}${{LOGS_SUFFIX}}"
    marzneshin logs --no-follow > "$LOGS_FILE" 2>/dev/null
    
    if [[ -f "$LOGS_FILE" ]]; then
        BACKUP_DIRS="$BACKUP_DIRS $LOGS_FILE"
        TEMP_FILES="$TEMP_FILES $LOGS_FILE"
    fi
fi

# Create tar.gz backup
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null

# Clean up temp files
if [[ ! -z "$TEMP_FILES" ]]; then
    rm -f $TEMP_FILES
fi

# Send to Telegram channel
if [[ -f "$BACKUP_FILE" ]]; then
    curl -F "chat_id=$CHANNEL_ID" \\
         -F "document=@$BACKUP_FILE" \\
         -F "caption=بکاپ خودکار Marzneshin%0APanel ID: $PANEL_ID%0Aتاریخ: $DATE" \\
         "https://api.telegram.org/bot$BOT_TOKEN/sendDocument" >/dev/null 2>&1
    
    rm -f $BACKUP_FILE
fi
"""
        
        elif panel_type == 'pasarguard':
            # Create Pasarguard backup script
            backup_script = f"""#!/bin/bash
# Pasarguard Backup Script
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="/tmp/pasarguard_backup_$DATE.tar.gz"
PANEL_ID="{panel_id}"
CHANNEL_ID="{channel}"
BOT_TOKEN="{BOT_TOKEN}"
REMARK="pasarguard"
DATABASE_SUFFIX="_database.sql"

# Check environment file
ENV_FILE="/opt/pasarguard/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    exit 1
fi

# Extract DATABASE_URL
DATABASE_URL=$(grep -v '^#' "$ENV_FILE" | grep 'SQLALCHEMY_DATABASE_URL' | awk -F '=' '{{print $2}}' | tr -d ' ' | tr -d '"' | tr -d "'")

# Initialize backup directories
BACKUP_DIRS="/opt/pasarguard /var/lib/pasarguard"
TEMP_FILES=""

# Determine database type and backup accordingly
if [[ -z "$DATABASE_URL" || "$DATABASE_URL" == *"sqlite"* ]]; then
    DB_TYPE="sqlite"
else
    if [[ "$DATABASE_URL" =~ ^(postgresql|postgres|timescaledb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_TYPE="postgresql"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="${{BASH_REMATCH[6]}}"
        DB_NAME="${{BASH_REMATCH[7]}}"
        
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        PG_CONTAINER=$(docker ps --filter "ancestor=postgres" --filter "ancestor=timescaledb/timescaledb" --format "{{{{.Names}}}}" | head -n 1)
        if [[ -z "$PG_CONTAINER" ]]; then
            PG_CONTAINER=$(docker ps --filter "publish=$DB_PORT" --format "{{{{.Names}}}}" | head -n 1)
        fi
        
        if [[ ! -z "$PG_CONTAINER" ]]; then
            docker exec -e PGPASSWORD="$DB_PASSWORD" $PG_CONTAINER pg_dump -U $DB_USER -d "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
            if [[ -f "$DB_BACKUP_FILE" ]]; then
                BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
                TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
            fi
        fi
        
    elif [[ "$DATABASE_URL" =~ ^(postgresql|postgres|timescaledb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^/]+)/(.+)$ ]]; then
        DB_TYPE="postgresql"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="5432"
        DB_NAME="${{BASH_REMATCH[6]}}"
        
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        PG_CONTAINER=$(docker ps --filter "ancestor=postgres" --filter "ancestor=timescaledb/timescaledb" --format "{{{{.Names}}}}" | head -n 1)
        if [[ ! -z "$PG_CONTAINER" ]]; then
            docker exec -e PGPASSWORD="$DB_PASSWORD" $PG_CONTAINER pg_dump -U $DB_USER -d "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
            if [[ -f "$DB_BACKUP_FILE" ]]; then
                BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
                TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
            fi
        fi
        
    elif [[ "$DATABASE_URL" =~ ^(mysql|mariadb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^:]+):([0-9]+)/(.+)$ ]]; then
        DB_TYPE="${{BASH_REMATCH[1]}}"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="${{BASH_REMATCH[6]}}"
        DB_NAME="${{BASH_REMATCH[7]}}"
        
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        mysqldump --column-statistics=0 -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
        if [[ -f "$DB_BACKUP_FILE" ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
            TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
        fi
        
    elif [[ "$DATABASE_URL" =~ ^(mysql|mariadb)(\\+[a-z0-9]+)?://([^:]+):([^@]+)@([^/]+)/(.+)$ ]]; then
        DB_TYPE="${{BASH_REMATCH[1]}}"
        DB_USER="${{BASH_REMATCH[3]}}"
        DB_PASSWORD="${{BASH_REMATCH[4]}}"
        DB_HOST="${{BASH_REMATCH[5]}}"
        DB_PORT="3306"
        DB_NAME="${{BASH_REMATCH[6]}}"
        
        DB_BACKUP_FILE="/root/_${{REMARK}}${{DATABASE_SUFFIX}}"
        mysqldump --column-statistics=0 -h $DB_HOST -P $DB_PORT -u $DB_USER -p"$DB_PASSWORD" "$DB_NAME" > "$DB_BACKUP_FILE" 2>/dev/null
        if [[ -f "$DB_BACKUP_FILE" ]]; then
            BACKUP_DIRS="$BACKUP_DIRS $DB_BACKUP_FILE"
            TEMP_FILES="$TEMP_FILES $DB_BACKUP_FILE"
        fi
    fi
fi

# Create tar.gz backup
tar -czf "$BACKUP_FILE" $BACKUP_DIRS 2>/dev/null

# Clean up temp files
if [[ ! -z "$TEMP_FILES" ]]; then
    rm -f $TEMP_FILES
fi

# Send to Telegram channel
if [[ -f "$BACKUP_FILE" ]]; then
    curl -F "chat_id=$CHANNEL_ID" \\
         -F "document=@$BACKUP_FILE" \\
         -F "caption=بکاپ خودکار Pasarguard%0APanel ID: $PANEL_ID%0Aتاریخ: $DATE" \\
         "https://api.telegram.org/bot$BOT_TOKEN/sendDocument" >/dev/null 2>&1
    
    rm -f $BACKUP_FILE
fi
"""
        
        else:
            await query.edit_message_text(f"بکاپ خودکار برای پنل نوع {panel_type} هنوز پشتیبانی نمی‌شود.")
            ssh.disconnect()
            return ConversationHandler.END
        
        # Upload backup script
        script_name = f'/root/backup_{panel_type}_{panel_id}.sh'
        ssh.upload_string(backup_script, script_name)
        ssh.execute_command(f'chmod +x {script_name}')
        
        # Setup cron job
        cron_schedule = f"0 */{hours} * * *"  # Every X hours
        cron_command = f'{cron_schedule} {script_name}'
        
        # Add cron job (remove existing ones for this panel first)
        ssh.execute_command(f"(crontab -l 2>/dev/null | grep -v '{panel_id}'; echo '{cron_command}') | crontab -")
        
        ssh.disconnect()
        
        keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'panel_info_{panel_id}')]]
        
        message = f"✅ بکاپ خودکار با موفقیت تنظیم شد!\n\n"
        message += f"📊 پنل: {panel_type.upper()}\n"
        message += f"⏰ زمان‌بندی: هر {hours} ساعت\n"
        message += f"📢 کانال: {channel}\n\n"
        message += f"بکاپ‌ها به صورت خودکار در بازه‌های زمانی مشخص شده به کانال تلگرام شما ارسال خواهند شد."
        
        await query.edit_message_text(
            text=message,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    except Exception as e:
        await query.edit_message_text(f"خطا در تنظیم بکاپ خودکار:\n{str(e)}")
    
    await query.answer()
    return ConversationHandler.END

async def cancel_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel backup process"""
    query = update.callback_query
    panel_id = context.user_data.get('backup_panel_id')
    
    keyboard = [[InlineKeyboardButton("بازگشت", callback_data=f'panel_info_{panel_id}')]]
    
    await query.edit_message_text(
        text="عملیات بکاپ لغو شد.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await query.answer()
    
    return ConversationHandler.END

async def backup_temporary_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle temporary backup button"""
    query = update.callback_query
    await query.answer()
    
    # Extract panel_id from callback_data: backup_temp_{panel_type}_{panel_id}
    parts = query.data.split('_')
    panel_type = parts[2]
    panel_id = int(parts[3])
    
    # Get panel details
    # This line uses the imported db module, which was removed earlier in the updates.
    # Assuming 'db' module is not available or intended to be used here,
    # we'll use get_panel_config as done in other backup functions for consistency.
    # If 'db' module is crucial, it needs to be re-imported.
    # For now, let's use get_panel_config
    
    config = get_panel_config(str(panel_id)) # Ensure panel_id is string if get_panel_config expects it
    if not config:
        await query.edit_message_text("پنل پیدا نشد.")
        return
    
    await query.edit_message_text("در حال ایجاد بکاپ، لطفا صبر کنید...")
    
    server_ip = config['server_ip']
    ssh_port = config.get('ssh_port', 22)
    server_username = config.get('server_username', 'root')
    server_password = config.get('server_password', '')

    # Connect to server via SSH
    ssh = SSHManager()
    if not ssh.connect(server_ip, ssh_port, server_username, server_password):
        await query.edit_message_text("خطا در اتصال به سرور.")
        return
    
    try:
        date_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        if panel_type == '3xui':
            # Backup 3x-ui database
            backup_filename = f"3xui_backup_{date_str}.tar.gz"
            remote_backup_path = f"/root/{backup_filename}"
            
            # Create tar.gz backup of x-ui.db
            command = f"cd /etc/x-ui && tar -czf {remote_backup_path} x-ui.db"
            output, error = ssh.execute_command(command)
            
            if error and "warning" not in error.lower():
                await query.edit_message_text(f"خطا در ایجاد بکاپ:\n{error}")
                ssh.disconnect()
                return
            
            # Download the backup file
            sftp = ssh.ssh.open_sftp()
            file_data = io.BytesIO()
            sftp.getfo(remote_backup_path, file_data)
            file_data.seek(0)
            sftp.close()
            
            # Delete remote backup file
            ssh.execute_command(f"rm -f {remote_backup_path}")
            ssh.disconnect()
            
            # Send backup file to user
            await context.bot.send_document(
                chat_id=query.from_user.id,
                document=file_data,
                filename=backup_filename,
                caption=f"بکاپ پنل 3X-UI\n\nPanel ID: `{panel_id}`\n\nتاریخ: {date_str.replace('_', ' ')}",
                parse_mode='Markdown'
            )
        # Add other panel types if needed for temporary backups
        # elif panel_type == 'marzban':
        #     ...

    except Exception as e:
        await query.edit_message_text(f"خطا در تهیه بکاپ:\n{str(e)}")
        if ssh:
            ssh.disconnect()
    finally:
        # Ensure SSH connection is closed if it was opened
        if 'ssh' in locals() and ssh and ssh.ssh and ssh.ssh.get_transport() and ssh.ssh.get_transport().is_active():
            ssh.disconnect()
