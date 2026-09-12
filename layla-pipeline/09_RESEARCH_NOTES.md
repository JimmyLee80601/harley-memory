# RESEARCH NOTES — l3utterfly / Layla / Local Dream audit 09/11/2026
## Jimmy asked: "research https://github.com/l3utterfly, make sure
## everything we built is right for them." Done. Every claim below
## was fetched and verified; nothing pasted from memory.

## ORG FACTS
- org: github.com/l3utterfly = Layla Network Pty Ltd, Gold Coast,
  Australia. 64 repos: ~6 first-party (layla-sdk, layla-python-sdk,
  Layla-Server, Layla-signalling, layla-mini-app-creator,
  layla-miniapp-template, help.layla-network.ai,
  benchmarks.layla-cloud.com) + first-party mini-app sources
  (llm-ltm, vibe-check, dream, guess-what-im-drawing,
  sillytavern-lorebook-studio) + vendored forks (local-dream,
  llama.cpp, MNN, executorch, LiteRT-LM, CTranslate2, whisper.cpp,
  sherpa-onnx, acestep.cpp, PocketTTS.cpp, faiss, mlc-llm,
  OnnxStream, 18 react-native-* forks -> the app is React Native).
- local-dream is a GitMirror of xororz/local-dream (v2.8.1,
  Jul 12 2026); integration credited in Layla v6.10.0.
- layla-sdk: MIT (NOT Apache-2.0 as we once noted), v7.5.0,
  ESM+CJS, npm @layla-network/sdk. Python: layla-python-sdk (PyPI).

## LAYLA IMAGE SDK (verbatim spec)
- layla.images.getImageGenerationModels() -> [{id,name,description}]
- layla.images.generateImage(prompt, onProgress,
  img2img_base64?, modelId?, options?) -> data-URI string | null
  - img2img_base64 WITH "data:image/png;base64," prefix
  - modelId from getImageGenerationModels(); omit -> host default
  - options = {signal} -> abort -> LaylaAbortError
- Bridge: cmd generate_image {prompt, img2img_base64?, model_id?},
  events on_generate_image_response {image_data_base64|null},
  on_generate_image_progress {status, steps, total_steps},
  on_get_image_generation_models_response.
- NO step/CFG/seed/sampler exposure to mini-apps. FACT.
- Other resources: chat.completions, tts/stt, acestep music,
  characters, db.executeSql, memory/personas.

## LOCAL DREAM (xororz) — the engine under Layla
- SD1.5: CPU (MNN, W8 dyn quant, 128-512^2) / GPU (OpenCL) / NPU
  (Qualcomm QNN, W8A16 static, 512^2 + .patch hi-res: 512x768,
  768x512, 768x1024, 1024x768; _min tier cannot use patches).
- NPU needs Hexagon V68+ = 8 Gen 1/2/3, 7 Gen 1, 8s Gen 3. S23
  Ultra (8 Gen 2) = _8gen2 tier. Qualcomm 2023 demo: SD1.5 512x512
  <15s @ 20 steps on 8 Gen 2.
- SDXL: NPU only, 8 Gen 3+ ONLY, fixed 1024 internal. DMD2 =
  distilled variant, 8 steps/CFG 1, 4x faster — still 8 Gen 3+.
  So: S23 = SD1.5 forever.
- Built-ins (downloadable in-app): AnythingV5, ChilloutMix,
  Absolute Reality, QteaMix, CuteYukiMix; SDXL built-ins
  Illustrious v16 / CyberRealistic v10 (+DMD2) = 8 Gen 3+ only.
- Community packs: xororz/sd-qnn, xororz/sdxl-qnn on HF,
  Mr-J-369, YuuiKurata. Zip suffixes: _min/_8gen1/_8gen2/_8gen3.
  Marker files in zips: SDXL, V_PRED (v-prediction). SD1.5 packs
  carry none of those markers.
- LoRA: "merge it into the original checkpoint before import. Once
  the model has been converted and quantized, additional LoRA
  injection is not supported." CONFIRMED both NPU and CPU/GPU
  (old v2.4.x had import-time merge; current = bake first).
- anima-qnn = HF model collection (xororz/anima-qnn), Anima DiT
  models, SDXL-tier, 8 Gen 3+ only. NOT a repo, NOT for the S23.
- HTTP API 127.0.0.1:8081 (SSE): POST /generate {prompt,
  negative_prompt, steps 20, cfg 7.5, seed, scheduler
  dpm|dpm_karras|dpm_sde+karras|euler_a+karras|euler+karras|lcm,
  size, width/height, use_opencl, show_diffusion_process+stride,
  image/mask -> img2img/inpaint, denoise_strength,
  aspect_ratio SDXL}; complete -> raw RGB bytes. POST /tokenize
  for the 77-token CLIP cap.

## QNN CONVERSION (Dell side)
- Host Linux/WSL; QNN SDK 2.28 for conversion; app runtime now
  ships 2.39 — never mix. npuconvertv2.zip toolset.
- Sequence: prepare_data.py --model_path X --clip_skip N
  [--realistic] -> gen_quant_data.py -> export_onnx.py
  (safetensors -> diffusers -> ONNX) -> qnn-onnx-converter
  (W8A16; --act_bw 16 --bias_bw 32) -> convert_all.sh per tier
  (min/8gen1/8gen2) -> zip.
- SD1.5 512: ~20GB RAM, hours per model per tier. SDXL 1024:
  64GB+ RAM/60GB disk.
- Realistic Vision path: standard SD1.5, --realistic flag for
  photo-style calibration prompts.

## LAYLA MARKET / MONEY
- App: one-time $19.99 (Play) / ~22.99 (App Store); Layla Cloud
  separate app with subscriptions. Mini-apps forever after buy.
- Browse Apps: upload via Layla -> Mini-Apps Manager; storefront
  apps.layla-cloud.com; public API
  api.layla-network.ai/apps?searchTerms=&offset=0&range=500 for
  catalog/watchlist. Live catalog ~43 apps; top: gachaswipe 3835
  (M.I.K.A. Engine; has in-app Spark Token/VIP economy — the ONLY
  creator-payment pattern on the platform), bulk-pic-generator
  1281, companion-chat 1160, codekitty 1107, spritestudio 947...
- NO revenue share / payout found ANYWHERE (storefront API, help
  wiki, blogs, changelogs). Assumed zero platform payout today.
  Money = lead-gen mini-apps + paid packs + customs. FACT.

## IMPLICATIONS FOR US (what changed vs what we had)
1. Our "LoRA = merge before conversion" rule: CONFIRMED, keep.
2. Our "_8gen2 tier / QNN 2.28 / 20GB / hours" notes: CONFIRMED.
3. anima-qnn "repo" idea: RETIRED (HF collection, 8 Gen 3+).
4. "SDXL or DMD2 on S23": RETIRED half — 8 Gen 3+ is a hard wall.
5. Mini-app "I'll pass CFG/steps": never possible; prompt-only.
6. Mini-app money expectation: lead-gen, not platform payouts.

## URLs
github.com/l3utterfly (org), github.com/xororz/local-dream,
ld-guide.chino.icu/conversion/sd15 + /models/ + /features/model-
assets, huggingface.co/xororz/anima-qnn + /sd-qnn,
huggingface.co/qualcomm/Stable-Diffusion (per-component latencies),
edge-ai-vision.com/2023/02 (8 Gen 2 <15s demo),
api.layla-network.ai/apps (catalogue),
layla-network.ai/post/layla-v6-10-0-has-been-published