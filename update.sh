#!/bin/bash
# Quick update script for the Telegram bot
# Run this after making code changes: ./update.sh

cd /opt/telegram-bot
echo "📥 Pulling latest code..."
git pull

echo "📦 Updating dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "🔄 Restarting bot service..."
sudo systemctl restart bot

echo "✅ Bot updated and restarted!"
echo "📊 Check status with: sudo systemctl status bot"
echo "📋 View logs with: sudo journalctl -u bot -f"

