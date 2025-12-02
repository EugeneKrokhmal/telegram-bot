# AWS Deployment Checklist

## Pre-Deployment

- [ ] **GitHub Repository**: Push your bot code to GitHub
  - If you don't have a repo yet:
    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
    git push -u origin main
    ```

- [ ] **Get your keys ready**:
  - [ ] Telegram Bot Token (from [@BotFather](https://t.me/botfather))
  - [ ] OpenAI API Key (from [OpenAI Platform](https://platform.openai.com/api-keys))

## AWS Setup

- [ ] Create EC2 key pair (`telegram-bot-key.pem`)
- [ ] Launch EC2 instance (Ubuntu 22.04, t2.micro)
- [ ] Configure security group (SSH + outbound traffic)
- [ ] (Optional) Allocate Elastic IP
- [ ] Note your EC2 instance IP address

## Server Setup

1. **SSH into server**:
   ```bash
   ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP
   ```

2. **Upload and run setup script**:
   ```bash
   # Option 1: Clone from GitHub (if script is in repo)
   git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
   cd YOUR_REPO
   chmod +x setup_bot_server.sh
   ./setup_bot_server.sh https://github.com/YOUR_USERNAME/YOUR_REPO.git
   
   # Option 2: Copy script manually
   nano setup_bot_server.sh  # Paste script content
   chmod +x setup_bot_server.sh
   ./setup_bot_server.sh https://github.com/YOUR_USERNAME/YOUR_REPO.git
   ```

3. **Configure environment variables**:
   ```bash
   nano /opt/telegram-bot/.env
   ```
   Add:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```
   Save with `Ctrl+X`, then `Y`, then `Enter`

4. **Install systemd service**:
   ```bash
   cd /opt/telegram-bot
   sudo cp bot.service /etc/systemd/system/bot.service
   sudo systemctl daemon-reload
   sudo systemctl enable bot
   sudo systemctl start bot
   ```

5. **Verify it's running**:
   ```bash
   sudo systemctl status bot
   sudo journalctl -u bot -f
   ```

## Testing

- [ ] Bot responds to `/start` command in Telegram
- [ ] Bot responds to `/help` command
- [ ] Bot can process messages and reply
- [ ] Check logs show no errors: `sudo journalctl -u bot -n 50`

## Future Updates

When you make code changes:

```bash
ssh -i telegram-bot-key.pem ubuntu@YOUR_EC2_IP
cd /opt/telegram-bot
./update.sh  # or manually: git pull && source venv/bin/activate && pip install -r requirements.txt && sudo systemctl restart bot
```

## Troubleshooting

- **Bot not starting**: Check logs with `sudo journalctl -u bot -n 100`
- **Can't SSH**: Verify security group allows SSH from your IP
- **Bot not responding**: Verify `.env` file has correct tokens
- **Service won't start**: Check file paths in `bot.service` match your setup

