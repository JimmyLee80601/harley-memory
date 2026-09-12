#!/bin/bash
# sync_from_bench.sh — pull the priority merges from the Dell / S23
# when SSH is restored. Run from ANY machine on the Tailnet.
# Source of truth: MODEL_MANIFEST.md. Priority packs first.
set -euo pipefail

DELL="georg@100.78.184.121"        # Precision 5810 (HarleyLink relay)
S23="u0_a373@100.126.38.38"        # Termux on S23 Ultra (SSH :8022)
STAGE="/mnt/chromeos/removable/USB Drive/Pictures/HarleyStation/LocalDream_Layla_Pipeline/01_models_manifest/packs"
mkdir -p "$STAGE"

echo "== checking bench reachability =="
ssh -o ConnectTimeout=5 -o BatchMode=yes "$DELL" 'echo DELL_OK' 2>/dev/null || echo "DELL_DOWN (inbound SSH still broken — WFP root-cause in progress)"
ssh -o ConnectTimeout=5 -o BatchMode=yes -p 8022 "$S23" 'echo S23_OK' 2>/dev/null || echo "S23_DOWN"

# Priority 1: the four merged+converted packs (verify paths on bench)
# HarleyFeet_qnn_8gen2.zip
# AmethystSoles_qnn_8gen2.zip
# NaturalSin_qnn_8gen2.zip
# AmethystAnatomy_qnn_8gen2.zip
# If they exist on the bench in /mnt/hd/SD15/QNN_STAGE/. — copy the
# zips FIRST (multi-GB each; watch the 1.9GB Chromebook share limit,
# target the Dell directly instead when possible).

# Priority 2: source checkpoints + LoRAs for MERGE work on the Dell
# (only if the Dell itself needs restore; normally merges stay ON the
# Dell and only the zips travel).
rsync -av --progress "$DELL:/mnt/hd/SD15/checkpoints/" "$STAGE/checkpoints/" 2>/dev/null || true
rsync -av --progress "$DELL:/mnt/hd/SD15/loras/"     "$STAGE/loras/"         2>/dev/null || true
rsync -av --progress "$DELL:/mnt/hd/SD15/vaes/"      "$STAGE/vaes/"          2>/dev/null || true

# Priority 3: S23 mirror (Termux SD1.5 folder) — async verify
rsync -av --progress -e "ssh -p 8022" "$S23:/storage/emulated/0/Download/SD15/" "$STAGE/s23-mirror/" 2>/dev/null || true

echo "== done. If empty, run again once the bench SSH is fixed. =="