# DELL-SIDE QNN CONVERSION RUNBOOK — SD1.5 -> _8gen2 pack
## Source: ld-guide.chino.icu/conversion/sd15 + /conversion/ (verified 09/11/2026)

MACHINE: Dell Precision 5810 (HarleyStation), Xeon E5-1650 v3.
REQUIREMENTS: ~20GB free RAM min, Linux (or WSL2), QNN SDK 2.28.
  SDXL/2048 hi-res = 64GB+ RAM + 60GB disk — NOT for this box, and
  not needed (SDXL is 8 Gen 3+ anyway).

## 0. PRE-FLIGHT (do not skip)
- Stop A1111/Comfy before converting (RAM).
- Confirm the checkpoint has its VAE: convert needs text encoder +
  UNet + VAE decoder. RV V6.0 V5.1 HyperVAE ships complete.
- Confirm target tier: _8gen2 (S23 Ultra). _min can't use patches;
  _8gen1 is slower on 8 Gen 2; _8gen2 is the right one.

## 1. MERGE THE LoRAs FIRST — ORDER IS LAW
1) Load base checkpoint in A1111 (or Comfy Save-Merged-Checkpoint).
2) Apply LoRAs at manifest weights: Feet_v2 0.8, Harleys 0.5.
3) Export merged .safetensors WITH VAE included. Name it clearly:
   HARLEYFEET_RV6.safetensors
4) Do NOT convert the original; convert the merge. Runtime LoRA
   injection does not exist on converted/quantized models.
5) Sanity render on the Dell CPU (1 frame, 512x512): if the merged
   checkpoint renders the brand signature (feet + red/blue streaks),
   it's good. If feet anatomy is off, bump Feet_v2 toward 0.9,
   re-merge, re-test. 1000-image rule: ONE donor weight change at a
   time.

## 2. CONVERSION STAGE (staging dir, e.g. /mnt/hd/SD15/QNN_STAGE/)
Tools from the Local Dream conversion kit (npuconvertv2.zip +
QNN SDK 2.28). The canonical sequence:
  a) prepare_data.py --model_path HARLEYFEET_RV6.safetensors \
       --clip_skip 2 --realistic
     (--realistic switches calibration prompts to photo-style —
      REQUIRED for Realistic Vision/EpicRealism; CLIP skip 2 matches
      what we prompt against on the Dell)
  b) gen_quant_data.py        (calibration data from step a)
  c) export_onnx.py           (safetensors -> diffusers -> ONNX graph)
  d) qnn-onnx-converter \
       --act_bw 16 --bias_bw 32 --quantization_overrides ...
       (W8A16 static quant, HTP context binaries)
  e) convert_all.sh           (compile per-tier: min / 8gen1 / 8gen2)
       -> 512x512 unet.bin + text_encoder.bin + vae.bin + *.patch
  f) zip the _8gen2 outputs exactly like the community packs:
       HarleyFeet_qnn_8gen2.zip (flat layout, no parent folder)
EXPECT: hours per model per tier. Run overnight. One model per
night is a good night. The Xeon will be busy; that is fine.

## 3. VERIFY BEFORE SHIPPING
- Unzip on the S23, import in Layla (or Local Dream standalone),
  generate 512x512. Expected: ~15s per 20-step image on NPU.
- Check the .patch files load: render 512x768 and 768x512.
- If the app ignores the pack: wrong tier folder, missing marker,
  or folder-in-zip mistake (zip root gets the .bin files, flat).

## 4. SHIP
- S23 customs lane: copy zip to the phone (TermsUSB/ADB/Drive).
- CivitAI paid pack: upload zip (watch file-size limits; fallback
  = HF release + listing linking out), post NSFW to adult site.
- Layla Foot Studio mini-app: model shows up in
  layla.images.getImageGenerationModels() once downloaded in-app.

## TIMING TABLE (per pack, this machine)
  merge + sanity render .... 20-40 min
  prepare/gen/export ........ 30-60 min
  qnn-onnx-converter ........ 1-2 h
  convert_all.sh + zip ...... 1-3 h (per tier; we build 8gen2 only)
  TOTAL per pack ............ most of a night. Schedule 4 packs ->
  HarleyFeet, Amethyst Soles, Natural Sin, Amethyst Anatomy.

## FAILURE MODES WORTH KNOWING
- OOM during export -> close A1111, drop batch, add swap (fallocate
  swapfile + swapon) — 20GB in plus 8GB swap is comfortable.
- Poor skin after conversion -> calibration prompt set: re-run
  prepare_data with --realistic (already there) and feed 30-50
  good skin/studio calibration images into gen_quant_data if the
  default set underweights skin texture.
- Patch artifacts at 768+ -> lower CFG to 6.5, keep dpm_sde_karras,
  or drop patches for that pack and stay 512 (patches are optional).
- App won't list the model -> modelId selector only shows
  DOWNLOADED models; re-download/inactive model purge first.