import assert from 'node:assert/strict';
import test from 'node:test';

import { openUrlQueue } from '../url-queue.mjs';

test('opens each URL in order with a five-second wait between tabs', async () => {
  const urls = [
    'https://example.test/1',
    'https://example.test/2',
    'https://example.test/3',
    'https://example.test/4'
  ];
  const events = [];

  await openUrlQueue(urls, {
    intervalMs: 5000,
    openTab: async (createProperties) => events.push(['open', createProperties]),
    wait: async (milliseconds) => events.push(['wait', milliseconds]),
    onProgress: (opened, total) => events.push(['progress', opened, total])
  });

  assert.deepEqual(events, [
    ['open', { url: urls[0], active: false }],
    ['progress', 1, 4],
    ['wait', 5000],
    ['open', { url: urls[1], active: false }],
    ['progress', 2, 4],
    ['wait', 5000],
    ['open', { url: urls[2], active: false }],
    ['progress', 3, 4],
    ['wait', 5000],
    ['open', { url: urls[3], active: false }],
    ['progress', 4, 4]
  ]);
});
