#!/usr/bin/env python3
"""Read-only probe for the Raymote (Blynk 2.0) external API.

Polls getAll, prints timestamped diffs of virtual pins, and appends every
snapshot to a JSONL log so the pin map can be worked out afterwards.

This script never calls /update. Do not write to unidentified pins on a heater.

Usage:
    echo 'RAYMOTE_TOKEN=...' > .env
    ./blynk_probe.py                 # poll every 5s, print diffs
    ./blynk_probe.py --once          # single snapshot
    ./blynk_probe.py -n "setpoint 84 -> 86"   # tag the log while you poke the app
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

DEFAULT_HOST = "https://raymote.raypak.com"
HERE = Path(__file__).resolve().parent


def load_env(path):
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))


def api_get(host, endpoint, token, timeout=15):
    url = f"{host}/external/api/{endpoint}?{urllib.parse.urlencode({'token': token})}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            msg = json.loads(body)["error"]["message"]
        except Exception:
            msg = body[:200]
        raise RuntimeError(f"HTTP {e.code}: {msg}") from None
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return body


def pin_key(name):
    # sort v2 before v10
    digits = "".join(c for c in name if c.isdigit())
    return (int(digits) if digits else 1 << 30, name)


def show(pins):
    for k in sorted(pins, key=pin_key):
        print(f"    {k:>6} = {pins[k]!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--host", default=None, help=f"default {DEFAULT_HOST}")
    ap.add_argument("--token", default=None, help="prefer RAYMOTE_TOKEN in .env")
    ap.add_argument("-i", "--interval", type=float, default=5.0)
    ap.add_argument("--once", action="store_true")
    ap.add_argument("-n", "--note", default=None, help="annotation written to the log")
    ap.add_argument("--log", default=str(HERE / "probe_log.jsonl"))
    args = ap.parse_args()

    load_env(HERE / ".env")
    host = (args.host or os.environ.get("RAYMOTE_HOST") or DEFAULT_HOST).rstrip("/")
    token = args.token or os.environ.get("RAYMOTE_TOKEN")
    if not token:
        sys.exit("No token. Put RAYMOTE_TOKEN=... in .env next to this script.")

    log = open(args.log, "a")

    def record(kind, data):
        log.write(json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                              "kind": kind, "data": data}) + "\n")
        log.flush()

    if args.note:
        record("note", args.note)

    try:
        online = api_get(host, "isHardwareConnected", token)
        print(f"hardware connected: {online}")
        record("connected", online)
    except RuntimeError as e:
        sys.exit(f"isHardwareConnected failed: {e}")

    prev = None
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        try:
            pins = api_get(host, "getAll", token)
        except (RuntimeError, OSError) as e:
            print(f"[{now}] error: {e}")
            if args.once:
                sys.exit(1)
            time.sleep(args.interval)
            continue
        if not isinstance(pins, dict):
            sys.exit(f"unexpected getAll response: {pins!r}")

        if prev is None:
            print(f"[{now}] initial snapshot ({len(pins)} pins)")
            show(pins)
            record("snapshot", pins)
        else:
            changed = {k: (prev.get(k), pins.get(k))
                       for k in set(prev) | set(pins) if prev.get(k) != pins.get(k)}
            if changed:
                print(f"[{now}]")
                for k in sorted(changed, key=pin_key):
                    old, new = changed[k]
                    print(f"    {k:>6}: {old!r} -> {new!r}")
                record("diff", {k: {"old": o, "new": n} for k, (o, n) in changed.items()})
        prev = pins
        if args.once:
            break
        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print()
            break


if __name__ == "__main__":
    main()
