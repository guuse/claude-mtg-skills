#!/bin/bash
# SUDO_ASKPASS helper for the MTGA collection exporter (macOS only).
#
# The macOS memory scan needs root, but `sudo` normally demands a TTY to read the
# password — which a non-interactive shell (e.g. an agent's Bash tool) doesn't have,
# so plain `sudo` fails with "a terminal is required to read the password".
#
# With `sudo -A` and SUDO_ASKPASS pointing at this script, sudo instead runs this
# helper to obtain the password. We pop a native, secure macOS dialog (hidden answer),
# so the password is typed into a GUI prompt — no terminal, no new tab, and the
# password never appears on the command line or in the transcript.
#
# Usage:
#   SUDO_ASKPASS="$(dirname "$0")/macos-askpass.sh" \
#     sudo -A python3 "$(dirname "$0")/export_collection.py"
exec /usr/bin/osascript <<'APPLESCRIPT'
text returned of (display dialog ¬
    "Password (sudo) — needed to read the MTG Arena collection from game memory:" ¬
    default answer "" with title "MTGA Collection Export" ¬
    with icon caution with hidden answer)
APPLESCRIPT
