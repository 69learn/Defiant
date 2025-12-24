#!/bin/bash

echo "🔄 Syncing all project files..."

# Create directories if they don't exist
mkdir -p handlers
mkdir -p utils
mkdir -p scripts

# List of all required files
echo "📁 Checking required files..."

required_files=(
    "telegram_bot.py"
    "config.py"
    "database.py"
    "handlers/__init__.py"
    "handlers/start_handler.py"
    "handlers/tunnel_handler.py"
    "handlers/backhaul_handler.py"
    "handlers/chisel_handler.py"
    "handlers/vxlan_handler.py"
    "handlers/mux_handler.py"
    "handlers/panel_handler.py"
    "handlers/panel_3xui_handler.py"
    "handlers/other_handler.py"
    "handlers/service_handler.py"
    "utils/__init__.py"
    "utils/ssh_manager.py"
    "utils/tunnel_utils.py"
    "utils/chisel_scripts.py"
    "utils/vxlan_scripts.py"
    "utils/mux_scripts.py"
    "utils/tunnel_delete_scripts.py"
)

missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
        echo "❌ Missing: $file"
    else
        echo "✅ Found: $file"
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo ""
    echo "✅ All required files are present!"
    echo ""
    echo "🚀 You can now run the bot with: ./runbot.sh"
else
    echo ""
    echo "⚠️  Missing ${#missing_files[@]} file(s)"
    echo ""
    echo "Please make sure you have downloaded all files from v0 and copied them to the server."
fi
