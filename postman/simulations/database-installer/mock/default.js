const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
http.createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (!url.pathname.startsWith('/download/')) { res.writeHead(501); res.end(); return; }
  const name = url.pathname.slice('/download/'.length);
  const cases = JSON.parse(fs.readFileSync(path.join(__dirname, 'cases.json'), 'utf8'));
  const test = cases[name];
  if (!test || url.searchParams.get('apiKey') !== 'TEST_ONLY_NOT_A_REAL_KEY' || [...url.searchParams.keys()].length !== 1) {
    res.writeHead(401); res.end('Unauthorized'); return;
  }
  const respond = () => { res.writeHead(test.status, {'Content-Type': 'application/zip'}); res.end(Buffer.from(test.body, 'base64')); };
  if (test.delay) setTimeout(respond, test.delay); else respond();
}).listen(process.env.PORT);
