/**
 * TRACE Demo Video — Playwright screenshot capture
 * Order: Landing → Upload → Analysing → Results → Model Comparison → SOP → History
 *
 * Usage:  node make_trace_demo_playwright.mjs
 * Output: dataset/demo-videos/TRACE_demo_video.mp4
 */

import { chromium } from 'playwright';
import { execSync } from 'child_process';
import { mkdirSync, writeFileSync, readdirSync, unlinkSync, existsSync } from 'fs';
import { join, resolve, dirname } from 'path';
import { tmpdir } from 'os';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const APP_URL = process.env.APP_URL || 'http://localhost:5173';
const OUT_VIDEO = resolve(__dirname, 'dataset/demo-videos/TRACE_demo_video.mp4');
const FRAMES_DIR = join(tmpdir(), 'trace_demo_frames');
const W = 1280, H = 800;

const DEMO_CANDIDATES = [
  'dataset/demo-videos/demo_safe_coding_workflow.mp4',
  'dataset/demo-videos/demo_cicd_pipeline.mp4',
  'dataset/demo-videos/demo_kubernetes_ops.mp4',
];
const UPLOAD_FILE = DEMO_CANDIDATES.map(p => resolve(__dirname, p)).find(existsSync);
if (!UPLOAD_FILE) { console.error('No demo video found in dataset/demo-videos/'); process.exit(1); }
console.log(`Upload file: ${UPLOAD_FILE}`);

mkdirSync(FRAMES_DIR, { recursive: true });
mkdirSync(resolve(__dirname, 'dataset/demo-videos'), { recursive: true });

let frameN = 0;

async function shot(page, holdSeconds = 2) {
  const buf = await page.screenshot({ type: 'png' });
  const frames = Math.round(holdSeconds * 25);
  for (let i = 0; i < frames; i++)
    writeFileSync(join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`), buf);
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function liveCapture(page, ms) {
  const interval = 40; // 25 fps
  const end = Date.now() + ms;
  while (Date.now() < end) {
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

  // ── 1. LANDING PAGE ──────────────────────────────────────────────────────
  console.log('[1/7] Landing page...');
  await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await sleep(800);
  await shot(page, 3);                        // hero with upload zone

  await page.evaluate(() => window.scrollBy(0, 320));
  await sleep(500);
  await shot(page, 2.5);                      // pipeline steps + recognised activities

  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(400);

  // ── 2. UPLOAD VIDEO ───────────────────────────────────────────────────────
  console.log('[2/7] Uploading video...');
  // Hover dropzone to show active border
  try {
    const dz = page.locator('.upload-zone, label[class*="upload"], [class*="dropzone"]').first();
    await dz.hover({ timeout: 3000 });
    await sleep(500);
    await shot(page, 1.5);                    // hover state
  } catch { await shot(page, 1); }

  // Trigger file upload via hidden input
  await page.locator('input[type="file"]').setInputFiles(UPLOAD_FILE);
  await sleep(500);
  await shot(page, 1.5);                      // file selected / transitioning

  // ── 3. ANALYSING SCREEN (live capture) ───────────────────────────────────
  console.log('[3/7] Analysing screen...');
  // Wait for .analyzing class to appear (AnalyzingProgress component)
  try {
    await page.waitForSelector('.analyzing', { timeout: 8000 });
    console.log('  → Analyzing screen detected');
  } catch { console.log('  → Analyzing screen not found, continuing...'); }

  // Live capture until .results appears — up to 90s
  const analysisStart = Date.now();
  while (Date.now() - analysisStart < 90_000) {
    const buf = await page.screenshot({ type: 'png' });
    writeFileSync(join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`), buf);
    await sleep(40);
    // Only exit when .results div is present (exact class from VideoResults.tsx)
    const resultsReady = await page.locator('div.results').count();
    if (resultsReady > 0 && Date.now() - analysisStart > 5000) {
      console.log('  → Results page (.results) detected');
      break;
    }
  }
  await sleep(1000);

  // ── 4. RESULTS PAGE ───────────────────────────────────────────────────────
  console.log('[4/7] Results page...');
  await shot(page, 3);                        // top: video player + summary

  await page.evaluate(() => window.scrollBy(0, 380));
  await sleep(500);
  await shot(page, 2.5);                      // classified workflow steps

  await page.evaluate(() => window.scrollBy(0, 380));
  await sleep(400);
  await shot(page, 2);                        // more steps

  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(400);

  // ── 5. MODEL COMPARISON ───────────────────────────────────────────────────
  console.log('[5/7] Model comparison...');
  // Button text from VideoResults.tsx: "▼ Show Model Comparison (N classifiers)"
  const compBtn = page.locator('button:has-text("Show Model Comparison")').first();
  if (await compBtn.count() > 0) {
    await compBtn.scrollIntoViewIfNeeded();
    await sleep(400);
    await shot(page, 1);                      // button visible before click
    await compBtn.click();
    await sleep(600);
    await shot(page, 3);                      // comparison table expanded
    await page.evaluate(() => window.scrollBy(0, 300));
    await sleep(400);
    await shot(page, 2.5);                    // scroll through table rows
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(300);
  } else {
    console.log('  → Comparison button not found, scrolling to find it');
    await page.evaluate(() => window.scrollBy(0, 500));
    await sleep(400);
    await shot(page, 3);
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(300);
  }

  // ── 6. SOP GENERATION ────────────────────────────────────────────────────
  console.log('[6/7] SOP generation...');
  // Scroll down to KnowledgePanel — button text: "Generate SOP"
  const sopBtn = page.locator('button:has-text("Generate SOP")').first();
  if (await sopBtn.count() > 0) {
    await sopBtn.scrollIntoViewIfNeeded();
    await sleep(400);
    await shot(page, 1.5);                    // Generate SOP button visible
    await sopBtn.click();
    console.log('  → SOP generating... (live capture up to 20s)');
    await liveCapture(page, 12000);           // live capture while LLM writes
    await sleep(500);
    await shot(page, 3);                      // SOP document shown
    // Scroll through the SOP content
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(400);
    await shot(page, 2.5);
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(300);
  } else {
    console.log('  → SOP button not found, skipping');
  }

  // ── 7. HISTORY PAGE ───────────────────────────────────────────────────────
  console.log('[7/7] History page...');
  try {
    await page.click('text=History', { timeout: 5000 });
  } catch {
    try {
      await page.locator('nav a, .nav a').last().click({ timeout: 3000 });
    } catch { console.log('  → History nav click failed, continuing'); }
  }
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await sleep(1500);
  await shot(page, 4);                        // history table with newly analysed video

  await browser.close();
  const durationSec = Math.round(frameN / 25);
  console.log(`\nTotal frames: ${frameN} (~${durationSec}s / ${Math.round(durationSec/60)}m${durationSec%60}s video)`);

  // ── ENCODE ────────────────────────────────────────────────────────────────
  console.log('Encoding with ffmpeg...');
  execSync(
    `ffmpeg -y -framerate 25 -i "${FRAMES_DIR}/frame_%06d.png" ` +
    `-vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2" ` +
    `-c:v libx264 -crf 22 -preset medium -pix_fmt yuv420p "${OUT_VIDEO}"`,
    { stdio: 'inherit' }
  );

  readdirSync(FRAMES_DIR).forEach(f => unlinkSync(join(FRAMES_DIR, f)));
  console.log(`\nDone! → ${OUT_VIDEO}`);
})();
