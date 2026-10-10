/**
 * Clean browser DOM-based HTML sanitizer.
 * Safely strips script, object, embed, iframe and all inline event handlers (on*),
 * while preserving safe styling and formatting elements for artifact preview.
 */
export function sanitizeHtml(rawHtml: string): string {
  if (!rawHtml) return '';

  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(rawHtml, 'text/html');

    // Forbidden tags to remove entirely along with their contents
    const forbiddenTags = ['script', 'iframe', 'object', 'embed', 'link', 'base', 'meta'];
    forbiddenTags.forEach((tag) => {
      const elements = doc.querySelectorAll(tag);
      elements.forEach((el) => el.remove());
    });

    // Walk all remaining elements and clean attributes
    const allElements = doc.querySelectorAll('*');
    allElements.forEach((el) => {
      // Remove any attribute starting with 'on' (onclick, onload, onerror...)
      Array.from(el.attributes).forEach((attr) => {
        const attrName = attr.name.toLowerCase();
        const attrVal = attr.value.toLowerCase().trim();

        if (attrName.startsWith('on') || attrVal.startsWith('javascript:')) {
          el.removeAttribute(attr.name);
        }
      });
    });

    return doc.body.innerHTML || doc.documentElement.innerHTML;
  } catch (err) {
    console.error('sanitizeHtml fallback error:', err);
    // Simple regex fallback
    return rawHtml
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
      .replace(/\son\w+="[^"]*"/gi, '')
      .replace(/\son\w+='[^']*'/gi, '');
  }
}
