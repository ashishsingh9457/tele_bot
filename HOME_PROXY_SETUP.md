# Setting Up Home PC as Residential Proxy

This guide will help you set up your home PC as a residential proxy server for the Terabox bot.

---

## **Prerequisites**

- Home PC/laptop running 24/7 (Windows, Linux, or Mac)
- Home internet connection (residential IP)
- Router access (for port forwarding)
- Basic command line knowledge

---

## **Step 1: Choose Your Proxy Server Software**

### **Option A: 3proxy (Recommended - Works on All OS)** ⭐

**Why 3proxy:**
- ✅ Lightweight and fast
- ✅ Works on Windows, Linux, Mac
- ✅ Easy to configure
- ✅ Supports SOCKS5 and HTTP

### **Option B: Dante (Linux Only)**
- Good for Linux servers
- More complex configuration

### **Option C: TinyProxy (HTTP Only)**
- Simpler but only HTTP (not SOCKS5)

---

## **Step 2: Install Proxy Server**

### **For Windows (3proxy):**

1. **Download 3proxy:**
```powershell
# Download from: https://github.com/3proxy/3proxy/releases
# Get: 3proxy-0.9.4.x86_64.zip (or latest version)
```

2. **Extract to folder:**
```powershell
# Extract to: C:\3proxy
```

3. **Create config file** `C:\3proxy\3proxy.cfg`:
```ini
# 3proxy configuration
nserver 8.8.8.8
nserver 8.8.4.4

# Log settings
log "C:\3proxy\3proxy.log" D
logformat "- +_L%t.%. %N.%p %E %U %C:%c %R:%r %O %I %h %T"

# Authentication (optional - recommended for security)
users terabox:CL:yourpassword

# SOCKS5 proxy on port 1080
auth strong
allow terabox
socks -p1080

# HTTP proxy on port 3128 (alternative)
auth strong
allow terabox
proxy -p3128
```

4. **Create start script** `C:\3proxy\start.bat`:
```batch
@echo off
cd C:\3proxy
3proxy.exe 3proxy.cfg
pause
```

5. **Run as Administrator:**
```powershell
# Right-click start.bat -> Run as Administrator
```

6. **Make it run on startup:**
```powershell
# Press Win+R, type: shell:startup
# Create shortcut to start.bat in this folder
```

---

### **For Linux (3proxy):**

1. **Install dependencies:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential git
```

2. **Download and compile 3proxy:**
```bash
cd /tmp
git clone https://github.com/3proxy/3proxy.git
cd 3proxy
make -f Makefile.Linux
sudo make -f Makefile.Linux install
```

3. **Create config file** `/etc/3proxy/3proxy.cfg`:
```ini
# 3proxy configuration
nserver 8.8.8.8
nserver 8.8.4.4

# Log settings
log /var/log/3proxy.log D
logformat "- +_L%t.%. %N.%p %E %U %C:%c %R:%r %O %I %h %T"

# Authentication
users terabox:CL:yourpassword

# SOCKS5 proxy on port 1080
auth strong
allow terabox
socks -p1080

# HTTP proxy on port 3128
auth strong
allow terabox
proxy -p3128
```

4. **Create systemd service** `/etc/systemd/system/3proxy.service`:
```ini
[Unit]
Description=3proxy Proxy Server
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/3proxy /etc/3proxy/3proxy.cfg
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

5. **Start and enable service:**
```bash
sudo systemctl daemon-reload
sudo systemctl start 3proxy
sudo systemctl enable 3proxy
sudo systemctl status 3proxy
```

---

### **For Mac (3proxy):**

1. **Install Homebrew (if not installed):**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

2. **Install 3proxy:**
```bash
brew install 3proxy
```

3. **Create config file** `/usr/local/etc/3proxy.cfg`:
```ini
# Same config as Linux above
nserver 8.8.8.8
nserver 8.8.4.4
log /usr/local/var/log/3proxy.log D
users terabox:CL:yourpassword
auth strong
allow terabox
socks -p1080
proxy -p3128
```

4. **Start 3proxy:**
```bash
3proxy /usr/local/etc/3proxy.cfg
```

5. **Make it run on startup:**
```bash
# Create LaunchAgent plist file
# Or add to Login Items in System Preferences
```

---

## **Step 3: Configure Router Port Forwarding**

You need to forward ports from your router to your home PC.

### **Find Your Local IP:**

**Windows:**
```powershell
ipconfig
# Look for "IPv4 Address" (e.g., 192.168.1.100)
```

**Linux/Mac:**
```bash
ip addr show
# or
ifconfig
# Look for inet address (e.g., 192.168.1.100)
```

### **Access Router Settings:**

1. Open browser and go to router IP:
   - Common IPs: `192.168.1.1`, `192.168.0.1`, `10.0.0.1`
   - Check router label or manual

2. Login with admin credentials

3. Find "Port Forwarding" or "Virtual Server" section

4. **Add port forwarding rules:**

| Service Name | External Port | Internal IP | Internal Port | Protocol |
|--------------|---------------|-------------|---------------|----------|
| Terabox-SOCKS | 1080 | 192.168.1.100 | 1080 | TCP |
| Terabox-HTTP | 3128 | 192.168.1.100 | 3128 | TCP |

Replace `192.168.1.100` with your PC's local IP.

5. Save settings and reboot router if needed

---

## **Step 4: Set Up Dynamic DNS (If No Static IP)**

Most home internet has dynamic IPs that change. Use Dynamic DNS to get a permanent hostname.

### **Option A: No-IP (Free)** ⭐

1. **Sign up at:** https://www.noip.com/sign-up
2. **Create hostname:** `yourname.ddns.net`
3. **Download No-IP DUC (Dynamic Update Client):**
   - Windows: https://www.noip.com/download?page=win
   - Linux: https://www.noip.com/download?page=linux
   - Mac: https://www.noip.com/download?page=mac

4. **Install and configure:**
```bash
# Linux example:
cd /usr/local/src/
wget https://www.noip.com/client/linux/noip-duc-linux.tar.gz
tar xf noip-duc-linux.tar.gz
cd noip-2.1.9-1/
make install

# Run configuration
/usr/local/bin/noip2 -C

# Start service
/usr/local/bin/noip2
```

5. **Your proxy URL will be:**
```
socks5://terabox:yourpassword@yourname.ddns.net:1080
```

### **Option B: DuckDNS (Free, Simpler)**

1. **Sign up at:** https://www.duckdns.org/
2. **Create subdomain:** `yourname.duckdns.org`
3. **Get your token**
4. **Set up auto-update:**

**Linux cron job:**
```bash
# Edit crontab
crontab -e

# Add line (replace TOKEN and SUBDOMAIN):
*/5 * * * * curl "https://www.duckdns.org/update?domains=yourname&token=YOUR_TOKEN&ip="
```

**Windows Task Scheduler:**
```powershell
# Create script: C:\duckdns\update.bat
@echo off
curl "https://www.duckdns.org/update?domains=yourname&token=YOUR_TOKEN&ip="

# Add to Task Scheduler to run every 5 minutes
```

---

## **Step 5: Test Your Proxy**

### **Test Locally First:**

**Windows:**
```powershell
# Test SOCKS5
curl --socks5 localhost:1080 --proxy-user terabox:yourpassword https://api.ipify.org
# Should show your home IP

# Test HTTP
curl --proxy http://terabox:yourpassword@localhost:3128 https://api.ipify.org
```

**Linux/Mac:**
```bash
# Test SOCKS5
curl --socks5 localhost:1080 --proxy-user terabox:yourpassword https://api.ipify.org

# Test HTTP
curl --proxy http://terabox:yourpassword@localhost:3128 https://api.ipify.org
```

### **Test Remotely:**

From another network (use your phone's data):
```bash
# Replace with your dynamic DNS hostname
curl --socks5 yourname.ddns.net:1080 --proxy-user terabox:yourpassword https://api.ipify.org
```

Should return your home IP address.

---

## **Step 6: Configure Bot to Use Your Proxy**

### **Add to Railway Environment Variables:**

**For SOCKS5 (Recommended):**
```bash
PROXY_URL=socks5://terabox:yourpassword@yourname.ddns.net:1080
```

**For HTTP:**
```bash
PROXY_URL=http://terabox:yourpassword@yourname.ddns.net:3128
```

### **Update Bot Code (Already Supported!):**

The bot already supports proxies via `PROXY_URL` environment variable. No code changes needed!

---

## **Step 7: Test Terabox Bot**

1. **Deploy to Railway** with `PROXY_URL` set
2. **Test command:**
```
/terabox https://www.terabox.app/wap/share/filelist?surl=Q7Y43GIZe28Hytdwxyup3g
```

3. **Check logs for:**
```
✅ Using residential proxy to bypass detection
✅ Got jsToken: ...
✅ File info response: errno=0  ← Should be 0, not 400210
✅ Got download link: ...
```

---

## **Troubleshooting**

### **Problem: Can't connect to proxy from Railway**

**Check:**
1. Port forwarding is configured correctly
2. Firewall allows incoming connections on ports 1080/3128
3. Dynamic DNS is updating correctly
4. Proxy server is running

**Windows Firewall:**
```powershell
# Allow ports through firewall
netsh advfirewall firewall add rule name="3proxy SOCKS" dir=in action=allow protocol=TCP localport=1080
netsh advfirewall firewall add rule name="3proxy HTTP" dir=in action=allow protocol=TCP localport=3128
```

**Linux Firewall (ufw):**
```bash
sudo ufw allow 1080/tcp
sudo ufw allow 3128/tcp
sudo ufw reload
```

### **Problem: Proxy works but still getting errno 400210**

**Possible causes:**
1. Terabox detected proxy pattern
2. Too many requests from same IP
3. Need to add cookies as well

**Solution:**
```bash
# Use both proxy AND cookies for maximum reliability
PROXY_URL=socks5://terabox:yourpassword@yourname.ddns.net:1080
TERABOX_COOKIES='[{"name":"BDUSS","value":"..."}]'
```

### **Problem: Slow performance**

**Optimize:**
1. Use SOCKS5 instead of HTTP (faster)
2. Check home internet upload speed (should be >5 Mbps)
3. Reduce bot request frequency
4. Consider upgrading home internet

---

## **Security Best Practices**

### **1. Use Strong Password:**
```bash
# Change default password in config
users terabox:CL:Use_A_Strong_Password_Here_123!
```

### **2. Restrict Access by IP (Optional):**
```ini
# In 3proxy.cfg, allow only Railway IPs
# Get Railway IPs from their docs
allow 35.190.0.0/16  # Example Railway IP range
deny *
```

### **3. Monitor Logs:**
```bash
# Linux
tail -f /var/log/3proxy.log

# Windows
# Check C:\3proxy\3proxy.log
```

### **4. Rotate Password Regularly:**
Change password every 3-6 months.

---

## **Maintenance**

### **Keep Proxy Running:**
- Ensure home PC doesn't sleep/hibernate
- Set up auto-restart on crashes
- Monitor uptime

### **Monitor Bandwidth:**
- Check if bot is using too much bandwidth
- Set up alerts if needed

### **Update Dynamic DNS:**
- Verify DNS updates are working
- Check if IP changed unexpectedly

---

## **Cost Analysis**

**Setup Cost:** $0 (free)

**Monthly Costs:**
- Electricity: ~$5-10 (running PC 24/7)
- Internet: $0 (already have)
- Dynamic DNS: $0 (free tier)

**Total:** ~$5-10/month

**vs. Paid Proxy:** $10-75/month

**Savings:** ~$5-65/month

---

## **Alternative: Use Raspberry Pi**

For lower electricity costs:

1. **Get Raspberry Pi 4** (~$50 one-time)
2. **Install Raspberry Pi OS**
3. **Follow Linux instructions above**
4. **Power consumption:** ~3W (~$0.50/month electricity)

**Total cost:** $50 one-time + $0.50/month

---

## **Summary**

✅ **Setup Steps:**
1. Install 3proxy on home PC
2. Configure port forwarding on router
3. Set up Dynamic DNS (No-IP or DuckDNS)
4. Test proxy locally and remotely
5. Add `PROXY_URL` to Railway
6. Test Terabox bot

✅ **Expected Result:**
- Bot uses your residential IP
- Bypasses Terabox server detection
- Downloads work without cookies
- Free (except electricity)

✅ **Maintenance:**
- Keep PC running 24/7
- Monitor logs occasionally
- Update Dynamic DNS if IP changes

Need help? Check logs and troubleshooting section above!
