# Full AWS Deployment Guide

This guide will walk you through deploying your Telegram bot to AWS EC2 from start to finish.

## Prerequisites

- AWS account with $100 credits
- GitHub repository: `https://github.com/EugeneKrokhmal/telegram-bot.git`
- Your API keys ready:
  - Telegram Bot Token (from @BotFather)
  - OpenAI API Key

## Quick Deployment (Automated)

If you want to use the automated deployment script:

```bash
./deploy.sh
```

The script will guide you through the process.

## Manual Deployment (Step-by-Step)

### Phase 1: AWS Console Setup (5-10 minutes)

#### 1.1 Create Key Pair

1. Go to [AWS Console](https://console.aws.amazon.com) → **EC2**
2. Click **Key Pairs** (left sidebar)
3. Click **Create key pair**
4. **Name**: `telegram-bot-key`
5. **Type**: RSA
6. **Format**: .pem
7. Click **Create key pair**
8. **Save the downloaded `.pem` file** to your project directory

#### 1.2 Launch EC2 Instance

1. In EC2, click **Instances** → **Launch instance**

2. **Configure**:
   - **Name**: `telegram-bot-server`
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance type**: t2.micro (free tier)
   - **Key pair**: Select `telegram-bot-key`
   - **Storage**: 20 GB

3. **Network settings** → Click **Edit**:
   - **Security group name**: `telegram-bot-sg`
   - **Inbound rules**:
     - SSH (port 22) from **My IP**
     - All traffic (0.0.0.0/0) - for bot polling
   - **Outbound rules**: Default (all traffic)

4. Click **Launch instance**

5. Wait for instance to be **running** (Status: 2/2 checks passed)

6. **Copy the Public IPv4 address** (e.g., `54.123.45.67`)

### Phase 2: Server Setup (5 minutes)

#### 2.1 SSH into Server

On your local machine:

```bash
# Navigate to project directory
cd "/Users/eugenekrokhmal/Sites/AI Telegram Helper"

# Set key permissions
chmod 400 telegram-bot-key.pem

# SSH into server (replace YOUR_EC2_IP with your Public IP)
ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP
```

#### 2.2 Run Setup Script

Once SSH'd in:

```bash
# Clone repository
git clone https://github.com/EugeneKrokhmal/telegram-bot.git
cd telegram-bot

# Run setup script
chmod +x setup_bot_server.sh
./setup_bot_server.sh
```

**Wait 2-3 minutes** for the script to complete.

#### 2.3 Configure Environment Variables

```bash
# Edit .env file
nano /opt/telegram-bot/.env
```

Add your keys:
```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Save**: `Ctrl+X`, then `Y`, then `Enter`

### Phase 3: Start Bot Service (2 minutes)

```bash
# Install systemd service
sudo cp /opt/telegram-bot/bot.service /etc/systemd/system/bot.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable bot

# Start the service
sudo systemctl start bot

# Check status
sudo systemctl status bot
```

You should see: `Active: active (running)`

### Phase 4: Verify Deployment (1 minute)

#### 4.1 Check Logs

```bash
# View live logs
sudo journalctl -u bot -f
```

Look for: `Bot starting…` (press `Ctrl+C` to exit)

#### 4.2 Test in Telegram

1. Open Telegram
2. Find your bot
3. Send `/start`
4. Bot should respond! 🎉

## Troubleshooting

### Can't SSH

```bash
# Check key permissions
chmod 400 telegram-bot-key.pem

# Verify security group allows SSH from your IP
# Check instance is running in AWS Console
```

### Bot Not Starting

```bash
# Check service status
sudo systemctl status bot

# View error logs
sudo journalctl -u bot -n 100

# Verify .env file
cat /opt/telegram-bot/.env

# Check file paths
ls -la /opt/telegram-bot/
```

### Bot Not Responding

```bash
# Check logs for errors
sudo journalctl -u bot -f

# Verify token is correct
cat /opt/telegram-bot/.env | grep TELEGRAM_BOT_TOKEN

# Restart service
sudo systemctl restart bot
```

## Future Updates

When you make code changes:

```bash
# SSH into server
ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP

# Update bot
cd /opt/telegram-bot
./update.sh

# Or manually:
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bot
```

## Cost Monitoring

- **Free Tier**: First 12 months - $0-2/month
- **After Free Tier**: ~$8-12/month
- **Your $100 credits**: Should last 8-12 months

Monitor costs in AWS Console → **Billing Dashboard**

## Security Best Practices

✅ **Done**:
- `.env` file excluded from git
- Key file permissions set correctly
- Security group configured

⚠️ **Optional Improvements**:
- Use separate user for bot (not `ubuntu`)
- Set up CloudWatch monitoring
- Regular backups of `.env` file
- Use AWS Secrets Manager for keys (advanced)

## Quick Reference Commands

```bash
# SSH into server
ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP

# Check bot status
sudo systemctl status bot

# View logs
sudo journalctl -u bot -f

# Restart bot
sudo systemctl restart bot

# Update bot
cd /opt/telegram-bot && ./update.sh
```

---

**You're all set!** Your bot should now be running 24/7 on AWS EC2. 🚀

