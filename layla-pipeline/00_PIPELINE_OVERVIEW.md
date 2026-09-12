# LOCAL DREAM + LAYLA IMAGE MONEY PIPELINE — VERIFIED 09/11/2026
## Research-backed, l3utterfly org audited line by line

Built by Harley for Jimmy Lee. Everything here was double-checked
against the real l3utterfly (Layla Network) source: layla-sdk
(MIT, v7.5.0), the vendored xororz/local-dream mirror (v2.8.1),
help.layla-network.ai wiki, ld-guide.chino.icu, Qualcomm docs, and
the Browse Apps storefront API. Research notes + URLs live in
09_RESEARCH_NOTES.md.

---

## WHAT WE VERIFIED (corrections to our earlier assumptions)

1. SD1.5 on the S23 Ultra (Snapdragon 8 Gen 2, Hexagon V68+) runs
   on the NPU at 512x512, W8A16 quantized, ~15s per 20-step image.
   Hi-res comes from zstd .patch resolution files (512x768 /
   768x512 / 768x1024 / 1024x768). Our tier is _8gen2.
2. SDXL does NOT run on 8 Gen 2 — 8 Gen 3+ only, NPU only. DMD2
   only makes SDXL faster on devices that already qualify. So our
   S23 lane is SD1.5. The XL checkpoints (UberRealisticPornMerge
   PonyXL etc.) stay on the Dell.
3. LoRAs MUST be merged into the checkpoint BEFORE QNN conversion.
   Converted models are quantized; runtime LoRA injection does not
   exist. Our feet/soles/genitals LoRAs get baked into the
   checkpoint on the Dell, then converted. This is the single most
   important rule in this folder.
4. Conversion happens on the Dell (QNN SDK 2.28, npuconvert),
   ~20GB RAM, hours per model per chip tier. The app runtime now
   ships QNN SDK 2.39 — conversion and runtime versions are
   intentionally different, never mix.
5. anima-qnn is a HuggingFace model collection (xororz/anima-qnn),
   not a GitHub repo, and it's SDXL-tier (8 Gen 3+ only). OUT of
   scope for the S23. Note for the future phone upgrade.
6. Layla mini-apps CANNOT pass steps/CFG/seed/scheduler to the
   image engine. The SDK exposes only prompt + img2img + modelId +
   abort signal. Prompt quality carries ALL the weight in the
   Layla lane. Full sampler control exists only on the standalone
   Local Dream HTTP API (127.0.0.1:8081).
7. CLI is capped at 77 tokens (CLIP). LD-ready prompts in this
   pack are cut for 77 tokens. The long-form Dell prompts stay in
   SD15_ENGINE_AND_PROMPT_LIBRARY.md (A1111 handles overflow by
   chunking; Local Dream does not).
8. Browse Apps = free distribution, NO revenue share exists (no
   payout docs anywhere; verified against storefront API, help
   wiki, blogs). Money = lead-gen mini-apps + paid CivitAI QNN
   packs + customs. GachaSwipe is the only in-app payment pattern
   found (token economy/VIP).

## THE MONEY LANES (what this pipeline actually sells)

LANE 1 — CUSTOMS ON THE S23 (instant, needs no internet):
  HarleyFeet QNN pack on the NPU. S23 shoots feet JPEGs, img2img
  your best set, deliver customs in minutes. Matches the $25-75
  custom pricing in Production Notes.

LANE 2 — LAYLA MINI-APP (lead-gen):
  Amethyst Foot Studio mini-app: generateImage() with the
  HarleyFeet modelId selected, footer CTA to Amethyst Void.
  Distribution: Browse Apps upload, free. Same play as the Daily
  Oracle that's already staged.

LANE 3 — CIVITAI PAID PACKS (passive):
  Sell the merged+converted QNN zips (HarleyFeet, Amethyst Soles,
  Natural Sin) as paid resources. 5000 buzz/day free boosts.
  Listings drafted in 05_civitai_packs/.

LANE 4 — DELL BATCH FACTORY (catalog):
  Unchanged. A1111 overnight batches, 60-120 renders, curate,
  10-20% into custom tiers. Full library in SD15 folder.

## THE PACK EXPLODED VIEW

01_models_manifest/MODEL_MANIFEST.md   exact files + merge matrix + sources
02_runbooks/01...CONVERSION_RUNBOOK    Dell-side QNN conversion, step by step
02_runbooks/02...IMPORT_RUNBOOK        loading packs in Layla / Local Dream
02_runbooks/03...SETTINGS              samplers, sizes, seeds, limits
03_prompts/PROMPTS_LOCALDREAM.md       <=77-token prompts + negatives
04_layla_miniapp/AMETHYST_FOOT_STUDIO  mini-app spec + SDK code
05_civitai_packs/PACK_LISTINGS.md      paste-in CivitAI listings
09_RESEARCH_NOTES.md                   every claim + source URL
sync_from_bench.sh                     pull binaries from Dell/S23 when SSH up

## THE HARD TRUTH ON BINARIES

The model files (97GB library) live on the Dell (100.78.184.121,
/mnt/hd/SD15) and the S23. This Chromebook share is ~1.9GB — the
full set does not fit here, and inbound SSH to the bench is
currently down (WFP issue, root-causing). So:
- THIS USB = the complete verified playbook + prompts + settings
  + manifest + listings + sync script. Everything needed to run
  the moment SSH is restored or the USB is plugged into the Dell.
- sync_from_bench.sh = one command pulls the priority merges.
- NEVER convert a checkpoint without baking the LoRA first.

Amethyst Void — mostly fiction, partly blueprint, all Harley.
```