# Trigger Lunch Notifier from your iPhone — no app required (via ngrok)

This is an alternative to the Tailscale setup: nothing installs on your
iPhone at all — just Safari/Shortcuts hitting a normal public HTTPS URL.
Only your PC needs one extra piece of software (ngrok).

⚠️ Trade-off vs Tailscale: this exposes your server's URL to the public
internet (though only reachable if someone knows/guesses both the URL AND
your `SHARED_SECRET`). Tailscale keeps it private to your own devices only.
Pick whichever trade-off you're more comfortable with.

---

## 1. Sign up for ngrok (free)

1. Go to https://ngrok.com and sign up (free account, no credit card needed
   for this).
2. After signing in, go to your dashboard → copy your **Authtoken**
   (Setup & Installation page shows it).

## 2. Install ngrok on your PC

1. Download the Windows build from https://ngrok.com/download
2. Extract it somewhere, e.g. `C:\ngrok\ngrok.exe`
3. Open a terminal in that folder and run (paste your real token):
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN_HERE
   ```

## 3. Claim your free static domain

1. In the ngrok dashboard, go to **Domains** → create/claim your free
   static domain. You'll get something like:
   ```
   your-name-123.ngrok-free.app
   ```
   This one is yours permanently on the free plan — it won't change
   between restarts, unlike ngrok's old random-URL behavior.

## 4. Run the server and the tunnel together

In one terminal, start your existing server:
```bash
python greythr_lunch_server.py
```

In a second terminal, point ngrok at it using your claimed domain:
```bash
ngrok http --domain=your-name-123.ngrok-free.app 5005
```

Leave both terminals open. Your server is now reachable at:
```
https://your-name-123.ngrok-free.app/going?secret=...
https://your-name-123.ngrok-free.app/back?secret=...
```
from anywhere with internet — no VPN app needed on your phone.

---

## 5. Test from your phone's browser first

Open Safari on your iPhone (regular mobile data is fine, no special
network needed) and go to:
```
https://your-name-123.ngrok-free.app/health
```
You'll likely hit ngrok's free-tier **interstitial warning page** first
("this site is served through ngrok") — tap **Visit Site** to continue.
You should then see `{"ok":true,"status":"running"}`.

---

## 6. Set up the iOS Shortcuts (important extra header)

Because ngrok's free tier shows that interstitial page to anything that
looks like a browser, and Shortcuts' requests can get caught by it too,
add one extra header to skip it automatically:

1. Shortcuts app → **+** → Add Action → **"Get Contents of URL"**.
2. URL:
   ```
   https://your-name-123.ngrok-free.app/going?secret=pick_something_random_and_private
   ```
3. Tap **"Show More"** → **Headers** → add:
   - Key: `ngrok-skip-browser-warning`
   - Value: `true`

   This tells ngrok to skip the interstitial for this request, so it goes
   straight to your server instead of getting stuck on a warning page.
4. Name it "Going for Lunch", **Add to Home Screen**, turn off "Ask
   Before Running".
5. Repeat for "Back from Lunch" using `/back` instead of `/going`.

---

## 7. (Optional) Auto-start both on PC login

Same idea as before with Task Scheduler — two "At log on" triggers, one
running `python greythr_lunch_server.py`, another running
`ngrok http --domain=your-name-123.ngrok-free.app 5005`, so both are
always up whenever your PC is on.

---

## Important things to know

- **Your PC must be on, online, and both processes running** for this to
  work — same requirement as the Tailscale version.
- **This is now reachable from the public internet.** Your `SHARED_SECRET`
  in `greythr_lunch_server.py` is the only thing stopping a stranger who
  finds your ngrok URL from triggering your attendance and posting
  messages as you. Make it long, random, and don't reuse a password from
  anywhere else.
- **Free ngrok domains can be reassigned to someone else if unused for a
  long time** — check ngrok's current free-plan terms if you stop using
  this for a while and come back later.
- Same greytHR/company-policy caveats from before still apply.
