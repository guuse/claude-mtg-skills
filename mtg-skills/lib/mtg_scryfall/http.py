"""Shared robust HTTP/JSON fetch — one place that gets external requests right.

Every external request the skills make (Scryfall, EDHREC JSON, Archidekt and Moxfield
deck APIs) should route through here so they all behave the same way:

- **HTTPS only** — refuse plain-HTTP URLs outright.
- A **descriptive User-Agent** and explicit **Accept** header. Most 403s the skills
  used to hit were a missing or blocked UA (or Cloudflare-protected HTML), so we always
  send one and prefer structured JSON endpoints.
- A small **polite delay** after each call, and **retry with exponential backoff** on
  *transient* failures only (network errors, timeouts, HTTP 429/5xx).
- Permanent failures (404, a 403 that survives retries, non-JSON bodies) raise
  `FetchError` immediately so the caller can **fall back to the next source** and tell
  the user *which* source failed — never silently retry forever, never fabricate data.

Stdlib only — no pip install required.
"""

import json
import time
import urllib.error
import urllib.request

# Version is kept in sync with the plugin manifest by hand; the UA only needs a coarse
# marker so site operators can identify (and, if they must, throttle) the client.
USER_AGENT = "ClaudeMTGSkills/1.10 (+https://github.com/guuse/claude-mtg-skills)"
DEFAULT_HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}

# Statuses worth retrying — rate limiting and server-side hiccups, not 4xx "you asked
# for the wrong thing" errors.
TRANSIENT_STATUS = {429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """A request that could not be satisfied — caller should fall back and say so.

    Carries the offending `url` and, when the failure was an HTTP response, its
    `status` so callers can word the fallback message precisely (e.g. "EDHREC returned
    403, using the local Scryfall database instead").
    """

    def __init__(self, message, url=None, status=None):
        super().__init__(message)
        self.url = url
        self.status = status


def get_json(url, headers=None, timeout=30, retries=3, backoff=1.0, delay=0.1):
    """GET `url` and parse the JSON body, with polite headers and bounded retries.

    `retries` is the number of *extra* attempts after the first; transient failures
    sleep `backoff * 2**attempt` seconds between tries (1s, 2s, 4s with the default
    backoff). Returns the decoded object, or raises `FetchError` on a permanent failure
    or once retries are exhausted.
    """
    if not url.lower().startswith("https://"):
        raise FetchError(f"refusing non-HTTPS URL: {url}", url=url)

    hdrs = dict(DEFAULT_HEADERS)
    if headers:
        hdrs.update(headers)

    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
            if delay:
                time.sleep(delay)
            try:
                return json.loads(raw)
            except ValueError as e:
                raise FetchError(f"non-JSON response from {url}: {e}", url=url)
        except urllib.error.HTTPError as e:
            last = e
            if e.code in TRANSIENT_STATUS and attempt < retries:
                time.sleep(backoff * (2 ** attempt))
                continue
            raise FetchError(f"HTTP {e.code} from {url}", url=url, status=e.code)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
                continue
            reason = getattr(e, "reason", e)
            raise FetchError(f"could not reach {url}: {reason}", url=url)
    # Defensive: the loop always returns or raises, but keep mypy/readers happy.
    raise FetchError(f"failed to fetch {url}: {last}", url=url)  # pragma: no cover
