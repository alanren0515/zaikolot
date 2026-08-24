export function parseUrlList(input) {
  const urls = [];
  const invalidLines = [];

  String(input).split(/\r?\n/).forEach((rawLine, index) => {
    const value = rawLine.trim();

    if (!value) {
      return;
    }

    try {
      const url = new URL(value);

      if (url.protocol !== 'http:' && url.protocol !== 'https:') {
        throw new TypeError('Unsupported URL protocol');
      }

      urls.push(url.href);
    } catch {
      invalidLines.push({ lineNumber: index + 1, value });
    }
  });

  return { urls, invalidLines };
}
