#!/bin/bash
set -e  # Exit on error

echo "🚀 Starting Telegram Bot server setup..."

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages
echo "📦 Installing Python, git, and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git

# Create bot directory
BOT_DIR="/opt/telegram-bot"
echo "📁 Creating bot directory at $BOT_DIR..."
sudo mkdir -p $BOT_DIR
sudo chown $USER:$USER $BOT_DIR

# Clone repository
# Default repo URL (can be overridden)
DEFAULT_REPO_URL="https://github.com/EugeneKrokhmal/telegram-bot.git"

# You can either:
# 1. Set REPO_URL as environment variable: export REPO_URL="https://github.com/username/repo.git"
# 2. Pass it as argument: ./setup_bot_server.sh https://github.com/username/repo.git
# 3. Use default (EugeneKrokhmal/telegram-bot)
if [ -z "$REPO_URL" ] && [ -n "$1" ]; then
    REPO_URL="$1"
elif [ -z "$REPO_URL" ]; then
    REPO_URL="$DEFAULT_REPO_URL"
    echo "📦 Using default repository: $REPO_URL"
fi

echo "📥 Cloning repository from $REPO_URL..."
if [ -d "$BOT_DIR/.git" ]; then
    echo "Repository already exists, pulling latest changes..."
    cd $BOT_DIR
    git pull
else
    git clone $REPO_URL $BOT_DIR
    cd $BOT_DIR
fi

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
if [ ! -d "$BOT_DIR/venv" ]; then
    python3 -m venv $BOT_DIR/venv
fi

# Activate venv and install dependencies
echo "📦 Installing Python dependencies..."
source $BOT_DIR/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create environment file template
echo "📝 Creating environment file template..."
if [ ! -f "$BOT_DIR/.env" ]; then
    cat > $BOT_DIR/.env << EOF
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_here

# OpenAI API Key (if needed)
OPENAI_API_KEY=your_openai_key_here
EOF
    echo "⚠️  IMPORTANT: Edit $BOT_DIR/.env and add your BOT_TOKEN!"
    echo "   Run: nano $BOT_DIR/.env"
else
    echo "✅ .env file already exists"
fi

# Set proper permissions
echo "🔒 Setting file permissions..."
chmod 600 $BOT_DIR/.env  # Only owner can read/write

echo "✅ Server setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file: nano $BOT_DIR/.env"
echo "2. Add your TELEGRAM_BOT_TOKEN"
echo "3. Copy systemd service: sudo cp bot.service /etc/systemd/system/"
echo "4. Enable service: sudo systemctl enable bot"
echo "5. Start service: sudo systemctl start bot"
echo "6. Check status: sudo systemctl status bot"

