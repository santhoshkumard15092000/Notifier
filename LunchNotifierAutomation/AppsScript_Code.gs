// Deploy this at script.google.com -- see APPS_SCRIPT_SETUP.md for exact
// steps. This needs no installation anywhere; it runs on Google's servers.
//
// It acts as a simple "mailbox":
//   - Your iPhone Shortcut calls it with mode=set to drop off a request
//     ("going" or "back").
//   - Your PC (running plain Python, already installed) calls it with
//     mode=poll every few seconds to check for a waiting request, then
//     mode=clear once it's handled it.
//
// CONFIG: Apps Script can't read a local .env file (it runs on Google's
// servers, not your PC) -- the closest equivalent is Script Properties,
// which keeps the secret out of this visible source code. Set it via:
//   Project Settings (gear icon) -> Script Properties -> Add script property
//   Property: SHARED_SECRET   Value: <the same value you put in your .env>
// See APPS_SCRIPT_SETUP.md for the exact click-path.

function getSharedSecret() {
  return PropertiesService.getScriptProperties().getProperty("SHARED_SECRET");
}

function doGet(e) {
  return handleRequest(e);
}

function doPost(e) {
  return handleRequest(e);
}

function handleRequest(e) {
  var params = e.parameter;
  var expectedSecret = getSharedSecret();

  if (!expectedSecret) {
    return jsonResponse({ ok: false, error: "SHARED_SECRET not configured in Script Properties" });
  }

  if (params.secret !== expectedSecret) {
    return jsonResponse({ ok: false, error: "unauthorized" });
  }

  var props = PropertiesService.getScriptProperties();

  if (params.mode === "set") {
    var action = params.action; // "going" or "back"
    if (action !== "going" && action !== "back") {
      return jsonResponse({ ok: false, error: "invalid action" });
    }
    props.setProperty("pending_action", action);
    props.setProperty("pending_time", new Date().toISOString());
    return jsonResponse({ ok: true, queued: action });
  }

  if (params.mode === "poll") {
    var pending = props.getProperty("pending_action");
    return jsonResponse({ ok: true, action: pending || null });
  }

  if (params.mode === "clear") {
    props.deleteProperty("pending_action");
    props.deleteProperty("pending_time");
    return jsonResponse({ ok: true });
  }

  return jsonResponse({ ok: false, error: "invalid mode" });
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
