# Terabox Authentication Setup

Terabox requires authentication to download files. This guide explains how to set up authentication for the bot.

## Option 1: Using Cookies (Recommended)

### Step 1: Login to Terabox
1. Open your browser and go to https://www.terabox.com
2. Login with your Terabox account (free account works)

### Step 2: Export Cookies
Using a browser extension like **EditThisCookie** or **Cookie-Editor**:

1. Install the extension:
   - Chrome: [EditThisCookie](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg)
   - Firefox: [Cookie-Editor](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/)

2. After logging in to Terabox, click the extension icon
3. Export cookies as JSON
4. Copy the entire JSON array

### Step 3: Set Environment Variable

#### For Railway Deployment:
1. Go to your Railway project
2. Click on "Variables" tab
3. Add a new variable:
   - **Name**: `TERABOX_COOKIES`
   - **Value**: Paste the entire JSON array (e.g., `[{"name":"BDUSS","value":"...","domain":".terabox.com",...},...]`)

#### For Local Development:
Add to your `.env` file:
```bash
TERABOX_COOKIES='[{"name":"BDUSS","value":"...","domain":".terabox.com",...},...]'
```

### Important Cookies
The most important cookies are:
- `BDUSS` - Main authentication token
- `STOKEN` - Session token
- `ndus` - User session

Make sure these are included in your exported cookies.

---

## Option 2: External APIs (Fallback)

The bot automatically tries external Terabox downloader APIs as a fallback. These may work for some files but are unreliable.

---

## How It Works

The bot uses this priority order:

1. **Try to intercept video streaming URLs** (if page loads video preview)
2. **Try external APIs** (unreliable, may fail)
3. **Use authenticated session** (if cookies are provided) ✅ Most reliable
4. **Fail gracefully** (if nothing works)

---

## Cookie Expiration

Terabox cookies typically expire after 30-90 days. When downloads stop working:

1. Login to Terabox again in your browser
2. Export fresh cookies
3. Update the `TERABOX_COOKIES` environment variable

---

## Security Notes

- **Never share your cookies publicly** - they give full access to your Terabox account
- Use a dedicated Terabox account for the bot (not your personal account)
- Store cookies as environment variables (never commit to git)
- The bot only uses cookies for downloading shared files, not accessing private files

---

## Troubleshooting

### "No download link available"
- Make sure cookies are set correctly
- Check if cookies have expired (re-export them)
- Verify the Terabox URL is a valid share link

### "Authentication may be required"
- The `TERABOX_COOKIES` environment variable is not set
- Cookies are invalid or expired
- Cookie format is incorrect (must be valid JSON array)

### Testing Cookies
Check Railway logs for:
```
✅ Loaded Terabox authentication cookies
✅ Trying authenticated download API with cookies...
✅ Got authenticated download link: https://...
```

If you see these logs, authentication is working correctly.
