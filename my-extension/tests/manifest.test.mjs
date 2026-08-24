import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const manifestUrl = new URL('../manifest.json', import.meta.url);

test('toolbar action opens the Side Panel instead of a popup', async () => {
  const manifest = JSON.parse(await readFile(manifestUrl, 'utf8'));

  assert.equal(manifest.action.default_popup, undefined);
  assert.equal(manifest.side_panel.default_path, 'sidepanel.html');
  assert.ok(manifest.permissions.includes('sidePanel'));
});
