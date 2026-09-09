
import os
from datetime import datetime

import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# Loads config from a .env file sitting next to this script.
load_dotenv()

# ---------------------------------------------------------------------------
# Config -- all values come from .env (see .env.example)
# ---------------------------------------------------------------------------

GREYTHR_USER = os.environ.get("GREYTHR_USER", "")
GREYTHR_PASS = os.environ.get("GREYTHR_PASS", "")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")

# A password only your iPhone Shortcut knows. Pick your own random string --
# anyone who has this can trigger your attendance, so keep it private, the
# same way you'd treat a password.
SHARED_SECRET = os.environ.get("SHARED_SECRET", "")

GREYTHR_BASE_URL = "https://n-j-s-infotech.greythr.com"

ACTIONS = {
    "going": {"expected_button": "Sign Out", "message": "Going for lunch"},
    "back": {"expected_button": "Sign In", "message": "Back from lunch"},
}

app = Flask(__name__)


# ---------------------------------------------------------------------------
# Core automation (same logic as the desktop app)
# ---------------------------------------------------------------------------

def punch_greythr(expected_button: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()
        try:
            page.goto(GREYTHR_BASE_URL, wait_until="networkidle")

            username_field = page.locator("#username")
            try:
                username_field.wait_for(state="visible", timeout=8000)
                username_field.fill(GREYTHR_USER)
                page.locator("#password").fill(GREYTHR_PASS)
                page.get_by_role("button", name="Login").click()
            except PWTimeoutError:
                pass  # Already logged in.

            page.wait_for_selector(
                "gt-button:has-text('Sign In'), gt-button:has-text('Sign Out')",
                timeout=20000,
            )

            button = page.get_by_role("button", name=expected_button)
            if button.count() == 0:
                raise RuntimeError(
                    f'Expected a "{expected_button}" button but did not find one -- '
                    f"attendance status may already be in that state."
                )

            button.first.click()
            page.wait_for_timeout(3000)
        finally:
            browser.close()


def send_chat_message(text: str) -> None:
    response = requests.post(WEBHOOK_URL, json={"text": text}, timeout=10)
    response.raise_for_status()


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

def _check_secret() -> bool:
    provided = request.args.get("secret") or request.headers.get("X-Auth-Token")
    return provided == SHARED_SECRET


def _handle_action(action_key: str):
    if not _check_secret():
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    action = ACTIONS[action_key]
    try:
        punch_greythr(action["expected_button"])
        send_chat_message(action["message"])
        return jsonify({
            "ok": True,
            "message": action["message"],
            "time": datetime.now().strftime("%I:%M %p"),
        })
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/going", methods=["GET"])
def going():
    return _handle_action("going")


@app.route("/back", methods=["GET"])
def back():
    return _handle_action("back")


@app.route("/health", methods=["GET"])
def health():
    # No secret required -- just confirms the server is reachable at all,
    # handy for testing the Tailscale connection from your phone's browser.
    return jsonify({"ok": True, "status": "running"})


if __name__ == "__main__":
    missing = [
        name for name, value in {
            "GREYTHR_USER": GREYTHR_USER,
            "GREYTHR_PASS": GREYTHR_PASS,
            "WEBHOOK_URL": WEBHOOK_URL,
            "SHARED_SECRET": SHARED_SECRET,
        }.items() if not value
    ]
    if missing:
        print(f"Missing required .env values: {', '.join(missing)}")
        print("Copy .env.example to .env in this same folder and fill them in.")
        raise SystemExit(1)
    app.run(host="0.0.0.0", port=5005)
