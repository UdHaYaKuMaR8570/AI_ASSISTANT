import { describe, it, expect } from 'vitest';
import { sanitizeHtml } from './sanitize';

describe('sanitizeHtml', () => {
  it('strips malicious script tags', () => {
    const dirty = '<div>Hello <script>alert("hack")</script>world</div>';
    const clean = sanitizeHtml(dirty);
    expect(clean).not.toContain('<script>');
    expect(clean).not.toContain('alert');
    expect(clean).toContain('Hello');
    expect(clean).toContain('world');
  });

  it('strips inline onerror handlers', () => {
    const dirty = '<img src="x" onerror="alert(1)" />';
    const clean = sanitizeHtml(dirty);
    expect(clean).not.toContain('onerror');
  });

  it('allows safe HTML markup and styles', () => {
    const safe = '<div class="card" style="color: red;"><p>Safe text</p></div>';
    const clean = sanitizeHtml(safe);
    expect(clean).toContain('Safe text');
    expect(clean).toContain('style="color: red;"');
  });
});
