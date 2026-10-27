/**
 * TRACE Demo Video — Playwright screenshot capture
 *
 * Creates TWO demo videos:
 *   TRACE_demo_normal.mp4   — safe coding workflow (no anomalies)
 *   TRACE_demo_anomaly.mp4  — risk video with anomaly detection
 *
 * Scene order for both:
 *   1. Landing page
 *   2. Upload video
 *   3. Analysing screen (live progress bar)
 *   4. Results page (video + classified steps)
 *   5. Generate SOP → live capture → show document
 *   6. Report View (📝 Report View tab)
 *   7. Show Model Comparison
 *   8. History page
 *
 * Usage:  node make_trace_demo_playwright.mjs
 */

import { chromium } from 'playwright';
import { execSync } from 'child_process';
import { mkdirSync, writeFileSync, readdirSync, unlinkSync, existsSync } from 'fs';
import { join, resolve, dirname } from 'path';
import { tmpdir } from 'os';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const APP_URL   = process.env.APP_URL || 'http://localhost:5173';
const OUT_DIR   = resolve(__dirname, 'dataset/demo-videos');
const FRAMES_DIR = join(tmpdir(), 'trace_demo_frames');
const W = 1280, H = 800;

const NORMAL_VIDEO = [
  'dataset/demo-videos/demo_safe_coding_workflow.mp4',
  'dataset/demo-videos/demo_cicd_pipeline.mp4',
].map(p => resolve(__dirname, p)).find(existsSync);

const ANOMALY_VIDEO = [
  'dataset/demo-videos/risk_test_video.mp4',       // purpose-built: rm -rf, force-push, chmod 777, AWS key
  'dataset/demo-videos/demo_docker_risk.mp4',
  'dataset/demo-videos/demo_git_credential_leak.mp4',
  'dataset/demo-videos/demo_terraform_destroy.mp4',
].map(p => resolve(__dirname, p)).find(existsSync);

mkdirSync(OUT_DIR, { recursive: true });
mkdirSync(FRAMES_DIR, { recursive: true });

let frameN = 0;

function clearFrames() {
  try { readdirSync(FRAMES_DIR).forEach(f => unlinkSync(join(FRAMES_DIR, f))); } catch {}
  frameN = 0;
}

async function shot(page, holdSeconds = 2) {
  const buf = await page.screenshot({ type: 'png' });
  const frames = Math.round(holdSeconds * 25);
  for (let i = 0; i < frames; i++)
    writeFileSync(join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`), buf);
}

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function liveCapture(page, ms) {
  const interval = 40;
  const end = Date.now() + ms;
  while (Date.now() < end) {
    writeFileSync(
      join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`),
      await page.screenshot({ type: 'png' })
    );
    await sleep(interval);
  }
}

function encode(outFile) {
  console.log(`Encoding → ${outFile}`);
  execSync(
    `ffmpeg -y -framerate 25 -i "${FRAMES_DIR}/frame_%06d.png" ` +
    `-vf "scale=${W}:${H}:force_original_aspect_ratio=decrease,pad=${W}:${H}:(ow-iw)/2:(oh-ih)/2" ` +
    `-c:v libx264 -crf 22 -preset medium -pix_fmt yuv420p "${outFile}"`,
    { stdio: 'inherit' }
  );
}

async function recordDemo(page, uploadFile, label) {
  clearFrames();
  console.log(`\n===== Recording: ${label} =====`);

  // ── 1. LANDING PAGE ──────────────────────────────────────────────────────
  console.log('[1/8] Landing page...');
  await page.goto(APP_URL, { waitUntil: 'networkidle', timeout: 60000 });
  await sleep(800);
  await shot(page, 3);                        // hero

  await page.evaluate(() => window.scrollBy(0, 320));
  await sleep(500);
  await shot(page, 2.5);                      // pipeline + recognised activities panel

  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(400);

  // ── 2. UPLOAD VIDEO ───────────────────────────────────────────────────────
  console.log('[2/8] Uploading video...');
  try {
    const dz = page.locator('.upload-zone, label[class*="upload"], [class*="dropzone"]').first();
    await dz.hover({ timeout: 3000 });
    await sleep(500);
    await shot(page, 1.5);
  } catch { await shot(page, 1); }

  await page.locator('input[type="file"]').setInputFiles(uploadFile);
  await sleep(500);
  await shot(page, 1.5);                      // transitioning to analysing

  // ── 3. ANALYSING SCREEN ───────────────────────────────────────────────────
  console.log('[3/8] Analysing screen...');
  try {
    await page.waitForSelector('.analyzing', { timeout: 8000 });
    console.log('  → .analyzing detected');
  } catch { console.log('  → .analyzing not found, continuing'); }

  const analysisStart = Date.now();
  while (Date.now() - analysisStart < 90_000) {
    writeFileSync(
      join(FRAMES_DIR, `frame_${String(frameN++).padStart(6, '0')}.png`),
      await page.screenshot({ type: 'png' })
    );
    await sleep(40);
    if (await page.locator('div.results').count() > 0 && Date.now() - analysisStart > 5000) {
      console.log('  → div.results detected');
      break;
    }
  }
  await sleep(1000);

  // ── 4. RESULTS PAGE ───────────────────────────────────────────────────────
  console.log('[4/8] Results page...');
  await shot(page, 3);                        // video player + summary

  await page.evaluate(() => window.scrollBy(0, 380));
  await sleep(500);
  await shot(page, 2.5);                      // classified steps (with risk badges if anomaly)

  await page.evaluate(() => window.scrollBy(0, 380));
  await sleep(400);
  await shot(page, 2);

  await page.evaluate(() => window.scrollTo(0, 0));
  await sleep(400);

  // ── 5. GENERATE SOP ───────────────────────────────────────────────────────
  console.log('[5/8] Generate SOP...');
  const sopBtn = page.locator('button:has-text("Generate SOP")').first();
  if (await sopBtn.count() > 0) {
    await sopBtn.scrollIntoViewIfNeeded();
    await sleep(400);
    await shot(page, 1.5);                    // button visible
    await sopBtn.click();
    console.log('  → SOP generating (live 15s)...');
    await liveCapture(page, 15000);           // live while LLM writes
    await sleep(500);
    await shot(page, 3);                      // SOP document shown
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(400);
    await shot(page, 2.5);                    // scroll through SOP content
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(400);
  } else {
    console.log('  → SOP button not found');
  }

  // ── 6. REPORT VIEW ────────────────────────────────────────────────────────
  console.log('[6/8] Report View...');
  // Button text from VideoResults.tsx: "📝 Report View"
  const reportBtn = page.locator('button:has-text("Report View")').first();
  if (await reportBtn.count() > 0) {
    await reportBtn.scrollIntoViewIfNeeded();
    await sleep(300);
    await reportBtn.click();
    await sleep(1500);                        // report loads
    await shot(page, 3);                      // report document
    await page.evaluate(() => window.scrollBy(0, 400));
    await sleep(400);
    await shot(page, 2.5);
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(300);
    // Switch back to screen view for model comparison
    const screenBtn = page.locator('button:has-text("Screen View")').first();
    if (await screenBtn.count() > 0) await screenBtn.click();
    await sleep(400);
  } else {
    console.log('  → Report View button not found');
  }

  // ── 7. MODEL COMPARISON ───────────────────────────────────────────────────
  console.log('[7/8] Model comparison...');
  const compBtn = page.locator('button:has-text("Show Model Comparison")').first();
  if (await compBtn.count() > 0) {
    await compBtn.scrollIntoViewIfNeeded();
    await sleep(400);
    await shot(page, 1);
    await compBtn.click();
    await sleep(600);
    await shot(page, 3);                      // comparison table expanded
    await page.evaluate(() => window.scrollBy(0, 300));
    await sleep(400);
    await shot(page, 2.5);
    await page.evaluate(() => window.scrollTo(0, 0));
    await sleep(300);
  } else {
    console.log('  → Model comparison button not found');
    await page.evaluate(() => window.scrollBy(0, 500));
    await sleep(400);
    await shot(page, 3);
    await page.evaluate(() => window.scrollTo(0, 0));
  }

  // ── 8. HISTORY PAGE ───────────────────────────────────────────────────────
  console.log('[8/8] History page...');
  try {
    await page.click('text=History', { timeout: 5000 });
  } catch {
    try { await page.locator('nav a, .nav a').last().click({ timeout: 3000 }); } catch {}
  }
  await page.waitForLoadState('networkidle', { timeout: 15000 }).catch(() => {});
  await sleep(1500);
  await shot(page, 4);

  const sec = Math.round(frameN / 25);
  console.log(`Total frames: ${frameN} (~${Math.floor(sec/60)}m${sec%60}s)`);
}

(async () => {
  if (!NORMAL_VIDEO)  { console.error('Normal demo video not found'); process.exit(1); }
  if (!ANOMALY_VIDEO) { console.error('Anomaly demo video not found'); process.exit(1); }

  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: W, height: H } });
  const page = await ctx.newPage();

  // ── VIDEO 1: Normal (no anomalies) ────────────────────────────────────────
  await recordDemo(page, NORMAL_VIDEO, 'NORMAL — safe coding workflow');
  encode(join(OUT_DIR, 'TRACE_demo_normal.mp4'));

  // ── VIDEO 2: Anomaly detected ─────────────────────────────────────────────
  await recordDemo(page, ANOMALY_VIDEO, 'ANOMALY — risk video');
  encode(join(OUT_DIR, 'TRACE_demo_anomaly.mp4'));

  await browser.close();
  console.log('\n✓ Done!');
  console.log(`  Normal : ${join(OUT_DIR, 'TRACE_demo_normal.mp4')}`);
  console.log(`  Anomaly: ${join(OUT_DIR, 'TRACE_demo_anomaly.mp4')}`);
})();
