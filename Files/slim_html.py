#!/usr/bin/env python3
"""
slim_html.py — One-time helper to extract embedded base64 data URLs from
humanity-contained.html into separate asset files, and rewrite the HTML to
reference them with relative paths.

Usage:
    cd /path/to/your/Humanity-Contained/repo
    python3 slim_html.py humanity-contained.html

What it does:
    - Finds every data:video/<ext>;base64,... and data:audio/<ext>;base64,...
      embedded in the HTML.
    - Writes each one out to assets/video/ or assets/audio/ with a
      content-hash filename (so duplicates dedupe automatically).
    - Replaces the data URL in the HTML with the relative path.
    - Writes the slimmed HTML to humanity-contained.slim.html (does NOT
      overwrite your original — you can rename after you've verified).

After running, your folder should look like:
    Humanity-Contained/
    ├── humanity-contained.html         (your original, untouched)
    ├── humanity-contained.slim.html    (the slimmed version)
    └── assets/
        ├── video/  <hash>.mp4 ...
        └── audio/  <hash>.mp3 ...

Then commit + push everything, and rename the slim version to index.html
when you're ready.
"""
import re
import sys
import base64
import hashlib
from pathlib import Path

if len(sys.argv) != 2:
    print("Usage: python3 slim_html.py humanity-contained.html")
    sys.exit(1)

src_path = Path(sys.argv[1])
if not src_path.exists():
    print(f"Error: {src_path} not found")
    sys.exit(1)

html = src_path.read_text(encoding="utf-8")
print(f"Read {len(html):,} characters from {src_path}")

# Match data:<type>/<subtype>;base64,<payload> until the next quote or paren
pattern = re.compile(
    r"data:(video|audio|image)/([a-zA-Z0-9+\-.]+);base64,([A-Za-z0-9+/=\\\n\r]+?)(?=['\"\)])"
)

assets_root = Path("assets")
counts = {"video": 0, "audio": 0, "image": 0}

def replace(m):
    kind, ext, payload = m.group(1), m.group(2), m.group(3)
    # Clean stray whitespace / line continuations from inside the payload
    clean = re.sub(r"\s+", "", payload)
    try:
        raw = base64.b64decode(clean, validate=False)
    except Exception as e:
        print(f"  ! skipped a {kind}/{ext} block (decode failed: {e})")
        return m.group(0)

    h = hashlib.sha1(raw).hexdigest()[:12]
    # Normalize a couple common ext spellings
    ext_norm = {"jpeg": "jpg", "x-png": "png", "mpeg": "mp3"}.get(ext, ext)
    out_dir = assets_root / kind
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / f"{h}.{ext_norm}"
    if not out_file.exists():
        out_file.write_bytes(raw)
        print(f"  + {out_file}  ({len(raw):,} bytes)")
    else:
        print(f"  = {out_file}  (already existed)")
    counts[kind] += 1
    return f"assets/{kind}/{h}.{ext_norm}"

print("Extracting embedded data URLs ...")
new_html = pattern.sub(replace, html)

out_path = src_path.with_name(src_path.stem + ".slim" + src_path.suffix)
out_path.write_text(new_html, encoding="utf-8")

print()
print(f"Done. Extracted {counts['video']} video, {counts['audio']} audio, "
      f"{counts['image']} image asset(s).")
print(f"Wrote slimmed HTML to {out_path}  "
      f"({len(new_html):,} characters, was {len(html):,})")
print()
print("Next steps:")
print(f"  1. Open {out_path} in a browser locally to make sure it still works.")
print(f"  2. git add assets/ {out_path}")
print(f"  3. git commit -m 'extract embedded media to assets/'")
print(f"  4. git push")
print(f"  5. (optional) rename {out_path.name} to index.html for GitHub Pages.")
