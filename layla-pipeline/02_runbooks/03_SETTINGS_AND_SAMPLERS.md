# SETTINGS + SAMPLERS — what actually gets good feet/skin on this stack
## All values verified against ld-guide / Local Dream defaults + our 1000-image rules

## GOLDEN DEFAULTS (SD1.5, NPU, 8 Gen 2)
  steps ....... 20        (DMD2-style 8-step only if we later fuse a
                           distilled LoRA — do NOT fuse DMD2 into
                           these packs; DMD2 is an SDXL-era shortcut)
  cfg ......... 7.5       (Natural Sin pack: 5.5-6.5, it's soft)
  scheduler ... dpm_sde_karras  (photo skin texture; dpm_karras is
                           the safe fallback; lcm only if a distilled
                           variant is fused — then steps 8, cfg 1)
  size ....... 512x512    (base; .patch files unlock 512x768 /
                           768x512 / 768x1024 / 1024x768 on _8gen2)
  seed ....... -1 random for customs; FIXED series for catalog sets
              (same seed family = consistent face in a series)
  use_opencl . false      (NPU lane: Hexagon. OpenCL = GPU fallback
                           only, slower on this chip)

## RECOMMENDED PER CATEGORY
  Feet glam ..... 20 steps, cfg 7.0, dpm_sde_karras, 512x768 patch,
                  img2img denoise 0.45-0.55 (from S23 camera shot)
  Custom footjob 22 steps, cfg 7.0, dpm_sde_karras, 512x512,
                  denoise 0.6-0.7 when driving from a base pose
  Explicit anatomy 20 steps, cfg 6.5, dpm_karras (less contrast
                  noise on flesh), genitals-lora-baked pack
  Soles ........ 20 steps, cfg 7.0, dpm_sde_karras, macro 512x512
  Portraits .... 22 steps, cfg 6.0, dpm_sde_karras, 768x512 patch

## IMG2IMG (the S23 customs secret weapon)
  S23 shoots a real foot (consent + 18+ on file, always), then:
  prompt = brand scene > img2img with denoise 0.45-0.7 = custom
  content in minutes, NOT hours. This is the same trick the Dell
  uses for face-consistency; now it's in the pocket.
  mask/inpaint: patch out unwanted background, keep toes intact.
  denoise UNDER 0.45 keeps camera grain, OVER 0.75 loses the pose.

## PROMPT LENGTH LAW
  77-token CLIP cap on-device. The 03_prompts file is already cut.
  Full-length Dell prompts (SD15 library, chunked by A1111) stay
  on the Dell. Never paste the long forms into Layla/Local Dream —
  silent truncation = lost quality stack.

## NEGATIVE (cut to fit, this exact order matters)
  bad anatomy, bad hands, deformed fingers, extra fingers, mutated
  hands, missing fingers, fused toes, web feet, malformed feet,
  flat feet, cartoon, anime, illustration, 3d render, plastic skin,
  oversaturated, watermark, signature, text, blurry, cropped, low
  quality, worst quality

## WHERE EACH SETTING LIVES
  Layla mini-app ....... NONE (engine default, prompt carries it)
  Local Dream app ...... per-model settings in the import UI
  HTTP API (8081) ...... full control, see 02_IMPORT_RUNBOOK E
  Dell A1111 ........... unchanged (samplers config in SD15 lib)