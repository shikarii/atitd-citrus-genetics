// Placeholder build script for Phase 2 Docker smoke tests.
// Phase 3 replaces this with Vite + React.
const fs = require("fs");
const path = require("path");

const dist = path.join(__dirname, "dist");
fs.mkdirSync(dist, { recursive: true });
fs.writeFileSync(
  path.join(dist, "index.html"),
  "<!DOCTYPE html><html><body><p>Citrus Genetics - dashboard pending (Phase 3)</p></body></html>\n",
);
