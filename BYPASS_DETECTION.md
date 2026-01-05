# Bypassing Terabox Server Detection

Terabox blocks automated requests from server IPs with `errno: 400210 - need verify_v2`. Here are methods to bypass this detection:

---

## **Method 1: Residential Proxy (Recommended)** ⭐

### What it does:
Routes your requests through real residential IP addresses instead of datacenter IPs.

### How to set up:

1. **Get a residential proxy service:**
   - [Bright Data](https://brightdata.com/) - $500/month (premium)
   - [Smartproxy](https://smartproxy.com/) - $75/month
   - [Oxylabs](https://oxylabs.io/) - $300/month
   - [ProxyMesh](https://proxymesh.com/) - $10/month (budget option)

2. **Add proxy to Railway:**
   ```bash
   PROXY_URL=http://username:password@proxy-host:port
   ```

3. **The bot will automatically use it** - no code changes needed!

### Pros:
- ✅ Most reliable method
- ✅ Mimics real user traffic
- ✅ No authentication needed
- ✅ Works for all users

### Cons:
- ❌ Costs money ($10-500/month)
- ❌ Adds latency (1-3 seconds)

---

## **Method 2: Authenticated Cookies (Free Alternative)** ⭐

### What it does:
Uses your Terabox account credentials to bypass verification.

### How to set up:
See `TERABOX_SETUP.md` for detailed instructions.

### Pros:
- ✅ Free (uses your Terabox account)
- ✅ Reliable
- ✅ Fast

### Cons:
- ❌ Requires manual cookie export
- ❌ Cookies expire every 30-90 days
- ❌ Risk of account ban if overused

---

## **Method 3: Browser Fingerprinting (Advanced)**

### What it does:
Mimics a real browser's fingerprint to avoid detection.

### Implementation:

```python
# Install: pip install playwright-stealth
from playwright_stealth import stealth_async

async def get_with_stealth():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            permissions=['geolocation'],
        )
        page = await context.new_page()
        await stealth_async(page)  # Apply stealth techniques
        # ... make requests
```

### Pros:
- ✅ No ongoing costs
- ✅ Can bypass some detection

### Cons:
- ❌ Still uses datacenter IP (may not work)
- ❌ Heavy resource usage
- ❌ Slower (15-30 seconds)

---

## **Method 4: VPN/VPS in Residential Network**

### What it does:
Run the bot on a VPS with a residential IP address.

### How to set up:

1. **Get a residential VPS:**
   - Rent a VPS from a residential ISP
   - Use a home server with dynamic DNS
   - Use cloud providers with residential IPs (rare)

2. **Deploy bot there instead of Railway**

### Pros:
- ✅ Permanent residential IP
- ✅ No per-request costs
- ✅ Fast

### Cons:
- ❌ Hard to find residential VPS providers
- ❌ More expensive than datacenter VPS
- ❌ Complex setup

---

## **Method 5: Hybrid Approach (Best Balance)**

Combine multiple methods for maximum reliability:

```python
# Priority order:
1. Try with residential proxy (if configured)
2. Fall back to authenticated cookies (if configured)
3. Try browser automation with stealth
4. Show error message
```

This is **already implemented** in the current code!

---

## **Current Implementation**

The bot currently supports:

### ✅ **Residential Proxy Support**
Set `PROXY_URL` environment variable:
```bash
PROXY_URL=http://user:pass@proxy-host:port
```

### ✅ **Cookie Authentication**
Set `TERABOX_COOKIES` environment variable (see TERABOX_SETUP.md)

### ✅ **Enhanced Browser Headers**
Mimics real Chrome browser with proper headers

---

## **Recommended Setup**

### **For Personal Use (Free):**
```bash
# Use authenticated cookies
TERABOX_COOKIES='[{"name":"BDUSS","value":"..."}]'
```

### **For Public Bot (Paid):**
```bash
# Use residential proxy + cookies as fallback
PROXY_URL=http://user:pass@smartproxy.com:10000
TERABOX_COOKIES='[{"name":"BDUSS","value":"..."}]'  # Optional fallback
```

---

## **Testing Detection Bypass**

To test if your setup bypasses detection:

```bash
# Test with terabox command
/terabox https://www.terabox.app/wap/share/filelist?surl=Q7Y43GIZe28Hytdwxyup3g
```

**Success indicators:**
```
✅ Got jsToken: ...
✅ Got browserid: ...
✅ File info response: errno=0  ← Should be 0, not 400210
✅ Got download link: ...
```

**Failure indicators:**
```
❌ File info response: errno=400210
❌ API error: 400210 - need verify_v2
```

---

## **Cost Comparison**

| Method | Setup Cost | Monthly Cost | Reliability |
|--------|-----------|--------------|-------------|
| Cookies (Free) | Free | Free | Medium (expires) |
| ProxyMesh | Free | $10 | High |
| Smartproxy | Free | $75 | Very High |
| Bright Data | Free | $500 | Excellent |
| Residential VPS | $50-200 | $20-100 | High |

---

## **Why Terabox Blocks Server IPs**

Terabox detects:
1. **Datacenter IP ranges** (AWS, GCP, Railway, etc.)
2. **Missing browser fingerprints** (canvas, WebGL, fonts)
3. **Suspicious request patterns** (too fast, no cookies)
4. **Missing TLS fingerprints** (server TLS vs browser TLS)

**Residential proxies solve all of these** by routing through real user devices.

---

## **Legal & Ethical Considerations**

⚠️ **Important:**
- Using proxies to bypass restrictions may violate Terabox ToS
- Use authenticated cookies from your own account only
- Don't abuse the service with excessive requests
- Consider rate limiting your bot (1 request per 5 seconds)

---

## **Support**

If you're still getting verification errors after setup:
1. Check Railway logs for error details
2. Verify proxy/cookies are configured correctly
3. Test proxy connection independently
4. Try a different proxy provider

For questions, open an issue on GitHub.
