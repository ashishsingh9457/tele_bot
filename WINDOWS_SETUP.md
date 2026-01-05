# Running Terabox Bot on Windows PC

This guide will help you run the Telegram bot directly on your Windows PC, using your home residential IP to avoid Terabox detection issues.

---

## **Prerequisites**

- Windows 10 or 11
- Internet connection
- Telegram Bot Token (from @BotFather)

---

## **Step 1: Install Python**

1. **Download Python 3.11:**
   - Go to: https://www.python.org/downloads/
   - Download Python 3.11.x (latest stable version)

2. **Install Python:**
   - Run the installer
   - ✅ **IMPORTANT:** Check "Add Python to PATH"
   - Click "Install Now"

3. **Verify installation:**
   ```cmd
   python --version
   ```
   Should show: `Python 3.11.x`

---

## **Step 2: Download Bot Code**

1. **Install Git (if not installed):**
   - Download from: https://git-scm.com/download/win
   - Install with default settings

2. **Clone the repository:**
   ```cmd
   cd C:\Users\YourUsername\Desktop
   git clone https://github.com/ashishsingh9457/tele_bot.git
   cd tele_bot
   ```

   Or download ZIP:
   - Go to: https://github.com/ashishsingh9457/tele_bot
   - Click "Code" → "Download ZIP"
   - Extract to Desktop

---

## **Step 3: Install Dependencies**

Open Command Prompt in the bot folder:

```cmd
cd C:\Users\YourUsername\Desktop\tele_bot
pip install -r requirements.txt
```

This will install:
- python-telegram-bot
- httpx
- requests
- beautifulsoup4
- python-dotenv

---

## **Step 4: Configure Bot Token**

1. **Create `.env` file:**
   - Open Notepad
   - Copy this content:
   ```
   TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
   ```
   - Replace `YOUR_BOT_TOKEN_HERE` with your actual bot token from @BotFather
   - Save as `.env` (NOT `.env.txt`) in the `tele_bot` folder

2. **Verify `.env` file:**
   ```cmd
   type .env
   ```
   Should show your token

---

## **Step 5: Run the Bot**

```cmd
python bot.py
```

You should see:
```
Bot is starting...
```

**The bot is now running!** 🎉

---

## **Step 6: Test the Bot**

1. Open Telegram
2. Go to your bot
3. Send: `/start`
4. Test Terabox: `/terabox https://www.terabox.app/wap/share/filelist?surl=xxxxx`

---

## **Running Bot 24/7**

### **Option A: Keep Command Prompt Open**
- Just leave the Command Prompt window open
- Bot runs as long as PC is on

### **Option B: Run as Background Service (Advanced)**

1. **Install NSSM (Non-Sucking Service Manager):**
   - Download from: https://nssm.cc/download
   - Extract `nssm.exe` to `C:\nssm\`

2. **Create Windows Service:**
   ```cmd
   cd C:\nssm
   nssm install TeraboxBot "C:\Users\YourUsername\AppData\Local\Programs\Python\Python311\python.exe" "C:\Users\YourUsername\Desktop\tele_bot\bot.py"
   ```

3. **Start the service:**
   ```cmd
   nssm start TeraboxBot
   ```

4. **Bot now runs automatically on Windows startup!**

To stop:
```cmd
nssm stop TeraboxBot
```

To remove:
```cmd
nssm remove TeraboxBot
```

---

## **Updating the Bot**

When there are updates:

```cmd
cd C:\Users\YourUsername\Desktop\tele_bot
git pull
pip install -r requirements.txt --upgrade
python bot.py
```

---

## **Troubleshooting**

### **"Python not found"**
- Reinstall Python with "Add to PATH" checked
- Or add manually: System Properties → Environment Variables → Path → Add Python folder

### **"Module not found"**
```cmd
pip install -r requirements.txt --force-reinstall
```

### **Bot not responding**
- Check if bot is running (Command Prompt window open)
- Verify `.env` file has correct token
- Check internet connection

### **Terabox download fails**
- Your home IP should work fine (residential IP)
- If still fails, the link might be invalid or password protected

### **"Address already in use"**
- Another instance is running
- Close other Command Prompt windows
- Or restart PC

---

## **Firewall Settings**

If Windows Firewall blocks the bot:

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Click "Change settings"
4. Click "Allow another app"
5. Browse to Python executable
6. Check both Private and Public
7. Click OK

---

## **Performance Tips**

- **Keep PC awake:** Settings → Power → Never sleep
- **Stable internet:** Use wired connection if possible
- **Close unnecessary apps:** Free up RAM
- **Windows updates:** Keep Windows updated

---

## **Advantages of Running on Home PC**

✅ **Residential IP** - No Terabox detection issues
✅ **No server costs** - Completely free
✅ **Full control** - Can debug easily
✅ **Fast** - Direct connection, no proxy needed
✅ **Reliable** - Works as long as PC is on

---

## **Disadvantages**

❌ **PC must stay on** - Bot stops if PC shuts down
❌ **Uses your internet** - Bandwidth from your home connection
❌ **Power costs** - PC running 24/7 (~$5-10/month electricity)
❌ **No redundancy** - If internet goes down, bot goes down

---

## **Remote Access (Optional)**

To control your PC remotely:

### **Option 1: Windows Remote Desktop**
1. Enable Remote Desktop in Windows settings
2. Use Microsoft Remote Desktop app on phone/laptop
3. Connect using your home IP address

### **Option 2: TeamViewer**
1. Download: https://www.teamviewer.com/
2. Install on home PC
3. Use TeamViewer app to access from anywhere

### **Option 3: Chrome Remote Desktop**
1. Go to: https://remotedesktop.google.com/
2. Set up remote access
3. Access from any browser

---

## **Security Recommendations**

🔒 **Keep .env file private** - Never share your bot token
🔒 **Use strong Windows password** - Protect your PC
🔒 **Enable Windows Firewall** - Block unauthorized access
🔒 **Regular updates** - Keep Windows and Python updated
🔒 **Antivirus** - Use Windows Defender or similar

---

## **Monitoring Bot Status**

Create a simple batch file to restart bot if it crashes:

**restart_bot.bat:**
```batch
@echo off
:start
echo Starting Terabox Bot...
cd C:\Users\YourUsername\Desktop\tele_bot
python bot.py
echo Bot stopped. Restarting in 5 seconds...
timeout /t 5
goto start
```

Double-click this file to run the bot with auto-restart.

---

## **Getting Help**

If you encounter issues:

1. Check the logs in Command Prompt
2. Verify all steps were followed correctly
3. Test with a simple command like `/start`
4. Check GitHub issues: https://github.com/ashishsingh9457/tele_bot/issues

---

## **Next Steps**

Once the bot is running:

1. Test with various Terabox links
2. Share bot with friends (optional)
3. Monitor performance
4. Keep bot updated with `git pull`

**Enjoy your Terabox downloader bot running on your home PC!** 🚀
