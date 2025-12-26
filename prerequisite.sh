#!/bin/bash

echo "شروع نصب پیش‌نیازها..."

# Update system
apt update && apt upgrade -y

# Install basic tools
apt install -y curl wget git unzip tar ca-certificates gnupg lsb-release net-tools iptables openssl

# Install Python and expect
apt install -y python3 python3-pip expect

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Certbot
apt install -y certbot

# Install lab

pip install python-telegram-bot paramiko asyncio python-dotenv pymysql

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 2087/tcp
ufw allow 8000/tcp
ufw allow 8080/tcp
ufw allow 8880/tcp
ufw --force enable

echo "نصب پیش‌نیازها با موفقیت انجام شد!"
