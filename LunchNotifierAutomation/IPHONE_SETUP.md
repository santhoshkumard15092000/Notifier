# Trigger Lunch Notifier from your iPhone (via Tailscale)

Your PC runs the actual automation (`greythr_lunch_server.py`). Your
iPhone just sends a request to it over Tailscale — a private VPN that
connects your devices directly, so this works whether you're on the same
Wi-Fi or on mobile data anywhere.

---

## 1. Install Tailscale on your PC

1. Go to https://tailscale.com/download and download the Windows client.
2. Install it, sign in (Google/Microsoft/GitHub account — anything works).
3. It'll assign your PC a private Tailscale IP, something like `100.x.x.x`,
   and a name like `your-pc-name` you can use instead of remembering the IP.

## 2. Install Tailscale on your iPhone

1. Get "Tailscale" from the App Store.
2. Sign in with the **same account** you used on your PC.
3. Toggle the VPN connection on (it'll ask for permission once — this is
   normal for VPN apps, not a security concern here since it only routes
   traffic between your own devices).

Now your phone can reach your PC directly, from anywhere with internet.

---

## 3. Configure and run the server on your PC

1. In `greythr_lunch_server.py`, fill in:
   ```python
   GREYTHR_USER = "NJS0024"
   GREYTHR_PASS = "your_real_password"
   WEBHOOK_URL = "your_real_webhook_url"
   SHARED_SECRET = "pick_something_random_and_private"
   ```
   `SHARED_SECRET` is like a password just for this server — make it long
   and random (e.g. a passphrase you wouldn't reuse elsewhere). Anyone who
   has it can trigger your attendance and post as you, so treat it that way.

2. Install dependencies and run it:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   python greythr_lunch_server.py
   ```
   You should see Flask start up and print something like
   `Running on http://0.0.0.0:5005`. Leave this terminal open — the server
   only responds while this is running.

3. Find your PC's Tailscale name: open the Tailscale app on your PC (or
   run `tailscale status` in a terminal) — note the name, e.g.
   `santhosh-pc`.

---

## 4. Test it from your phone's browser first

Before setting up Shortcuts, confirm connectivity works at all. On your
iPhone (Tailscale connected), open Safari and go to:
```
http://santhosh-pc:5005/health
```
(replace `santhosh-pc` with your actual Tailscale device name)

You should see `{"ok":true,"status":"running"}`. If this doesn't load,
Tailscale isn't connecting properly — double check both devices are
signed into the same Tailscale account and the toggle is on.

---

## 5. Set up the iOS Shortcuts

1. Open the **Shortcuts** app → **+** to create a new shortcut.
2. Add action **"Get Contents of URL"**.
3. URL:
   ```
   http://santhosh-pc:5005/going?secret=pick_something_random_and_private
   ```
   (use your actual Tailscale name and your actual `SHARED_SECRET` value)
4. Method: GET (default — no need to change).
5. Rename the shortcut "Going for Lunch", pick an icon, tap Done.
6. In the shortcut's settings, **Add to Home Screen**, and turn off
   "Ask Before Running" so it fires with a single tap.
7. Repeat for a second shortcut "Back from Lunch", using `/back` instead
   of `/going` in the URL.

Tapping either home screen icon now: wakes your PC's browser
automation → punches greytHR → posts to Chat — all triggered remotely
from your phone.

---

## 6. (Optional) Auto-start the server so you don't forget to leave it running

Use Windows Task Scheduler (same idea as before) with a trigger of **"At
log on"** instead of a daily time, running:
```
python.exe  greythr_lunch_server.py
```
so it's always running in the background whenever your PC is on.

---

## Important things to know

- **Your PC must be powered on and connected to the internet** for this to
  work at all — if it's asleep, off, or offline, the phone request will
  just fail (timeout in Safari / an error in Shortcuts).
- **Never expose this server outside Tailscale** — e.g. don't set up
  router port-forwarding for it. Tailscale keeps it reachable only by your
  own signed-in devices; the public internet should never be able to
  reach `/going` or `/back`, secret or not.
- **The `SHARED_SECRET` is your only real protection** if anyone else
  ever joins your Tailscale network (e.g. a shared/team Tailscale
  account) — keep it private, and pick something you're not reusing
  elsewhere.
- Same caveats as before still apply: this may go against greytHR's terms
  of use or your company's IT policy, and it's fragile if greytHR changes
  their page — worth periodic sanity checks.

## Files

| File | Purpose |
|---|---|
| `greythr_lunch_server.py` | The local server your PC runs |
| `requirements.txt` | Now includes `flask` too |
