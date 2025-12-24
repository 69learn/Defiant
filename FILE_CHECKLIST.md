# File Checklist for Telegram Bot

## Core Files
- [ ] telegram_bot.py
- [ ] config.py
- [ ] database.py
- [ ] requirements.txt
- [ ] .env (create from .env.example)

## Scripts
- [ ] runbot.sh
- [ ] setup_database.sh
- [ ] sync_files.sh

## Handlers Directory
- [ ] handlers/__init__.py
- [ ] handlers/start_handler.py
- [ ] handlers/tunnel_handler.py
- [ ] handlers/backhaul_handler.py
- [ ] handlers/chisel_handler.py
- [ ] handlers/vxlan_handler.py
- [ ] handlers/mux_handler.py
- [ ] handlers/panel_handler.py
- [ ] handlers/panel_3xui_handler.py
- [ ] handlers/other_handler.py
- [ ] handlers/service_handler.py

## Utils Directory
- [ ] utils/__init__.py
- [ ] utils/ssh_manager.py
- [ ] utils/tunnel_utils.py
- [ ] utils/chisel_scripts.py
- [ ] utils/vxlan_scripts.py
- [ ] utils/mux_scripts.py
- [ ] utils/tunnel_delete_scripts.py

## Installation Steps

1. Download all files from v0 project
2. Upload to server in `/root/telegram-bot/` directory
3. Run sync check:
   \`\`\`bash
   chmod +x sync_files.sh
   ./sync_files.sh
   \`\`\`
4. If all files present, setup database:
   \`\`\`bash
   chmod +x setup_database.sh
   sudo ./setup_database.sh
   \`\`\`
5. Run the bot:
   \`\`\`bash
   chmod +x runbot.sh
   ./runbot.sh
   \`\`\`

## Troubleshooting

If you get "Module not found" errors:
- Make sure ALL files are uploaded to the correct directories
- Check that __init__.py files exist in handlers/ and utils/
- Verify file permissions (should be readable)
- Run sync_files.sh to check for missing files
