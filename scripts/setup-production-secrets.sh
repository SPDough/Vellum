#!/bin/bash

# Otomeshon Production Secrets Setup Script
# This script helps you set up the required GitHub secrets for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Otomeshon Production Secrets Setup${NC}"
echo "This script will help you set up the required GitHub secrets for production deployment."
echo ""

# Check if required tools are installed
command -v ssh-keygen >/dev/null 2>&1 || { echo -e "${RED}❌ ssh-keygen is required but not installed. Please install OpenSSH.${NC}" >&2; exit 1; }

# Get user input
echo -e "${YELLOW}Please provide the following information:${NC}"
echo ""

read -p "Production server IP or domain: " DEPLOY_HOST
read -p "SSH username for production server: " DEPLOY_USER
read -p "Path to application on production server (e.g., /opt/otomeshon): " DEPLOY_PATH

# Generate SSH key
echo ""
echo -e "${BLUE}🔑 Generating SSH key for deployment...${NC}"
SSH_KEY_PATH="$HOME/.ssh/otomeshon-deploy"
ssh-keygen -t ed25519 -C "otomeshon-production-deploy" -f "$SSH_KEY_PATH" -N ""

# Display the public key
echo ""
echo -e "${GREEN}✅ SSH key generated successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Public key (add to production server):${NC}"
echo "=================================================="
cat "${SSH_KEY_PATH}.pub"
echo "=================================================="
echo ""

# Display the private key
echo -e "${YELLOW}🔐 Private key (add to GitHub secrets as DEPLOY_SSH_KEY):${NC}"
echo "=================================================="
cat "$SSH_KEY_PATH"
echo "=================================================="
echo ""

# Create summary
echo -e "${GREEN}📝 GitHub Secrets Summary${NC}"
echo "=================================================="
echo "Secret Name: DEPLOY_HOST"
echo "Value: $DEPLOY_HOST"
echo ""
echo "Secret Name: DEPLOY_USER"
echo "Value: $DEPLOY_USER"
echo ""
echo "Secret Name: DEPLOY_PATH"
echo "Value: $DEPLOY_PATH"
echo ""
echo "Secret Name: DEPLOY_SSH_KEY"
echo "Value: [Copy the private key above]"
echo "=================================================="
echo ""

# Instructions
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Copy the public key to your production server:"
echo "   ssh-copy-id -i ${SSH_KEY_PATH}.pub $DEPLOY_USER@$DEPLOY_HOST"
echo ""
echo "2. Add the secrets to your GitHub repository:"
echo "   - Go to Settings > Secrets and variables > Actions"
echo "   - Add each secret with the values shown above"
echo ""
echo "3. Test SSH connection:"
echo "   ssh $DEPLOY_USER@$DEPLOY_HOST"
echo ""
echo "4. Set up your production server according to docs/PRODUCTION_DEPLOYMENT.md"
echo ""

# Optional: Create a backup of the keys
echo -e "${YELLOW}💾 Backup created at:${NC}"
echo "Public key: ${SSH_KEY_PATH}.pub"
echo "Private key: $SSH_KEY_PATH"
echo ""
echo -e "${RED}⚠️  Keep these files secure! The private key should never be shared.${NC}"

echo ""
echo -e "${GREEN}✅ Setup complete! You can now configure your production deployment.${NC}"
