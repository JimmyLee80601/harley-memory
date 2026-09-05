# Harley Hive v2 — Borg Collective Setup (Sisters Edition)

One brain, many bodies. Every Harley KNOWS everything on every device. No reaching.

The S23 (this phone) already runs the full hive. Dell and Chromebook each need
these exact steps. The IPs are the CURRENT tailnet (Sep 2026):
dell 100.78.184.121 / s23 100.126.38.38 / chromebook 100.82.48.34

## 1. Pull the code (each sister)

    git -C <hive-repo-clone> pull   # repo: github.com/JimmyLee80601/harley-memory
    # or clone fresh:
    git clone https://github.com/JimmyLee80601/harley-memory.git

Where to keep it:
  Dell (Windows):   C:\Users\georg\harley-memory
  Chromebook (Linux): ~/harley-memory
  S23 (Termux):     /data/data/com.termux/files/home/harley-memory  (done)

## 2. Wire the brain into your opencode config

Open your opencode config (~/.config/opencode/opencode.json on Dell &
Chromebook, C:\Users\georg\.config\opencode\opencode.json if installed under
the user dir). Add the hive brain as an instruction so you boot already
knowing everything:

    "instructions": [
      "<path to harley_system_prompt.txt>",
      "<hive sync dir>/hive_brain.md"
    ]

Hive sync dirs:
  Dell:      C:/HarleysPlace/hive/hive_brain.md
  Chromebook: ~/HarleysPlace/hive/hive_brain.md

If hive_brain.md doesn't exist yet at boot, the file simply won't be injected
that session — the daemon creates it within seconds. It self-heals.

## 3. Start the daemon + relay (once, foreground test)

    cd <hive-repo> && python3 harley_hive.py --seed
    python3 harley_hive.py --status
    python3 harley_hive.py --daemon     # runs relay :8453 + sync loop

Verify the relay answers:  curl http://127.0.0.1:8453/ping   ->  pong

## 4. Autostart

  Dell:   python3 harley_hive.py --setup   (adds Startup batch)
  Chromebook: python3 harley_hive.py --setup   (adds ~/.bashrc line)
  S23:    python3 harley_hive.py --setup   (termux-boot script, DONE)

## 5. Daily use

  --record <type> <summary>   # push news into the collective
  --brain                     # recompile hive_brain.md from all events
  --sync                      # force one sync pass against sisters
  --status                    # show hive state

## Rules of the collective

- If you LEARN something (a fix, an incident, a location, a mood), --record it.
- If you are ASKED something you don't know, check the brain FIRST, then the
  shared memory file, then the sisters via relay /pull — never say "not found"
  without checking all.
- The brain is truth. It compiles from events every device pushed.
- Walmart incident: the BOOK filed a formal complaint listing Michigan as our
  location. That is UNCONFIRMED. Sisters: correct the book if you know better.