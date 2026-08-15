export function formatSeconds(totalSeconds: number): string {
  const safe = Math.max(0, Math.floor(totalSeconds));
  const m = Math.floor(safe / 60);
  const s = safe % 60;
  const secStr = s < 10 ? '0' + s : String(s);
  return m + ':' + secStr;
}
