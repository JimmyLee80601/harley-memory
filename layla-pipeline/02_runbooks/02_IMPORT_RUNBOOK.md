# IMPORT + USAGE RUNBOOK — getting packs onto Layla / Local Dream
## Source: ld-guide.chino.icu/models, xororz/local-dream README, layla blog (verified)

## A. IMPORT A QNN PACK (the fast NPU lane)
1) Get the zip on the phone (copy over USB/ADB, or download).
2) Layla: image settings -> Local Dream model import -> pick the
   zip. OR standalone Local Dream app: Import button, same thing.
3) The app reads tier suffix (_8gen2) and markers. SD1.5 packs
   ship: 512x512 unet.bin + text_encoder.bin + vae.bin (+.patch).
   No SDXL / no V_PRED marker for our SD1.5 epsilon models.
4) Verify in the model list, then generate 512x512.

## B. IMPORT A RAW SAFETENSORS (CPU/GPU lane — no conversion)
- App accepts any SD1.5 safetensors ON DEVICE, converted in-app.
- MUST include VAE weights (RV6 V5.1 HyperVAE, EpicRealism RC1 do).
- Slower than NPU (CPU/GPU, not Hexagon), fine for testing merges
  before burning a conversion night on the Dell.
- Older app versions merged LoRAs at import time on the CPU/GPU
  path; current behavior = bake the LoRA before importing. Follow
  the bake rule everywhere; never rely on import-time merging.

## C. BUILT-INS (zero work, good for side brand / testing)
Already downloadable in-app (CivitAI-sourced): Anything V5.0,
ChilloutMix, Absolute Reality, QteaMix, CuteYukiMix (SD1.5);
Illustrious v16 + CyberRealistic v10 (+DMD2 variants) are SDXL =
8 Gen 3+ only, useless on the S23, ignore them here.

## D. LAYLA MINI-APP SIDE (how a mini-app talks to this)
SDK (npm @layla-network/sdk v7.5.0, MIT):
  const models = await layla.images.getImageGenerationModels();
  // [{id, name, description}] — ONLY downloaded models appear;
  // call layla.images.generateImage(prompt, onProgress) returns
  // a data-URI string (or null);
  // optional args: img2img_base64 (data:image/png;base64,...),
  // modelId (select one from getImageGenerationModels()),
  // options {signal} for abort (LaylaAbortError).
Mini-apps CANNOT set steps/CFG/seed/scheduler. The engine default
applies (Local Dream default: 20 steps, CFG 7.5, dpm). Prompt
quality = everything in this lane. See 04_layla_miniapp/.

## E. STANDALONE LOCAL DREAM HTTP API (full control, advanced)
Local Dream exposes a local backend on 127.0.0.1:8081 (SSE):
  POST /generate  {prompt, negative_prompt, steps(20), cfg(7.5),
    seed, scheduler: dpm|dpm_karras|dpm_sde(+karras)|euler_a(+karras)|
    euler(+karras)|lcm, size, width, height, use_opencl(bool),
    show_diffusion_process+stride, image/mask (base64 -> img2img /
    inpaint), denoise_strength, aspect_ratio (SDXL only)}
  complete event -> raw RGB bytes (not PNG) -> wrap before saving.
  POST /tokenize -> check prompt against the 77-token CLIP cap.
USE CASE: our future batch/queue mini-app or Tasker automation
drives this directly for unprompted-capped work.

## F. RUNTIME VERSION LAW
App runtime now ships QNN SDK 2.39. Conversion stays pinned to
QNN SDK 2.28. Do not "helpfully" upgrade the converter or mix
versions — the packs are built FOR the app's runtime. Keep 2.28
installed on the Dell and leave it alone.