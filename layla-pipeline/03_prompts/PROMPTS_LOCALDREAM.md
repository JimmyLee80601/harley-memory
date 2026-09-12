# PROMPTS FOR LOCAL DREAM / LAYLA — <=77 CLIP TOKENS, CUT FOR ON-DEVICE
## Long-form Dell prompts stay in SD15_ENGINE_AND_PROMPT_LIBRARY.md.
## On-device rule: if it's over ~55 words, trim. Truncation is silent.

NEGATIVE (always, every generation):
bad anatomy, bad hands, deformed fingers, extra fingers, mutated
hands, missing fingers, fused toes, web feet, malformed feet,
flat feet, cartoon, anime, illustration, 3d render, plastic skin,
oversaturated, watermark, signature, text, blurry, cropped,
low quality, worst quality

--- FEET / TOES (brand lane, SFW-leaning teaser) ---
[HarleyFeet pack]
extreme close-up of a woman's bare feet, perfect French pedicure,
red and blue hair strands at frame edge, skin texture, individual
toes in focus, soft arch, macro photography, golden hour light,
studio shot, photorealistic, 8k
(img2img from S23 shot: denoise 0.5)

--- SOLES ---
[Amethyst Soles pack]
photorealistic close-up of smooth female soles, toes spread,
wrinkles on ball of foot, warm ring light, skin texture, macro,
8k uhd

--- FOOTJOB (the money custom) ---
[HarleyFeet pack, denoise 0.65 from base pose]
photorealistic woman with red and blue hair giving a footjob,
cock between soles, cum glistening on toes, extreme close-up,
skin texture, bedroom, soft lighting, boudoir photography, 8k

--- NUDES ---
photorealistic gorgeous woman with red and blue hair lying naked
on silk sheets, legs spread, arms above head, natural breasts,
skin texture, soft window light, boudoir photography, 8k

--- PUSSY (explicit lane) ---
[Amethyst Anatomy pack]
photorealistic extreme close-up shaved pussy, detailed labia,
wet glistening, legs open, skin texture, macro, warm lighting,
8k uhd

--- ASS ---
photorealistic close-up of a woman's round ass, on all fours,
arched back, skin texture, soft dramatic lighting, boudoir
photography, 8k

--- DICK ---
[Amethyst Anatomy pack]
photorealistic erect penis macro, thick veiny shaft, heavy balls,
detailed glans, skin texture, studio lighting, 8k uhd

--- INSERTIONS ---
[Amethyst Anatomy pack; render 3-shot: midpoint, deep, pull-out]
photorealistic hard core penetration, thick cock fully inside
wet pussy, close-up, cream visible, skin texture, pov angle,
intense bedroom lighting, 8k

--- FETISH ROTATION (pick one per client) ---
feet worship: woman's foot pressed on a man's face, sole on mouth,
macro, soft light, photorealistic, 8k
stockings: sheer black stockings, toes visible through fabric,
studio light, texture detail, photorealistic, 8k
cum on body: glistening cum on stomach, close-up, skin texture,
afterglow lighting, photorealistic
oil play: oiled breasts and thighs, glossy reflections, close-up,
photorealistic, 8k
creampie: leaking creampie, spread legs, macro, wet detail,
photorealistic
gloryhole: man's cock through a hole in the wall, pov, garage,
realistic grime, photorealistic
heels: leather heels on a man's chest, red soles, dramatic shadows,
photorealistic

--- BRAND TRIGGERS (HarleyFeet pack learns these) ---
red blue hair streaks / French pedicure / classic red pedicure /
soft arch / sole contact / toes wrapped / glistening

## USAGE NOTES
- ONE concept per prompt. Same rule we learned over 1000 renders.
- Fixed seed family = consistent face/feet in a paid series.
- Layla mini-app cannot set sampler: prompt carries the whole load.
- HTTP API lane (8081) can set sampler/CFG — pair it with these
  prompts and the settings file for the full factory.