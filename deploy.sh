#!/bin/bash
# AWS Deployment Helper Script
# This script helps you deploy your Telegram bot to AWS EC2

set -e

echo "🚀 AWS Telegram Bot Deployment Helper"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}⚠️  AWS CLI not found.${NC}"
    echo "You can still deploy manually using the AWS Console."
    echo "See AWS_QUICK_START.md for manual instructions."
    echo ""
    read -p "Continue with manual deployment guide? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Configuration
KEY_NAME="telegram-bot-key"
INSTANCE_NAME="telegram-bot-server"
AMI_ID="ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS - will auto-detect for us-east-2
INSTANCE_TYPE="t2.micro"
REGION="us-east-2"  # Your AWS region

echo "📋 Deployment Configuration:"
echo "  Key Pair: $KEY_NAME"
echo "  Instance Name: $INSTANCE_NAME"
echo "  Instance Type: $INSTANCE_TYPE"
echo "  Region: $REGION"
echo ""

# Step 1: Check for key pair
echo "Step 1: Checking for key pair..."
if [ -f "$KEY_NAME.pem" ]; then
    echo -e "${GREEN}✅ Key pair file found: $KEY_NAME.pem${NC}"
    chmod 400 "$KEY_NAME.pem"
else
    echo -e "${YELLOW}⚠️  Key pair file not found: $KEY_NAME.pem${NC}"
    echo ""
    echo "You need to:"
    echo "1. Go to AWS Console → EC2 → Key Pairs"
    echo "2. Create key pair named: $KEY_NAME"
    echo "3. Download the .pem file to this directory"
    echo ""
    read -p "Have you created the key pair? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Please create the key pair first. See AWS_QUICK_START.md"
        exit 1
    fi
fi

# Step 2: Get instance IP or create instance
echo ""
echo "Step 2: EC2 Instance Setup"
echo ""

if command -v aws &> /dev/null; then
    echo "Checking for existing instance..."
    INSTANCE_ID=$(aws ec2 describe-instances \
        --region $REGION \
        --filters "Name=tag:Name,Values=$INSTANCE_NAME" "Name=instance-state-name,Values=running" \
        --query 'Reservations[0].Instances[0].InstanceId' \
        --output text 2>/dev/null || echo "")
    
    if [ "$INSTANCE_ID" != "None" ] && [ -n "$INSTANCE_ID" ]; then
        echo -e "${GREEN}✅ Found running instance: $INSTANCE_ID${NC}"
        PUBLIC_IP=$(aws ec2 describe-instances \
            --region $REGION \
            --instance-ids $INSTANCE_ID \
            --query 'Reservations[0].Instances[0].PublicIpAddress' \
            --output text)
        echo -e "${GREEN}   Public IP: $PUBLIC_IP${NC}"
    else
        echo "No running instance found."
        echo ""
        read -p "Do you want to create a new EC2 instance via AWS CLI? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Creating EC2 instance..."
            # This would require more complex setup with security groups, etc.
            echo -e "${YELLOW}⚠️  Automatic instance creation requires security group setup.${NC}"
            echo "Please create the instance manually via AWS Console."
            echo "See AWS_QUICK_START.md Step 2 for instructions."
            exit 1
        else
            echo "Please provide your EC2 instance Public IP:"
            read -p "Public IP: " PUBLIC_IP
        fi
    fi
else
    echo "AWS CLI not available. Please provide your EC2 instance details."
    read -p "EC2 Public IP: " PUBLIC_IP
fi

if [ -z "$PUBLIC_IP" ] || [ "$PUBLIC_IP" == "None" ]; then
    echo -e "${RED}❌ No valid IP address. Exiting.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Using EC2 IP: $PUBLIC_IP${NC}"

# Step 3: Test SSH connection
echo ""
echo "Step 3: Testing SSH connection..."
if ssh -i "$KEY_NAME.pem" -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "echo 'SSH connection successful'" 2>/dev/null; then
    echo -e "${GREEN}✅ SSH connection successful!${NC}"
else
    echo -e "${YELLOW}⚠️  Could not connect via SSH.${NC}"
    echo "This might be normal if:"
    echo "  - Instance is still starting up"
    echo "  - Security group doesn't allow SSH from your IP"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 4: Deploy to server
echo ""
echo "Step 4: Deploying to server..."
echo ""

# Create deployment script
DEPLOY_SCRIPT=$(cat <<'DEPLOY_EOF'
#!/bin/bash
set -e

echo "🚀 Starting deployment on server..."

# Clone or update repository
if [ -d "/opt/telegram-bot" ]; then
    echo "📥 Updating existing repository..."
    cd /opt/telegram-bot
    git pull
else
    echo "📥 Cloning repository..."
    sudo mkdir -p /opt/telegram-bot
    sudo chown ubuntu:ubuntu /opt/telegram-bot
    git clone https://github.com/EugeneKrokhmal/telegram-bot.git /opt/telegram-bot
    cd /opt/telegram-bot
fi

# Run setup script if it exists
if [ -f "setup_bot_server.sh" ]; then
    echo "🔧 Running setup script..."
    chmod +x setup_bot_server.sh
    ./setup_bot_server.sh
else
    echo "⚠️  Setup script not found. Running manual setup..."
    
    # Install dependencies
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv git
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Install Python packages
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
fi

echo "✅ Deployment complete!"
DEPLOY_EOF
)

# Copy deployment script to server
echo "Uploading deployment script..."
echo "$DEPLOY_SCRIPT" | ssh -i "$KEY_NAME.pem" ubuntu@$PUBLIC_IP "cat > /tmp/deploy.sh && chmod +x /tmp/deploy.sh"

# Run deployment script
echo "Running deployment on server..."
ssh -i "$KEY_NAME.pem" ubuntu@$PUBLIC_IP "bash /tmp/deploy.sh"

echo ""
echo -e "${GREEN}✅ Deployment to server complete!${NC}"
echo ""
echo "Next steps:"
echo "1. SSH into server: ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo "2. Configure .env file: nano /opt/telegram-bot/.env"
echo "   Add your TELEGRAM_BOT_TOKEN and OPENAI_API_KEY"
echo "3. Install systemd service:"
echo "   sudo cp /opt/telegram-bot/bot.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable bot"
echo "   sudo systemctl start bot"
echo "4. Check status: sudo systemctl status bot"
echo ""
echo "Or run the automated setup:"
echo "  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP 'cd /opt/telegram-bot && ./setup_bot_server.sh'"

