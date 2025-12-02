# AWS EC2 Deployment Guide for Telegram Bot

## 1. High-Level Plan

### Architecture Overview

Your Telegram bot will run on a single EC2 instance with the following setup:

- **EC2 Instance**: Ubuntu 22.04 LTS (free tier eligible)
- **Instance Type**: `t2.micro` or `t3.micro` (1 vCPU, 1GB RAM)
- **Python Environment**: Python 3.10+ with virtualenv
- **Service Management**: systemd service for automatic startup and restart
- **Bot Location**: `/opt/telegram-bot`
- **Polling Method**: Long polling (no webhook needed)

### Cost Analysis

- **EC2 t2.micro**: Free tier eligible (750 hours/month for 12 months) OR ~$8-10/month after free tier
- **Data Transfer**: First 100GB/month free, then ~$0.09/GB
- **Storage**: 8GB EBS (free tier) or ~$0.80/month for 20GB
- **Elastic IP**: Free if attached to running instance, $0.005/hour if stopped

**Expected Monthly Cost**: 
- **Free Tier (first 12 months)**: $0-2/month (only data transfer/storage)
- **After Free Tier**: $8-12/month (well within your $100 credits)

This setup will easily run for 8-12 months on $100 AWS credits.

---

## 2. AWS Console Setup Instructions

### Step 1: Create a Key Pair

1. Go to AWS Console → **EC2** → **Key Pairs** (left sidebar)
2. Click **Create key pair**
3. Name: `telegram-bot-key`
4. Key pair type: **RSA**
5. Private key file format: **.pem**
6. Click **Create key pair**
7. **IMPORTANT**: Download the `.pem` file and save it securely (you'll need it to SSH)

### Step 2: Launch EC2 Instance

1. Go to **EC2** → **Instances** → **Launch instance**
2. **Name**: `telegram-bot-server`
3. **AMI**: Select **Ubuntu Server 22.04 LTS** (free tier eligible)
4. **Instance type**: `t2.micro` (free tier eligible) or `t3.micro`
5. **Key pair**: Select `telegram-bot-key` (created in Step 1)
6. **Network settings**: 
   - Click **Edit**
   - **Security group**: Create new security group
   - **Security group name**: `telegram-bot-sg`
   - **Description**: `SSH and bot traffic`
   - **Inbound rules**: 
     - Type: **SSH**, Port: **22**, Source: **My IP** (or your IP address)
     - Click **Add security group rule**
     - Type: **All traffic**, Port: **All**, Source: **0.0.0.0/0** (for bot polling - optional, can be removed if you want stricter security)
   - **Outbound rules**: Leave default (all traffic)
7. **Configure storage**: 
   - **Volume size**: 20 GB (free tier: 8GB, but 20GB is cheap)
   - **Volume type**: gp3 (default)
8. Click **Launch instance**

### Step 3: Get Your Instance IP

1. Go to **EC2** → **Instances**
2. Find your instance `telegram-bot-server`
3. Copy the **Public IPv4 address** (e.g., `54.123.45.67`)

### Step 4: (Optional) Allocate Elastic IP

**Why**: Elastic IP gives you a static IP that doesn't change when you restart the instance.

1. Go to **EC2** → **Elastic IPs** → **Allocate Elastic IP address**
2. Click **Allocate**
3. Select the Elastic IP → **Actions** → **Associate Elastic IP address**
4. Select your instance → **Associate**

**Note**: Elastic IP is free as long as it's attached to a running instance.

---

## 3. Server Bootstrap Script

The script below will set up everything on your EC2 instance. Save it as `setup_bot_server.sh`.

**Before running**: Replace `YOUR_GITHUB_USERNAME/telegram-bot` with your actual GitHub repo URL.

```bash
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
# You can either:
# 1. Set REPO_URL as environment variable: export REPO_URL="https://github.com/username/repo.git"
# 2. Pass it as argument: ./setup_bot_server.sh https://github.com/username/repo.git
# 3. Or edit this script and set it below
if [ -z "$REPO_URL" ] && [ -n "$1" ]; then
    REPO_URL="$1"
fi

if [ -z "$REPO_URL" ]; then
    echo "⚠️  REPO_URL not set!"
    echo "Please provide your GitHub repository URL:"
    echo "  Option 1: export REPO_URL='https://github.com/username/repo.git' && ./setup_bot_server.sh"
    echo "  Option 2: ./setup_bot_server.sh https://github.com/username/repo.git"
    echo "  Option 3: Edit this script and set REPO_URL variable"
    exit 1
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
```

**To run the script:**

1. SSH into your EC2 instance:
   ```bash
   ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP
   ```

2. **Option A - Clone from GitHub** (if script is in your repo):
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   chmod +x setup_bot_server.sh
   ./setup_bot_server.sh https://github.com/YOUR_USERNAME/YOUR_REPO.git
   ```

3. **Option B - Copy script manually**:
   ```bash
   nano setup_bot_server.sh
   ```
   (Paste the script content, save with Ctrl+X, then Y, then Enter)
   
   Make it executable and run with your repo URL:
   ```bash
   chmod +x setup_bot_server.sh
   ./setup_bot_server.sh https://github.com/YOUR_USERNAME/YOUR_REPO.git
   ```

   Or set it as environment variable:
   ```bash
   export REPO_URL="https://github.com/YOUR_USERNAME/YOUR_REPO.git"
   ./setup_bot_server.sh
   ```

---

## 4. Systemd Service File

Create a file called `bot.service` with the following content:

```ini
[Unit]
Description=Telegram Bot Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/telegram-bot
Environment="PATH=/opt/telegram-bot/venv/bin"
EnvironmentFile=/opt/telegram-bot/.env
ExecStart=/opt/telegram-bot/venv/bin/python /opt/telegram-bot/bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Installing the Service

After running the bootstrap script and setting up your `.env` file:

```bash
# Copy service file to systemd directory
sudo cp /opt/telegram-bot/bot.service /etc/systemd/system/bot.service

# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable bot

# Start the service
sudo systemctl start bot

# Check status
sudo systemctl status bot
```

### Useful Service Management Commands

```bash
# Check if service is running
sudo systemctl status bot

# View live logs
sudo journalctl -u bot -f

# View last 100 lines of logs
sudo journalctl -u bot -n 100

# Restart the service
sudo systemctl restart bot

# Stop the service
sudo systemctl stop bot

# Start the service
sudo systemctl start bot
```

---

## 5. Deployment / Update Instructions

### Initial Setup (One-Time)

1. **SSH into server**:
   ```bash
   ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP
   ```

2. **Run bootstrap script** (see Section 3)

3. **Configure environment variables**:
   ```bash
   nano /opt/telegram-bot/.env
   ```
   Add your `TELEGRAM_BOT_TOKEN` and other required variables.

4. **Install systemd service** (see Section 4)

### Updating the Bot (When You Make Code Changes)

1. **SSH into server**:
   ```bash
   ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP
   ```

2. **Navigate to bot directory**:
   ```bash
   cd /opt/telegram-bot
   ```

3. **Pull latest code**:
   ```bash
   git pull
   ```

4. **Update dependencies** (if `requirements.txt` changed):
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Restart the service**:
   ```bash
   sudo systemctl restart bot
   ```

6. **Verify it's running**:
   ```bash
   sudo systemctl status bot
   sudo journalctl -u bot -n 50
   ```

### Quick Update Script

You can create a simple update script at `/opt/telegram-bot/update.sh`:

```bash
#!/bin/bash
cd /opt/telegram-bot
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bot
echo "✅ Bot updated and restarted!"
```

Make it executable:
```bash
chmod +x /opt/telegram-bot/update.sh
```

Then updates are just:
```bash
./update.sh
```

---

## 6. Environment Variable Handling

### Recommended Approach: `.env` File

**Location**: `/opt/telegram-bot/.env`

**Format**:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
```

**Security**:
- File permissions: `600` (only owner can read/write)
- Never commit `.env` to Git (add to `.gitignore`)
- The systemd service reads this file via `EnvironmentFile=/opt/telegram-bot/.env`

**To edit**:
```bash
nano /opt/telegram-bot/.env
```

**To verify it's being read**:
```bash
sudo systemctl show bot | grep EnvironmentFile
```

### Alternative: Direct Environment Variables in systemd

If you prefer not to use a file, you can edit the systemd service:

```bash
sudo nano /etc/systemd/system/bot.service
```

Add lines like:
```ini
Environment="TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
Environment="OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx"
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart bot
```

**Recommendation**: Use `.env` file (easier to manage and update).

---

## 7. Validation Steps

### Step 1: Verify Process is Running

```bash
# Check systemd status
sudo systemctl status bot

# Should show: "Active: active (running)"
```

### Step 2: Check Logs for Errors

```bash
# View recent logs
sudo journalctl -u bot -n 50

# Look for:
# - "Bot starting…" message
# - No Python tracebacks or errors
# - Successful connection messages
```

### Step 3: Test Bot in Telegram

1. Open Telegram and find your bot
2. Send `/start` command
3. Bot should respond with welcome message
4. Try other commands like `/help`, `/summary`

### Step 4: Verify Auto-Restart

```bash
# Simulate a crash (kill the process)
sudo pkill -f "bot.py"

# Wait 10 seconds, then check status
sleep 10
sudo systemctl status bot

# Should show it restarted automatically
```

### Step 5: Verify Boot Startup

```bash
# Reboot the instance
sudo reboot

# Wait 2-3 minutes, then SSH back in and check:
sudo systemctl status bot

# Should show "Active: active (running)"
```

---

## 8. Optional Improvements

### A. Run Bot as Non-Root User (Recommended)

**Why**: Better security practice

**Steps**:
1. Create a dedicated user:
   ```bash
   sudo useradd -r -s /bin/false telegrambot
   sudo chown -R telegrambot:telegrambot /opt/telegram-bot
   ```

2. Update `bot.service`:
   ```ini
   User=telegrambot
   ```

3. Reload and restart:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl restart bot
   ```

### B. Basic Monitoring with CloudWatch

**What**: Monitor CPU, memory, disk usage

**Steps**:
1. EC2 Console → Your instance → **Monitoring** tab
2. Set up CloudWatch alarms for:
   - CPU utilization > 80%
   - Status check failures

**Cost**: Free tier includes basic monitoring

### C. Automated Backups

**What**: Backup your `.env` file and code

**Simple script** (`/opt/telegram-bot/backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/bot-backup-$(date +%Y%m%d).tar.gz /opt/telegram-bot/.env /opt/telegram-bot/*.py
# Keep only last 7 days
find $BACKUP_DIR -name "bot-backup-*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
crontab -e
# Add: 0 2 * * * /opt/telegram-bot/backup.sh
```

### D. Health Check Endpoint (Advanced)

If you want to add a simple HTTP health check endpoint, you could add a small Flask/FastAPI server alongside the bot, but this is optional and adds complexity.

---

## Troubleshooting

### Bot Not Starting

```bash
# Check service status
sudo systemctl status bot

# Check logs
sudo journalctl -u bot -n 100

# Common issues:
# - Missing .env file or wrong token
# - Python dependencies not installed
# - Wrong path in service file
```

### Bot Crashes Frequently

```bash
# Check logs for errors
sudo journalctl -u bot -f

# Check system resources
htop  # or: free -h, df -h

# Verify .env file is readable
cat /opt/telegram-bot/.env
```

### Can't SSH to Server

1. Check security group allows SSH from your IP
2. Verify key file permissions: `chmod 400 telegram-bot-key.pem`
3. Check instance is running in EC2 console

### Bot Not Responding in Telegram

1. Verify token is correct in `.env`
2. Check logs: `sudo journalctl -u bot -f`
3. Test token manually (use curl or Python script)
4. Ensure security group allows outbound traffic

---

## Summary Checklist

- [ ] Created EC2 key pair
- [ ] Launched EC2 instance (Ubuntu 22.04, t2.micro)
- [ ] Configured security group
- [ ] SSH'd into instance
- [ ] Ran `setup_bot_server.sh`
- [ ] Edited `.env` with `TELEGRAM_BOT_TOKEN`
- [ ] Installed systemd service
- [ ] Started and enabled service
- [ ] Verified bot responds in Telegram
- [ ] Tested auto-restart
- [ ] Verified boot startup

---

**You're all set!** Your bot should now be running 24/7 on AWS EC2. 🎉

