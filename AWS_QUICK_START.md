# AWS Quick Start Guide

Follow these steps to deploy your Telegram bot to AWS EC2.

## Step 1: Create EC2 Key Pair

1. Go to [AWS Console](https://console.aws.amazon.com) → **EC2**
2. In the left sidebar, click **Key Pairs** (under "Network & Security")
3. Click **Create key pair**
4. **Name**: `telegram-bot-key`
5. **Key pair type**: RSA
6. **Private key file format**: `.pem`
7. Click **Create key pair**
8. **IMPORTANT**: The `.pem` file will download automatically - save it securely!

## Step 2: Launch EC2 Instance

1. In EC2 console, click **Instances** → **Launch instance**

2. **Name**: `telegram-bot-server`

3. **Application and OS Images (Amazon Machine Image)**:
   - Search for: `Ubuntu`
   - Select: **Ubuntu Server 22.04 LTS** (free tier eligible)

4. **Instance type**:
   - Select: **t2.micro** (free tier eligible) or **t3.micro**

5. **Key pair (login)**:
   - Select: `telegram-bot-key` (the one you just created)

6. **Network settings** - Click **Edit**:
   - **Security group name**: `telegram-bot-sg`
   - **Description**: `SSH and bot traffic`
   - **Inbound security group rules**:
     - Click **Add security group rule**
     - **Type**: SSH
     - **Port**: 22
     - **Source**: My IP (or select "Anywhere-IPv4" if you want to SSH from anywhere - less secure)
     - Click **Add security group rule** again
     - **Type**: All traffic
     - **Port**: All
     - **Source**: 0.0.0.0/0 (for bot polling - this is safe for long polling)
   - **Outbound rules**: Leave default (all traffic allowed)

7. **Configure storage**:
   - **Volume size**: 20 GB (free tier: 8GB, but 20GB is cheap ~$2/month)
   - **Volume type**: gp3 (default)

8. Click **Launch instance**

9. Click **View all instances** at the bottom

## Step 3: Get Your Instance Details

1. Wait for instance to show **Status**: `running` and **Status check**: `2/2 checks passed` (takes 1-2 minutes)

2. Select your instance and note:
   - **Public IPv4 address** (e.g., `54.123.45.67`)
   - **Instance ID** (e.g., `i-0123456789abcdef0`)

3. **Copy the Public IPv4 address** - you'll need it for SSH

## Step 4: (Optional) Allocate Elastic IP

**Why**: Gives you a static IP that doesn't change when you restart the instance.

1. Go to **EC2** → **Elastic IPs** (left sidebar)
2. Click **Allocate Elastic IP address**
3. Click **Allocate**
4. Select the Elastic IP → **Actions** → **Associate Elastic IP address**
5. Select your instance → **Associate**

**Note**: Elastic IP is free as long as it's attached to a running instance.

## Step 5: SSH into Your Instance

On your local machine, open terminal and run:

```bash
# Make sure your .pem file has correct permissions
chmod 400 telegram-bot-key.pem

# SSH into the instance (replace YOUR_EC2_IP with your Public IPv4 address)
ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP
```

If you see a message about host authenticity, type `yes` and press Enter.

You should now be logged into your Ubuntu server! 🎉

## Step 6: Run Setup Script

Once you're SSH'd into the server:

```bash
# Clone your repository
git clone https://github.com/EugeneKrokhmal/telegram-bot.git
cd telegram-bot

# Make setup script executable
chmod +x setup_bot_server.sh

# Run setup script (it will use your repo URL automatically)
./setup_bot_server.sh
```

The script will:
- Update the system
- Install Python, git, and dependencies
- Clone your repository
- Set up virtual environment
- Install Python packages
- Create `.env` file template

**This takes about 2-3 minutes.**

## Step 7: Configure Environment Variables

After the setup script completes:

```bash
# Edit the .env file
nano /opt/telegram-bot/.env
```

You'll need to add:
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `OPENAI_API_KEY` - Your OpenAI API key

**Save with**: `Ctrl+X`, then `Y`, then `Enter`

## Step 8: Install and Start Bot Service

```bash
# Copy systemd service file
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

## Step 9: Verify Bot is Working

1. **Check logs**:
   ```bash
   sudo journalctl -u bot -f
   ```
   Look for: `Bot starting…` and no errors

2. **Test in Telegram**:
   - Open Telegram
   - Find your bot
   - Send `/start`
   - Bot should respond! 🎉

## Troubleshooting

### Can't SSH
- Check security group allows SSH from your IP
- Verify key file permissions: `chmod 400 telegram-bot-key.pem`
- Make sure you're using the correct Public IP

### Bot not starting
- Check logs: `sudo journalctl -u bot -n 100`
- Verify `.env` file has correct tokens: `cat /opt/telegram-bot/.env`
- Check service status: `sudo systemctl status bot`

### Bot not responding in Telegram
- Verify token is correct in `.env`
- Check logs for errors
- Ensure security group allows outbound traffic

## Next Steps

Once everything is working:

- **Monitor logs**: `sudo journalctl -u bot -f`
- **Update bot**: `cd /opt/telegram-bot && ./update.sh`
- **Restart bot**: `sudo systemctl restart bot`

## Cost Estimate

- **Free Tier (first 12 months)**: $0-2/month
- **After Free Tier**: $8-12/month
- Your $100 credits should last **8-12 months**!

---

**Ready?** Let's start with Step 1! 🚀

