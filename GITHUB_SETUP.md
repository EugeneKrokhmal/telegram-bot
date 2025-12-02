# GitHub Repository Setup

Your git repository is initialized and ready! Here's how to push it to GitHub:

## Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the **+** icon in the top right → **New repository**
3. Repository name: `telegram-bot` (or your preferred name)
4. Description: `AI-powered Telegram bot with daily summaries`
5. Visibility: **Private** (recommended, since it contains deployment info) or **Public**
6. **DO NOT** initialize with README, .gitignore, or license (we already have these)
7. Click **Create repository**

## Step 2: Connect Local Repo to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
cd "/Users/eugenekrokhmal/Sites/AI Telegram Helper"

# Add GitHub as remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/telegram-bot.git

# Verify remote was added
git remote -v

# Push to GitHub
git push -u origin main
```

## Step 3: Verify

1. Go to your GitHub repository page
2. You should see all your files there
3. Check that `.env` is **NOT** visible (it's in .gitignore)

## Your Repository URL

Once pushed, your repository URL will be:
```
https://github.com/YOUR_USERNAME/telegram-bot.git
```

**Save this URL** - you'll need it for the AWS deployment script!

## Next Steps

After pushing to GitHub:

1. **Update AWS deployment script** with your repo URL:
   - The `setup_bot_server.sh` script will use this URL
   - Or pass it as argument: `./setup_bot_server.sh https://github.com/YOUR_USERNAME/telegram-bot.git`

2. **Continue with AWS deployment**:
   - Follow `AWS_DEPLOYMENT_GUIDE.md`
   - Use `DEPLOYMENT_CHECKLIST.md` to track progress

## Security Notes

✅ **Good** - These are already in `.gitignore`:
- `.env` (contains your API keys)
- `venv/` (virtual environment)
- `*.pem` (AWS keys)

⚠️ **Important**: Never commit:
- Your actual `.env` file with real tokens
- AWS key pair files (`.pem` files)
- Any hardcoded API keys or secrets

## Future Updates

When you make changes:

```bash
git add .
git commit -m "Description of changes"
git push
```

Then on your AWS server:
```bash
cd /opt/telegram-bot
./update.sh  # or: git pull && sudo systemctl restart bot
```

