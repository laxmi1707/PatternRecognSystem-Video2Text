/**
 * TRACE Demo Video — Playwright screenshot capture
 * Order: Landing → Upload → Analysing → Results → Model Comparison → History
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
if (!UPLOAD_FILE) { console.error('No demo video found.'); process.exit(1); }
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
  console.log('[1/6] Landing page...');
  await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await sleep(800);
  await shot(page, 3);                         // hold on hero

  await page.evaluate(() => window.scrollBy(0, 300));
  await sleep(400);
  await shot(page, 2);                         // show pipeline steps panel

  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(300);
  await shot(page, 1);

  // ── 2. UPLOAD VIDEO ───────────────────────────────────────────────────────
  console.log('[2/6] Uploading video...');
  // Hover dropzone to show active state
  try {
    const dz = page.locator('label, [class*="drop"], [class*="upload-zone"]').first();
    await dz.hover({ timeout: 3000 });
    await sleep(400);
    await shot(page, 1.5);
  } catch { await shot(page, 1); }

  // Set the file on the hidden input
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(UPLOAD_FILE);
  await sleep(600);
  await shot(page, 1.5);                       // show file selected state

  // ── 3. ANALYSING SCREEN ───────────────────────────────────────────────────
  console.log('[3/6] Analysing... (live capture until results appear)');
  try {
    await page.waitForSelector(
      '[class*="analyz"], [class*="progress"], [class*="Processing"]',
      { timeout: 8000 }
    );
  } catch { /* might transition fast */ }

  // Capture live frames — up to 90s — until results page appears
  const start = Date.now();
  while (Date.now() - start < 90_000) {
    const buf = await page.screenshot({ type: 'png' });
    writeFileSync(join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`), buf);
    await sleep(40);
    const done = await page.locator(
      '[class*="result"], [class*="workflow"], [class*="step"], h2'
    ).count();
    if (done > 0 && Date.now() - start > 5000) { console.log('  → Results detected'); break; }
  }
  await sleep(800);

  // ── 4. RESULTS PAGE ───────────────────────────────────────────────────────
  console.log('[4/6] Results page...');
  await shot(page, 3);                         // top of results with video

  await page.evaluate(() => window.scrollBy(0, 350));
  await sleep(500);
  await shot(page, 2.5);                       // classified steps list

  await page.evaluate(() => window.scrollBy(0, 350));
  await sleep(400);
  await shot(page, 2);                         // more steps

  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(300);

  // ── 5. MODEL COMPARISON ───────────────────────────────────────────────────
  console.log('[5/6] Model comparison...');
  // Try clicking a Models / Comparison tab
  const modelTab = page.locator(
    'button:has-text("Model"), button:has-text("Comparison"), [role="tab"]:has-text("Model")'
  ).first();
  if (await modelTab.count() > 0) {
    await modelTab.scrollIntoViewIfNeeded();
    await sleep(300);
    await shot(page, 1);
    await modelTab.click();
    await sleep(800);
    await shot(page, 3);
    // Scroll through comparison table
    await page.evaluate(() => window.scrollBy(0, 300));
    await sleep(400);
    await shot(page, 2);
  } else {
    // Scroll to wherever model comparison is rendered on the page
    await page.evaluate(() => window.scrollBy(0, 600));
    await sleep(500);
    await shot(page, 3);
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(400);
    await shot(page, 2);
  }
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(300);

  // ── 6. HISTORY PAGE ───────────────────────────────────────────────────────
  console.log('[6/6] History page...');
  try {
    await page.click('text=History', { timeout: 5000 });
  } catch {
    try { await page.locator('nav a, .nav a').last().click({ timeout: 3000 }); } catch { /* skip */ }
  }
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await sleep(1200);
  await shot(page, 4);                         // history table with newly analysed video

  await browser.close();
  console.log(`\nTotal frames: ${frameN} (~${Math.round(frameN / 25)}s video)`);

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
