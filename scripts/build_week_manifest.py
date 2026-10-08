#!/usr/bin/env python3
"""Read-only verification of the retained historical reviewer manifest.

    python3 scripts/build_week_manifest.py --verify

The old --write entrypoint and scheduled campaign check list are retired.
This verifies the existing record without relabeling it as current evidence.
"""
from __future__ import annotations

import argparse, hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "week-2026-09-19"
MANIFEST = OUT / "manifest.json"

def sha(rel: str):
    p = ROOT / rel
    if not p.is_file():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args(argv)
    if not a.verify:
        ap.error("give --verify; packet creation is retired")
    old = json.loads(MANIFEST.read_text())
    drift = [rel for rel, rec in old["files"].items() if sha(rel) != rec["sha256"]]
    gone = [rel for rel in old["files"] if not (ROOT / rel).is_file()]
    if drift or gone:
        print("MANIFEST VERIFICATION FAILED", file=sys.stderr)
        for rel in drift:
            print(f"  hash drift: {rel}", file=sys.stderr)
        for rel in gone:
            print(f"  missing:    {rel}", file=sys.stderr)
        return 1
    print(f"manifest verified: {len(old['files'])} artifacts match their recorded hashes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
