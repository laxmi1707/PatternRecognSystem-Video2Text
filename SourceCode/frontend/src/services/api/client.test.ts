import { describe, it, expect, vi, afterEach } from 'vitest';
import { apiGet, apiPost, ApiError } from './client';

describe('apiGet', () => {
  afterEach(() => vi.restoreAllMocks());

  it('returns parsed JSON on success', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ data: 'test' }) } as Response),
    );
    const result = await apiGet<{ data: string }>('/test');
    expect(result).toEqual({ data: 'test' });
  });

  it('throws ApiError on non-OK response', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 404,
        statusText: 'Not Found',
        json: () => Promise.resolve({ detail: 'Not found' }),
      } as Response),
    );
    await expect(apiGet('/missing')).rejects.toThrow(ApiError);
    await expect(apiGet('/missing')).rejects.toThrow('API 404');
  });
});

describe('apiPost', () => {
  afterEach(() => vi.restoreAllMocks());

  it('sends query params on the URL', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ id: 1 }) } as Response),
    );
    await apiPost('/videos/upload', { original_filename: 'test.mp4', file_size_bytes: 100 });
    const calledUrl = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(calledUrl).toContain('original_filename=test.mp4');
    expect(calledUrl).toContain('file_size_bytes=100');
  });

  it('uses POST method', async () => {
    globalThis.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) } as Response),
    );
    await apiPost('/jobs/1/run');
    const calledOpts = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls[0][1] as RequestInit;
    expect(calledOpts.method).toBe('POST');
  });
});
