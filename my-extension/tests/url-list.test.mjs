import assert from 'node:assert/strict';
import test from 'node:test';

import { parseUrlList } from '../url-list.mjs';

test('parses HTTP and HTTPS URLs in their original order', () => {
  const result = parseUrlList(`
    https://akb48.zaiko.io/ja/e/first
    http://example.test/second?frame=2
  `);

  assert.deepEqual(result, {
    urls: [
      'https://akb48.zaiko.io/ja/e/first',
      'http://example.test/second?frame=2'
    ],
    invalidLines: []
  });
});

test('reports invalid and unsupported URLs with line numbers', () => {
  const result = parseUrlList('https://example.test\nnot-a-url\nfile:///tmp/page.html');

  assert.deepEqual(result.urls, ['https://example.test/']);
  assert.deepEqual(result.invalidLines, [
    { lineNumber: 2, value: 'not-a-url' },
    { lineNumber: 3, value: 'file:///tmp/page.html' }
  ]);
});

test('ignores empty lines', () => {
  assert.deepEqual(parseUrlList('\n  \n'), { urls: [], invalidLines: [] });
});
