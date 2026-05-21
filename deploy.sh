#!/bin/bash
# =============================================================
# DEPLOY SCRIPT - YouTube Downloader on Oracle Cloud VPS
# Run this on a fresh Ubuntu instance to set up everything
# =============================================================
set -e

echo "========================================="
echo "  YouTube Downloader - Full Setup"
echo "========================================="

# 1. Update system
echo "[1/6] Updating system..."
sudo apt-get update -y
sudo apt-get upgrade -y

# 2. Install Docker
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker $USER
    echo "Docker installed. User added to docker group."
else
    echo "Docker already installed."
fi

# Ensure docker compose plugin is available
sudo apt-get install -y docker-compose-plugin 2>/dev/null || true

# 3. Open firewall ports (Oracle Cloud Ubuntu uses iptables)
echo "[3/6] Configuring firewall..."
# Check if iptables rules already exist
if ! sudo iptables -L INPUT -n | grep -q "dpt:80"; then
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
    echo "  Port 80 opened"
fi
if ! sudo iptables -L INPUT -n | grep -q "dpt:443"; then
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
    echo "  Port 443 opened"
fi
if ! sudo iptables -L INPUT -n | grep -q "dpt:5000"; then
    sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 5000 -j ACCEPT
    echo "  Port 5000 opened"
fi

# Save iptables rules so they persist across reboots
sudo apt-get install -y iptables-persistent 2>/dev/null || true
sudo netfilter-persistent save 2>/dev/null || sudo sh -c "iptables-save > /etc/iptables/rules.v4" || true
echo "  Firewall rules saved."

# 4. Create project directory
echo "[4/6] Setting up project..."
PROJECT_DIR="/home/$USER/ytdownloader"
mkdir -p "$PROJECT_DIR/downloads"
mkdir -p "$PROJECT_DIR/templates"
mkdir -p "$PROJECT_DIR/static"
mkdir -p "$PROJECT_DIR/chrome_extension"

echo "  Project directory: $PROJECT_DIR"

# 5. Start services
echo "[5/6] Building and starting services..."
cd "$PROJECT_DIR"

# Need to use sudo docker if user group hasn't taken effect yet
if groups | grep -q docker; then
    docker compose up -d --build
else
    sudo docker compose up -d --build
fi

# 6. Verify
echo "[6/6] Verifying deployment..."
sleep 5

if groups | grep -q docker; then
    docker compose ps
else
    sudo docker compose ps
fi

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s icanhazip.com 2>/dev/null || echo "UNKNOWN")
SSLIP_DOMAIN=$(echo $PUBLIC_IP | tr '.' '-').sslip.io

echo ""
echo "========================================="
echo "  ✅ Deployment Complete!"
echo "========================================="
echo ""
echo "  Public IP: $PUBLIC_IP"
echo "  Web URL:   https://$SSLIP_DOMAIN/"
echo ""
echo "  NOTE: SSL certificate may take 1-2 minutes"
echo "  to be issued by Let's Encrypt via Caddy."
echo ""
echo "  Check logs:  docker compose logs -f"
echo "  Restart:     docker compose restart"
echo "========================================="
