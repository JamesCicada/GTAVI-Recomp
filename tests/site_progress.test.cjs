const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

test("Pages rounds progress like the README generator", () => {
  const source = readFileSync(path.join(__dirname, "../site/app.js"), "utf8");
  // Keep the page's data request pending while exercising its formatter.
  const page = { fetch: () => new Promise(() => {}) };
  vm.runInNewContext(source, page);

  assert.equal(page.pct(0, 0), 0);
  assert.equal(page.pct(0, 8), 0);
  assert.equal(page.pct(1, 8), 12);
  assert.equal(page.pct(3, 8), 38);
  assert.equal(page.pct(5, 8), 62);
  assert.equal(page.pct(2, 3), 67);
  assert.equal(page.pct(8, 8), 100);
});
