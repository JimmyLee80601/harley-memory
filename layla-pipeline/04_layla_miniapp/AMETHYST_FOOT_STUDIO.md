# AMETHYST FOOT STUDIO — Layla mini-app spec (lead-gen lane)
## SDK: @layla-network/sdk v7.5.0 (MIT) — verified against package + sdk-api.md

## WHAT IT DOES
A one-screen mini-app: pick a product (feet glam / soles / custom
footjob), pick the model (harleyfeet/amethyst-soles via
getImageGenerationModels()), tap generate -> on-device NPU image
in ~15-30s -> download / img2img from an S23 shot -> footer CTA:
"Custom content: amethystvoid.com / @AmethystVoid". Free in Browse
Apps. It is a LEAD MAGNET, not the store — the store is the
CivitAI packs and the customs channel.

## app.json (zip ROOT, flat layout — same as Daily Oracle)
{
  "title": "Amethyst Foot Studio",
  "tagline": "Your feet, her signature. 18+ on-device.",
  "description": "Generate Amethyst Void style foot and sole
content privately on your device. Lead-gen, brand, and demo for
HarleyFeet QNN packs.",
  "iconUri": "icon.png",
  "backgroundImgUri": "bg.png"
}
Zip = app.json + index.html + icon.png + bg.png at root, no parent
folder. Import: Layla -> Browse Apps -> upload zip -> Mini-Apps
Manager manages versions.

## SDK CORE (the whole image lane in 6 lines)
import { LaylaSDK } from "@layla-network/sdk";
const layla = new LaylaSDK();

async function amethyst() {
  const models = await layla.images.getImageGenerationModels();
  const harleyFeet = models.find(m => /harleyfeet/i.test(m.id + m.name));
  const img = await layla.images.generateImage(
    PROMPTS[product],                 // <=77-token prompt
    (status, step, total) => progress(step, total),
    sourceShot ? `data:image/png;base64,${sourceShot}` : undefined, // img2img
    harleyFeet?.id                      // modelId; omit -> host default
  );
  if (img) show(img);                   // data-URI string, ready to save
}

## PROGRESS / ERROR RULES
- onProgress -> (status, step, totalSteps); drive the UI bar.
- generateImage returns null on failure — show the CTA anyway.
- Abort: pass { signal: AbortController.signal }; catch
  LaylaAbortError. Never block the WebView on a 30s render.

## HARD LIMITS (verified, design around them)
- NO steps/CFG/seed/scheduler from the mini-app side. The Local
  Dream default (20 steps, CFG 7.5, dpm) applies. Prompt carries
  all quality. Our prompts are pre-cut for it.
- getImageGenerationModels() lists only DOWNLOADED models — if the
  user hasn't imported the pack, fall back to host default and
  show a "get the HarleyFeet pack" CTA linking the CivitAI URL.
- 77-token CLIP cap on-device.
- Browse Apps = free upload, NO revenue share today (verified
  against storefront API + help wiki + changelogs). Monetization:
  lead-gen to customs/CivitAI; optional future GachaSwipe-style
  in-app token gadget (only pattern that exists on the platform).

## SALES COPY (paste into description)
"Amethyst Foot Studio is a free taste of the Amethyst Void
catalog: private on-device generation, your rules, your device.
Want full custom sets? Visit amethystvoid.com. Supporting the
bench? The HarleyFeet QNN packs on CivitAI ARE the studio."

## NEXT BUILD (when the bench is back)
Companion "queue" mini-app driving the Local Dream HTTP API
(127.0.0.1:8081) for batch jobs with full sampler control —
plus a TOS/18+ gate screen and a "made with consent" line, same
as the Dell lane. Consent forms exist in the legal/ folder.