#!/usr/bin/env python3
"""export_collection.py — one-shot MTG Arena collection exporter.

Reads the owned-card collection straight out of the running MTG Arena process's memory
(no user input, no anchor cards) and writes it to the MTG workspace as
`collection/MTGA-export-<YYYY-MM-DD>.csv` in Moxfield's CSV shape — the same format the
deckbuilding skills already read for "cards you own".

Card names come from the **local Scryfall database** built by the `mtg-db` skill
(`<workspace>/database/cards.sqlite`, its `arena_cards` table) — this script never
downloads or builds its own card data. When MTG Arena's own bundled card files are
present they're merged in as a best-effort supplement so brand-new cards missing from a
stale database still resolve, but the Scryfall DB is the source of truth.

Cross-platform: Windows (via `pymem`) and macOS (via Mach `task_for_pid`, needs `sudo`).
`numpy` is required for the memory scan.

This script only *exports*. Pushing the collection to the user's synced repo is done by
the orchestrating skill afterwards via **mtg-sync**, run as the normal user — never from
here. (On macOS the scan needs `sudo`; a push from inside this process would run git as
root, which has neither the user's SSH key nor their git config. Keeping the push out of
the script avoids that whole class of failure.) When run under `sudo`, the written CSV is
chown'd back to the invoking user so exports never land root-owned.

Usage:
  python export_collection.py                 # scan + write the CSV into the workspace
  python export_collection.py --db PATH         # explicit cards.sqlite location
  python export_collection.py --out-dir DIR     # explicit collection output directory
  python export_collection.py --process NAME    # override the Arena process name

Exit codes: 0 success · 2 setup/dependency problem · 3 could not locate the collection.
"""

import argparse
import csv
import ctypes
import datetime
import os
import platform
import subprocess
import sys

# Print the progress bar / status to stderr so stdout stays clean for any caller.
try:
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PLATFORM = platform.system()  # 'Windows', 'Darwin', 'Linux'

if PLATFORM == "Windows":
    try:
        import pymem
        import pymem.pattern  # noqa: F401  (imported for side effects / parity with upstream)
    except ImportError:
        pymem = None

try:
    import numpy as np
except ImportError:
    np = None

# ---- locate the shared mtg_scryfall library (same bootstrap as the other skills) ---- #
_HERE = os.path.dirname(os.path.abspath(__file__))
_LIB = None
for _rel in ("../../../lib", "../../lib", "../lib", "lib", "."):
    _cand = os.path.normpath(os.path.join(_HERE, _rel))
    if os.path.isdir(os.path.join(_cand, "mtg_scryfall")):
        _LIB = _cand
        break
if _LIB and _LIB not in sys.path:
    sys.path.insert(0, _LIB)

try:
    from mtg_scryfall import arena_lookup, arena_table_present
    from mtg_scryfall.paths import collection_dir, default_db_path
except ImportError as e:  # pragma: no cover
    print(f"ERROR: could not import the shared mtg_scryfall library from {_LIB}: {e}",
          file=sys.stderr)
    sys.exit(2)


def log(msg=""):
    print(msg, file=sys.stderr, flush=True)


def print_progress(iteration, total, prefix="", suffix="", length=30, fill="█"):
    if total == 0:
        total = 1
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled = int(length * iteration // total)
    bar = fill * filled + "-" * (length - filled)
    end = "\n" if iteration >= total else "\r"
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end=end, file=sys.stderr, flush=True)


# ─── macOS memory reader ──────────────────────────────────────────────────────

class MacOSMemReader:
    """Reads process memory on macOS using Mach kernel APIs.

    Requires the script to be run with sudo, or SIP disabled. Works for the native
    Steam MTGA app and for MTGA running via CrossOver (Wine).
    """

    KERN_SUCCESS = 0
    VM_REGION_BASIC_INFO_64 = 9
    VM_REGION_BASIC_INFO_COUNT_64 = 9
    VM_PROT_READ = 0x01

    def __init__(self, process_name):
        self._lib = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
        self._configure_argtypes()

        pid = self._find_pid(process_name)
        if pid is None:
            raise Exception(
                f"Process '{process_name}' not found.\n"
                "Make sure MTG Arena is running and you have visited the Collection/Decks tab."
            )

        self.process_id = pid
        task = ctypes.c_uint(0)
        ret = self._lib.task_for_pid(
            self._lib.mach_task_self(), ctypes.c_int(pid), ctypes.byref(task)
        )
        if ret != self.KERN_SUCCESS:
            raise PermissionError(
                f"Cannot access game memory (Mach error {ret}).\n"
                "On macOS, run with: sudo python3 export_collection.py"
            )
        self._task = task

    def _configure_argtypes(self):
        lib = self._lib
        lib.mach_task_self.restype = ctypes.c_uint
        lib.mach_task_self.argtypes = []
        lib.task_for_pid.restype = ctypes.c_int
        lib.task_for_pid.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.POINTER(ctypes.c_uint)]
        lib.mach_vm_read_overwrite.restype = ctypes.c_int
        lib.mach_vm_read_overwrite.argtypes = [
            ctypes.c_uint, ctypes.c_uint64, ctypes.c_uint64,
            ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint64),
        ]
        lib.mach_vm_region.restype = ctypes.c_int
        lib.mach_vm_region.argtypes = [
            ctypes.c_uint, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
            ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint),
        ]

    def _find_pid(self, process_name):
        """Find PID by name or command-line substring (for CrossOver/Wine processes)."""
        try:
            result = subprocess.run(["pgrep", "-x", process_name], capture_output=True, text=True)
            pids = [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
            if pids:
                return pids[0]
            result = subprocess.run(["pgrep", "-f", process_name], capture_output=True, text=True)
            pids = [int(p) for p in result.stdout.strip().split("\n") if p.strip()]
            pids = [p for p in pids if p != os.getpid()]
            return pids[0] if pids else None
        except Exception:
            return None

    def read_bytes(self, address, size):
        """Read bytes from process memory, handling partial failures gracefully."""
        if address < 0:
            address = 0
        buf = ctypes.create_string_buffer(size)
        out_size = ctypes.c_uint64(0)
        ret = self._lib.mach_vm_read_overwrite(
            self._task, ctypes.c_uint64(address), ctypes.c_uint64(size),
            buf, ctypes.byref(out_size)
        )
        if ret == self.KERN_SUCCESS:
            return bytes(buf.raw[:out_size.value])

        # Fall back to page-by-page reads for ranges crossing unreadable pages.
        result = bytearray()
        page = 4096
        for off in range(0, size, page):
            chunk = min(page, size - off)
            cb = ctypes.create_string_buffer(chunk)
            co = ctypes.c_uint64(0)
            r = self._lib.mach_vm_read_overwrite(
                self._task, ctypes.c_uint64(address + off), ctypes.c_uint64(chunk),
                cb, ctypes.byref(co)
            )
            result.extend(cb.raw[:co.value] if r == self.KERN_SUCCESS else b"\x00" * chunk)
        return bytes(result)

    def get_readable_regions(self):
        """Return list of (address, size) for all readable memory regions."""
        regions = []
        address = ctypes.c_uint64(1)
        while True:
            size = ctypes.c_uint64(0)
            info_buf = (ctypes.c_int * self.VM_REGION_BASIC_INFO_COUNT_64)()
            info_count = ctypes.c_uint(self.VM_REGION_BASIC_INFO_COUNT_64)
            object_name = ctypes.c_uint(0)
            ret = self._lib.mach_vm_region(
                self._task, ctypes.byref(address), ctypes.byref(size),
                self.VM_REGION_BASIC_INFO_64, ctypes.cast(info_buf, ctypes.c_void_p),
                ctypes.byref(info_count), ctypes.byref(object_name)
            )
            if ret != self.KERN_SUCCESS:
                break
            if info_buf[0] & self.VM_PROT_READ:
                regions.append((address.value, size.value))
            next_addr = address.value + size.value
            if next_addr <= address.value:
                break
            address.value = next_addr
        return regions


# ─── Local MTGA bundled-card files (best-effort supplement) ────────────────────

def get_local_mtga_path():
    """Find the MTGA 'Raw' data folder across Windows and macOS."""
    from pathlib import Path
    if PLATFORM == "Windows":
        candidates = [
            Path(r"C:\Program Files (x86)\Steam\steamapps\common\MTGA\MTGA_Data\Downloads\Raw"),
            Path(r"C:\Program Files\Wizards of the Coast\MTGA\MTGA_Data\Downloads\Raw"),
            Path(r"C:\Program Files (x86)\Wizards of the Coast\MTGA\MTGA_Data\Downloads\Raw"),
        ]
    else:
        steam_base = Path.home() / "Library" / "Application Support" / "Steam" / "steamapps" / "common"
        candidates = [steam_base / "MTGA" / "MTGA_Data" / "Downloads" / "Raw"]
        crossover_bottles = Path.home() / "Library" / "Application Support" / "CrossOver" / "Bottles"
        if crossover_bottles.exists():
            for bottle in crossover_bottles.iterdir():
                drive_c = bottle / "drive_c"
                candidates += [
                    drive_c / "Program Files (x86)" / "Steam" / "steamapps" / "common" / "MTGA" / "MTGA_Data" / "Downloads" / "Raw",
                    drive_c / "Program Files" / "Wizards of the Coast" / "MTGA" / "MTGA_Data" / "Downloads" / "Raw",
                    drive_c / "Program Files (x86)" / "Wizards of the Coast" / "MTGA" / "MTGA_Data" / "Downloads" / "Raw",
                ]
    for p in candidates:
        if p.exists():
            return p
    return None


def load_local_mtga_database():
    """Scan MTGA's own bundled SQLite files for grpId -> {name, set, collector_number}.

    Best-effort supplement only: fills in arena_ids the Scryfall DB doesn't yet know
    (e.g. cards from a set newer than the local database). No network, no download.
    """
    import sqlite3
    raw_path = get_local_mtga_path()
    if not raw_path:
        return {}

    log(f"Supplementing from local MTGA card files in {raw_path}...")
    lookup = {}
    try:
        all_files = sorted(raw_path.glob("*.mtga"), key=lambda f: f.stat().st_size, reverse=True)
        for f in all_files:
            if f.stat().st_size < 500 * 1024:
                continue
            try:
                conn = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
                cursor = conn.cursor()
                tables = {row[0] for row in cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                if "Cards" in tables and "Localizations" in tables:
                    loc_map = {}
                    try:
                        cursor.execute(
                            "SELECT Id, Text FROM Localizations "
                            "WHERE Format LIKE '%en-US%' OR Format IS NULL")
                        for lid, text in cursor.fetchall():
                            if text:
                                loc_map[lid] = text
                    except sqlite3.Error:
                        cursor.execute("SELECT Id, Text FROM Localizations")
                        for lid, text in cursor.fetchall():
                            if text:
                                loc_map[lid] = text

                    cols = [row[1] for row in cursor.execute("PRAGMA table_info(Cards)")]
                    has_set = "ExpansionCode" in cols
                    has_cn = "CollectorNumber" in cols
                    query = (f"SELECT GrpId, TitleId, "
                             f"{'ExpansionCode' if has_set else 'NULL'}, "
                             f"{'CollectorNumber' if has_cn else 'NULL'} FROM Cards")
                    for row in cursor.execute(query):
                        grp_id, title_id, set_code, cn = row
                        if title_id in loc_map:
                            lookup[grp_id] = {
                                "name": loc_map[title_id],
                                "set": (set_code or "").upper(),
                                "collector_number": str(cn) if cn else "",
                            }
                    if len(lookup) > 1000:
                        conn.close()
                        log(f"  Loaded {len(lookup)} cards from local MTGA files.")
                        return lookup
                conn.close()
            except sqlite3.Error:
                continue
    except Exception as e:
        log(f"  (local MTGA scan skipped: {e})")
    return lookup


# ─── Memory scanning (anchor-free) ────────────────────────────────────────────
#
# MTGA keeps the owned collection in a C# Dictionary<int,int> (grpId -> count). A .NET
# dictionary stores entries as [hashCode, next, key, value] -> 4x uint32 (stride 4); key
# and value sit at offsets 2 and 3. Older/array layouts use a plain [id, count] pairing
# (stride 2). We don't need anchor cards: we read every readable private region, validate
# ids against the card database, and keep the largest contiguous block of valid entries.

_MEM_COMMIT = 0x1000
_MEM_PRIVATE = 0x20000
_PAGE_GUARD = 0x100
_READABLE_PROT = {0x02, 0x04, 0x20, 0x40}


class _MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_ulonglong),
        ("AllocationBase", ctypes.c_ulonglong),
        ("AllocationProtect", ctypes.c_ulong),
        ("__alignment1", ctypes.c_ulong),
        ("RegionSize", ctypes.c_ulonglong),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
        ("__alignment2", ctypes.c_ulong),
    ]


def iter_readable_regions(pm):
    """Yield (base, size) for readable memory regions, platform-aware."""
    if PLATFORM == "Windows":
        VirtualQueryEx = ctypes.windll.kernel32.VirtualQueryEx
        VirtualQueryEx.restype = ctypes.c_size_t
        VirtualQueryEx.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p,
            ctypes.POINTER(_MEMORY_BASIC_INFORMATION), ctypes.c_size_t,
        ]
        handle = pm.process_handle
        mbi = _MEMORY_BASIC_INFORMATION()
        addr = 0
        while VirtualQueryEx(handle, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)):
            if (mbi.State == _MEM_COMMIT and mbi.Type == _MEM_PRIVATE
                    and (mbi.Protect & 0xFF) in _READABLE_PROT and not (mbi.Protect & _PAGE_GUARD)):
                yield mbi.BaseAddress, mbi.RegionSize
            nxt = mbi.BaseAddress + mbi.RegionSize
            if nxt <= addr:
                break
            addr = nxt
    else:
        for base, size in pm.get_readable_regions():
            yield base, size


def _merged_runs(mask, gap):
    """Return (start, end) for True-runs in a bool array, bridging gaps <= gap."""
    if not mask.any():
        return []
    edges = np.flatnonzero(np.diff(np.concatenate(([0], mask.view(np.int8), [0]))))
    starts, ends = edges[0::2], edges[1::2]
    merged = []
    for s, e in zip(starts.tolist(), ends.tolist()):
        if merged and s - merged[-1][1] <= gap:
            merged[-1][1] = e
        else:
            merged.append([s, e])
    return merged


def scan_collection(pm, db):
    """Anchor-free scan: return the largest {grpId: count} block found in memory."""
    if np is None:
        raise Exception("numpy is required for scanning. Install it with: pip install numpy")

    valid = np.array(sorted(db.keys()), dtype=np.uint32)

    log("Enumerating memory regions...")
    regions = list(iter_readable_regions(pm))
    total = len(regions) or 1

    MIN_ENTRIES = 30   # ignore tiny coincidental blocks
    MAX_COUNT = 1000   # owned counts are small; rejects pointer/garbage values
    GAP = 32           # bridge gaps from deleted slots / cards missing from the database

    best = {}
    print_progress(0, total, prefix="Mem Scan:", suffix="Starting", length=25)
    for ri, (base, size) in enumerate(regions):
        try:
            data = pm.read_bytes(base, size)
        except Exception:
            data = None
        if data:
            n = len(data) // 4
            if n >= 8:
                a = np.frombuffer(data, dtype=np.uint32, count=n)
                for stride, idoff, cntoff in ((4, 2, 3), (2, 0, 1)):
                    for align in range(stride):
                        ids = a[align + idoff::stride]
                        counts = a[align + cntoff::stride]
                        m = min(len(ids), len(counts))
                        if m < MIN_ENTRIES:
                            continue
                        ids, counts = ids[:m], counts[:m]
                        mask = np.isin(ids, valid) & (counts >= 1) & (counts <= MAX_COUNT)
                        for s, e in _merged_runs(mask, GAP):
                            span = mask[s:e]
                            if int(span.sum()) <= len(best):
                                continue
                            d = {int(i): int(c)
                                 for i, c in zip(ids[s:e][span].tolist(),
                                                 counts[s:e][span].tolist())}
                            if len(d) > len(best):
                                best = d
        print_progress(ri + 1, total, prefix="Mem Scan:", suffix=f"{len(best)} cards", length=25)
    return best


def connect_to_mtga(process_override=None):
    """Connect to the MTGA process, platform-aware."""
    if PLATFORM == "Windows":
        if pymem is None:
            raise Exception("pymem not installed. Run: pip install pymem")
        return pymem.Pymem(process_override or "MTGA.exe")
    elif PLATFORM == "Darwin":
        names = [process_override] if process_override else ["MTGA", "MTGA.exe", "mtga"]
        for name in names:
            try:
                return MacOSMemReader(name)
            except PermissionError:
                raise  # propagate the sudo error immediately
            except Exception:
                continue
        raise Exception(
            "MTG Arena not found. Make sure it is running (Steam or CrossOver) and you have "
            "visited the Collection/Decks tab."
        )
    else:
        raise Exception(f"Unsupported platform: {PLATFORM}. Only Windows and macOS are supported.")


# ─── Main ─────────────────────────────────────────────────────────────────────

def build_lookup(db_path):
    """Build the arena_id -> card lookup from the Scryfall DB, supplemented locally."""
    db = arena_lookup(db_path)
    if db:
        log(f"Loaded {len(db)} Arena cards from the Scryfall database.")
    # Best-effort: merge in MTGA's own card files for anything the DB doesn't know yet.
    local = load_local_mtga_database()
    added = 0
    for grp_id, info in local.items():
        if grp_id not in db:
            db[grp_id] = info
            added += 1
    if added:
        log(f"Supplemented {added} cards from local MTGA files.")
    return db


def chown_back(path):
    """When run under sudo, give the written file back to the invoking user.

    macOS requires root to read game memory, so the script often runs via sudo and the
    CSV would otherwise be root-owned (the user couldn't overwrite or delete it without
    sudo, and a later non-root mtg-sync push couldn't stage it cleanly). sudo exports
    SUDO_UID/SUDO_GID; restore ownership to them. Best-effort and silent on non-sudo runs.
    """
    uid, gid = os.environ.get("SUDO_UID"), os.environ.get("SUDO_GID")
    if not uid or not gid:
        return
    try:
        os.chown(path, int(uid), int(gid))
    except Exception as e:
        log(f"[note] could not restore ownership of {path} to the invoking user: {e}")


def main():
    ap = argparse.ArgumentParser(description="One-shot MTG Arena collection exporter.")
    ap.add_argument("--db", help="Explicit cards.sqlite path (default: workspace database).")
    ap.add_argument("--out-dir", help="Explicit collection output directory.")
    ap.add_argument("--process", help="Override the MTG Arena process name.")
    args = ap.parse_args()

    log(f"MTGA Collection Exporter | {PLATFORM}")

    if np is None:
        log("[Error] numpy is required. Install it with: pip install numpy")
        sys.exit(2)

    db_path = args.db or default_db_path()
    if not arena_table_present(db_path):
        log(f"[Error] No Arena card map in the Scryfall database ({db_path}).")
        log("        Build/refresh it first with the mtg-db skill, e.g.:")
        log('          python ../mtg-db/scripts/build_database.py --refresh')
        sys.exit(2)

    db = build_lookup(db_path)
    if not db:
        log("[Error] Card database is empty — refresh it with the mtg-db skill.")
        sys.exit(2)

    log("Connecting to MTGA...")
    try:
        pm = connect_to_mtga(args.process)
        log(f"Connected (PID: {pm.process_id})")
    except PermissionError as e:
        log(str(e))
        sys.exit(2)
    except Exception as e:
        log(str(e))
        sys.exit(3)

    log("Scanning memory for collection data (no anchors needed)...")
    collection = scan_collection(pm, db)
    if not collection:
        log("\nCould not locate your collection in memory.")
        log("Open MTG Arena, visit the Collection or Decks tab and scroll through your")
        log("cards (so they load into memory), then run this again.")
        sys.exit(3)

    log(f"\n[Success] Found {len(collection)} unique cards "
        f"({sum(collection.values())} total).")

    processed = {}
    for cid, qty in collection.items():
        info = db.get(cid)
        if not info:
            continue
        key = (info["name"], info["set"])
        if key not in processed:
            processed[key] = {"count": 0, "name": info["name"], "set": info["set"]}
        processed[key]["count"] += qty

    final_list = sorted(processed.values(), key=lambda x: (x["name"], x["set"]))

    out_dir = args.out_dir or collection_dir()
    os.makedirs(out_dir, exist_ok=True)
    today = datetime.date.today().isoformat()
    out_csv = os.path.join(out_dir, f"MTGA-export-{today}.csv")

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Count", "Name", "Edition", "Condition", "Language", "Foil", "Tag"])
        for i in final_list:
            writer.writerow([i["count"], i["name"], i["set"], "Near Mint", "English", "", ""])

    chown_back(out_csv)  # if run via sudo, hand the file back to the invoking user
    log(f"\nExport complete -> {out_csv}")
    print(out_csv)  # stdout: the one machine-readable line (the path we wrote)


if __name__ == "__main__":
    main()
