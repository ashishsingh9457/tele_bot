#!/bin/bash
# Quick setup script for 3proxy on Linux
# Run as root: sudo bash setup_home_proxy.sh

set -e

echo "=========================================="
echo "  Home Proxy Setup for Terabox Bot"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo bash $0"
    exit 1
fi

# Get configuration from user
echo "📝 Configuration:"
read -p "Enter proxy username [terabox]: " PROXY_USER
PROXY_USER=${PROXY_USER:-terabox}

read -sp "Enter proxy password: " PROXY_PASS
echo ""

if [ -z "$PROXY_PASS" ]; then
    echo "❌ Password cannot be empty"
    exit 1
fi

read -p "Enter SOCKS5 port [1080]: " SOCKS_PORT
SOCKS_PORT=${SOCKS_PORT:-1080}

read -p "Enter HTTP proxy port [3128]: " HTTP_PORT
HTTP_PORT=${HTTP_PORT:-3128}

echo ""
echo "✅ Configuration:"
echo "   Username: $PROXY_USER"
echo "   Password: ********"
echo "   SOCKS5 Port: $SOCKS_PORT"
echo "   HTTP Port: $HTTP_PORT"
echo ""

read -p "Continue with installation? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
apt-get update -qq
apt-get install -y build-essential git curl

# Download and compile 3proxy
echo "⬇️  Downloading 3proxy..."
cd /tmp
rm -rf 3proxy
git clone https://github.com/3proxy/3proxy.git
cd 3proxy

echo "🔨 Compiling 3proxy..."
make -f Makefile.Linux
make -f Makefile.Linux install

# Create config directory
mkdir -p /etc/3proxy
mkdir -p /var/log

# Create configuration file
echo "📝 Creating configuration..."
cat > /etc/3proxy/3proxy.cfg <<EOF
# 3proxy configuration for Terabox Bot
nserver 8.8.8.8
nserver 8.8.4.4

# Log settings
log /var/log/3proxy.log D
logformat "- +_L%t.%. %N.%p %E %U %C:%c %R:%r %O %I %h %T"
rotate 30

# Authentication
users $PROXY_USER:CL:$PROXY_PASS

# SOCKS5 proxy
auth strong
allow $PROXY_USER
socks -p$SOCKS_PORT

# HTTP proxy
auth strong
allow $PROXY_USER
proxy -p$HTTP_PORT
EOF

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/3proxy.service <<EOF
[Unit]
Description=3proxy Proxy Server for Terabox Bot
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
echo "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw allow $SOCKS_PORT/tcp comment "3proxy SOCKS5"
    ufw allow $HTTP_PORT/tcp comment "3proxy HTTP"
    ufw reload
    echo "✅ UFW firewall rules added"
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=$SOCKS_PORT/tcp
    firewall-cmd --permanent --add-port=$HTTP_PORT/tcp
    firewall-cmd --reload
    echo "✅ Firewalld rules added"
else
    echo "⚠️  No firewall detected. Make sure ports $SOCKS_PORT and $HTTP_PORT are open."
fi

# Start and enable service
echo "🚀 Starting 3proxy service..."
systemctl daemon-reload
systemctl enable 3proxy
systemctl start 3proxy

# Wait a moment for service to start
sleep 2

# Check status
if systemctl is-active --quiet 3proxy; then
    echo ""
    echo "=========================================="
    echo "  ✅ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "📊 Service Status:"
    systemctl status 3proxy --no-pager -l
    echo ""
    echo "📝 Configuration:"
    echo "   Config file: /etc/3proxy/3proxy.cfg"
    echo "   Log file: /var/log/3proxy.log"
    echo ""
    echo "🔌 Your Local IP:"
    LOCAL_IP=$(hostname -I | awk '{print $1}')
    echo "   $LOCAL_IP"
    echo ""
    echo "🧪 Test locally:"
    echo "   curl --socks5 localhost:$SOCKS_PORT --proxy-user $PROXY_USER:$PROXY_PASS https://api.ipify.org"
    echo ""
    echo "📋 Next Steps:"
    echo "   1. Configure port forwarding on your router:"
    echo "      - Forward port $SOCKS_PORT to $LOCAL_IP:$SOCKS_PORT (TCP)"
    echo "      - Forward port $HTTP_PORT to $LOCAL_IP:$HTTP_PORT (TCP)"
    echo ""
    echo "   2. Set up Dynamic DNS (if no static IP):"
    echo "      - Sign up at https://www.noip.com/ or https://www.duckdns.org/"
    echo "      - Create hostname (e.g., yourname.ddns.net)"
    echo ""
    echo "   3. Add to Railway environment variables:"
    echo "      PROXY_URL=socks5://$PROXY_USER:$PROXY_PASS@yourname.ddns.net:$SOCKS_PORT"
    echo ""
    echo "   4. Test from external network:"
    echo "      curl --socks5 yourname.ddns.net:$SOCKS_PORT --proxy-user $PROXY_USER:$PROXY_PASS https://api.ipify.org"
    echo ""
    echo "📖 Full guide: HOME_PROXY_SETUP.md"
    echo "=========================================="
else
    echo ""
    echo "❌ Failed to start 3proxy service"
    echo "Check logs: journalctl -u 3proxy -n 50"
    exit 1
fi
