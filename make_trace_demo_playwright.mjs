/**
 * TRACE Demo Video — Playwright screenshot capture
 * Takes real screenshots of the running app at 54.255.213.206:5173
 * and stitches them into a demo MP4 using ffmpeg.
 *
 * Usage:
 *   node make_trace_demo_playwright.mjs
 *
 * Output: dataset/demo-videos/TRACE_demo_video.mp4
 */

import { chromium } from 'playwright';
import { execSync } from 'child_process';
import { mkdirSync, writeFileSync, readdirSync, unlinkSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

const APP_URL = 'http://54.255.213.206:5173';
const OUT_VIDEO = 'dataset/demo-videos/TRACE_demo_video.mp4';
const FRAMES_DIR = join(tmpdir(), 'trace_demo_frames');
const W = 1280, H = 800;

mkdirSync(FRAMES_DIR, { recursive: true });

let frameN = 0;
async function shot(page, holdSeconds = 2) {
  const fps = 25;
  const frames = Math.round(holdSeconds * fps);
  const buf = await page.screenshot({ type: 'png' });
  for (let i = 0; i < frames; i++) {
    const name = `frame_${String(frameN++).padStart(6, '0')}.png`;
    writeFileSync(join(FRAMES_DIR, name), buf);
  }
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function waitAndShot(page, ms, fps = 25) {
  // Capture live-updating frames during wait
  const interval = Math.round(1000 / fps);
  const steps = Math.round(ms / interval);
  for (let i = 0; i < steps; i++) {
    const buf = await page.screenshot({ type: 'png' });
    writeFileSync(join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`), buf);
    await sleep(interval);
  }
}

(async () => {
  console.log('Launching browser...');
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: W, height: H } });
  const page = await ctx.newPage();

  // ── Scene 1: Home / Upload page ─────────────────────────────────────────
  console.log('[1/8] Home page...');
  await page.goto(APP_URL, { waitUntil: 'networkidle' });
  await sleep(1000);
  await shot(page, 3);  // hold 3s on landing page

  // Scroll down to show pipeline steps
  await page.evaluate(() => window.scrollBy(0, 300));
  await sleep(500);
  await shot(page, 2);

  // Scroll back up
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(400);
  await shot(page, 1);

  // ── Scene 2: Drag-over the upload zone (simulate hover) ──────────────────
  console.log('[2/8] Upload zone hover...');
  const dropzone = page.locator('.upload-dropzone, [class*="dropzone"], [class*="drop-area"]').first();
  try {
    await dropzone.hover({ timeout: 3000 });
    await sleep(300);
    await shot(page, 1.5);
  } catch { await shot(page, 1.5); }

  // ── Scene 3: Navigate to History page ────────────────────────────────────
  console.log('[3/8] History page...');
  await page.click('text=History');
  await page.waitForLoadState('networkidle');
  await sleep(1200);
  await shot(page, 3.5);

  // ── Scene 4: Click View on first history item (if any) ───────────────────
  console.log('[4/8] History → View...');
  const viewBtn = page.locator('button:has-text("View"), a:has-text("View")').first();
  const hasView = await viewBtn.count() > 0;
  if (hasView) {
    await viewBtn.click();
    await sleep(1500);
    await shot(page, 3);

    // ── Scene 5: Results page – scroll through steps ───────────────────────
    console.log('[5/8] Results page scroll...');
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(600);
    await shot(page, 2);
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(600);
    await shot(page, 2);

    // ── Scene 6: Generate SOP ─────────────────────────────────────────────
    console.log('[6/8] Generate SOP...');
    const sopBtn = page.locator('button:has-text("Generate SOP"), button:has-text("SOP")').first();
    if (await sopBtn.count() > 0) {
      // scroll SOP panel into view
      await sopBtn.scrollIntoViewIfNeeded();
      await sleep(400);
      await shot(page, 1);
      await sopBtn.click();
      // capture loading frames for up to 12s
      await waitAndShot(page, 8000);
      await sleep(800);
      await shot(page, 3);
    } else {
      await shot(page, 2);
    }

    // ── Scene 7: Model comparison tab ────────────────────────────────────
    console.log('[7/8] Model comparison...');
    const modelTab = page.locator('button:has-text("Models"), [role="tab"]:has-text("Model")').first();
    if (await modelTab.count() > 0) {
      await modelTab.scrollIntoViewIfNeeded();
      await modelTab.click();
      await sleep(800);
      await shot(page, 2.5);
    }
  } else {
    // No history — go back to upload and show upload state
    await page.click('text=Upload');
    await sleep(800);
    await shot(page, 3);
  }

  // ── Scene 8: Back to Upload page for outro ───────────────────────────────
  console.log('[8/8] Outro – upload page...');
  await page.click('text=Upload');
  await page.waitForLoadState('networkidle');
  await sleep(800);
  await shot(page, 3);

  await browser.close();
  console.log(`\nTotal frames: ${frameN}`);

  // ── Stitch into MP4 ──────────────────────────────────────────────────────
  console.log('Encoding video with ffmpeg...');
  execSync(`ffmpeg -y -framerate 25 -i "${FRAMES_DIR}/frame_%06d.png" \
    -vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2" \
    -c:v libx264 -crf 22 -preset medium -pix_fmt yuv420p \
    "${OUT_VIDEO}"`, { stdio: 'inherit' });

  // Cleanup frames
  readdirSync(FRAMES_DIR).forEach(f => unlinkSync(join(FRAMES_DIR, f)));
  console.log(`\nDone! Video saved to: ${OUT_VIDEO}`);
})();
