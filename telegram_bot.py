import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN
from database import init_database
from handlers.start_handler import start_command, main_menu, my_account_callback
from handlers.backhaul_handler import (
    backhaul_start, 
    get_iran_info as backhaul_get_iran_info, 
    get_foreign_info as backhaul_get_foreign_info, 
    IRAN_INFO as BACKHAUL_IRAN_INFO, 
    FOREIGN_INFO as BACKHAUL_FOREIGN_INFO
)
from handlers.chisel_handler import (
    chisel_start, 
    get_iran_info as chisel_get_iran_info, 
    get_foreign_info as chisel_get_foreign_info, 
    IRAN_INFO as CHISEL_IRAN_INFO, 
    FOREIGN_INFO as CHISEL_FOREIGN_INFO
)
from handlers.vxlan_handler import (
    vxlan_start, 
    get_iran_info as vxlan_get_iran_info, 
    get_foreign_info as vxlan_get_foreign_info, 
    VXLAN_IRAN_INFO, 
    VXLAN_FOREIGN_INFO
)
from handlers.mux_handler import (
    mux_start, 
    mux_get_iran_info, 
    mux_get_foreign_info, 
    MUX_IRAN_INFO, 
    MUX_FOREIGN_INFO
)
from handlers.panel_3xui_handler import (
    panel_3xui_start,
    get_server_info,
    SERVER_INFO
)
from handlers.panel_marzban_handler import (
    panel_marzban_start,
    get_marzban_server_info,
    MARZBAN_SERVER_INFO
)
from handlers.panel_pasarguard_handler import (
    panel_pasarguard_start,
    get_pasarguard_server_info,
    PASARGUARD_SERVER_INFO
)
from handlers.panel_marzneshin_handler import (
    panel_marzneshin_start,
    get_marzneshin_server_info,
    MARZNESHIN_SERVER_INFO
)
from handlers.tunnel_handler import tunnel_menu
from handlers.panel_handler import panel_menu
from handlers.other_handler import about_callback
from handlers.service_handler import manage_services_callback, my_tunnels_callback, my_panels_callback, tunnel_info_callback, delete_tunnel_callback, panel_info_callback, delete_panel_callback, force_delete_panel_callback
from handlers.admin_handler import (
    admin_panel,
    admin_users_list,
    admin_financial,
    admin_broadcast_start,
    admin_broadcast_send,
    admin_broadcast_cancel,
    BROADCAST_MESSAGE
)
from handlers.access_handler import (
    access_management_callback,
    add_admin_callback,
    receive_admin_id,
    cancel_add_admin,
    list_my_admins_callback,
    admin_detail_callback,
    toggle_admin_callback,
    remove_admin_callback,
    list_accessible_accounts_callback,
    switch_account_callback,
    reset_account_callback,
    WAITING_ADMIN_ID
)
from handlers.backup_handler import (
    backup_panel_callback,
    backup_instant_callback,
    backup_cron_start,
    backup_receive_channel,
    backup_setup_cron,
    cancel_backup,
    test_backup_to_channel,  # Added test backup handler import
    WAITING_CHANNEL,
    WAITING_CRON_SCHEDULE
)
# Added force join handler imports
from handlers.force_join_handler import (
    force_join_check,
    check_membership_callback,
    force_join_management,
    toggle_force_join,
    add_channel_start,
    receive_channel_id,
    remove_channel_menu,
    confirm_remove_channel,
    cancel_add_channel,
    WAITING_CHANNEL_ID
)
from handlers.payment_handler import (
    add_credit_callback,
    card_to_card_callback,
    crypto_gateway_callback,
    receive_amount,
    verify_account_callback,
    receive_phone,
    send_receipt_callback,
    receive_receipt,
    approve_transaction_callback,
    reject_transaction_callback,
    cancel_payment,
    SELECTING_PAYMENT_METHOD,
    ENTERING_AMOUNT,
    VERIFYING_PHONE,
    UPLOADING_RECEIPT
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def cancel_conversation_and_go_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel any ongoing conversation and return to main menu"""
    await main_menu(update, context)
    return ConversationHandler.END

async def main():
    init_database()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    await application.initialize()
    
    backhaul_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(backhaul_start, pattern='^tunnel_backhaul$')],
        states={
            BACKHAUL_IRAN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, backhaul_get_iran_info)],
            BACKHAUL_FOREIGN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, backhaul_get_foreign_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(backhaul_conversation)
    
    chisel_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(chisel_start, pattern='^tunnel_chisel$')],
        states={
            CHISEL_IRAN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, chisel_get_iran_info)],
            CHISEL_FOREIGN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, chisel_get_foreign_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(chisel_conversation)
    
    vxlan_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(vxlan_start, pattern='^tunnel_vxlan$')],
        states={
            VXLAN_IRAN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, vxlan_get_iran_info)],
            VXLAN_FOREIGN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, vxlan_get_foreign_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(vxlan_conversation)
    
    mux_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(mux_start, pattern='^tunnel_mux$')],
        states={
            MUX_IRAN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, mux_get_iran_info)],
            MUX_FOREIGN_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, mux_get_foreign_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(mux_conversation)
    
    panel_3xui_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(panel_3xui_start, pattern='^panel_3xui$')],
        states={
            SERVER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_server_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(panel_3xui_conversation)
    
    panel_marzban_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(panel_marzban_start, pattern='^panel_marzban$')],
        states={
            MARZBAN_SERVER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_marzban_server_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(panel_marzban_conversation)
    
    panel_pasarguard_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(panel_pasarguard_start, pattern='^panel_pasarguard$')],
        states={
            PASARGUARD_SERVER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pasarguard_server_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(panel_pasarguard_conversation)
    
    panel_marzneshin_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(panel_marzneshin_start, pattern='^panel_marzneshin$')],
        states={
            MARZNESHIN_SERVER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_marzneshin_server_info)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(panel_marzneshin_conversation)
    
    broadcast_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_broadcast_start, pattern='^admin_broadcast$')],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(admin_broadcast_cancel, pattern='^admin_panel$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(broadcast_conversation)
    
    access_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_admin_callback, pattern='^add_admin$')],
        states={
            WAITING_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_admin_id)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel_add_admin),
            CallbackQueryHandler(cancel_add_admin, pattern='^access_management$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(access_conversation)
    
    backup_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(backup_cron_start, pattern='^backup_cron_')],
        states={
            WAITING_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, backup_receive_channel)],
            WAITING_CRON_SCHEDULE: [
                CallbackQueryHandler(backup_setup_cron, pattern='^cron_schedule_'),
                CallbackQueryHandler(test_backup_to_channel, pattern='^test_backup_channel_')
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_backup, pattern='^backup_panel_')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(backup_conversation)
    
    force_join_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern='^add_force_join_channel$')],
        states={
            WAITING_CHANNEL_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_channel_id)],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CallbackQueryHandler(cancel_add_channel, pattern='^force_join_management$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(force_join_conversation)
    
    payment_conversation = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_credit_callback, pattern='^add_credit$')],
        states={
            SELECTING_PAYMENT_METHOD: [
                CallbackQueryHandler(card_to_card_callback, pattern='^payment_card_to_card$'),
                CallbackQueryHandler(crypto_gateway_callback, pattern='^payment_crypto_gateway$'),
            ],
            ENTERING_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_amount)],
            VERIFYING_PHONE: [
                MessageHandler(filters.CONTACT, receive_phone),
                CallbackQueryHandler(verify_account_callback, pattern='^verify_account$')
            ],
            UPLOADING_RECEIPT: [
                MessageHandler(filters.PHOTO, receive_receipt),
                CallbackQueryHandler(send_receipt_callback, pattern='^send_receipt$')
            ],
        },
        fallbacks=[
            CommandHandler("start", start_command),
            CommandHandler("cancel", cancel_payment),
            CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$')
        ],
        per_message=False,
        allow_reentry=True
    )
    
    application.add_handler(payment_conversation)
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(tunnel_menu, pattern='^install_tunnel$'))
    application.add_handler(CallbackQueryHandler(panel_menu, pattern='^install_panel$'))
    application.add_handler(CallbackQueryHandler(about_callback, pattern='^about$'))
    application.add_handler(CallbackQueryHandler(manage_services_callback, pattern='^manage_services$'))
    application.add_handler(CallbackQueryHandler(my_tunnels_callback, pattern='^my_tunnels$'))
    application.add_handler(CallbackQueryHandler(my_panels_callback, pattern='^my_panels$'))
    application.add_handler(CallbackQueryHandler(tunnel_info_callback, pattern='^tunnel_info_'))
    application.add_handler(CallbackQueryHandler(delete_tunnel_callback, pattern='^delete_tunnel_'))
    application.add_handler(CallbackQueryHandler(panel_info_callback, pattern='^panel_info_'))
    application.add_handler(CallbackQueryHandler(delete_panel_callback, pattern='^delete_panel_'))
    application.add_handler(CallbackQueryHandler(force_delete_panel_callback, pattern='^force_delete_panel_'))
    
    application.add_handler(CallbackQueryHandler(backup_panel_callback, pattern='^backup_panel_'))
    application.add_handler(CallbackQueryHandler(backup_instant_callback, pattern='^backup_instant_'))
    
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_users_list, pattern='^admin_users_list'))
    application.add_handler(CallbackQueryHandler(admin_financial, pattern='^admin_financial$'))
    
    application.add_handler(CallbackQueryHandler(access_management_callback, pattern='^access_management$'))
    application.add_handler(CallbackQueryHandler(list_my_admins_callback, pattern='^list_my_admins$'))
    application.add_handler(CallbackQueryHandler(admin_detail_callback, pattern='^admin_detail_'))
    application.add_handler(CallbackQueryHandler(toggle_admin_callback, pattern='^toggle_admin_'))
    application.add_handler(CallbackQueryHandler(remove_admin_callback, pattern='^remove_admin_'))
    application.add_handler(CallbackQueryHandler(list_accessible_accounts_callback, pattern='^list_accessible_accounts$'))
    application.add_handler(CallbackQueryHandler(switch_account_callback, pattern='^switch_account_'))
    application.add_handler(CallbackQueryHandler(reset_account_callback, pattern='^reset_account$'))
    
    application.add_handler(CallbackQueryHandler(check_membership_callback, pattern='^check_membership$'))
    application.add_handler(CallbackQueryHandler(force_join_management, pattern='^force_join_management$'))
    application.add_handler(CallbackQueryHandler(toggle_force_join, pattern='^toggle_force_join$'))
    application.add_handler(CallbackQueryHandler(remove_channel_menu, pattern='^remove_force_join_channel$'))
    application.add_handler(CallbackQueryHandler(confirm_remove_channel, pattern='^confirm_remove_channel_'))
    
    application.add_handler(CallbackQueryHandler(approve_transaction_callback, pattern='^approve_transaction_'))
    application.add_handler(CallbackQueryHandler(reject_transaction_callback, pattern='^reject_transaction_'))
    
    application.add_handler(CallbackQueryHandler(my_account_callback, pattern='^my_account$'))
    
    application.add_handler(CallbackQueryHandler(cancel_conversation_and_go_main_menu, pattern='^main_menu$'))
    
    await application.start()
    await application.updater.start_polling()
    
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopping bot...")
    finally:
        await application.stop()

if __name__ == '__main__':
    asyncio.run(main())
