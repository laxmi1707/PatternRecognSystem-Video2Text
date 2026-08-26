import { describe, it, expect } from 'vitest';
import { formatSeconds } from './formatTime';

describe('formatSeconds', () => {
  it('formats zero seconds', () => {
    expect(formatSeconds(0)).toBe('0:00');
  });

  it('pads single-digit seconds', () => {
    expect(formatSeconds(67)).toBe('1:07');
  });

  it('handles whole minutes', () => {
    expect(formatSeconds(180)).toBe('3:00');
  });

  it('floors fractional seconds', () => {
    expect(formatSeconds(59.8)).toBe('0:59');
  });
});
