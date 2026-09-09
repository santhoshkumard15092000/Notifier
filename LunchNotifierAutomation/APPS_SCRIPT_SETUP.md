# Trigger Lunch Notifier from your iPhone — nothing installed anywhere

This is for when you can't install new software on either your PC or your
iPhone (common on managed/corporate machines). Nothing gets installed:

- **PC side**: just runs `greythr_lunch_poller.py` with Python you already
  have — no new `.exe`, no agent, no listening port.
- **Phone side**: just Safari/Shortcuts hitting a normal Google URL — no
  app, no VPN.
- **The "server" is Google's own infrastructure** (Apps Script), which you
  set up entirely through a website — script.google.com — in your browser.

## How it works

Your iPhone doesn't talk to your PC directly at all. Instead:

1. You tap a Shortcut → it tells a small Google Apps Script "drop off
   your request here."
2. Your PC, running `greythr_lunch_poller.py`, checks in with that same
   Apps Script every 10 seconds asking "anything for me?"
3. When it finds your request, it does the greytHR + Chat automation,
   then tells Apps Script "handled, clear it."

So there's a few seconds of delay (up to `POLL_INTERVAL_SECONDS`) between
tapping the Shortcut and it actually happening — a reasonable trade-off
for needing zero installs.

---

## 1. Deploy the Apps Script (all in-browser, nothing installed)

1. Go to https://script.google.com and sign in with your Google account.
2. Click **New project**.
3. Delete the placeholder code in the editor, and paste in the entire
   contents of `AppsScript_Code.gs` (included alongside this file).
4. Set the secret via **Script Properties** (not the code itself — Apps
   Script can't read your local `.env` file since it runs on Google's
   servers, not your PC):
   - Click the gear icon (**Project Settings**) in the left sidebar.
   - Scroll to **Script Properties** → **Add script property**.
   - Property: `SHARED_SECRET`
   - Value: the same random string you'll put in your `.env` file's
     `SHARED_SECRET` — pick one now if you haven't yet.
   - Click **Save script properties**.
5. Click **Deploy** (top right) → **New deployment**.
6. Click the gear icon next to "Select type" → choose **Web app**.
7. Fill in:
   - Description: anything, e.g. "Lunch Notifier"
   - Execute as: **Me**
   - Who has access: **Anyone**
     (this sounds alarming, but access to the *actions* is still gated by
     your `SHARED_SECRET` check inside the script — "Anyone" here just
     means Google won't additionally require the *caller* to be signed
     into a Google account, which your iPhone Shortcut isn't)
8. Click **Deploy**. The first time, Google will ask you to authorize the
   script — click through the "unverified app" warning (it's your own
   script, this is expected for personal Apps Script projects) and
   approve.
9. Copy the **Web app URL** shown — it looks like:
   ```
   https://script.google.com/macros/s/AKfycb.../exec
   ```
   You'll need this in both the Python script and the Shortcuts.

---

## 2. Configure and run the poller on your PC

1. Copy `.env.example` to a new file named exactly `.env`, in the same
   folder as the scripts, and fill in your real values:
   ```
   GREYTHR_USER=NJS0024
   GREYTHR_PASS=your_real_password
   WEBHOOK_URL=your_real_webhook_url
   SHARED_SECRET=the_same_random_value_from_step_1
   APPS_SCRIPT_URL=https://script.google.com/macros/s/AKfycb.../exec
   ```
2. Everything else needed (`playwright`, `requests`) should already be
   installed from earlier — if not:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Run it:
   ```bash
   python greythr_lunch_poller.py
   ```
   You should see `Polling every 10s. Press Ctrl+C to stop.` — leave this
   terminal open; it's doing the checking-in in the background.

---

## 3. Test the mailbox directly first

Before setting up Shortcuts, confirm the Apps Script works. From your
iPhone's Safari (or even just your PC's browser), visit:
```
https://script.google.com/macros/s/AKfycb.../exec?mode=set&action=going&secret=YOUR_SECRET
```
You should see `{"ok":true,"queued":"going"}`. Within ~10 seconds, your
PC's terminal (running the poller) should print
`Request received: going` and start the automation. If that happens, the
whole pipeline works end to end.

---

## 4. Set up the iOS Shortcuts

1. Shortcuts app → **+** → Add Action → **"Get Contents of URL"**.
2. URL:
   ```
   https://script.google.com/macros/s/AKfycb.../exec?mode=set&action=going&secret=YOUR_SECRET
   ```
3. Name it "Going for Lunch" → **Add to Home Screen** → turn off "Ask
   Before Running".
4. Repeat for "Back from Lunch", using `action=back` instead.

Tapping either icon now works from anywhere with internet — no VPN, no
app, no direct connection to your PC at all.

---

## Important things to know

- **Your PC must be on, online, and the poller running** for anything to
  actually happen — same requirement every other version had. If it's
  off, your phone's request just sits in the Apps Script mailbox until
  the PC comes back and checks in.
- **There's a delay** of up to `POLL_INTERVAL_SECONDS` (10s by default) —
  lower it if you want faster response, at the cost of slightly more
  background traffic.
- **`SHARED_SECRET` is doing all the security work** here too, same as
  the other remote versions — anyone with your Apps Script URL and secret
  could queue actions. Keep both private.
- **Google Apps Script free quotas** are generous for this kind of light,
  personal use (well under daily execution limits), so cost isn't a
  concern.
- Same greytHR/company-policy caveats from before still apply.

## Files

| File | Purpose |
|---|---|
| `AppsScript_Code.gs` | Paste into script.google.com — the "mailbox" |
| `greythr_lunch_poller.py` | Runs on your PC, checks in periodically |
