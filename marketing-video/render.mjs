import puppeteer from 'puppeteer-core';
import { mkdirSync } from 'node:fs';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const FPS = 30;
const outDir = path.resolve('frames');
mkdirSync(outDir, { recursive: true });

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME_PATH || '/usr/local/bin/google-chrome',
  headless: true,
  args: ['--no-sandbox', '--allow-file-access-from-files', '--hide-scrollbars'],
});
const page = await browser.newPage();
await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
await page.goto(pathToFileURL(path.resolve('index.html')).href, { waitUntil: 'networkidle0' });
await page.evaluate(() => document.fonts.ready);

const only = process.argv[2] ? process.argv[2].split(',').map(Number) : null;
const duration = await page.evaluate(() => window.DURATION);
const times = only ?? Array.from({ length: Math.round(duration * FPS) }, (_, i) => i / FPS);

for (let i = 0; i < times.length; i++) {
  await page.evaluate((t) => window.render(t), times[i]);
  const name = only ? `still_${times[i]}.jpg` : `f_${String(i).padStart(5, '0')}.jpg`;
  await page.screenshot({ path: path.join(outDir, name), type: 'jpeg', quality: 92 });
  if (i % 60 === 0) console.log(`frame ${i}/${times.length}`);
}
await browser.close();
