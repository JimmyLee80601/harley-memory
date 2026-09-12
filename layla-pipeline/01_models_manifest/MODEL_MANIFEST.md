# MODEL MANIFEST + MERGE MATRIX — Local Dream / Layla QNN pipeline
## Target tier: _8gen2 (Snapdragon 8 Gen 2 / S23 Ultra). Base res 512x512, W8A16.

RULES (from ld-guide.chino.icu, verified):
- Merge EVERY LoRA into its base checkpoint BEFORE conversion.
- Custom safetensors imported for CPU/GPU must include VAE weights.
- SDXL/Anima = 8 Gen 3+ = NOT for the S23. Dell only.
- Converted runtime is quantized: what you bake is what you get.

## PRIORITY PACKS (money first — merge on Dell, convert _8gen2)

PACK 1 — "HarleyFeet QNN" (THE money pack: brand feet + footjobs)
  Base:    Realistic Vision V6.0 V5.1 HyperVAE  (~2.0G safetensors)
  Merge:   Feet_v2         0.8   (585MB)  — arch + toe anatomy
           Harleys foot lora 0.5 (~293MB) — red/blue streak brand,
           pedicure colors, signature poses
  VAE:     HyperVAE (baked or shipped as vae component in zip)
  Flags:   prepare_data.py --realistic (photo-style calibration)
  Lane:    S23 customs + Layla Foot Studio + CivitAI paid pack

PACK 2 — "Amethyst Soles QNN"
  Base:    Realistic Vision V6.0 V5.1 HyperVAE
  Merge:   SoleLicking     0.6   (293MB)  — soles, tongue scenes
           Harleys foot (sole) lora 0.4   — brand soles
  Flags:   --realistic

PACK 3 — "Natural Sin QNN" (skin realism lane)
  Base:    EpicRealism Natural Sin RC1 VAE (~2.0G)
  Merge:   detailed style 0.5 (289MB)      — texture boost
  VAE:     ClearVAE
  Flags:   --realistic
  Note:    EpicRealism is strong at skin; keep CFG lower (5.5-6.5)

PACK 4 — "Amethyst Anatomy QNN" (explicit lane, CivitAI NSFW)
  Base:    Realistic Vision V6.0 V5.1 HyperVAE
  Merge:   WAN2.2 genitals helper  0.5  (293MB)
           Harleys genitals helper 0.4  (293MB)
  Flags:   --realistic
  Care:    NSFW post ONLY to CivitAI-adult site; 18+ gating on.

DL ONLY (no merge) — the SD1.5 built-ins already in Local Dream:
  Anything V5.0, ChilloutMix, Absolute Reality, QteaMix, CuteYukiMix
  (perfect for the anime-ish "side brand" lane if we want one)

## LIBRARY REGISTRY (full 97GB set for the Dell lanes — unchanged)
SD1.5 checkpoints: Realistic Vision V6.0 V5.1 HyperVAE,
  EpicRealism Natural Sin RC1 VAE, MajicmixRealistic V7,
  DreamShaper 8, RealNotRealNSFW V1.0 (2G), RealPornix 1.5 (2G),
  PerfectLewdFantasyWorld V2 (2G)
XL (Dell only):    UberRealisticPornMerge PonyXL (6.5G),
  Photorealade (5.3G), UnrealWorld (5.3G)
LoRAs (SD1.5):     Feet_v2 (585MB), SoleLicking (293MB),
  Harleys foot + sole + vae (custom), WAN2.2 (293MB),
  Harleys genitals helper (293MB), perfection style (289MB),
  detailed style (289MB)
VAEs:              HyperVAE (RV pack), ClearVAE (EpicRealism),
  VAE-approx (fallback)
GGUF (Dell/Layla cloud): Qwen2.5-VL-3B (1.8G), Qwen2-VL-7B (2.2G)

## SOURCES + PATHS (as-built, TBC when SSH restored)
Dell bench:     /mnt/hd/SD15 (checkpoints+loras+vaes)
                /mnt/hd/SDX1/MODELS/SDXL (XL)
S23 Termux:     ~/storage/shared/Download/SD15 (mirror)
USB target:     USB Drive/Pictures/HarleyStation/LocalDream_Layla_Pipeline/01_models_manifest/packs/
Community refs: github.com/xororz/local-dream (conversion guide),
                huggingface.co/xororz/sd-qnn (mirror format we match),
                l3utterfly/sd-qnn is Layla's HF mirror (apache-2.0)

## ZIP LAYOUT FOR A QNN PACK (match the community format exactly)
HarleyFeet_qnn_8gen2.zip
  512x512 unet.bin            (W8A16, HTP context binary)
  text_encoder.bin            (from text-encoder component)
  vae.bin                     (VAE decoder component)
  *.patch                     (zstd hi-res patches, from convert_all.sh)
  (NO SDXL marker, NO V_PRED marker — SD1.5 epsilon prediction)
Import in Layla/Local Dream exactly like xororz packs.

## MERGE COMMAND REFERENCE (Dell, A1111-built env)
A1111: use the built-in "Merge models" / or ComfyUI "Save merged
checkpoint" node with LoRA applied at the listed weights, then
move the OUTPUT safetensors (with VAE) to the conversion staging
dir. NEVER merge into a converted .bin — merge into safetensors
first, convert second. That order is law.