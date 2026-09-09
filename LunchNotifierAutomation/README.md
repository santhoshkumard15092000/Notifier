# greytHR + Lunch Notifier — full automation

Logs into greytHR with a real headless browser (Playwright drives Chromium
exactly like a human clicking through the page — your credentials go
through greytHR's own login form and its own JavaScript, nothing is
reverse-engineered), clicks Sign In/Sign Out, then posts to your Google
Chat webhook.

---

## 1. Install

```bash
pip install -r requirements.txt
playwright install chromium
```

The second command downloads a bundled Chromium browser for Playwright to
drive (one-time, a few hundred MB).

---

## 2. Set your credentials

**Option A — directly in `LunchNotifier.py` (simplest, but plaintext)**

Near the top of `LunchNotifier.py`, fill in:
```python
GREYTHR_USER = "NJS0024"
GREYTHR_PASS = "your_real_password"
```

⚠️ This puts your password in plaintext inside the script file. Once
filled in:
- **Never commit this file to git**, share it, paste its contents anywhere
  (including to me in chat), or screenshot it.
- If this folder is or ever becomes a git repo, add `LunchNotifier.py` to
  `.gitignore` too, or split the credentials into a separate untracked
  file.

**Option B — `.env` file (keeps credentials out of the script)**

1. Copy `.env.example` to a new file named exactly `.env`, same folder.
2. Fill in `GREYTHR_USER=...` / `GREYTHR_PASS=...` there instead.
3. This requires `python-dotenv` (`pip install python-dotenv`) and adding
   `from dotenv import load_dotenv; load_dotenv()` back near the top of
   the script, and reading credentials via `os.environ.get(...)` instead
   of the hardcoded variables — ask if you'd like this switched back.

**Option C — Windows environment variables**

Set `GREYTHR_USER` / `GREYTHR_PASS` via System Properties → Environment
Variables (same idea as Option B, just system-wide instead of per-folder).

---

## 3. Set your webhook URL

Run the app once and enter it directly in the window:
```bash
python LunchNotifier.py
```
Paste your Google Chat webhook URL into the **"Google Chat Webhook URL:"**
box at the top and click **Save**. This writes it to
`~/.lunch_notifier/settings.json`, so it's remembered for every future run
— you only do this once.

---

## 4. Run it manually first

```bash
python greythr_lunch_automation.py going
python greythr_lunch_automation.py back
```

- `going` → clicks **Sign Out** in greytHR, then sends "Going for lunch"
- `back` → clicks **Sign In** in greytHR, then sends "Back from lunch"

The script checks which button (Sign In vs Sign Out) is actually showing
before clicking — if it doesn't match what you asked for (e.g. you're
already signed out and you run `going` again), it stops and prints an
error instead of clicking the wrong thing.

Watch the console output for errors on your first few runs before trusting
it unattended.

---

## 5. (Optional) Schedule it with Task Scheduler

1. Open **Task Scheduler** → **Create Task**.
2. **General** tab: name it "Lunch - Going". Check "Run whether user is
   logged on or not" if you want it to fire even when locked (this will
   ask you to re-enter your Windows password once, to store it securely).
3. **Triggers** tab → New → Daily, set your usual lunch time, restrict to
   weekdays if you like.
4. **Actions** tab → New:
   - Program/script: full path to your venv's `python.exe`, e.g.
     `D:\Santhosh\Repo\Lunchnotify\env\Scripts\python.exe`
   - Add arguments: `greythr_lunch_automation.py going`
   - Start in: the folder containing the script, e.g.
     `D:\Santhosh\Repo\Lunchnotify`
5. Duplicate as "Lunch - Back" with a later trigger time and argument
   `back` instead.
6. Right-click each task → **Run** to test manually before relying on the
   schedule.

⚠️ A fixed daily time will punch you in/out at that exact time regardless
of whether you're actually starting/ending lunch then — worth keeping the
manual command above as a backup for days your schedule shifts.

---

## Important things to know

- **This may go against greytHR's terms of use or your company's IT/HR
  policy**, even though it's just automating clicks on the real page.
  Attendance records tie to pay and compliance — please confirm this is
  okay with your IT/HR admin before relying on it for real, rather than
  finding out after the fact.
- **It's fragile by nature.** If greytHR adds a CAPTCHA, 2FA, or changes
  their page layout, this will start failing silently from Task
  Scheduler's perspective (you'll only notice via missing Chat messages
  or missing attendance punches) — check in periodically.
- **Credentials live in `LunchNotifier.py` itself** (or `.env`/environment
  variables if you switch approaches) — never commit these values into git,
  a screenshot, or a chat message.
- If you ever paste your real password anywhere (including to me), change
  it immediately afterward.

## Files

| File | Purpose |
|---|---|
| `LunchNotifier.py` | GUI version — window with webhook field + two buttons |
| `greythr_lunch_automation.py` | Command-line version — same logic, driven by `going`/`back` args (useful for Task Scheduler) |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template if you use the `.env` credentials option |
