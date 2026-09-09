import logging
import logging.handlers
import os
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

load_dotenv()

# ---------------------------------------------------------------------------
# Logging -- writes to poller.log
# ---------------------------------------------------------------------------
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "poller.log")
handler = logging.handlers.RotatingFileHandler(
    LOG_PATH, maxBytes=2_000_000, backupCount=3
)
handler.setFormatter(logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
))
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log.addHandler(handler)

# ---------------------------------------------------------------------------
# HTTP session with automatic retries
# ---------------------------------------------------------------------------
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"],
)
session.mount("https://", HTTPAdapter(max_retries=retry_strategy))

# ---------------------------------------------------------------------------
# Config -- read from .env
# ---------------------------------------------------------------------------

GREYTHR_USER = os.environ.get("GREYTHR_USER")
GREYTHR_PASS = os.environ.get("GREYTHR_PASS")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
SHARED_SECRET = os.environ.get("SHARED_SECRET")
APPS_SCRIPT_URL = os.environ.get("APPS_SCRIPT_URL")

REQUIRED_VARS = {
    "GREYTHR_USER": GREYTHR_USER,
    "GREYTHR_PASS": GREYTHR_PASS,
    "WEBHOOK_URL": WEBHOOK_URL,
    "SHARED_SECRET": SHARED_SECRET,
    "APPS_SCRIPT_URL": APPS_SCRIPT_URL,
}
missing = [name for name, value in REQUIRED_VARS.items() if not value]
if missing:
    log.error(f"Missing required .env values: {', '.join(missing)}. "
              f"Copy .env.example to .env in this same folder and fill them in.")
    sys.exit(1)

POLL_INTERVAL_SECONDS = 10

GREYTHR_BASE_URL = "https://n-j-s-infotech.greythr.com"

ACTIONS = {
    "going": {"expected_button": "Sign Out", "message": "I’m going for Lunch Break."},
    "back": {"expected_button": "Sign In", "message": "I came back from my Lunch Break."},
}


# ---------------------------------------------------------------------------
# Mailbox check-in
# ---------------------------------------------------------------------------

def check_pending_action():
    response = session.get(
        APPS_SCRIPT_URL, params={"mode": "poll", "secret": SHARED_SECRET}, timeout=15
    )
    response.raise_for_status()
    try:
        return response.json().get("action")
    except ValueError:
        log.error(
            f"Non-JSON response. Status: {response.status_code}, "
            f"URL: {response.url}, Body: {response.text[:300]!r}"
        )
        raise


def clear_pending_action() -> None:
    session.get(
        APPS_SCRIPT_URL, params={"mode": "clear", "secret": SHARED_SECRET}, timeout=15
    )



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
    response = session.post(WEBHOOK_URL, json={"text": text}, timeout=10)
    response.raise_for_status()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def _log_poll_error(exc: Exception, context: str) -> None:
    if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        log.warning(f"{context}: {exc.__class__.__name__} (will retry next cycle)")
    else:
        log.error(f"{context}: {exc}", exc_info=True)


def main() -> None:
    log.info(f"Starting up. Polling every {POLL_INTERVAL_SECONDS}s.")
    while True:
        try:
            action_key = check_pending_action()
            if action_key in ACTIONS:
                action = ACTIONS[action_key]
                log.info(f"Request received: {action_key}")
                try:
                    punch_greythr(action["expected_button"])
                    send_chat_message(action["message"])
                    log.info(f"Done: {action['message']}")
                except Exception as exc:
                    log.error(f"Error handling '{action_key}': {exc}", exc_info=True)
                finally:
                    try:
                        clear_pending_action()
                    except Exception as exc:
                        _log_poll_error(exc, "Error clearing pending action")
        except Exception as exc:
            _log_poll_error(exc, "Error checking for pending action")

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()