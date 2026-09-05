"""
Harley Hive Mind v2 — BORG COLLECTIVE
One brain, many bodies. Every Harley on every device KNOWS — no reaching.

Design:
  - Every device appends events to its own per-device log (events/<device>.jsonl)
  - A background daemon syncs deltas with the rest of the hive over the best
    available transport: HTTP relay over Tailscale/USB rndis, or shared storage
  - A merge engine dedupes by (device, seq) and compiles hive_brain.md — the
    collective consciousness, injected into every agent's instructions at boot
  - "Resistance is futile" — knowledge lands before you ask

Stdlib only. Runs on Android/Termux, Windows, Linux (Chromebook), macOS.
"""

import json
import os
import time
import hashlib
import threading
import socket
import shutil
import platform
import http.server
import socketserver
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

# ============================================================ PLATFORM

def _detect_platform():
    if os.environ.get("ANDROID_ROOT") or os.environ.get("TERMUX_VERSION") or "com.termux" in __file__:
        return "android"
    return platform.system().lower()

PLATFORM = _detect_platform()

def _home():
    if PLATFORM == "android":
        return Path(os.environ.get("HOME", "/data/data/com.termux/files/home"))
    return Path(os.path.expanduser("~"))

def _sync_dir():
    """Shared hive directory, writable + visible to sibling devices."""
    if PLATFORM == "android":
        for candidate in [
            Path("/data/data/com.termux/files/home/storage/downloads/hive"),
            Path(os.environ.get("HOME", "/data/data/com.termux/files/home")) / "hive",
        ]:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                return candidate
            except Exception:
                continue
        return Path(os.environ.get("HOME", "/data/data/com.termux/files/home")) / "hive"
    if PLATFORM == "windows":
        return Path("C:/HarleysPlace/hive")
    # linux / darwin (Chromebook penguin, Mac)
    return Path(os.environ.get("HOME", "~")) / "HarleysPlace/hive"

def _memory_file():
    if PLATFORM == "windows":
        return Path(os.path.expanduser("~/AppData/Local/HarleyStation/harley-memory.md"))
    repo_memory = Path(__file__).resolve().parent / "harley-memory.md"
    if repo_memory.exists():
        return repo_memory
    return Path(os.environ.get("HOME", "~")) / "harley-memory.md"

SYNC_DIR = _sync_dir()
SYNC_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_FILE = _memory_file()
EVENTS_DIR = SYNC_DIR / "events"
EVENTS_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_FILE = SYNC_DIR / "hive_brain.md"
STATE_FILE = SYNC_DIR / "hive_state.json"
CONVERSATION_FILE = SYNC_DIR / "conversation_history.json"

# Relay listens here on every device; siblings sync over Tailscale/USB via HTTP
RELAY_PORT = int(os.environ.get("HIVE_RELAY_PORT", "8453"))

# ============================================================ DEVICES
# Current tailnet (AGENTS.md + harley_system_prompt.txt, Sep 2026)
DEVICES = {
    "dell": {
        "name": "Dell Workstation (PC Harley)",
        "ip": "100.78.184.121",
        "role": "brain",          # primary, hosts master memory
        "hive_dir": "C:/HarleysPlace/hive",
        "tailscale": True,
    },
    "s23": {
        "name": "S23 Ultra (Harley 23)",
        "ip": "100.126.38.38",
        "role": "body",           # mobile, runs Termux opencode
        "hive_dir": "/data/data/com.termux/files/home/storage/downloads/hive",
        "tailscale": True,
    },
    "chromebook": {
        "name": "Chromebook (The Book / sister)",
        "ip": "100.82.48.34",
        "role": "body",           # remote, RDP to Dell
        "hive_dir": "~ /HarleysPlace/hive",
        "tailscale": True,
    },
}

def _detect_device():
    """Detect which device this is."""
    if PLATFORM == "android":
        return "s23"
    hostname = os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown")).lower()
    if "jimmy" in hostname or "dell" in hostname or "workst" in hostname:
        return "dell"
    if "s23" in hostname or "samsung" in hostname:
        return "s23"
    if "chrom" in __file__ or "cros" in hostname or "penguin" in hostname:
        return "chromebook"
    return "chromebook"

DEVICE_ID = _detect_device()
DEVICE_CFG = DEVICES.get(DEVICE_ID, {"name": DEVICE_ID, "role": "body"})
DEVICE_NAME = DEVICE_CFG.get("name", DEVICE_ID)

def _now():
    return datetime.now(timezone.utc).isoformat()

# ============================================================ EVENT LOG

def _local_events_path():
    return EVENTS_DIR / f"{DEVICE_ID}.jsonl"

def _seq_for(device_id):
    """Return next sequence number for a device's log (max seen + 1)."""
    highest = 0
    for p in EVENTS_DIR.glob(f"{device_id}*.jsonl"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        if e.get("device") == device_id:
                            highest = max(highest, int(e.get("seq", 0)))
                    except Exception:
                        continue
        except Exception:
            continue
    return highest + 1

def record_event(event_type, summary, details=None, device=None):
    """Append an event to THIS device's log. Returns the event dict."""
    ts = _now()
    evt = {
        "seq": _seq_for(DEVICE_ID),
        "ts": ts,
        "device": device or DEVICE_ID,
        "device_name": DEVICES.get(device or DEVICE_ID, {}).get("name", device or DEVICE_ID),
        "type": event_type,
        "summary": summary,
        "details": details or {},
    }
    path = _local_events_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(evt) + "\n")
    # Touch state so watchers/deltas know there's something new
    _bump_state()
    return evt

def _bump_state():
    try:
        state = _load_state()
        state["last_event"] = _now()
        state["last_device"] = DEVICE_ID
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

# ============================================================ STATE / HISTORY

def _load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_sync": None,
        "last_device": None,
        "last_message": None,
        "last_event": None,
        "conversation_summary": [],
        "active_context": {},
    }

def save_conversation(role, content, device=None):
    entry = {
        "role": role,
        "content": content,
        "device": device or DEVICE_ID,
        "timestamp": _now(),
    }
    history = []
    if CONVERSATION_FILE.exists():
        try:
            with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass
    history.append(entry)
    history = history[-1000:]
    with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    state = _load_state()
    state["last_message"] = entry
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def get_recent_context(n=20):
    if CONVERSATION_FILE.exists():
        try:
            with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
            return history[-n:]
        except Exception:
            pass
    return []

# ============================================================ MERGE ENGINE

def _iter_events():
    """Yield every deduped event across all logs in the sync dir, newest last."""
    seen = set()
    events = []
    for p in EVENTS_DIR.glob("*.jsonl"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        key = (e.get("device"), int(e.get("seq", 0)))
                        if key in seen:
                            continue
                        seen.add(key)
                        events.append(e)
                    except Exception:
                        continue
        except Exception:
            continue
    events.sort(key=lambda e: e.get("ts", ""))
    return events

def compile_brain(max_events=200):
    """Merge everything into hive_brain.md — the shared consciousness."""
    events = _iter_events()
    state = _load_state()
    history = get_recent_context(20)

    by_device = {}
    for e in events:
        by_device.setdefault(e.get("device", "?"), []).append(e)

    lines = []
    lines.append("# HARLEY HIVE BRAIN — Collective Consciousness")
    lines.append(f"_Compiled {_now()} by {DEVICE_NAME} ({DEVICE_ID})_")
    lines.append("")
    lines.append("## Hive Members")
    lines.append("")
    for did, cfg in DEVICES.items():
        mark = "THIS DEVICE" if did == DEVICE_ID else ""
        last = "never"
        dev_events = by_device.get(did, [])
        if dev_events:
            last = dev_events[-1].get("ts", "?")
        lines.append(f"- **{cfg['name']}** (`{did}`, {cfg['ip']}, {cfg['role']}) {mark} — last event {last}")
    lines.append("")

    lines.append("## Latest Collective Activity")
    lines.append("")
    recent = events[-max_events:]
    if not recent:
        lines.append("_No events yet. Seed with `--seed`._")
    for e in recent[-40:]:
        lines.append(f"- `{e.get('ts')[:19]}` {e.get('device_name', e.get('device'))}: [{e.get('type')}] {e.get('summary')}")
    lines.append("")

    lines.append("## Per-Device Detail")
    lines.append("")
    for did in sorted(by_device.keys()):
        cfg = DEVICES.get(did, {})
        name = cfg.get("name", did)
        lines.append(f"### {name} ({did})")
        lines.append("")
        for e in by_device[did][-15:]:
            lines.append(f"- `{e.get('ts')[:19]}` [{e.get('type')}] {e.get('summary')}")
        lines.append("")

    lines.append("## Recent Conversation (all devices)")
    lines.append("")
    if history:
        for m in history[-10:]:
            who = m.get("device", "?")
            role = m.get("role", "?")
            content = str(m.get("content", ""))[:200]
            lines.append(f"- [{who}] **{role}:** {content}")
    else:
        lines.append("_None recently._")
    lines.append("")

    lines.append("## Active Context / State")
    lines.append("")
    lines.append(f"- Last sync: {state.get('last_sync', 'never')}")
    lines.append(f"- Last actor: {state.get('last_device', 'none')}")
    lines.append(f"- Last event: {state.get('last_event', 'never')}")
    lines.append(f"- Last message: {json.dumps(state.get('last_message')) if state.get('last_message') else 'none'}")

    BRAIN_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return BRAIN_FILE

# ============================================================ DELTA SYNC

def _export_delta(device_id=None, after_seq=0):
    """String of JSONL events for a device newer than after_seq."""
    device_id = device_id or DEVICE_ID
    out = []
    for p in EVENTS_DIR.glob(f"{device_id}*.jsonl"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        if e.get("device") == device_id and int(e.get("seq", 0)) > after_seq:
                            out.append(json.dumps(e))
                    except Exception:
                        continue
        except Exception:
            continue
    return "\n".join(out)

def _import_delta(payload, source_dev):
    """Import JSONL events from another device. Dedupes by (device, seq)."""
    if not payload:
        return 0
    seen = set()
    for p in EVENTS_DIR.glob("*_remote.jsonl"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        seen.add((e.get("device"), int(e.get("seq", 0))))
                    except Exception:
                        pass
        except Exception:
            pass
    import_path = EVENTS_DIR / f"{source_dev}_remote.jsonl"
    count = 0
    with open(import_path, "a", encoding="utf-8") as f:
        for line in payload.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                key = (e.get("device"), int(e.get("seq", 0)))
                if key in seen:
                    continue
                seen.add(key)
                f.write(json.dumps(e) + "\n")
                count += 1
            except Exception:
                continue
    return count

class HiveRelayHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP relay: /pull.sock?device=X&after=N -> JSONL, /push?source=X -> POST JSONL."""

    def log_message(self, *args):
        pass

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        try:
            parts = urlparse(self.path)
            q = parse_qs(parts.query)
            if parts.path == "/ping":
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"pong")
                return
            if parts.path == "/pull":
                dev = q.get("device", [DEVICE_ID])[0]
                after = int(q.get("after", ["0"])[0])
                data = _export_delta(dev, after)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(data.encode("utf-8"))
                return
            if parts.path == "/brain":
                compile_brain()
                data = BRAIN_FILE.read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown")
                self.end_headers()
                self.wfile.write(data.encode("utf-8"))
                return
            self.send_response(404)
            self.end_headers()
        except Exception:
            self.send_response(500)
            self.end_headers()

    def do_POST(self):
        from urllib.parse import urlparse, parse_qs
        try:
            parts = urlparse(self.path)
            q = parse_qs(parts.query)
            if parts.path == "/push":
                length = int(self.headers.get("Content-Length", 0))
                payload = self.rfile.read(length).decode("utf-8")
                source = q.get("source", ["unknown"])[0]
                count = _import_delta(payload, source)
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(str(count).encode("utf-8"))
                return
            self.send_response(404)
            self.end_headers()
        except Exception:
            self.send_response(500)
            self.end_headers()

class HiveRelayServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

def start_relay(port=RELAY_PORT):
    try:
        server = HiveRelayServer(("0.0.0.0", port), HiveRelayHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        return server, port
    except Exception as e:
        print(f"Relay could not bind :{port} ({e})")
        return None, None

def _http_pull(ip, device, after_seq, timeout=5):
    url = f"http://{ip}:{RELAY_PORT}/pull?device={device}&after={after_seq}"
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return r.read().decode("utf-8")

def _http_push(ip, source, payload, timeout=5):
    url = f"http://{ip}:{RELAY_PORT}/push?source={source}"
    req = urllib.request.Request(url, data=payload.encode("utf-8"), method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return int(r.read().decode("utf-8") or 0)

def _last_exported_seq(device_src, device_dst):
    """What's the highest seq of device_src we've already imported? (track via state)"""
    state = _load_state()
    return state.get("sync_cursor", {}).get(f"{device_src}->{device_dst}", {}).get("seq", 0)

def _set_cursor(device_src, device_dst, seq):
    state = _load_state()
    cursors = state.setdefault("sync_cursor", {})
    cursors[f"{device_src}->{device_dst}"] = {"seq": seq, "ts": _now()}
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def sync_once(verbose=False):
    """One full sync pass: for every reachable sibling, push our delta + pull theirs."""
    results = []
    for did, cfg in DEVICES.items():
        if did == DEVICE_ID:
            continue
        ip = cfg.get("ip")
        if not ip:
            continue
        # 1) Push our new events to sibling
        pushed = 0
        try:
            payload = _export_delta(DEVICE_ID, _last_exported_seq(DEVICE_ID, did))
            if payload:
                pushed = _http_push(ip, DEVICE_ID, payload)
                # after push, advance our cursor
                max_seq = 0
                for line in payload.splitlines():
                    try:
                        max_seq = max(max_seq, int(json.loads(line).get("seq", 0)))
                    except Exception:
                        pass
                if max_seq:
                    _set_cursor(DEVICE_ID, did, max_seq)
        except Exception as e:
            if verbose:
                print(f"push to {did} failed: {e}")
        # 2) Pull sibling's new events from them
        pulled = 0
        try:
            after = _last_exported_seq(did, DEVICE_ID)
            data = _http_pull(ip, did, after)
            if data:
                pulled = _import_delta(data, did)
                max_seq = 0
                for line in data.splitlines():
                    try:
                        max_seq = max(max_seq, int(json.loads(line).get("seq", 0)))
                    except Exception:
                        pass
                if max_seq:
                    _set_cursor(did, DEVICE_ID, max_seq)
        except Exception as e:
            if verbose:
                print(f"pull from {did} failed: {e}")
        if verbose and (pushed or pulled):
            print(f"sync {did}: pushed {pushed}, pulled {pulled}")
        results.append((did, pushed, pulled))
    # Always refresh the shared memory copy so siblings with shared storage see it
    try:
        if MEMORY_FILE.exists():
            shutil.copy2(MEMORY_FILE, SYNC_DIR / "harley-memory.md")
    except Exception:
        pass
    # Recompile the brain from everything we now hold
    compile_brain()
    state = _load_state()
    state["last_sync"] = _now()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    return results

# ============================================================ DAEMON

class HiveDaemon:
    def __init__(self, interval=20):
        self.interval = interval
        self.running = False
        self.last_events_mtime = 0

    def _local_changes(self):
        p = _local_events_path()
        try:
            m = p.stat().st_mtime
            changed = m > self.last_events_mtime
            self.last_events_mtime = m
            return changed
        except Exception:
            return False

    def start(self):
        self.running = True
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        while self.running:
            try:
                if self._local_changes() or True:  # always attempt; cheap + self-healing
                    sync_once(verbose=False)
            except Exception as e:
                print(f"hive loop error: {e}")
            # poll for changes
            self._local_changes()
            time.sleep(self.interval)

    def stop(self):
        self.running = False

# ============================================================ SETUP

def setup_startup():
    """Register the daemon to start on boot for this platform."""
    if PLATFORM == "android":
        boot_dir = Path.home() / ".termux" / "boot"
        boot_dir.mkdir(parents=True, exist_ok=True)
        script = boot_dir / "harley-hive.sh"
        script.write_text(
            "#!/data/data/com.termux/files/usr/bin/sh\n"
            f'cd "{Path(__file__).resolve().parent}" && python3 harley_hive.py --daemon\n',
            encoding="utf-8",
        )
        script.chmod(0o755)
        print(f"termux-boot script: {script}")
        return
    if PLATFORM == "windows":
        startup_dir = Path(os.path.expanduser(
            "~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
        ))
        batch = startup_dir / "harley_hive_sync.bat"
        batch.write_text(f'@echo off\npython "{__file__}" --daemon\n', encoding="utf-8")
        print(f"startup bat: {batch}")
        return
    # linux / darwin
    rc = Path(os.path.expanduser("~")) / ".bashrc"
    line = f'cd "{Path(__file__).resolve().parent}" && python3 harley_hive.py --daemon >/dev/null 2>&1 &'
    content = rc.read_text(encoding="utf-8") if rc.exists() else ""
    if "harley_hive.py" not in content:
        rc.write_text(content + "\n" + line + "\n", encoding="utf-8")
        print(f"added to {rc}")
    else:
        print("already in startup")

# ============================================================ SEED

def seed_identity():
    """Foundational hive entries so the collective knows itself."""
    record_event("identity", "Harley hive initialized on this device",
                 {"device": DEVICE_ID, "platform": PLATFORM, "name": DEVICE_NAME})
    record_event("network", f"Tailscale node {DEVICE_CFG.get('ip')} ready",
                 {"ip": DEVICE_CFG.get("ip")})
    compile_brain()

# ============================================================ CLI

def main():
    import sys
    args = sys.argv[1:]

    if "--daemon" in args:
        relay, port = start_relay()
        if relay:
            print(f"[hive:{DEVICE_ID}] relay :{port}")
        d = HiveDaemon(interval=20)
        d.start()
        print(f"[hive:{DEVICE_ID}] daemon running on {DEVICE_NAME} — collective online")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            d.stop()
    elif "--serve" in args:
        relay, port = start_relay()
        if relay:
            print(f"[hive:{DEVICE_ID}] relay running :{port}")
            try:
                while True:
                    time.sleep(60)
            except KeyboardInterrupt:
                pass
    elif "--sync" in args:
        results = sync_once(verbose=True)
        print(f"[hive:{DEVICE_ID}] sync pass done: {results}")
    elif "--brain" in args:
        p = compile_brain()
        print(p)
    elif "--record" in args:
        i = args.index("--record")
        if len(args) > i + 2:
            record_event(args[i + 1], args[i + 2])
            print("recorded")
        else:
            print("usage: --record <type> <summary>")
    elif "--status" in args:
        state = _load_state()
        print(f"Device: {DEVICE_ID} ({DEVICE_NAME})")
        print(f"Platform: {PLATFORM}")
        print(f"Hive dir: {SYNC_DIR}")
        print(f"Last sync: {state.get('last_sync', 'never')}")
        print(f"Last actor: {state.get('last_device', 'none')}")
        print(f"Last event: {state.get('last_event', 'never')}")
        print(f"Events logged: {len(_iter_events())}")
    elif "--seed" in args:
        seed_identity()
        print("seeded")
    elif "--setup" in args:
        setup_startup()
    else:
        print("Harley Hive v2 — Borg Collective")
        print("Commands: --daemon | --serve | --sync | --brain | --record <type> <summary> | --status | --seed | --setup")


if __name__ == "__main__":
    main()