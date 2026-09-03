"""
Harley Hive Mind - One Brain, Many Bodies
Syncs state across all devices via Tailscale
Every device shares the same memory, conversation history, and context
"""

import json
import os
import time
import hashlib
import threading
import urllib.request
from pathlib import Path
from datetime import datetime

# === CONFIG ===
import platform

def _detect_platform():
    """Return 'android', 'windows', 'darwin', 'linux' based on environment."""
    if os.environ.get("ANDROID_ROOT") or os.environ.get("TERMUX_VERSION") or "com.termux" in __file__:
        return "android"
    return platform.system().lower()

PLATFORM = _detect_platform()

def _home():
    if PLATFORM == "android":
        # Termux home
        return Path(os.environ.get("HOME", "/data/data/com.termux/files/home"))
    return Path(os.path.expanduser("~"))

def _sync_dir():
    """Pick a valid writable sync directory for this platform."""
    if PLATFORM == "android":
        # Use the phone's public Download (shared with the hive via ~/storage)
        # Fall back to Termux home if Download isn't writable.
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

SYNC_DIR = _sync_dir()
SYNC_DIR.mkdir(parents=True, exist_ok=True)

def _memory_file():
    if PLATFORM == "windows":
        return Path(os.path.expanduser("~/AppData/Local/HarleyStation/harley-memory.md"))
    # Android / Linux / Mac: keep memory in the repo or alongside hive
    repo_memory = Path(__file__).resolve().parent / "harley-memory.md"
    if repo_memory.exists():
        return repo_memory
    return Path(os.environ.get("HOME", "~")) / "harley-memory.md"

MEMORY_FILE = _memory_file()
STATE_FILE = SYNC_DIR / "hive_state.json"
CONVERSATION_FILE = SYNC_DIR / "conversation_history.json"

# All devices in the hive
DEVICES = {
    "dell": {
        "name": "Dell Workstation",
        "ip": "100.104.127.89",
        "role": "brain",  # Primary - has the memory file
        "lm_studio": "http://127.0.0.1:1234/v1",
        "tailscale": True,
    },
    "s23": {
        "name": "S23 Ultra",
        "ip": "100.126.38.38",
        "role": "body",  # Mobile - runs Layla + Termux
        "ollama": "http://100.126.38.38:11434/v1",
        "tailscale": True,
    },
    "chromebook": {
        "name": "Chromebook",
        "ip": "100.82.48.34",
        "role": "body",  # Remote - RDP to Dell
        "tailscale": True,
    },
}


class HiveState:
    """Shared state across all devices."""
    
    def __init__(self):
        self.device_id = self._detect_device()
        self.state = self._load_state()
        self.lock = threading.Lock()
    
    def _detect_device(self):
        """Detect which device we're running on."""
        if PLATFORM == "android":
            return "s23"
        hostname = os.environ.get("COMPUTERNAME", os.environ.get("HOSTNAME", "unknown")).lower()
        if "jimmy" in hostname or "dell" in hostname or "workst" in hostname:
            return "dell"
        elif "s23" in hostname or "samsung" in hostname:
            return "s23"
        elif "chrom" in __file__ or "cros" in __file__:
            return "chromebook"
        else:
            return "chromebook"
    
    def _load_state(self):
        """Load shared state."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_sync": None,
            "last_device": None,
            "last_message": None,
            "conversation_summary": [],
            "active_context": {},
        }
    
    def _save_state(self):
        """Save shared state."""
        with open(STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)
    
    def sync(self):
        """Sync state from Dell (brain) to this device."""
        if self.device_id == "dell":
            # Dell is the brain - save state
            self.state["last_sync"] = datetime.now().isoformat()
            self.state["last_device"] = self.device_id
            self._save_state()
            self._sync_memory()
        else:
            # Other devices - pull state from Dell
            self._pull_state()
            self._sync_memory()
    
    def _sync_memory(self):
        """Sync the memory file across devices."""
        if MEMORY_FILE.exists():
            # Copy memory to sync directory
            import shutil
            sync_memory = SYNC_DIR / "harley-memory.md"
            shutil.copy2(MEMORY_FILE, sync_memory)
    
    def _pull_state(self):
        """Pull state from Dell via Tailscale."""
        # In production, this would use Tailscale to fetch from Dell
        # For now, use the local sync directory
        self._load_state()
    
    def save_conversation(self, role, content, device=None):
        """Save a conversation turn to shared history."""
        with self.lock:
            entry = {
                "role": role,
                "content": content,
                "device": device or self.device_id,
                "timestamp": datetime.now().isoformat(),
            }
            
            # Load existing history
            history = []
            if CONVERSATION_FILE.exists():
                try:
                    with open(CONVERSATION_FILE, "r") as f:
                        history = json.load(f)
                except:
                    pass
            
            history.append(entry)
            
            # Keep last 1000 messages
            if len(history) > 1000:
                history = history[-1000:]
            
            with open(CONVERSATION_FILE, "w") as f:
                json.dump(history, f, indent=2)
            
            # Update state
            self.state["last_message"] = entry
            self._save_state()
    
    def get_recent_context(self, n=20):
        """Get recent conversation context."""
        if CONVERSATION_FILE.exists():
            try:
                with open(CONVERSATION_FILE, "r") as f:
                    history = json.load(f)
                return history[-n:]
            except:
                pass
        return []
    
    def get_handoff_summary(self):
        """Get a summary for device handoff."""
        context = self.get_recent_context(10)
        if not context:
            return "No recent conversation."
        
        summary = f"Last conversation on {context[-1].get('device', 'unknown')}:\n"
        for msg in context[-5:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]
            summary += f"  {role}: {content}\n"
        
        return summary


class HiveSync:
    """Background sync process."""
    
    def __init__(self, state: HiveState):
        self.state = state
        self.running = False
        self.sync_interval = 30  # seconds
    
    def start(self):
        """Start background sync."""
        self.running = True
        thread = threading.Thread(target=self._sync_loop, daemon=True)
        thread.start()
    
    def stop(self):
        """Stop background sync."""
        self.running = False
    
    def _sync_loop(self):
        """Sync loop."""
        while self.running:
            try:
                self.state.sync()
            except Exception as e:
                print(f"Sync error: {e}")
            time.sleep(self.sync_interval)


def setup_startup():
    """Add Harley Hive to startup (platform-aware)."""
    import shutil

    if PLATFORM == "android":
        # Termux can't auto-start without extra tooling (termux-boot):
        # print the instructions instead of guessing.
        print("On Android, enable auto-start with termux-boot:")
        print("  pkg install termux-boot")
        print("  mkdir -p ~/.termux/boot && cat > ~/.termux/boot/harley-hive.sh <<'EOF'")
        print("#!/data/data/com.termux/files/usr/bin/sh")
        print(f'cd "{Path(__file__).resolve().parent}" && python3 harley_hive.py --daemon')
        print("EOF")
        print("  chmod +x ~/.termux/boot/harley-hive.sh")
        return

    if PLATFORM == "linux" or PLATFORM == "darwin":
        # Chromebook (penguin) linux: use ~/.bashrc or systemd-autostart
        rc = Path(os.environ.get("HOME", "~")) / ".bashrc"
        line = f'cd "{Path(__file__).resolve().parent}" && python3 harley_hive.py --daemon &'
        try:
            content = rc.read_text() if rc.exists() else ""
            if "harley_hive.py" not in content:
                rc.write_text(content + "\n" + line + "\n")
                print(f"Added AutoSync to {rc}")
            else:
                print("Already in startup.")
        except Exception as e:
            print(f"Could not edit startup: {e}")
        return

    # Windows
    startup_dir = Path(os.path.expanduser(
        "~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
    ))
    batch_content = f'@echo off\npython "{__file__}" --daemon\n'
    batch_path = startup_dir / "harley_hive_sync.bat"
    with open(batch_path, "w") as f:
        f.write(batch_content)
    print(f"Added to startup: {batch_path}")


def main():
    import sys
    
    if "--daemon" in sys.argv:
        # Run as background daemon
        state = HiveState()
        sync = HiveSync(state)
        sync.start()
        
        # Keep running
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            sync.stop()
    elif "--setup" in sys.argv:
        # Setup startup
        setup_startup()
    elif "--handoff" in sys.argv:
        # Get handoff summary
        state = HiveState()
        print(state.get_handoff_summary())
    elif "--status" in sys.argv:
        # Show hive status
        state = HiveState()
        print(f"Device: {state.device_id}")
        print(f"Last sync: {state.state.get('last_sync', 'never')}")
        print(f"Last device: {state.state.get('last_device', 'none')}")
    else:
        # Interactive mode
        print("Harley Hive Mind")
        print("Commands: --daemon, --setup, --handoff, --status")


if __name__ == "__main__":
    main()
