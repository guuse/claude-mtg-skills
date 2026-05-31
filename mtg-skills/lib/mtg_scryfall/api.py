"""Live Scryfall API client — the fallback path.

Used for: (1) queries the local database can't serve (`function:`/`otag:` Tagger tags
and any unsupported operator), (2) when no database can be built (no FS / no code
execution), and (3) the bulk-data metadata + download that builds the database.

Respects Scryfall etiquette: descriptive User-Agent, explicit Accept header, and a
small delay between paginated calls.
"""

import json
import time
import urllib.parse
import urllib.request
import urllib.error

API = "https://api.scryfall.com"
HEADERS = {
    "User-Agent": "ClaudeMTGSkills/1.0 (https://github.com/guuse/claude-mtg-skills)",
    "Accept": "application/json",
}
DELAY_SECONDS = 0.1  # be polite between paginated calls


class ScryfallUnreachable(RuntimeError):
    """Raised when api.scryfall.com can't be reached at all."""


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(url, timeout=30):
    """Public GET helper that maps connection failures to ScryfallUnreachable."""
    try:
        return _get(url, timeout=timeout)
    except urllib.error.URLError as e:
        if isinstance(e, urllib.error.HTTPError):
            raise
        raise ScryfallUnreachable(str(e))


def search(query, limit=30, order="edhrec", unique="cards"):
    """Paginate Scryfall /cards/search up to `limit` raw card objects."""
    results = []
    params = {"q": query, "order": order, "unique": unique}
    url = f"{API}/cards/search?" + urllib.parse.urlencode(params)
    while url and len(results) < limit:
        try:
            data = get_json(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:  # no cards matched
                break
            raise
        for card in data.get("data", []):
            results.append(card)
            if len(results) >= limit:
                break
        url = data.get("next_page") if data.get("has_more") else None
        if url:
            time.sleep(DELAY_SECONDS)
    return results


def named(name):
    """Exact (then fuzzy) single-card lookup. Returns a raw card object or None."""
    base = f"{API}/cards/named?"
    try:
        return get_json(base + urllib.parse.urlencode({"exact": name}))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            try:
                return get_json(base + urllib.parse.urlencode({"fuzzy": name}))
            except urllib.error.HTTPError:
                return None
        raise


def bulk_metadata(kind="default_cards"):
    """Return the Scryfall bulk-data descriptor for `kind` (default: default_cards).

    The descriptor carries `download_uri`, `updated_at`, `size`, and an `id` we use
    as the version marker for staleness checks. One small call — negligible against
    the card-query volume the database removes.
    """
    data = get_json(f"{API}/bulk-data")
    for entry in data.get("data", []):
        if entry.get("type") == kind:
            return entry
    raise RuntimeError(f"Scryfall bulk-data has no entry of type {kind!r}")


def download_to(url, dest, progress=None, chunk=1 << 20):
    """Stream a (large) download to `dest`, calling progress(bytes_done, total)."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as resp:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        with open(dest, "wb") as fh:
            while True:
                buf = resp.read(chunk)
                if not buf:
                    break
                fh.write(buf)
                done += len(buf)
                if progress:
                    progress(done, total)
    return dest
