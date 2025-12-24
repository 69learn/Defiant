#!/usr/bin/env python3
"""
Test script to check if all modules can be imported correctly
"""

import sys
import os

print("🔍 Testing imports...")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print()

# Test if handlers directory exists
if os.path.exists('handlers'):
    print("✅ handlers/ directory exists")
    print(f"   Files in handlers/: {os.listdir('handlers')}")
else:
    print("❌ handlers/ directory NOT found!")
print()

# Test if utils directory exists
if os.path.exists('utils'):
    print("✅ utils/ directory exists")
    print(f"   Files in utils/: {os.listdir('utils')}")
else:
    print("❌ utils/ directory NOT found!")
print()

# Test if backhaul_handler.py exists
if os.path.exists('handlers/backhaul_handler.py'):
    print("✅ handlers/backhaul_handler.py file exists")
else:
    print("❌ handlers/backhaul_handler.py file NOT found!")
print()

# Try importing modules one by one
modules_to_test = [
    'config',
    'database',
    'utils.ssh_manager',
    'utils.tunnel_utils',
    'handlers.start_handler',
    'handlers.tunnel_handler',
    'handlers.panel_handler',
    'handlers.other_handler',
    'handlers.backhaul_handler',
]

print("Testing imports:")
for module in modules_to_test:
    try:
        __import__(module)
        print(f"✅ {module}")
    except Exception as e:
        print(f"❌ {module}: {str(e)}")

print("\n🏁 Test complete!")
