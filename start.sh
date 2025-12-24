#!/bin/bash

# Set Python path to current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the bot
python3 telegram_bot.py
