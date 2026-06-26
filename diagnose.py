"""
Diagnostic-only script. No Playwright, no Excel parsing, no automation.
Purpose: figure out WHERE the connection is being blocked, before we spend
time fixing anything in the real scraper.

Three checks:
  1. Can this machine reach the general internet at all? (sanity check)
  2. What public IP / rough location is this machine making requests from?
  3. Can this machine reach the Vahan URL with a plain HTTP request
     (no browser, no JS) — both with and without browser-like headers?

Read the output top to bottom. The conclusions section at the end tells you
what the result implies.
"""

import sys
import time
import urllib.request
import urllib.error
import socket

VAHAN_URL = "https://vahan.parivahan.gov.in/vahan4dashboard/vahan/view/reportview.xhtml"
SANITY_URL = "https://www.google.com"
IP_CHECK_URL = "https://api.ipify.org?format=json"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

results = {}


def attempt(label, url, headers=None, timeout=15):
    print(f"\n--- {label} ---")
    print(f"URL: {url}")
    print(f"Headers: {headers if headers else '(none — default urllib)'}")
    req = urllib.request.Request(url, headers=headers or {})
    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - start
            body = resp.read(500)  # just a peek, not the whole page
            print(f"RESULT: SUCCESS — HTTP {resp.status} in {elapsed:.2f}s")
            print(f"First 200 bytes of body: {body[:200]!r}")
            results[label] = ("success", resp.status)
            return True
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        print(f"RESULT: HTTP ERROR — status {e.code} in {elapsed:.2f}s")
        print(f"Reason: {e.reason}")
        results[label] = ("http_error", e.code)
        return False
    except urllib.error.URLError as e:
        elapsed = time.time() - start
        reason = str(e.reason)
        print(f"RESULT: CONNECTION FAILED in {elapsed:.2f}s")
        print(f"Reason: {reason}")
        results[label] = ("connection_failed", reason)
        return False
    except socket.timeout:
        elapsed = time.time() - start
        print(f"RESULT: TIMED OUT after {elapsed:.2f}s")
        results[label] = ("timeout", None)
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"RESULT: UNEXPECTED ERROR ({type(e).__name__}) in {elapsed:.2f}s")
        print(f"Detail: {e}")
        results[label] = ("unexpected_error", str(e))
        return False


print("=" * 70)
print("DIAGNOSTIC RUN STARTING")
print("=" * 70)

# 1. Sanity check — does this machine have working internet at all?
attempt("Sanity check (google.com)", SANITY_URL)

# 2. What IP is this runner making requests from?
attempt("Public IP lookup", IP_CHECK_URL)

# 3a. Vahan with no special headers (closest to a "bot-like" plain request)
attempt("Vahan — plain request, no headers", VAHAN_URL)

# 3b. Vahan with browser-like headers (closer to what Playwright sends)
attempt("Vahan — with browser-like headers", VAHAN_URL, headers=BROWSER_HEADERS)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
for label, (status, detail) in results.items():
    print(f"  {label}: {status} {detail if detail is not None else ''}")

print("\n" + "=" * 70)
print("HOW TO READ THIS")
print("=" * 70)
print("""
- If "Sanity check" FAILS too:
    The runner has no working internet at all (unrelated to Vahan).
    This would be a GitHub Actions infra/network issue, not a Vahan block.

- If "Sanity check" SUCCEEDS but BOTH Vahan attempts FAIL with
  "connection_failed" (especially mentioning reset/refused):
    Strong sign of an IP/network-level block — i.e. Vahan (or the network
    in front of it) is rejecting connections from this runner's IP range
    before any page logic is involved. Headers and browser fingerprinting
    are irrelevant in this case. This matches what we saw with Playwright.

- If "Sanity check" SUCCEEDS and the "no headers" attempt FAILS but the
  "browser-like headers" attempt SUCCEEDS:
    Vahan is filtering on basic request signatures, not blocking the IP
    outright. Different, more solvable problem than a geo/IP block.

- If BOTH Vahan attempts SUCCEED here, but Playwright still fails:
    The block is specific to automated *browser* sessions (headless
    fingerprinting), not basic HTTP access. Different fix path again.

Check the public IP from check #2 — if you want, look it up against an
IP geolocation tool afterwards to confirm which country/datacenter it
reports as. That, plus the result pattern above, tells us which of the
fix paths from the conversation applies.
""")

sys.exit(0)
