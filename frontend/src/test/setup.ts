import '@testing-library/jest-dom';

if (!('createObjectURL' in URL)) {
  // @ts-expect-error jsdom polyfill
  URL.createObjectURL = () => 'blob:mock-url';
}
if (!('revokeObjectURL' in URL)) {
  // @ts-expect-error jsdom polyfill
  URL.revokeObjectURL = () => {};
}
URL.createObjectURL = vi.fn(() => 'blob:mock-url');
URL.revokeObjectURL = vi.fn();
