/**
 * TRACE Demo Video — Playwright screenshot capture
 * Visits the live app, uploads a real video, waits for analysis,
 * then captures every step into an MP4.
 *
 * Usage:
 *   node make_trace_demo_playwright.mjs
 *
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

// Pick a demo video to upload — prefer a coding/safe one for the demo
const DEMO_CANDIDATES = [
  'dataset/demo-videos/demo_safe_coding_workflow.mp4',
  'dataset/demo-videos/demo_cicd_pipeline.mp4',
  'dataset/demo-videos/demo_kubernetes_ops.mp4',
];
const UPLOAD_FILE = DEMO_CANDIDATES.map(p => resolve(__dirname, p)).find(existsSync);
if (!UPLOAD_FILE) {
  console.error('No demo video found in dataset/demo-videos/ to upload. Add one first.');
  process.exit(1);
}
console.log(`Using upload file: ${UPLOAD_FILE}`);

mkdirSync(FRAMES_DIR, { recursive: true });
mkdirSync(resolve(__dirname, 'dataset/demo-videos'), { recursive: true });

let frameN = 0;

async function shot(page, holdSeconds = 2) {
  const frames = Math.round(holdSeconds * 25);
  const buf = await page.screenshot({ type: 'png' });
  for (let i = 0; i < frames; i++) {
    writeFileSync(join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`), buf);
  }
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function liveCapture(page, ms) {
  const interval = 40; // 25 fps
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

  // ── Scene 1: Landing page — 4s ──────────────────────────────────────────
  console.log('[1/9] Landing page...');
  await page.goto(APP_URL, { waitUntil: 'networkidle' });
  await sleep(800);
  await shot(page, 3);

  // Scroll to show pipeline steps panel on right
  await page.evaluate(() => window.scrollBy(0, 280));
  await sleep(400);
  await shot(page, 2);
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(300);

  // ── Scene 2: Hover over dropzone ────────────────────────────────────────
  console.log('[2/9] Dropzone hover...');
  try {
    const dz = page.locator('label[for], .upload-zone, [class*="dropzone"], [class*="drop"]').first();
    await dz.hover({ timeout: 3000 });
    await sleep(300);
    await shot(page, 1.5);
  } catch { await shot(page, 1); }

  // ── Scene 3: Upload a real video file ───────────────────────────────────
  console.log('[3/9] Uploading video...');
  const fileInput = page.locator('input[type="file"]');
  await fileInput.setInputFiles(UPLOAD_FILE);
  await sleep(600);
  await shot(page, 1.5);

  // ── Scene 4: Analyzing progress screen — live capture up to 90s ─────────
  console.log('[4/9] Analyzing... (this may take a while)');
  // Wait for the analyzing screen to appear
  try {
    await page.waitForSelector('[class*="analyzing"], [class*="progress"], text=Analysing', { timeout: 8000 });
  } catch { /* already past that screen or different class */ }

  // Capture live frames during analysis (up to 90 seconds)
  const analysisStart = Date.now();
  const MAX_ANALYSIS_MS = 90_000;
  while (Date.now() - analysisStart < MAX_ANALYSIS_MS) {
    const buf = await page.screenshot({ type: 'png' });
    writeFileSync(join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`), buf);
    await sleep(40);
    // Check if results page appeared
    const onResults = await page.locator('[class*="results"], [class*="workflow"], h2:has-text("Classified")').count();
    if (onResults > 0) { console.log('  → Results page detected'); break; }
    // Also check for result indicators
    const hasSteps = await page.locator('[class*="step"], [class*="timeline"]').count();
    if (hasSteps > 0 && Date.now() - analysisStart > 5000) { console.log('  → Steps detected'); break; }
  }
  await sleep(1000);
  await shot(page, 1);

  // ── Scene 5: Results page — video + classified steps ────────────────────
  console.log('[5/9] Results page...');
  await shot(page, 3);

  // Scroll through the step list
  await page.evaluate(() => window.scrollBy(0, 350));
  await sleep(500);
  await shot(page, 2);
  await page.evaluate(() => window.scrollBy(0, 350));
  await sleep(500);
  await shot(page, 2);
  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(300);

  // ── Scene 6: Generate SOP ────────────────────────────────────────────────
  console.log('[6/9] Generate SOP...');
  const sopBtn = page.locator('button:has-text("Generate SOP"), button:has-text("SOP")').first();
  if (await sopBtn.count() > 0) {
    await sopBtn.scrollIntoViewIfNeeded();
    await sleep(400);
    await shot(page, 1);
    await sopBtn.click();
    await liveCapture(page, 10000); // live capture while LLM generates
    await shot(page, 3);
    // Scroll to read the SOP
    await page.evaluate(() => window.scrollBy(0, 300));
    await sleep(400);
    await shot(page, 2);
  } else {
    await shot(page, 2);
  }

  // ── Scene 7: Generate Runbook ────────────────────────────────────────────
  console.log('[7/9] Generate Runbook...');
  const runbookBtn = page.locator('button:has-text("Runbook"), button:has-text("Generate Runbook")').first();
  if (await runbookBtn.count() > 0) {
    await runbookBtn.scrollIntoViewIfNeeded();
    await sleep(300);
    await runbookBtn.click();
    await liveCapture(page, 8000);
    await shot(page, 2.5);
  }

  // ── Scene 8: History page ────────────────────────────────────────────────
  console.log('[8/9] History page...');
  try {
    await page.click('text=History', { timeout: 5000 });
  } catch {
    try { await page.locator('nav a:last-child, .nav a:last-child').click({ timeout: 3000 }); } catch { /* skip */ }
  }
  await page.waitForLoadState('networkidle');
  await sleep(1200);
  await shot(page, 3);

  // ── Scene 9: Outro — back to upload ─────────────────────────────────────
  console.log('[9/9] Outro...');
  try {
    await page.click('text=Upload', { timeout: 5000 });
  } catch {
    // Try nav link fallback
    try { await page.locator('nav a, .nav a').first().click({ timeout: 3000 }); } catch { /* already there */ }
  }
  await sleep(800);
  await shot(page, 3);

  await browser.close();
  console.log(`\nTotal frames: ${frameN} (~${Math.round(frameN / 25)}s video)`);

  // ── Encode MP4 ────────────────────────────────────────────────────────────
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
