"""
greytHR + Lunch Notifier automation
------------------------------------
Logs into greytHR through a real (headless) browser, clicks the
Sign In / Sign Out attendance button, then posts a matching message
to your Google Chat webhook.

This drives the ACTUAL page like a human would (typing into the real
fields, clicking the real buttons) -- it does not touch or replay
greytHR's internal encrypted requests. Their own JavaScript handles
login exactly as it does when you do this by hand.

SECURITY: your greytHR username/password are read from environment
variables, never hardcoded here.

Setup:
    pip install playwright requests
    playwright install chromium

Environment variables required (set these in Windows System Properties
-> Environment Variables, or Task Scheduler action environment):
    GREYTHR_USER   - your greytHR Login ID (e.g. NJS0024)
    GREYTHR_PASS   - your greytHR password

Usage:
    python greythr_lunch_automation.py going   -> Sign Out + "Going for lunch"
    python greythr_lunch_automation.py back    -> Sign In  + "Back from lunch"
"""

import os
import sys

import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

# Loads GREYTHR_USER / GREYTHR_PASS / WEBHOOK_URL from a .env file sitting
# next to this script.
load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GREYTHR_BASE_URL = "https://n-j-s-infotech.greythr.com"

ACTIONS = {
    "going": {"expected_button": "Sign Out", "message": "Going for lunch"},
    "back": {"expected_button": "Sign In", "message": "Back from lunch"},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def send_chat_message(webhook_url: str, text: str) -> None:
    response = requests.post(webhook_url, json={"text": text}, timeout=10)
    response.raise_for_status()


def punch_greythr(expected_button: str) -> None:
    """
    Logs into greytHR and clicks the attendance button, but ONLY if the
    button currently showing matches `expected_button`. This prevents
    accidentally toggling the wrong direction (e.g. clicking "Sign Out"
    when you're already signed out).
    """
    username = os.environ.get("GREYTHR_USER")
    password = os.environ.get("GREYTHR_PASS")
    if not username or not password:
        raise RuntimeError(
            "GREYTHR_USER / GREYTHR_PASS are not set in your .env file."
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, channel="chrome")
        page = browser.new_page()

        try:
            # Navigating to the base URL lets greytHR's own app generate a
            # fresh login_challenge and redirect to the login page itself --
            # we never construct or reuse a login URL ourselves.
            page.goto(GREYTHR_BASE_URL, wait_until="networkidle")

            # If we're not already logged in (cookie expired etc.), the
            # login form will be present. If a previous session is still
            # valid, this step is skipped.
            username_field = page.locator("#username")
            try:
                username_field.wait_for(state="visible", timeout=8000)
                username_field.fill(username)
                page.locator("#password").fill(password)
                page.get_by_role("button", name="Login").click()
            except PWTimeoutError:
                pass  # Already logged in from a previous session.

            # Wait for the attendance button (either state) to appear,
            # confirming we're on the dashboard.
            page.wait_for_selector(
                "gt-button:has-text('Sign In'), gt-button:has-text('Sign Out')",
                timeout=20000,
            )

            button = page.get_by_role("button", name=expected_button)
            if button.count() == 0:
                raise RuntimeError(
                    f'Expected a "{expected_button}" button but did not find one -- '
                    f"your attendance status may not match what this script expected. "
                    f"Nothing was clicked, to avoid toggling the wrong direction."
                )

            button.first.click()
            # Give the click a moment to register with the backend before
            # we close the browser.
            page.wait_for_timeout(3000)

        finally:
            browser.close()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ACTIONS:
        print("Usage: python greythr_lunch_automation.py [going|back]")
        sys.exit(1)

    action = ACTIONS[sys.argv[1]]

    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        print("WEBHOOK_URL is not set in your .env file. Copy .env.example to .env and fill it in.")
        sys.exit(1)

    print(f"Logging into greytHR and clicking '{action['expected_button']}'...")
    punch_greythr(action["expected_button"])
    print("greytHR punch done. Sending Chat message...")

    send_chat_message(webhook_url, action["message"])
    print(f"Sent: {action['message']}")


if __name__ == "__main__":
    main()
